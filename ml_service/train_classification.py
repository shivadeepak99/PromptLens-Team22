"""
Classification Model Training
Trains Random Forest + XGBoost ensemble to predict prompt execution success
"""

import pandas as pd
import numpy as np
import yaml
import json
import joblib
import os
from datetime import datetime
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# Configure
CONFIG_FILE = "ml_service/config.yaml"
DATA_DIR = "ml_service/data"
MODELS_DIR = "ml_service/models"
os.makedirs(MODELS_DIR, exist_ok=True)

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

ml_config = config['ml']['classification']

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting classification model training...")

# ============================================================================
# Step 1: Load prepared data
# ============================================================================
print(f"\n[Step 1] Loading prepared data...")

try:
    X = pd.read_parquet(f"{DATA_DIR}/features.parquet")
    y = pd.read_parquet(f"{DATA_DIR}/target.parquet")
    
    with open(f"{DATA_DIR}/train_test_split.json", 'r') as f:
        splits_info = json.load(f)
    
    print(f"✓ Loaded: X shape {X.shape}, y shape {y.shape}")
except Exception as e:
    print(f"✗ Failed to load data: {e}")
    exit(1)

# ============================================================================
# Step 2: Prepare train/test splits
# ============================================================================
print(f"\n[Step 2] Preparing train/test splits...")

train_idx = splits_info['X_train_indices']
val_idx = splits_info['X_val_indices']
test_idx = splits_info['X_test_indices']

X_train = X.iloc[train_idx]
y_train = y.iloc[train_idx]

X_val = X.iloc[val_idx]
y_val = y.iloc[val_idx]

X_test = X.iloc[test_idx]
y_test = y.iloc[test_idx]

print(f"✓ Train: {len(X_train):,} samples")
print(f"✓ Val:   {len(X_val):,} samples")
print(f"✓ Test:  {len(X_test):,} samples")

# ============================================================================
# Step 3: Train Random Forest
# ============================================================================
print(f"\n[Step 3] Training Random Forest...")

rf_params = ml_config['rf_params']
rf_model = RandomForestRegressor(**rf_params, n_jobs=-1, verbose=1)

try:
    rf_model.fit(X_train, y_train)
    print(f"✓ Random Forest trained")
except Exception as e:
    print(f"✗ RF training failed: {e}")
    exit(1)

# Validation metrics
y_pred_rf_val = rf_model.predict(X_val)
rf_mae_val = mean_absolute_error(y_val, y_pred_rf_val)
rf_rmse_val = np.sqrt(mean_squared_error(y_val, y_pred_rf_val))
rf_r2_val = r2_score(y_val, y_pred_rf_val)

print(f"  Validation metrics:")
print(f"    MAE:  {rf_mae_val:.4f}")
print(f"    RMSE: {rf_rmse_val:.4f}")
print(f"    R²:   {rf_r2_val:.4f}")

# Test metrics
y_pred_rf_test = rf_model.predict(X_test)
rf_mae_test = mean_absolute_error(y_test, y_pred_rf_test)
rf_rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_rf_test))
rf_r2_test = r2_score(y_test, y_pred_rf_test)

print(f"  Test metrics:")
print(f"    MAE:  {rf_mae_test:.4f}")
print(f"    RMSE: {rf_rmse_test:.4f}")
print(f"    R²:   {rf_r2_test:.4f}")

# Feature importance
rf_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"  Top 5 features:")
for idx, row in rf_importance.head(5).iterrows():
    print(f"    {row['feature']}: {row['importance']:.4f}")

# ============================================================================
# Step 4: Train XGBoost
# ============================================================================
print(f"\n[Step 4] Training XGBoost...")

xgb_params = ml_config['xgb_params']
xgb_model = XGBRegressor(**xgb_params, verbosity=1)

try:
    xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    print(f"✓ XGBoost trained")
except Exception as e:
    print(f"✗ XGBoost training failed: {e}")
    exit(1)

# Validation metrics
y_pred_xgb_val = xgb_model.predict(X_val)
xgb_mae_val = mean_absolute_error(y_val, y_pred_xgb_val)
xgb_rmse_val = np.sqrt(mean_squared_error(y_val, y_pred_xgb_val))
xgb_r2_val = r2_score(y_val, y_pred_xgb_val)

print(f"  Validation metrics:")
print(f"    MAE:  {xgb_mae_val:.4f}")
print(f"    RMSE: {xgb_rmse_val:.4f}")
print(f"    R²:   {xgb_r2_val:.4f}")

# Test metrics
y_pred_xgb_test = xgb_model.predict(X_test)
xgb_mae_test = mean_absolute_error(y_test, y_pred_xgb_test)
xgb_rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_xgb_test))
xgb_r2_test = r2_score(y_test, y_pred_xgb_test)

print(f"  Test metrics:")
print(f"    MAE:  {xgb_mae_test:.4f}")
print(f"    RMSE: {xgb_rmse_test:.4f}")
print(f"    R²:   {xgb_r2_test:.4f}")

# Feature importance
xgb_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"  Top 5 features:")
for idx, row in xgb_importance.head(5).iterrows():
    print(f"    {row['feature']}: {row['importance']:.4f}")

# ============================================================================
# Step 5: Ensemble Predictions (60% RF + 40% XGB)
# ============================================================================
print(f"\n[Step 5] Creating ensemble...")

y_pred_ensemble_test = 0.6 * y_pred_rf_test + 0.4 * y_pred_xgb_test
ensemble_mae_test = mean_absolute_error(y_test, y_pred_ensemble_test)
ensemble_rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_ensemble_test))
ensemble_r2_test = r2_score(y_test, y_pred_ensemble_test)

print(f"  Ensemble (60% RF + 40% XGB) test metrics:")
print(f"    MAE:  {ensemble_mae_test:.4f} ⭐")
print(f"    RMSE: {ensemble_rmse_test:.4f}")
print(f"    R²:   {ensemble_r2_test:.4f}")

# ============================================================================
# Step 6: Save Models
# ============================================================================
print(f"\n[Step 6] Saving models...")

joblib.dump(rf_model, f"{MODELS_DIR}/rf_classifier.pkl")
print(f"✓ Saved: {MODELS_DIR}/rf_classifier.pkl")

joblib.dump(xgb_model, f"{MODELS_DIR}/xgb_classifier.pkl")
print(f"✓ Saved: {MODELS_DIR}/xgb_classifier.pkl")

# Save feature importance
rf_importance.to_csv(f"{MODELS_DIR}/rf_feature_importance.csv", index=False)
xgb_importance.to_csv(f"{MODELS_DIR}/xgb_feature_importance.csv", index=False)
print(f"✓ Saved feature importance CSVs")

# ============================================================================
# Step 7: Save Training Summary
# ============================================================================
print(f"\n[Step 7] Saving training summary...")

training_summary = {
    'timestamp': datetime.now().isoformat(),
    'model_type': 'classification_ensemble',
    'target': 'success_rate',
    'data': {
        'train_samples': len(X_train),
        'val_samples': len(X_val),
        'test_samples': len(X_test),
        'features': len(X_train.columns)
    },
    'random_forest': {
        'params': ml_config['rf_params'],
        'validation': {
            'mae': float(rf_mae_val),
            'rmse': float(rf_rmse_val),
            'r2': float(rf_r2_val)
        },
        'test': {
            'mae': float(rf_mae_test),
            'rmse': float(rf_rmse_test),
            'r2': float(rf_r2_test)
        }
    },
    'xgboost': {
        'params': ml_config['xgb_params'],
        'validation': {
            'mae': float(xgb_mae_val),
            'rmse': float(xgb_rmse_val),
            'r2': float(xgb_r2_val)
        },
        'test': {
            'mae': float(xgb_mae_test),
            'rmse': float(xgb_rmse_test),
            'r2': float(xgb_r2_test)
        }
    },
    'ensemble': {
        'strategy': '60% RF + 40% XGB',
        'test': {
            'mae': float(ensemble_mae_test),
            'rmse': float(ensemble_rmse_test),
            'r2': float(ensemble_r2_test)
        }
    },
    'feature_columns': X_train.columns.tolist()
}

with open(f"{MODELS_DIR}/training_summary.json", 'w') as f:
    json.dump(training_summary, f, indent=2)

print(f"✓ Saved: {MODELS_DIR}/training_summary.json")

# ============================================================================
# Summary
# ============================================================================
print(f"\n{'='*60}")
print(f"✓ CLASSIFICATION MODEL TRAINING COMPLETE")
print(f"{'='*60}")
print(f"\nBest Model Metrics (Test Set):")
print(f"  Random Forest:")
print(f"    MAE:  {rf_mae_test:.4f}")
print(f"    RMSE: {rf_rmse_test:.4f}")
print(f"    R²:   {rf_r2_test:.4f}")
print(f"\n  XGBoost:")
print(f"    MAE:  {xgb_mae_test:.4f}")
print(f"    RMSE: {xgb_rmse_test:.4f}")
print(f"    R²:   {xgb_r2_test:.4f}")
print(f"\n  Ensemble (60% RF + 40% XGB):")
print(f"    MAE:  {ensemble_mae_test:.4f} ⭐")
print(f"    RMSE: {ensemble_rmse_test:.4f}")
print(f"    R²:   {ensemble_r2_test:.4f}")
print(f"\nSaved models:")
print(f"  {MODELS_DIR}/rf_classifier.pkl")
print(f"  {MODELS_DIR}/xgb_classifier.pkl")
print(f"  {MODELS_DIR}/training_summary.json")
print(f"\nNext: python ml_service/train_clustering.py")
