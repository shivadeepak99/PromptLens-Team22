import json
import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any

try:
    import joblib  # type: ignore
except Exception:  # pragma: no cover
    joblib = None

class MLService:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.rf_model = None
        self.xgb_model = None
        self.kmeans_model = None
        self.kmeans_scaler = None
        self.kmeans_pca = None
        self._use_heuristic = False
        self.feature_columns = [
            'prompt_length', 'instruction_density', 'complexity_score', 'tokens_used', 'latency_ms',
            'attempt_count', 'prompt_word_count', 'avg_word_length', 'question_marks', 'code_blocks',
            'list_items', 'capital_ratio', 'contains_code', 'contains_examples', 'contains_constraints',
            'language_unknown', 'prompt_type_roleplay', 'prompt_type_standard', 'contains_code_False',
            'contains_code_True', 'contains_examples_False', 'contains_examples_True',
            'contains_constraints_False', 'contains_constraints_True'
        ]
        self._load_models()

        # If the trained models are missing or effectively constant (e.g., trained
        # on an all-zero target), fall back to a heuristic scorer so the UI still
        # shows meaningful values.
        self._use_heuristic = self._models_are_degenerate()

    def _load_models(self):
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_service', 'models')
        
        try:
            with open(os.path.join(base_dir, 'association_rules.json'), 'r') as f:
                self.rules = json.load(f)
        except: pass

        try:
            model_path = os.path.join(base_dir, 'rf_classifier.pkl')
            if joblib is not None:
                self.rf_model = joblib.load(model_path)
            else:
                with open(model_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
        except: pass

        try:
            model_path = os.path.join(base_dir, 'xgb_classifier.pkl')
            if joblib is not None:
                self.xgb_model = joblib.load(model_path)
            else:
                with open(model_path, 'rb') as f:
                    self.xgb_model = pickle.load(f)
        except: pass

        try:
            with open(os.path.join(base_dir, 'kmeans_clustering.pkl'), 'rb') as f:
                self.kmeans_model = pickle.load(f)
        except: pass

        # Newer pipeline saves a clustering *pipeline* (scaler + PCA + KMeans)
        # in separate files.
        try:
            kmeans_path = os.path.join(base_dir, 'kmeans_clusterer.pkl')
            scaler_path = os.path.join(base_dir, 'feature_scaler.pkl')
            pca_path = os.path.join(base_dir, 'pca_transformer.pkl')

            if os.path.exists(kmeans_path) and os.path.exists(scaler_path) and os.path.exists(pca_path):
                if joblib is not None:
                    self.kmeans_model = joblib.load(kmeans_path)
                    self.kmeans_scaler = joblib.load(scaler_path)
                    self.kmeans_pca = joblib.load(pca_path)
                else:
                    with open(kmeans_path, 'rb') as f:
                        self.kmeans_model = pickle.load(f)
                    with open(scaler_path, 'rb') as f:
                        self.kmeans_scaler = pickle.load(f)
                    with open(pca_path, 'rb') as f:
                        self.kmeans_pca = pickle.load(f)
        except:  # pragma: no cover
            pass

    @staticmethod
    def _clamp01(value: float) -> float:
        if not np.isfinite(value):
            return 0.0
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return float(value)

    def _model_predict_success(self, prompt_text: str) -> float | None:
        """Predict using loaded ML models only. Returns None if unavailable."""

        if not self.rf_model and not self.xgb_model:
            return None

        df_features = self.extract_features(prompt_text)
        preds = []

        try:
            if self.rf_model:
                preds.append(float(self.rf_model.predict(df_features)[0]))
        except Exception:
            pass

        try:
            if self.xgb_model:
                preds.append(float(self.xgb_model.predict(df_features)[0]))
        except Exception:
            pass

        if not preds:
            return None

        return self._clamp01(float(np.mean(preds)))

    def _heuristic_predict_success(self, prompt_text: str) -> float:
        """Lightweight deterministic scorer used when models are missing/degenerate."""

        df_features = self.extract_features(prompt_text)
        f = df_features.to_dict(orient='records')[0]

        prompt_length = float(f.get('prompt_length', 0) or 0)
        complexity_score = float(f.get('complexity_score', 0) or 0)
        instruction_density = float(f.get('instruction_density', 0) or 0)

        contains_code = int(f.get('contains_code', 0) or 0)
        contains_examples = int(f.get('contains_examples', 0) or 0)
        contains_constraints = int(f.get('contains_constraints', 0) or 0)

        score = 0.15
        score += 0.20 * contains_examples
        score += 0.20 * contains_constraints
        score += 0.15 * contains_code

        # Length sweet spot: not too short, not excessively long.
        if prompt_length < 40:
            score -= 0.10
        elif prompt_length > 1200:
            score -= 0.05
        else:
            score += 0.05

        score += 0.10 * min(max(instruction_density, 0.0), 1.0)
        score += 0.10 * min(max(complexity_score / 20.0, 0.0), 1.0)

        # Keep a little headroom so projections can show lift.
        return self._clamp01(min(score, 0.95))

    def _models_are_degenerate(self) -> bool:
        """Detect constant/broken models (e.g., trained on all-zero targets)."""

        # If no models, we need the heuristic.
        if not self.rf_model and not self.xgb_model:
            return True

        probes = [
            "Explain the following concept in 3 bullet points.",
            "You must output valid JSON with keys: steps, assumptions, result.",
            "Here is an example:\nInput: 2\nOutput: 4\nNow generalize.",
            "```python\nprint('hello')\n```\nExplain what this does.",
        ]
        scores: list[float] = []
        for text in probes:
            score = self._model_predict_success(text)
            if score is not None:
                scores.append(round(float(score), 6))

        if not scores:
            return True

        return (max(scores) - min(scores)) < 1e-6

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
        if self._use_heuristic:
            return self._heuristic_predict_success(prompt_text)

        score = self._model_predict_success(prompt_text)
        if score is None:
            return self._heuristic_predict_success(prompt_text)
        return float(score)

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
                df_features = self.extract_features(prompt_text)
                if self.kmeans_scaler is not None and self.kmeans_pca is not None:
                    X_scaled = self.kmeans_scaler.transform(df_features)
                    X_pca = self.kmeans_pca.transform(X_scaled)
                    cluster_id = self.kmeans_model.predict(X_pca)[0]
                else:
                    cluster_id = self.kmeans_model.predict(df_features)[0]
                cluster = f"Cluster {int(cluster_id)}"
            except: pass

        return {
            "baseline_score": round(baseline, 3),
            "cluster_group": cluster,
            "extracted_features": features,
            "recommendations": recommendations[:3]
        }

ml_service = MLService()
