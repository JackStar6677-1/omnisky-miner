import os
import joblib
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import config

MODEL_PATH = os.path.join(config.OMNISKY_ROOT, "models", "triage.pkl")

class TriageEngine:
    """
    Local Machine Learning Engine for Event Classification.
    Integrates a PyTorch 2D CNN model when spectrograms are available,
    falling back to a classical Scikit-Learn Random Forest or Heuristics.
    """
    
    def __init__(self):
        self.model = None
        self.is_ready = False
        self._load_model()
        
        # Load Deep Learning (PyTorch CNN) Engine
        try:
            from modules.triage_nn import DeepTriageEngine
            self.deep_engine = DeepTriageEngine()
        except Exception as e:
            logging.warning(f"Could not load DeepTriageEngine: {e}")
            self.deep_engine = None
        
    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.is_ready = True
                logging.info("🧠 ML Triage Model Loaded")
            except Exception as e:
                logging.warning(f"Failed to load ML model: {e}")
        else:
            logging.info("🧠 No ML model found. Triage running in Heuristic Mode.")
            
    def train_dummy(self):
        """Trains an initial dummy model to enable the feature."""
        # Fake data just to have a valid .pkl structure
        X = [[10, 0.0], [5, 1.0], [2, 0.5], [50, 0.0]] # SNR, Drift
        y = ["NOISE", "CANDIDATE", "NOISE", "CANDIDATE"]
        
        clf = RandomForestClassifier(n_estimators=10)
        clf.fit(X, y)
        
        if not os.path.exists(os.path.dirname(MODEL_PATH)):
            os.makedirs(os.path.dirname(MODEL_PATH))
            
        joblib.dump(clf, MODEL_PATH)
        self.model = clf
        self.is_ready = True
        
        # Also ensure deep learning dummy weights exist
        if self.deep_engine:
            self.deep_engine.train_dummy()
            
        return "Dummy Model Trained"

    def analyze(self, features: dict) -> dict:
        """
        Returns {score: 0-100, label: str, confidence: float, method: 'ML'|'HEURISTIC'|'DEEP_CNN'}
        """
        try:
            # 1. Check if a spectrogram is provided and deep engine is ready
            spectrogram = features.get('spectrogram')
            if spectrogram is not None and self.deep_engine and self.deep_engine.is_ready:
                try:
                    prob = self.deep_engine.predict(spectrogram)
                    return {
                        "score": prob * 100,
                        "label": "CANDIDATE" if prob >= 0.5 else "NOISE",
                        "confidence": prob,
                        "method": "DEEP_CNN"
                    }
                except Exception as e:
                    logging.warning(f"Deep CNN classification failed: {e}. Falling back to classical ML.")

            # 2. Classic ML / Heuristic Fallback
            snr = float(features.get('snr', 0) or features.get('sigma', 0))
            drift = abs(float(features.get('drift', 0)))
            
            # ML Prediction
            if self.is_ready and self.model:
                try:
                    vector = [[snr, drift]]
                    pred_label = self.model.predict(vector)[0]
                    pred_prob = np.max(self.model.predict_proba(vector))
                    
                    return {
                        "score": pred_prob * 100,
                        "label": pred_label,
                        "confidence": pred_prob,
                        "method": "ML_RF"
                    }
                except Exception:
                    pass # Fallback to Heuristic
            
            # Heuristic Fallback
            score = 0
            label = "NOISE"
            
            if snr > 10:
                score += 50
            if snr > 50:
                score += 30
            if 0.1 < drift < 2.0: # Moderate drift is good for ET
                score += 20
                
            if score > 60: label = "CANDIDATE"
            
            return {
                "score": score,
                "label": label,
                "confidence": 1.0, # Artificial confidence
                "method": "HEURISTIC"
            }
            
        except Exception as e:
            logging.error(f"Triage Error: {e}")
            return {"score": 0, "label": "ERROR", "confidence": 0, "method": "FAIL"}
