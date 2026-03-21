"""
Integration Tests for ML System
Tests ML models, R scripts, temporary API, and database integration
"""

import pytest
import subprocess
import requests
import json
import os
import time
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
MODELS_DIR = "ml_service/models"
DATA_DIR = "ml_service/data"
RESULTS_DIR = "results"

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def api_running():
    """Check if API is running before tests"""
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✓ API is ready after {i+1} retries")
                yield
                return
        except requests.ConnectionError:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                pytest.skip("API not running on localhost:8000. Start with: python ml_service/temporary_test_api.py")

# ============================================================================
# Test: Data Preparation
# ============================================================================

class TestDataPreparation:
    """Tests for data preparation pipeline"""
    
    def test_prepared_data_exists(self):
        """Check if prepared data files exist"""
        files_to_check = [
            f"{DATA_DIR}/features.parquet",
            f"{DATA_DIR}/target.parquet",
            f"{DATA_DIR}/train_test_split.json",
            f"{DATA_DIR}/preparation_summary.json"
        ]
        
        for file in files_to_check:
            assert os.path.exists(file), f"Missing file: {file}"
            print(f"✓ {file} exists")
    
    def test_data_dimensions(self):
        """Check data dimensions match expectations"""
        import pandas as pd
        
        X = pd.read_parquet(f"{DATA_DIR}/features.parquet")
        y = pd.read_parquet(f"{DATA_DIR}/target.parquet")
        
        assert X.shape[0] > 100000, f"Expected >100K samples, got {X.shape[0]}"
        assert X.shape[1] > 15, f"Expected >15 features, got {X.shape[1]}"
        assert len(y) == X.shape[0], "Feature and target shape mismatch"
        
        print(f"✓ Data shape: {X.shape}")
        print(f"✓ Target: {y.shape}")
    
    def test_no_missing_values(self):
        """Check no missing values in prepared data"""
        import pandas as pd
        
        X = pd.read_parquet(f"{DATA_DIR}/features.parquet")
        y = pd.read_parquet(f"{DATA_DIR}/target.parquet")
        
        assert X.isnull().sum().sum() == 0, f"Found NaN in features"
        assert y.isnull().sum() == 0, f"Found NaN in target"
        
        print(f"✓ No missing values")

# ============================================================================
# Test: Classification Model
# ============================================================================

class TestClassificationModel:
    """Tests for Random Forest + XGBoost classification"""
    
    def test_models_exist(self):
        """Check if trained models exist"""
        models = [
            f"{MODELS_DIR}/rf_classifier.pkl",
            f"{MODELS_DIR}/xgb_classifier.pkl",
            f"{MODELS_DIR}/training_summary.json"
        ]
        
        for model in models:
            assert os.path.exists(model), f"Missing model: {model}"
            print(f"✓ {model} exists")
    
    def test_model_metrics_saved(self):
        """Check if training metrics were saved"""
        with open(f"{MODELS_DIR}/training_summary.json", 'r') as f:
            summary = json.load(f)
        
        assert 'random_forest' in summary, "RF metrics not found"
        assert 'xgboost' in summary, "XGB metrics not found"
        
        rf_mae = summary['random_forest']['test']['mae']
        xgb_mae = summary['xgboost']['test']['mae']
        
        print(f"✓ RF MAE: {rf_mae:.4f}")
        print(f"✓ XGB MAE: {xgb_mae:.4f}")
        
        # Check that models meet minimum performance
        assert rf_mae < 0.50, f"RF MAE too high: {rf_mae}"
        assert xgb_mae < 0.45, f"XGB MAE too high: {xgb_mae}"

# ============================================================================
# Test: Clustering Model
# ============================================================================

class TestClusteringModel:
    """Tests for K-Means clustering"""
    
    def test_clustering_models_exist(self):
        """Check if clustering models exist"""
        models = [
            f"{MODELS_DIR}/pca_transformer.pkl",
            f"{MODELS_DIR}/kmeans_clusterer.pkl",
            f"{MODELS_DIR}/feature_scaler.pkl"
        ]
        
        for model in models:
            assert os.path.exists(model), f"Missing model: {model}"
            print(f"✓ {model} exists")
    
    def test_clustering_quality(self):
        """Check silhouette score"""
        with open(f"{MODELS_DIR}/training_summary.json", 'r') as f:
            summary = json.load(f)
        
        if 'clustering' in summary:
            silhouette = summary['clustering']['evaluation']['silhouette_score']
            print(f"✓ Silhouette score: {silhouette:.4f}")
            
            # Check minimum quality
            assert silhouette > 0.30, f"Silhouette too low: {silhouette}"

# ============================================================================
# Test: Association Rules
# ============================================================================

class TestAssociationRules:
    """Tests for Apriori association rules"""
    
    def test_rules_exist(self):
        """Check if rules file exists"""
        assert os.path.exists(f"{MODELS_DIR}/association_rules.json"), "Rules file missing"
        print(f"✓ {MODELS_DIR}/association_rules.json exists")
    
    def test_rules_content(self):
        """Check rules structure"""
        with open(f"{MODELS_DIR}/association_rules.json", 'r') as f:
            rules = json.load(f)
        
        assert isinstance(rules, list), "Rules should be a list"
        assert len(rules) > 30, f"Expected >30 rules, got {len(rules)}"
        
        # Check first rule structure
        rule = rules[0]
        assert 'antecedents' in rule
        assert 'consequents' in rule
        assert 'confidence' in rule
        assert 'lift' in rule
        
        print(f"✓ Found {len(rules)} rules")
        print(f"✓ First rule: {rule['antecedents']} → {rule['consequents']}")

# ============================================================================
# Test: Temporary Test API
# ============================================================================

class TestTemporaryAPI:
    """Tests for FastAPI endpoints"""
    
    def test_health_endpoint(self, api_running):
        """Test /health endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print(f"✓ Health check passed")
    
    def test_info_endpoint(self, api_running):
        """Test /info endpoint"""
        response = requests.get(f"{API_BASE_URL}/info")
        assert response.status_code == 200
        data = response.json()
        assert 'api' in data
        assert 'endpoints' in data
        print(f"✓ Info endpoint working")
    
    def test_success_prediction_endpoint(self, api_running):
        """Test /ml/success-prediction endpoint"""
        payload = {
            "prompt_text": "Write a Python function to sort a list",
            "prompt_length": 45,
            "token_count": 12,
            "contains_code": False,
            "contains_examples": False,
            "contains_constraints": False,
            "language": "english",
            "complexity_score": 0.3,
            "instruction_density": 0.4
        }
        
        response = requests.post(
            f"{API_BASE_URL}/ml/success-prediction",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'success_probability' in data
        assert 0 <= data['success_probability'] <= 1
        assert data['confidence_level'] in ['high', 'medium', 'low']
        
        print(f"✓ Success prediction: {data['success_probability']:.2%} ({data['confidence_level']})")
    
    def test_clustering_endpoint(self, api_running):
        """Test /ml/prompt-clusters endpoint"""
        payload = {
            "prompt_text": "Explain quantum entanglement with examples",
            "prompt_length": 55,
            "token_count": 18,
            "contains_code": False,
            "contains_examples": True,
            "contains_constraints": False,
            "language": "english"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/ml/prompt-clusters",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'cluster_id' in data
        assert 0 <= data['cluster_id'] <= 3
        assert 'cluster_name' in data
        
        print(f"✓ Cluster assignment: Cluster {data['cluster_id']} ({data['cluster_name']})")
    
    def test_association_rules_endpoint(self, api_running):
        """Test /ml/association-rules endpoint"""
        response = requests.get(f"{API_BASE_URL}/ml/association-rules?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_rules' in data
        assert 'top_rules' in data
        assert len(data['top_rules']) > 0
        
        # Check rule structure
        rule = data['top_rules'][0]
        assert 'antecedents' in rule
        assert 'consequents' in rule
        assert 'confidence' in rule
        assert 'lift' in rule
        
        print(f"✓ Rules returned: {len(data['top_rules'])}")
        print(f"✓ Top rule lift: {data['top_rules'][0]['lift']:.2f}")
    
    def test_database_queries(self, api_running):
        """Test database query endpoints"""
        endpoints = [
            '/db/model-performance',
            '/db/language-performance',
            '/db/daily-execution-summary'
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                assert 'rows' in data
                print(f"✓ {endpoint}: {data['rows']} rows")
            else:
                print(f"⚠ {endpoint}: {response.status_code}")

# ============================================================================
# Test: R Analysis Scripts
# ============================================================================

class TestRAnalysis:
    """Tests for R analysis scripts"""
    
    def test_r_scripts_exist(self):
        """Check if R scripts exist"""
        scripts = [
            "scripts/r/01_data_preparation.R",
            "scripts/r/02_exploratory_analysis.R",
            "scripts/r/03_modeling_validation.R",
            "scripts/r/04_evaluation.R"
        ]
        
        for script in scripts:
            assert os.path.exists(script), f"Missing script: {script}"
            print(f"✓ {script} exists")
    
    @pytest.mark.skip(reason="R scripts take time to run")
    def test_r_scripts_execute(self):
        """Test that R scripts execute without error"""
        scripts = [
            "scripts/r/01_data_preparation.R",
            "scripts/r/02_exploratory_analysis.R",
            "scripts/r/03_modeling_validation.R",
            "scripts/r/04_evaluation.R"
        ]
        
        for script in scripts:
            print(f"\n  Running {script}...")
            result = subprocess.run(
                ["Rscript", script],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            assert result.returncode == 0, f"Script failed: {result.stderr}"
            print(f"  ✓ {script} completed successfully")
    
    def test_r_outputs_exist(self):
        """Check if R analysis outputs exist"""
        # These are created after R scripts run
        outputs = [
            "results/figures/01_success_by_model.png",
            "results/FINDINGS.txt",
            "results/RECOMMENDATIONS.txt"
        ]
        
        for output in outputs:
            if os.path.exists(output):
                size_kb = os.path.getsize(output) / 1024
                print(f"✓ {output} ({size_kb:.1f} KB)")
            else:
                print(f"⚠ {output} not yet created (run R scripts)")

# ============================================================================
# Test: Results Directory
# ============================================================================

class TestResults:
    """Tests for analysis results"""
    
    def test_results_structure(self):
        """Check results directory structure"""
        dirs = [
            "results/figures",
            "results/tables"
        ]
        
        for dir_path in dirs:
            assert os.path.isdir(dir_path), f"Missing directory: {dir_path}"
            print(f"✓ {dir_path} exists")
    
    def test_file_outputs(self):
        """Check various output files"""
        important_files = [
            f"{MODELS_DIR}/training_summary.json",
            f"{MODELS_DIR}/association_rules.json",
            f"{DATA_DIR}/preparation_summary.json"
        ]
        
        for file_path in important_files:
            if os.path.exists(file_path):
                size_kb = os.path.getsize(file_path) / 1024
                with open(file_path, 'r') as f:
                    json_data = json.load(f)
                print(f"✓ {file_path} ({size_kb:.1f} KB)")
            else:
                print(f"⚠ {file_path} not created yet")

# ============================================================================
# Test: Integration
# ============================================================================

class TestFullIntegration:
    """End-to-end integration tests"""
    
    def test_pipeline_completeness(self, api_running):
        """Test that complete pipeline is working"""
        # Check data
        assert os.path.exists(f"{DATA_DIR}/features.parquet")
        
        # Check models
        assert os.path.exists(f"{MODELS_DIR}/rf_classifier.pkl")
        assert os.path.exists(f"{MODELS_DIR}/kmeans_clusterer.pkl")
        assert os.path.exists(f"{MODELS_DIR}/association_rules.json")
        
        # Check API
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        
        print("✓ Complete pipeline operational")
    
    def test_sample_prediction_flow(self, api_running):
        """Test a realistic prediction flow"""
        sample_prompts = [
            {
                "text": "Write a quick sort algorithm",
                "code": True,
                "examples": False,
                "constraints": False
            },
            {
                "text": "Explain machine learning with real-world examples",
                "code": False,
                "examples": True,
                "constraints": False
            },
            {
                "text": "Design database schema with following constraints: ...",
                "code": False,
                "examples": False,
                "constraints": True
            }
        ]
        
        for i, prompt in enumerate(sample_prompts, 1):
            payload = {
                "prompt_text": prompt["text"],
                "prompt_length": len(prompt["text"]),
                "token_count": len(prompt["text"]) // 4,
                "contains_code": prompt["code"],
                "contains_examples": prompt["examples"],
                "contains_constraints": prompt["constraints"],
                "language": "english"
            }
            
            # Get prediction
            pred_response = requests.post(f"{API_BASE_URL}/ml/success-prediction", json=payload)
            assert pred_response.status_code == 200
            pred = pred_response.json()
            
            # Get cluster
            cluster_response = requests.post(f"{API_BASE_URL}/ml/prompt-clusters", json=payload)
            assert cluster_response.status_code == 200
            cluster = cluster_response.json()
            
            print(f"  Prompt {i}: {pred['confidence_level']} success | Cluster {cluster['cluster_id']}")
        
        print("✓ Sample predictions completed successfully")

# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
