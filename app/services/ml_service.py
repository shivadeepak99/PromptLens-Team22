import json
import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class MLService:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.rf_model = None
        self.xgb_model = None
        self.kmeans_model = None
        self.feature_columns = [
            'prompt_length', 'instruction_density', 'complexity_score', 'tokens_used', 'latency_ms',
            'attempt_count', 'prompt_word_count', 'avg_word_length', 'question_marks', 'code_blocks',
            'list_items', 'capital_ratio', 'contains_code', 'contains_examples', 'contains_constraints',
            'language_unknown', 'prompt_type_roleplay', 'prompt_type_standard', 'contains_code_False',
            'contains_code_True', 'contains_examples_False', 'contains_examples_True',
            'contains_constraints_False', 'contains_constraints_True'
        ]
        self._load_models()

    def _load_models(self):
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_service', 'models')
        
        try:
            with open(os.path.join(base_dir, 'association_rules.json'), 'r') as f:
                self.rules = json.load(f)
        except: pass

        try:
            with open(os.path.join(base_dir, 'rf_classifier.pkl'), 'rb') as f:
                self.rf_model = pickle.load(f)
        except: pass

        try:
            with open(os.path.join(base_dir, 'xgb_classifier.pkl'), 'rb') as f:
                self.xgb_model = pickle.load(f)
        except: pass

        try:
            with open(os.path.join(base_dir, 'kmeans_clustering.pkl'), 'rb') as f:
                self.kmeans_model = pickle.load(f)
        except: pass

    def extract_features(self, prompt_text: str) -> pd.DataFrame:
        features = {}
        features['prompt_length'] = len(prompt_text)
        words = prompt_text.split()
        features['prompt_word_count'] = len(words)
        
        features['avg_word_length'] = len(prompt_text.replace(' ', '')) / (max(len(words), 1))
        features['question_marks'] = prompt_text.count('?')
        features['code_blocks'] = prompt_text.count('```')
        features['list_items'] = prompt_text.count('\n-') + prompt_text.count('\n*')
        features['capital_ratio'] = sum(1 for c in prompt_text if c.isupper()) / max(len(prompt_text), 1)

        features['instruction_density'] = 0.5 
        features['complexity_score'] = features['avg_word_length'] + (features['code_blocks'] * 2)
        features['tokens_used'] = len(words) * 1.3
        features['latency_ms'] = 100.0
        features['attempt_count'] = 1

        contains_code = '```' in prompt_text
        contains_examples = 'example' in prompt_text.lower() or 'e.g.' in prompt_text.lower()
        contains_constraints = 'must' in prompt_text.lower() or 'only' in prompt_text.lower()

        features['contains_code'] = int(contains_code)
        features['contains_examples'] = int(contains_examples)
        features['contains_constraints'] = int(contains_constraints)
        
        features['language_unknown'] = 1
        features['prompt_type_roleplay'] = 1 if 'act as' in prompt_text.lower() else 0
        features['prompt_type_standard'] = 1 if features['prompt_type_roleplay'] == 0 else 0
        
        features['contains_code_False'] = int(not contains_code)
        features['contains_code_True'] = int(contains_code)
        features['contains_examples_False'] = int(not contains_examples)
        features['contains_examples_True'] = int(contains_examples)
        features['contains_constraints_False'] = int(not contains_constraints)
        features['contains_constraints_True'] = int(contains_constraints)
        
        df = pd.DataFrame([features])[self.feature_columns]
        # Fill strictly
        return df.fillna(0)

    def predict_success(self, prompt_text: str) -> float:
        if not self.rf_model and not self.xgb_model:
            return 0.40 
        
        df_features = self.extract_features(prompt_text)
        preds = []
        if self.rf_model: 
            preds.append(self.rf_model.predict(df_features)[0])
        if self.xgb_model: 
            preds.append(self.xgb_model.predict(df_features)[0])
        
        return float(np.mean(preds))

    def recommend_improvements(self, prompt_text: str) -> Dict[str, Any]:
        baseline = self.predict_success(prompt_text)
        recommendations = []
        
        if '```' not in prompt_text:
            alt_text = prompt_text + "\n\n```python\n# Example Code\n```"
            score = self.predict_success(alt_text)
            if score > baseline:
                recommendations.append({"variant": "Add explicit code blocks", "predicted_score": round(score, 3)})
                
        if 'example' not in prompt_text.lower():
            alt_text = prompt_text + " Here is an example: "
            score = self.predict_success(alt_text)
            if score > baseline:
                recommendations.append({"variant": "Add context or examples", "predicted_score": round(score, 3)})

        if 'must' not in prompt_text.lower():
            alt_text = prompt_text + " You must only output valid JSON."
            score = self.predict_success(alt_text)
            if score > baseline:
                recommendations.append({"variant": "Add explicit constraints", "predicted_score": round(score, 3)})
        
        recommendations.sort(key=lambda x: x["predicted_score"], reverse=True)
        features = self.extract_features(prompt_text).to_dict(orient='records')[0]
        
        # Determine cluster
        cluster = "unknown"
        if self.kmeans_model:
            try:
                cluster_id = self.kmeans_model.predict(self.extract_features(prompt_text))[0]
                cluster = f"Cluster {cluster_id}"
            except: pass

        return {
            "baseline_score": round(baseline, 3),
            "cluster_group": cluster,
            "extracted_features": features,
            "recommendations": recommendations[:3]
        }

ml_service = MLService()
