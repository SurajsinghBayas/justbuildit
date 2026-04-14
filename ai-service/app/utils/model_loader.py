from typing import Optional
import joblib
import os

_model_cache: dict = {}


def load_model(path: str):
    """Load a joblib model with singleton caching."""
    if path in _model_cache:
        return _model_cache[path]

    if not os.path.exists(path):
        return None  # Model not trained yet

    model = joblib.load(path)
    _model_cache[path] = model
    return model
