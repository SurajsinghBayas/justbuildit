from typing import Optional
import joblib
import numpy as np

from app.utils.model_loader import load_model


class PredictionService:
    def __init__(self):
        self.model = load_model("app/models/delay_model.pkl")

    def predict_delay(self, features: dict) -> dict:
        """
        Predict task delay probability.

        Args:
            features: Dict with task features (complexity, assignee_load, days_remaining, etc.)

        Returns:
            Dict with prediction and confidence
        """
        if self.model is None:
            # Return a deterministic stub when model isn't trained yet
            return {"will_delay": False, "probability": 0.15, "confidence": 0.0, "note": "stub prediction"}

        feature_vector = np.array([
            features.get("complexity", 3),
            features.get("assignee_load", 5),
            features.get("days_remaining", 7),
            features.get("open_blockers", 0),
            features.get("team_velocity", 10),
        ]).reshape(1, -1)

        prob = float(self.model.predict_proba(feature_vector)[0][1])
        return {
            "will_delay": prob > 0.5,
            "probability": round(prob, 4),
            "confidence": round(abs(prob - 0.5) * 2, 4),
        }
