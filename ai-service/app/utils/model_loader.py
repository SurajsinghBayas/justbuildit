"""
Model + Encoder registry — lazy-loads and caches all artifacts.

Loaded artifacts:
  text_encoder.pkl           — fitted TF-IDF + LSA pipeline
  delay_model.pkl            — XGBoostClassifier (57-dim fused)
  duration_model.pkl         — XGBoostRegressor  (37-dim fused)
  bottleneck_model.pkl       — XGBoostClassifier (44-dim fused)
  assignee_model.pkl         — Siamese MLPClassifier (100-dim)
  next_task_model.pkl        — LightGBM Ranker (26-dim fused)
  sprint_completion_model.pkl— XGBoostRegressor  (9-dim)
  sprint_success_model.pkl   — XGBoostClassifier (9-dim)
  sprint_sequence_model.pkl  — MLPRegressor      (7-dim temporal)
"""
import os
import joblib

_cache: dict = {}
_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load(name: str):
    """Load a .pkl artifact by name. Returns None if not found."""
    if name in _cache:
        return _cache[name]
    path = os.path.join(_MODEL_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        return None
    obj = joblib.load(path)
    _cache[name] = obj
    return obj


# ── Encoders ──────────────────────────────────────────────────────────────────
def get_text_encoder():
    from app.encoders.text_encoder import TextEncoder
    key = "_text_enc_instance"
    if key in _cache:
        return _cache[key]
    enc = TextEncoder()
    enc.load(os.path.join(_MODEL_DIR, "text_encoder.pkl"))
    _cache[key] = enc
    return enc


# ── Prediction models ─────────────────────────────────────────────────────────
def get_delay_model():            return load("delay_model")
def get_duration_model():         return load("duration_model")
def get_bottleneck_model():       return load("bottleneck_model")
def get_assignee_model():         return load("assignee_model")
def get_next_task_model():        return load("next_task_model")
def get_sprint_completion_model():return load("sprint_completion_model")
def get_sprint_success_model():   return load("sprint_success_model")
def get_sprint_sequence_model():  return load("sprint_sequence_model")
