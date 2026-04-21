"""
Feature Fusion Layer.

Concatenates all three encoder outputs (text embeddings, sequence features,
graph features) with raw structured features into a single unified feature
vector before it is fed to any downstream model.

                ┌─────────────────────────────────────────────┐
                │              Feature Fusion                  │
                │                                              │
                │  structured (N_structured)                   │
                │  + text_emb  (32)                            │
                │  + seq_feats (10)                            │
                │  + graph_feats (8)                           │
                │  ─────────────────                           │
                │  = unified vector (50 + N_structured dims)  │
                └─────────────────────────────────────────────┘

Total fused dimension breakdown:
  Structured features:  7  (delay) / 5 (duration) / 4 (bottleneck) / etc.
  Text embedding:       32
  Sequence features:    10
  Graph features:        8
"""

import numpy as np
from typing import Optional

TEXT_DIM = 32   # from text_encoder.py
SEQ_DIM = 10    # from sequence_encoder.py
GRAPH_DIM = 8   # from graph_encoder.py


def fuse(
    structured: np.ndarray,
    text_emb: Optional[np.ndarray] = None,
    seq_feats: Optional[np.ndarray] = None,
    graph_feats: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Concatenate all feature blocks into a single row vector.

    Args:
        structured:  (N_s,) structured numeric features
        text_emb:    (32,)  text encoder output — None → zeros
        seq_feats:   (10,)  sequence encoder output — None → zeros
        graph_feats: (8,)   graph encoder output — None → zeros

    Returns:
        (N_s + 32 + 10 + 8,) unified float32 vector
    """
    parts = [structured.astype(np.float32).ravel()]

    parts.append(
        text_emb.ravel().astype(np.float32)
        if text_emb is not None
        else np.zeros(TEXT_DIM, dtype=np.float32)
    )
    parts.append(
        seq_feats.ravel().astype(np.float32)
        if seq_feats is not None
        else np.zeros(SEQ_DIM, dtype=np.float32)
    )
    parts.append(
        graph_feats.ravel().astype(np.float32)
        if graph_feats is not None
        else np.zeros(GRAPH_DIM, dtype=np.float32)
    )

    return np.concatenate(parts)


def fuse_batch(
    structured: np.ndarray,
    text_emb: Optional[np.ndarray] = None,
    seq_feats: Optional[np.ndarray] = None,
    graph_feats: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Batch version of fuse().

    Args:
        structured:  (N, N_s)
        text_emb:    (N, 32) or None
        seq_feats:   (N, 10) or None
        graph_feats: (N,  8) or None

    Returns:
        (N, N_s + 32 + 10 + 8) matrix
    """
    n = structured.shape[0]

    parts = [structured.astype(np.float32)]
    parts.append(
        text_emb.astype(np.float32)
        if text_emb is not None
        else np.zeros((n, TEXT_DIM), dtype=np.float32)
    )
    parts.append(
        seq_feats.astype(np.float32)
        if seq_feats is not None
        else np.zeros((n, SEQ_DIM), dtype=np.float32)
    )
    parts.append(
        graph_feats.astype(np.float32)
        if graph_feats is not None
        else np.zeros((n, GRAPH_DIM), dtype=np.float32)
    )

    return np.hstack(parts)


def total_dim(n_structured: int) -> int:
    """Return the total fused feature dimension."""
    return n_structured + TEXT_DIM + SEQ_DIM + GRAPH_DIM
