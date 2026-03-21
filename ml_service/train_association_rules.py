"""
Association Rules Mining
Mines patterns from prompt features using Apriori algorithm
"""

import pandas as pd
import numpy as np
import yaml
import json
import os
from datetime import datetime

from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

# Configure
CONFIG_FILE = "ml_service/config.yaml"
DATA_DIR = "ml_service/data"
MODELS_DIR = "ml_service/models"
os.makedirs(MODELS_DIR, exist_ok=True)

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

ml_config = config['ml']['association']

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting association rules mining...")

# ============================================================================
# Step 1: Load prepared data
# ============================================================================
print(f"\n[Step 1] Loading prepared data...")

try:
    X = pd.read_parquet(f"{DATA_DIR}/features.parquet")
    y = pd.read_parquet(f"{DATA_DIR}/target.parquet")
    data = pd.read_parquet(f"{DATA_DIR}/prepared_data.parquet")
    
    print(f"✓ Loaded: {len(X):,} samples, {len(X.columns)} features")
except Exception as e:
    print(f"✗ Failed to load data: {e}")
    exit(1)

# ============================================================================
# Step 2: Binarize Features for Apriori
# ============================================================================
print(f"\n[Step 2] Binarizing features...")

# Create binary features (itemsets)
# Select features to binarize
feature_cols = [
    'contains_code', 'contains_examples', 'contains_constraints',
    'prompt_length', 'token_estimate', 'instruction_density',
    'complexity_score', 'tokens_used', 'latency_ms'
]

# Filter to columns that exist
feature_cols = [col for col in feature_cols if col in X.columns]

# Create transactions (one row = one execution, columns = binary features)
transactions = []

for idx, row in X.iterrows():
    items = []
    
    # Binary features
    for col in X.columns:
        if X[col].dtype == 'int64' or X[col].dtype == 'int32':  # Already binary?
            if row[col] > 0:
                items.append(f"{col}=1")
        else:  # Continuous - discretize by quartiles
            if col in ['prompt_length', 'token_estimate', 'tokens_used']:
                q75 = X[col].quantile(0.75)
                if row[col] > q75:
                    items.append(f"{col}_high")
            elif col in ['instruction_density', 'complexity_score']:
                median = X[col].median()
                if row[col] > median:
                    items.append(f"{col}_high")
    
    # Add success indicator
    if idx < len(y):
        if y.iloc[idx] > 0.5:
            items.append("success_high")
    
    if items:
        transactions.append(items)

print(f"✓ Created {len(transactions):,} transactions")
print(f"  Example transaction: {transactions[0]}")

# ============================================================================
# Step 3: Apply Apriori Algorithm
# ============================================================================
print(f"\n[Step 3] Applying Apriori algorithm...")

# Use TransactionEncoder for mlxtend compatibility
te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df_transactions = pd.DataFrame(te_ary, columns=te.columns_)

print(f"✓ Transaction matrix: {df_transactions.shape}")
print(f"  Support threshold: {ml_config['min_support']}")

# Find frequent itemsets
frequent_itemsets = apriori(df_transactions, min_support=ml_config['min_support'], use_colnames=True)
print(f"✓ Found {len(frequent_itemsets)} frequent itemsets")

if len(frequent_itemsets) == 0:
    print(f"⚠ No frequent itemsets found. Try lowering min_support threshold.")
    exit(1)

# ============================================================================
# Step 4: Generate Association Rules
# ============================================================================
print(f"\n[Step 4] Generating association rules...")

rules = association_rules(
    frequent_itemsets,
    metric="confidence",
    min_threshold=ml_config['min_confidence']
)

if len(rules) == 0:
    print(f"⚠ No rules met confidence threshold. Lowering threshold...")
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=0.30
    )

print(f"✓ Generated {len(rules)} rules")

# Calculate lift and filter
rules['lift'] = rules['lift'].astype('float64')
rules = rules[rules['lift'] >= ml_config['min_lift']]
print(f"✓ Kept {len(rules)} rules with lift >= {ml_config['min_lift']}")

# Sort by lift
rules = rules.sort_values('lift', ascending=False)

# ============================================================================
# Step 5: Filter and Format Top Rules
# ============================================================================
print(f"\n[Step 5] Formatting top rules...")

top_n = ml_config['top_n_rules']
top_rules = rules.head(top_n)

print(f"✓ Top {len(top_rules)} rules by lift:")

formatted_rules = []
for idx, rule in top_rules.iterrows():
    antecedents = ', '.join(list(rule['antecedents']))
    consequents = ', '.join(list(rule['consequents']))
    
    formatted_rule = {
        'antecedents': antecedents,
        'consequents': consequents,
        'support': float(rule['support']),
        'confidence': float(rule['confidence']),
        'lift': float(rule['lift']),
        'leverage': float(rule.get('leverage', 0)),
        'conviction': float(rule.get('conviction', 0))
    }
    formatted_rules.append(formatted_rule)
    
    if len(formatted_rules) <= 5:  # Print first 5
        print(f"  Rule {len(formatted_rules)}:")
        print(f"    {antecedents} → {consequents}")
        print(f"    confidence: {formatted_rule['confidence']:.2%}, lift: {formatted_rule['lift']:.2f}")

# ============================================================================
# Step 6: Statistical Summary
# ============================================================================
print(f"\n[Step 6] Rule statistics...")

print(f"  All {len(rules)} rules:")
print(f"    Avg confidence: {rules['confidence'].mean():.2%}")
print(f"    Avg lift: {rules['lift'].mean():.2f}")
print(f"    Avg support: {rules['support'].mean():.4f}")

print(f"  Top {len(top_rules)} rules:")
print(f"    Avg confidence: {top_rules['confidence'].mean():.2%}")
print(f"    Avg lift: {top_rules['lift'].mean():.2f}")
print(f"    Avg support: {top_rules['support'].mean():.4f}")

# ============================================================================
# Step 7: Save Rules
# ============================================================================
print(f"\n[Step 7] Saving rules...")

with open(f"{MODELS_DIR}/association_rules.json", 'w') as f:
    json.dump(formatted_rules, f, indent=2)

print(f"✓ Saved: {MODELS_DIR}/association_rules.json")

# Also save CSV for reference
rules_csv = pd.DataFrame(formatted_rules)
rules_csv.to_csv(f"{MODELS_DIR}/association_rules.csv", index=False)
print(f"✓ Saved: {MODELS_DIR}/association_rules.csv")

# ============================================================================
# Step 8: Update Training Summary
# ============================================================================
print(f"\n[Step 8] Updating training summary...")

association_summary = {
    'timestamp': datetime.now().isoformat(),
    'model_type': 'association_rules_apriori',
    'parameters': {
        'min_support': ml_config['min_support'],
        'min_confidence': ml_config['min_confidence'],
        'min_lift': ml_config['min_lift'],
        'top_n_rules': ml_config['top_n_rules']
    },
    'results': {
        'total_frequent_itemsets': len(frequent_itemsets),
        'total_rules_generated': len(rules),
        'top_rules_count': len(top_rules)
    },
    'statistics': {
        'all_rules': {
            'avg_confidence': float(rules['confidence'].mean()),
            'avg_lift': float(rules['lift'].mean()),
            'avg_support': float(rules['support'].mean())
        },
        'top_rules': {
            'avg_confidence': float(top_rules['confidence'].mean()),
            'avg_lift': float(top_rules['lift'].mean()),
            'avg_support': float(top_rules['support'].mean())
        }
    },
    'top_rules': formatted_rules
}

summary_path = f"{MODELS_DIR}/training_summary.json"
if os.path.exists(summary_path):
    with open(summary_path, 'r') as f:
        existing_summary = json.load(f)
    existing_summary['association_rules'] = association_summary
    combined_summary = existing_summary
else:
    combined_summary = {'association_rules': association_summary}

with open(summary_path, 'w') as f:
    json.dump(combined_summary, f, indent=2)

print(f"✓ Saved: {MODELS_DIR}/training_summary.json")

# ============================================================================
# Summary
# ============================================================================
print(f"\n{'='*60}")
print(f"✓ ASSOCIATION RULES MINING COMPLETE")
print(f"{'='*60}")
print(f"\nResults:")
print(f"  Frequent itemsets: {len(frequent_itemsets)}")
print(f"  Rules generated: {len(rules)}")
print(f"  Top {len(top_rules)} rules saved")
print(f"\nTop rule statistics:")
print(f"  Avg confidence: {top_rules['confidence'].mean():.2%}")
print(f"  Avg lift: {top_rules['lift'].mean():.2f}")
print(f"\nSaved outputs:")
print(f"  {MODELS_DIR}/association_rules.json")
print(f"  {MODELS_DIR}/association_rules.csv")
print(f"  {MODELS_DIR}/training_summary.json")
print(f"\nNext: python ml_service/temporary_test_api.py")
