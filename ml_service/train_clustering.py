"""
Clustering Model Training
Trains K-Means clustering to group similar prompts
"""

import pandas as pd
import numpy as np
import yaml
import json
import joblib
import os
from datetime import datetime

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score

# Configure
CONFIG_FILE = "ml_service/config.yaml"
DATA_DIR = "ml_service/data"
MODELS_DIR = "ml_service/models"
os.makedirs(MODELS_DIR, exist_ok=True)

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

ml_config = config['ml']['clustering']

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting clustering model training...")

# ============================================================================
# Step 1: Load prepared data
# ============================================================================
print(f"\n[Step 1] Loading prepared data...")

try:
    X = pd.read_parquet(f"{DATA_DIR}/features.parquet")
    print(f"✓ Loaded: X shape {X.shape}")
except Exception as e:
    print(f"✗ Failed to load data: {e}")
    exit(1)

# ============================================================================
# Step 2: Standardize Features
# ============================================================================
print(f"\n[Step 2] Standardizing features...")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"✓ Features scaled: mean={X_scaled.mean():.6f}, std={X_scaled.std():.6f}")

# ============================================================================
# Step 3: Dimensionality Reduction (PCA)
# ============================================================================
print(f"\n[Step 3] PCA dimensionality reduction...")

n_components = ml_config['pca_components']
pca = PCA(n_components=n_components, random_state=ml_config['random_state'])
X_pca = pca.fit_transform(X_scaled)

print(f"✓ PCA reduced to {n_components} dimensions")
print(f"  Explained variance: {pca.explained_variance_ratio_.sum():.4f} ({pca.explained_variance_ratio_.sum()*100:.1f}%)")
print(f"  Variance by component:")
for i, var in enumerate(pca.explained_variance_ratio_[:5]):
    print(f"    PC{i+1}: {var:.4f}")

# ============================================================================
# Step 4: Train K-Means
# ============================================================================
print(f"\n[Step 4] Training K-Means (k={ml_config['n_clusters']})...")

kmeans = KMeans(
    n_clusters=ml_config['n_clusters'],
    random_state=ml_config['random_state'],
    n_init=20,
    verbose=1
)

clusters = kmeans.fit_predict(X_pca)
print(f"✓ K-Means trained")

# ============================================================================
# Step 5: Evaluate Clustering Quality
# ============================================================================
print(f"\n[Step 5] Evaluating clustering quality...")

silhouette_avg = silhouette_score(X_pca, clusters)
calinski_harabasz = calinski_harabasz_score(X_pca, clusters)

print(f"  Silhouette Score: {silhouette_avg:.4f} (target: >0.40)")
print(f"  Calinski-Harabasz: {calinski_harabasz:.2f} (higher is better)")

# Cluster sizes
cluster_sizes = pd.Series(clusters).value_counts().sort_index()
print(f"  Cluster distribution:")
for cluster_id, size in cluster_sizes.items():
    pct = size / len(clusters) * 100
    print(f"    Cluster {cluster_id}: {size:,} samples ({pct:.1f}%)")

# ============================================================================
# Step 6: Characterize Clusters
# ============================================================================
print(f"\n[Step 6] Characterizing clusters...")

# Reconstruct original features from PCA
X_reconstructed = pca.inverse_transform(X_pca)

cluster_characteristics = []
for cluster_id in range(ml_config['n_clusters']):
    mask = clusters == cluster_id
    cluster_data = X_reconstructed[mask]
    
    characteristics = {
        'cluster_id': int(cluster_id),
        'size': int(mask.sum()),
        'mean_prompt_length': float(cluster_data[:, X.columns.get_loc('prompt_length')].mean()),
        'mean_complexity': float(cluster_data[:, X.columns.get_loc('complexity_score')].mean()),
        'has_code_ratio': float(cluster_data[:, X.columns.get_loc('contains_code')].mean())
    }
    cluster_characteristics.append(characteristics)

for char in cluster_characteristics:
    print(f"  Cluster {char['cluster_id']}:")
    print(f"    Size: {char['size']:,}")
    print(f"    Avg prompt length: {char['mean_prompt_length']:.0f}")
    print(f"    Avg complexity: {char['mean_complexity']:.2f}")
    print(f"    Contains code: {char['has_code_ratio']:.1%}")

# ============================================================================
# Step 7: Save Models
# ============================================================================
print(f"\n[Step 7] Saving models...")

joblib.dump(pca, f"{MODELS_DIR}/pca_transformer.pkl")
print(f"✓ Saved: {MODELS_DIR}/pca_transformer.pkl")

joblib.dump(kmeans, f"{MODELS_DIR}/kmeans_clusterer.pkl")
print(f"✓ Saved: {MODELS_DIR}/kmeans_clusterer.pkl")

joblib.dump(scaler, f"{MODELS_DIR}/feature_scaler.pkl")
print(f"✓ Saved: {MODELS_DIR}/feature_scaler.pkl")

# ============================================================================
# Step 8: Save Training Summary
# ============================================================================
print(f"\n[Step 8] Saving training summary...")

clustering_summary = {
    'timestamp': datetime.now().isoformat(),
    'model_type': 'clustering_kmeans',
    'data': {
        'total_samples': len(X),
        'original_features': len(X.columns),
        'pca_components': n_components
    },
    'pca': {
        'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
        'total_variance_explained': float(pca.explained_variance_ratio_.sum())
    },
    'kmeans': {
        'n_clusters': ml_config['n_clusters'],
        'random_state': ml_config['random_state']
    },
    'evaluation': {
        'silhouette_score': float(silhouette_avg),
        'calinski_harabasz': float(calinski_harabasz)
    },
    'cluster_characteristics': cluster_characteristics,
    'feature_columns': X.columns.tolist()
}

# Merge with existing training_summary if it exists
summary_path = f"{MODELS_DIR}/training_summary.json"
if os.path.exists(summary_path):
    with open(summary_path, 'r') as f:
        existing_summary = json.load(f)
    existing_summary['clustering'] = clustering_summary
    combined_summary = existing_summary
else:
    combined_summary = {'clustering': clustering_summary}

with open(summary_path, 'w') as f:
    json.dump(combined_summary, f, indent=2)

print(f"✓ Saved: {MODELS_DIR}/training_summary.json")

# ============================================================================
# Summary
# ============================================================================
print(f"\n{'='*60}")
print(f"✓ CLUSTERING MODEL TRAINING COMPLETE")
print(f"{'='*60}")
print(f"\nModel Performance:")
print(f"  Silhouette Score: {silhouette_avg:.4f}")
print(f"  Calinski-Harabasz: {calinski_harabasz:.2f}")
print(f"  Clusters: {ml_config['n_clusters']}")
print(f"\nSaved models:")
print(f"  {MODELS_DIR}/pca_transformer.pkl")
print(f"  {MODELS_DIR}/kmeans_clusterer.pkl")
print(f"  {MODELS_DIR}/feature_scaler.pkl")
print(f"\nNext: python ml_service/train_association_rules.py")
