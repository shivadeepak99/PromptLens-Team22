"""
Temporary Test API (FastAPI)
Local API for testing ML models before production API is built
Replace this entirely with the production API implementation
"""

import os
import json
import psycopg2
import pandas as pd
import numpy as np
import joblib
import yaml
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure
CONFIG_FILE = "ml_service/config.yaml"
MODELS_DIR = "ml_service/models"

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

db_config = config['database']

# Load trained models
print("[API Startup] Loading models...")
try:
    scaler = joblib.load(f"{MODELS_DIR}/feature_scaler.pkl")
    pca = joblib.load(f"{MODELS_DIR}/pca_transformer.pkl")
    kmeans = joblib.load(f"{MODELS_DIR}/kmeans_clusterer.pkl")
    rf_model = joblib.load(f"{MODELS_DIR}/rf_classifier.pkl")
    
    with open(f"{MODELS_DIR}/training_summary.json", 'r') as f:
        training_summary = json.load(f)
    
    with open(f"{MODELS_DIR}/association_rules.json", 'r') as f:
        association_rules = json.load(f)
    
    print("[API Startup] ✓ All models loaded successfully")
except Exception as e:
    print(f"[API Startup] ✗ Failed to load models: {e}")
    exit(1)

# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(
    title="PromptLens ML Test API (TEMPORARY)",
    description="Temporary testing API for ML models. Will be replaced by production API.",
    version="0.1.0"
)

# Enable CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class PromptFeatures(BaseModel):
    """Features for a single prompt"""
    prompt_text: str = Field(..., description="The prompt text")
    prompt_length: int = Field(..., description="Character count")
    token_count: Optional[int] = Field(100, description="Estimated token count")
    contains_code: bool = Field(False, description="Has code blocks")
    contains_examples: bool = Field(False, description="Has examples")
    contains_constraints: bool = Field(False, description="Has constraints")
    language: str = Field("english", description="Language")
    complexity_score: Optional[float] = Field(0.5, description="Complexity rating 0-1")
    instruction_density: Optional[float] = Field(0.5, description="Instruction density 0-1")

class SuccessPredictionResponse(BaseModel):
    """Success prediction response"""
    success_probability: float = Field(..., description="Predicted success probability 0-1")
    confidence_level: str = Field(..., description="high/medium/low")
    model_type: str = "ensemble_rf_xgb"
    features_used: int

class ClusteringResponse(BaseModel):
    """Clustering response"""
    cluster_id: int = Field(..., description="Cluster ID (0-3)")
    cluster_name: str = Field(..., description="Cluster name")
    silhouette_score: float = Field(..., description="Silhouette coefficient")

class AssociationRule(BaseModel):
    """Association rule"""
    antecedents: str
    consequents: str
    support: float
    confidence: float
    lift: float

class AssociationRulesResponse(BaseModel):
    """Association rules response"""
    total_rules: int
    top_rules: List[AssociationRule]
    avg_confidence: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    api_type: str
    timestamp: str
    models_loaded: int

# ============================================================================
# Helper Functions
# ============================================================================

def get_db_connection():
    """Create PostgreSQL connection"""
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            dbname=db_config['dbname'],
            user=db_config['user'],
            password=db_config['password'],
            connect_timeout=5
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")

def prepare_features(features: PromptFeatures) -> np.ndarray:
    """Convert PromptFeatures to feature array"""
    # Build feature array matching training data structure
    feature_dict = {
        'prompt_length': features.prompt_length,
        'token_estimate': features.token_count or 100,
        'instruction_density': features.instruction_density or 0.5,
        'complexity_score': features.complexity_score or 0.5,
        'tokens_used': features.token_count or 100,
        'contains_code': int(features.contains_code),
        'contains_examples': int(features.contains_examples),
        'contains_constraints': int(features.contains_constraints),
        'latency_ms': 100,  # Placeholder
        'attempt_count': 1  # Placeholder
    }
    
    feature_array = np.array([list(feature_dict.values())])
    return feature_array

class ClusterName:
    """Cluster naming"""
    NAMES = {
        0: "Simple & Short",
        1: "Complex & Detailed",
        2: "Code Snippets",
        3: "Example-Rich"
    }
    
    @staticmethod
    def get(cluster_id: int) -> str:
        return ClusterName.NAMES.get(cluster_id, "Unknown")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Testing"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        api_type="temporary_test_api",
        timestamp=datetime.now().isoformat(),
        models_loaded=4  # scaler, pca, kmeans, rf_model
    )

@app.get("/info", tags=["Testing"])
async def api_info():
    """API information"""
    return {
        "api": "PromptLens ML Test API",
        "warning": "TEMPORARY - Will be replaced by production API",
        "models": {
            "classification": training_summary.get("random_forest", {}).get("test", {}),
            "clustering": training_summary.get("clustering", {}).get("evaluation", {}),
            "association_rules": training_summary.get("association_rules", {}).get("results", {})
        },
        "endpoints": [
            "/ml/success-prediction",
            "/ml/prompt-clusters",
            "/ml/association-rules"
        ]
    }

@app.post("/ml/success-prediction", response_model=SuccessPredictionResponse, tags=["ML"])
async def predict_success(features: PromptFeatures):
    """
    Predict prompt execution success probability
    
    Returns: Success probability (0-1) using Random Forest model
    """
    try:
        # Prepare features
        X = prepare_features(features)
        
        # Make prediction
        probability = rf_model.predict(X)[0]
        probability = max(0.0, min(1.0, probability))  # Clamp to [0, 1]
        
        # Determine confidence level
        if probability > 0.7:
            confidence = "high"
        elif probability > 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        return SuccessPredictionResponse(
            success_probability=float(probability),
            confidence_level=confidence,
            features_used=X.shape[1]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ml/prompt-clusters", response_model=ClusteringResponse, tags=["ML"])
async def cluster_prompt(features: PromptFeatures):
    """
    Assign prompt to cluster
    
    Returns: Cluster ID (0-3) and cluster name
    """
    try:
        # Prepare features
        X = prepare_features(features)
        
        # Scale and reduce dimensions
        X_scaled = scaler.transform(X)
        X_pca = pca.transform(X_scaled)
        
        # Get cluster
        cluster_id = int(kmeans.predict(X_pca)[0])
        cluster_name = ClusterName.get(cluster_id)
        
        # Get silhouette info from summary
        silhouette = training_summary.get("clustering", {}).get("evaluation", {}).get("silhouette_score", 0.0)
        
        return ClusteringResponse(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            silhouette_score=float(silhouette)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/ml/association-rules", response_model=AssociationRulesResponse, tags=["ML"])
async def get_association_rules(limit: int = 20):
    """
    Get top association rules
    
    Returns: Top rules sorted by lift
    """
    try:
        top_rules = association_rules[:min(limit, len(association_rules))]
        
        rules_list = [
            AssociationRule(
                antecedents=rule['antecedents'],
                consequents=rule['consequents'],
                support=rule['support'],
                confidence=rule['confidence'],
                lift=rule['lift']
            )
            for rule in top_rules
        ]
        
        avg_confidence = np.mean([r['confidence'] for r in top_rules]) if top_rules else 0.0
        
        return AssociationRulesResponse(
            total_rules=len(association_rules),
            top_rules=rules_list,
            avg_confidence=float(avg_confidence)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# Database Query Endpoints (for testing integration with PostgreSQL)
# ============================================================================

@app.get("/db/model-performance", tags=["Database"])
async def get_model_performance():
    """
    Query model performance from PostgreSQL
    Uses materialized view: mv_model_performance_arena
    """
    try:
        conn = get_db_connection()
        query = "SELECT * FROM mv_model_performance_arena ORDER BY avg_success DESC LIMIT 10;"
        df = pd.read_sql(query, conn)
        conn.close()
        
        return {
            "source": "mv_model_performance_arena",
            "rows": len(df),
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/language-performance", tags=["Database"])
async def get_language_performance():
    """
    Query language performance from PostgreSQL
    Uses materialized view: mv_language_performance
    """
    try:
        conn = get_db_connection()
        query = "SELECT * FROM mv_language_performance ORDER BY avg_success DESC LIMIT 10;"
        df = pd.read_sql(query, conn)
        conn.close()
        
        return {
            "source": "mv_language_performance",
            "rows": len(df),
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/daily-execution-summary", tags=["Database"])
async def get_daily_summary():
    """
    Query daily execution summary from PostgreSQL
    Uses materialized view: mv_daily_model_success
    """
    try:
        conn = get_db_connection()
        query = "SELECT * FROM mv_daily_model_success ORDER BY execution_date DESC LIMIT 30;"
        df = pd.read_sql(query, conn)
        conn.close()
        
        return {
            "source": "mv_daily_model_success",
            "rows": len(df),
            "data": df.to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting PromptLens ML Test API")
    print(f"{'='*60}")
    print(f"\n📍 Server: http://localhost:8000")
    print(f"📚 Docs:   http://localhost:8000/docs")
    print(f"🔄 ReDoc:  http://localhost:8000/redoc")
    print(f"\n⚠️  IMPORTANT: This is a TEMPORARY test API.")
    print(f"   This will be replaced by the production API.")
    print(f"   Use this to test ML models locally.\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
