"""
Data Preparation Pipeline
Loads 200K prompt execution records from PostgreSQL, engineers features, and splits data
"""

import psycopg2
import pandas as pd
import numpy as np
import yaml
import json
import os
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Configure paths
CONFIG_FILE = "ml_service/config.yaml"
DATA_DIR = "ml_service/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load config
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

db_config = config['database']
feature_config = config['features']
ml_config = config['ml']

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting data preparation pipeline...")

# ============================================================================
# Step 1: Connect to PostgreSQL and load raw data
# ============================================================================
print(f"\n[Step 1] Connecting to PostgreSQL...")
try:
    conn = psycopg2.connect("postgresql://postgres:supersecret@localhost:5432/promptlens")
    cursor = conn.cursor()
    print(f"✓ Connected to promptlens")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# ============================================================================
# Step 2: Load raw data from star schema
# ============================================================================
print(f"\n[Step 2] Loading data from PostgreSQL (200K+ records)...")

query = """
SELECT 
    e.fact_key as execution_key,
    e.prompt_key,
    e.model_key,
    e.task_key,
    CASE WHEN e.success_score >= 0.5 THEN 'success' ELSE 'failure' END as execution_status,
    e.tokens as tokens_used,
    e.latency as latency_ms,
    1 as attempt_count,
    e.success_score as success_rate,

    p.prompt_text,
    p.prompt_length,
    p.prompt_length as word_count,
    p.token_estimate as token_count,
    p.type as prompt_type,
    p.contains_code,
    p.contains_examples,
    p.contains_constraints,
    p.language,
    p.complexity_score,
    p.instruction_density,

    m.model_name,
    m.version as model_version,
    m.provider,

    t.task_type,
    t.domain,
    t.difficulty
FROM
    fact_promptexecution e
LEFT JOIN dim_prompt p ON e.prompt_key = p.prompt_key
LEFT JOIN dim_model m ON e.model_key = m.model_key
LEFT JOIN dim_task t ON e.task_key = t.task_key
ORDER BY e.fact_key DESC
LIMIT 100000;
"""
try:
    df = pd.read_sql(query, conn)
    print(f"✓ Loaded {len(df):,} records")
    print(f"  Columns: {df.shape[1]}")
    print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
except Exception as e:
    print(f"✗ Query failed: {e}")
    conn.close()
    exit(1)

conn.close()

# ============================================================================
# Step 3: Data Cleaning
# ============================================================================
print(f"\n[Step 3] Data cleaning...")

# Remove duplicates
df = df.drop_duplicates(subset=['execution_key'])
print(f"✓ Duplicates removed: {len(df):,} records")

# Handle missing values
df['latency_ms'] = df['latency_ms'].fillna(100.0)  # default if empty
df['tokens_used'] = df['tokens_used'].fillna(10.0)

missing_before = df.isnull().sum().sum()
df = df.dropna(subset=['prompt_text'])
df['model_name'] = df['model_name'].fillna('unknown')
df['task_type'] = df['task_type'].fillna('unknown')

for col in feature_config['numerical']:
    if col in df.columns:
        med = df[col].median()
        if pd.isna(med): med = 0.0
        df[col] = df[col].fillna(med)

df[feature_config['categorical']] = df[feature_config['categorical']].fillna('unknown')
missing_after = df.isnull().sum().sum()
print(f"✓ Missing values handled: {missing_before} → {missing_after}")

# Remove outliers (extreme latencies, token counts)
q99 = df['latency_ms'].quantile(0.99)
if not pd.isna(q99):
    df = df[df['latency_ms'] <= q99]
df = df[df['tokens_used'] > 0]
print(f"✓ Outliers removed: {len(df):,} records")

# ============================================================================
# Step 4: Feature Engineering
# ============================================================================
print(f"\n[Step 4] Engineering features...")

# Numerical features from raw data
# (already in config)

# NEW: Derived numerical features
df['prompt_word_count'] = df['prompt_text'].str.split().str.len()
df['avg_word_length'] = df['prompt_text'].str.replace(' ', '').str.len() / (df['prompt_word_count'] + 1)
df['question_marks'] = df['prompt_text'].str.count(r'\?')
df['code_blocks'] = df['prompt_text'].str.count(r'```|<code>')
df['list_items'] = df['prompt_text'].str.count(r'\n-|\n\d+\.')
df['capital_ratio'] = df['prompt_text'].str.count(r'[A-Z]') / (df['prompt_text'].str.len() + 1)

# Encode categorical features (one-hot)
categorical_cols = feature_config['categorical']
for col in categorical_cols:
    if col in df.columns:
        dummies = pd.get_dummies(df[col], prefix=col, dtype=int)
        df = pd.concat([df, dummies], axis=1)

# Binary features
if 'contains_code' in df.columns:
    df['contains_code'] = df['contains_code'].astype(int)
if 'contains_examples' in df.columns:
    df['contains_examples'] = df['contains_examples'].astype(int)
if 'contains_constraints' in df.columns:
    df['contains_constraints'] = df['contains_constraints'].astype(int)

print(f"✓ Features engineered: {df.shape[1]} columns")

# ============================================================================
# Step 5: Select features for ML
# ============================================================================
print(f"\n[Step 5] Selecting features for ML...")

# Numerical features
numeric_features = [
    'prompt_length', 'token_estimate', 'instruction_density',
    'complexity_score', 'tokens_used', 'latency_ms', 'attempt_count',
    'prompt_word_count', 'avg_word_length', 'question_marks',
    'code_blocks', 'list_items', 'capital_ratio'
]

# Add binary features
numeric_features += [col for col in df.columns if col.startswith(('contains_', 'prompt_type_', 'language_'))]

# Remove features that don't exist
numeric_features = [f for f in numeric_features if f in df.columns]

target = 'success_rate'

print(f"✓ Selected {len(numeric_features)} features")
print(f"  Features: {', '.join(numeric_features[:5])}... (+{len(numeric_features)-5} more)")

# ============================================================================
# Step 6: Feature Scaling & Normalization
# ============================================================================
print(f"\n[Step 6] Scaling features...")

from sklearn.preprocessing import StandardScaler, MinMaxScaler

# Scale for different purposes
scaler_standard = StandardScaler()
scaler_minmax = MinMaxScaler()

X = df[numeric_features].copy()
y = df[target].copy()

# Remove any remaining NaN
X = X.fillna(0)
y = y.fillna(0)
mask = ~(X.isnull().any(axis=1) | y.isnull())
X = X[mask]
y = y[mask]

print(f"✓ Features prepared: X shape {X.shape}, y shape {y.shape}")
print(f"  Success rate distribution:")
print(f"    Mean: {y.mean():.3f}")
print(f"    Std: {y.std():.3f}")
print(f"    Min: {y.min():.3f}")
print(f"    Max: {y.max():.3f}")

# ============================================================================
# Step 7: Train-Test Split
# ============================================================================
print(f"\n[Step 7] Splitting into train/val/test...")

from sklearn.model_selection import train_test_split

# 70% train, 15% val, 15% test
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=config['ml']['classification']['random_state']
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=config['ml']['classification']['random_state']
)

print(f"✓ Data split:")
print(f"  Train: {len(X_train):,} ({len(X_train)/len(X)*100:.1f}%)")
print(f"  Val:   {len(X_val):,} ({len(X_val)/len(X)*100:.1f}%)")
print(f"  Test:  {len(X_test):,} ({len(X_test)/len(X)*100:.1f}%)")

# ============================================================================
# Step 8: Save Prepared Data
# ============================================================================
print(f"\n[Step 8] Saving prepared data...")

# Save as Parquet (efficient, preserves types)
df.to_parquet(f"{DATA_DIR}/prepared_data.parquet", index=False)
print(f"✓ Saved: {DATA_DIR}/prepared_data.parquet")

# Save features and target separately
X.to_parquet(f"{DATA_DIR}/features.parquet", index=False)
y.to_frame().to_parquet(f"{DATA_DIR}/target.parquet", index=False)
print(f"✓ Saved: {DATA_DIR}/features.parquet, {DATA_DIR}/target.parquet")

# Save splits
splits = {
    'X_train_indices': X_train.index.tolist(),
    'X_val_indices': X_val.index.tolist(),
    'X_test_indices': X_test.index.tolist(),
    'feature_columns': numeric_features,
    'target_column': target,
    'shape': {
        'total': len(X),
        'train': len(X_train),
        'val': len(X_val),
        'test': len(X_test)
    }
}
with open(f"{DATA_DIR}/train_test_split.json", 'w') as f:
    json.dump(splits, f, indent=2)
print(f"✓ Saved: {DATA_DIR}/train_test_split.json")

# ============================================================================
# Step 9: Summary Statistics
# ============================================================================
print(f"\n[Step 9] Summary statistics...")

summary = {
    'timestamp': datetime.now().isoformat(),
    'total_records': len(df),
    'total_features': len(numeric_features),
    'feature_names': numeric_features,
    'target_stats': {
        'mean': float(y.mean()),
        'std': float(y.std()),
        'min': float(y.min()),
        'max': float(y.max()),
        'median': float(y.median())
    },
    'data_splits': {
        'train': len(X_train),
        'val': len(X_val),
        'test': len(X_test)
    },
    'missing_values': int(df.isnull().sum().sum()),
    'memory_mb': float(df.memory_usage(deep=True).sum() / 1024**2)
}

with open(f"{DATA_DIR}/preparation_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print(f"✓ DATA PREPARATION COMPLETE")
print(f"{'='*60}")
print(f"Records: {summary['total_records']:,}")
print(f"Features: {summary['total_features']}")
print(f"Target distribution: μ={summary['target_stats']['mean']:.3f}, σ={summary['target_stats']['std']:.3f}")
print(f"Memory: {summary['memory_mb']:.2f} MB")
print(f"\nNext steps:")
print(f"1. python ml_service/train_classification.py")
print(f"2. python ml_service/train_clustering.py")
print(f"3. python ml_service/train_association_rules.py")
