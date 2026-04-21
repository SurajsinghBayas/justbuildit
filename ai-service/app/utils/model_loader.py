"""Model registry — loads all XGBoost models at startup and caches them."""
import os
import joblib
from typing import Optional

_cache: dict = {}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_model(name: str):
    """Load a .pkl model by name (without extension). Returns None if not found."""
    if name in _cache:
        return _cache[name]
    path = os.path.join(MODEL_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        return None
    model = joblib.load(path)
    _cache[name] = model
    return model


def get_delay_model():
    return load_model("delay_model")

def get_duration_model():
    return load_model("duration_model")

def get_bottleneck_model():
    return load_model("bottleneck_model")

def get_assignee_model():
    return load_model("assignee_model")

def get_next_task_model():
    return load_model("next_task_model")

def get_sprint_completion_model():
    return load_model("sprint_completion_model")

def get_sprint_success_model():
    return load_model("sprint_success_model")
