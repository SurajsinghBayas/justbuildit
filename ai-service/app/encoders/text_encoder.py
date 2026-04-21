"""
Text Encoder — TF-IDF + Latent Semantic Analysis (LSA via TruncatedSVD).

Produces 32-dimensional semantic embeddings from free-form text:
  task titles, descriptions, skill lists, risk factor strings.

Architecture note:
  This is a lightweight Transformer-free encoder that works on CPU with no
  additional model weights to download. It can be swapped to a real
  SentenceTransformer ('all-MiniLM-L6-v2') for production use by changing
  the TextEncoder class without touching anything else in the pipeline.

Saved artifacts:
  app/models/text_encoder.pkl  — fitted TF-IDF + SVD pipeline
"""

import numpy as np
import joblib
import os
from typing import List, Union
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import Normalizer

EMB_DIM = 32          # embedding dimensionality
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "text_encoder.pkl")


class TextEncoder:
    """
    Lightweight LSA text encoder.
    Fits a TF-IDF → TruncatedSVD → L2-norm pipeline on a corpus.
    Produces 32-dim unit-norm embeddings for any text string.
    """

    def __init__(self, n_components: int = EMB_DIM):
        self.n_components = n_components
        self.pipeline: Pipeline | None = None

    def fit(self, corpus: List[str]) -> "TextEncoder":
        """Fit on a list of text strings (titles + descriptions + skills)."""
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=4096,
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            )),
            ("svd", TruncatedSVD(n_components=self.n_components, random_state=42)),
            ("norm", Normalizer(norm="l2")),
        ])
        self.pipeline.fit(corpus)
        return self

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Encode one or more strings → (N, EMB_DIM) float32 array.
        Unknown words are handled gracefully by TF-IDF.
        """
        if self.pipeline is None:
            raise RuntimeError("TextEncoder not fitted. Call fit() or load() first.")
        if isinstance(texts, str):
            texts = [texts]
        return self.pipeline.transform(texts).astype(np.float32)

    def cosine_similarity(self, a: str, b: str) -> float:
        """Scalar cosine similarity between two texts (both are L2-normed → dot product)."""
        ea = self.encode(a)   # (1, D)
        eb = self.encode(b)   # (1, D)
        return float(np.dot(ea, eb.T)[0, 0])

    def save(self, path: str = MODEL_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.pipeline, path)

    def load(self, path: str = MODEL_PATH) -> "TextEncoder":
        if os.path.exists(path):
            self.pipeline = joblib.load(path)
        return self

    @classmethod
    def from_saved(cls) -> "TextEncoder":
        enc = cls()
        return enc.load()


def build_skill_text(skills: List[str]) -> str:
    """Combine a skill list into a space-joined string for encoding."""
    return " ".join(skills).lower()


def build_task_text(title: str, description: str = "", tags: List[str] = None) -> str:
    """Combine task fields into a single text document for encoding."""
    parts = [title, description] + (tags or [])
    return " ".join(p for p in parts if p).lower()
