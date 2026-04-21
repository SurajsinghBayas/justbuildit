"""
Prediction endpoints — all models use the full 3-encoder + fusion pipeline.

Flow per request:
  1. Parse structured fields from JSON body
  2. Encode text via TextEncoder (TF-IDF + LSA)
  3. Encode sequence events via SequenceEncoder
  4. Get graph features from GraphEncoder
  5. fuse_batch() → unified feature vector
  6. XGBoost / MLP model → predictions
  7. Return JSON with "model" field showing which backend was used
"""
import numpy as np
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.utils.model_loader import (
    get_text_encoder,
    get_delay_model, get_duration_model, get_bottleneck_model,
    get_sprint_completion_model, get_sprint_success_model,
    get_sprint_sequence_model,
)
from app.encoders.text_encoder import build_task_text
from app.encoders.sequence_encoder import SequenceEncoder, SEQ_DIM
from app.encoders.graph_encoder import GraphEncoder, GRAPH_DIM
from app.pipelines.feature_fusion import fuse, TEXT_DIM

router = APIRouter()

_seq_enc   = SequenceEncoder()
_graph_enc = GraphEncoder()

_COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
_TASK_TYPE_MAP  = {"frontend": 0, "backend": 1, "devops": 2, "testing": 3, "bug": 4}

_BOTTLENECK_KEYWORDS = [
    "third-party", "external api", "payment", "oauth", "auth",
    "migration", "legacy", "no test coverage", "untested",
    "dependency", "integration", "webhook", "rate limit",
]


# ── Shared shared helpers ──────────────────────────────────────────────────────

def _text_emb(text: str) -> np.ndarray:
    enc = get_text_encoder()
    if enc.pipeline is None:
        return np.zeros(TEXT_DIM, dtype=np.float32)
    return enc.encode(text).ravel()


def _seq_feats(events: list) -> np.ndarray:
    return _seq_enc.encode(events)


def _graph_feats(edges, node_id: str) -> np.ndarray:
    if not edges:
        return np.zeros(GRAPH_DIM, dtype=np.float32)
    G = _graph_enc.build_graph(edges)
    return _graph_enc.encode_node(G, node_id)


# ══════════════════════════════════════════════════════════════════════════════
# 1. /predict/delay
# ══════════════════════════════════════════════════════════════════════════════

class DelayPredictRequest(BaseModel):
    task_id:                   Optional[str]  = None
    title:                     str            = ""
    description:               str            = ""
    tags:                      List[str]      = []
    complexity_label:          str            = "medium"
    risk_factors:              List[str]      = []
    subtask_count:             int            = 0
    days_remaining:            Optional[float]= None
    assignee_load:             int            = 0
    story_points:              int            = 3
    estimated_time:            float          = 4.0
    past_delay_rate_assignee:  float          = 0.2
    # Sequence context
    status_events:             List[dict]     = []
    # Graph context
    dependency_edges:          List[List[str]]= []   # [[from_id, to_id], ...]


@router.post("/delay")
async def predict_delay(payload: DelayPredictRequest):
    complexity = _COMPLEXITY_MAP.get(payload.complexity_label, 1)
    risk_count = len(payload.risk_factors)
    squeeze    = (
        max(payload.story_points - (payload.days_remaining or payload.story_points), 0)
        / max(payload.story_points, 1)
    )

    structured = np.array([
        float(complexity), float(payload.subtask_count), float(risk_count),
        float(payload.assignee_load), squeeze,
        float(len(payload.dependency_edges)),
        float(payload.past_delay_rate_assignee),
    ], dtype=np.float32)

    task_text = build_task_text(payload.title, payload.description, payload.tags)
    t_emb   = _text_emb(task_text if task_text.strip() else "task")
    s_feats = _seq_feats(payload.status_events)
    g_feats = _graph_feats(
        [tuple(e) for e in payload.dependency_edges],
        payload.task_id or "task"
    )

    X = fuse(structured, t_emb, s_feats, g_feats).reshape(1, -1)

    model = get_delay_model()
    if model is not None:
        prob       = float(model.predict_proba(X)[0][1])
        will_delay = bool(model.predict(X)[0])
        backend    = "xgboost+fusion"
    else:
        prob = min(complexity / 2 * 0.35 + risk_count / 5 * 0.30
                   + min(payload.assignee_load / 15, 1) * 0.15
                   + squeeze * 0.10 + payload.past_delay_rate_assignee * 0.10, 0.99)
        will_delay = prob > 0.45
        backend    = "heuristic"

    return {
        "task_id":        payload.task_id,
        "will_delay":     will_delay,
        "probability":    round(prob, 4),
        "risk_level":     "HIGH" if prob > 0.65 else "MEDIUM" if prob > 0.35 else "LOW",
        "confidence":     round(abs(prob - 0.5) * 2, 4),
        "top_risk_factors": payload.risk_factors[:3],
        "model":          backend,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. /predict/duration
# ══════════════════════════════════════════════════════════════════════════════

class DurationPredictRequest(BaseModel):
    task_id:          Optional[str] = None
    title:            str           = ""
    description:      str           = ""
    tags:             List[str]     = []
    complexity_label: str           = "medium"
    subtask_count:    int           = 0
    story_points:     int           = 3
    estimated_time:   float         = 4.0
    task_type:        str           = "backend"
    assignee_speed:   float         = 1.0


@router.post("/duration")
async def predict_duration(payload: DurationPredictRequest):
    complexity = float(_COMPLEXITY_MAP.get(payload.complexity_label, 1))
    task_type  = float(_TASK_TYPE_MAP.get(payload.task_type, 1))

    structured = np.array([
        complexity, float(payload.story_points),
        float(payload.subtask_count), task_type, float(payload.assignee_speed),
    ], dtype=np.float32)

    task_text = build_task_text(payload.title, payload.description, payload.tags)
    t_emb = _text_emb(task_text if task_text.strip() else "task")

    # Duration: structured + text only (no graph)
    X = fuse(structured, t_emb, seq_feats=None, graph_feats=None).reshape(1, -1)

    model = get_duration_model()
    if model is not None:
        predicted = float(model.predict(X)[0])
        backend   = "xgboost+text"
    else:
        mult      = {"easy": 0.8, "medium": 1.1, "hard": 1.5}.get(payload.complexity_label, 1.1)
        predicted = payload.estimated_time * mult + payload.subtask_count * 0.5
        backend   = "heuristic"

    predicted = round(max(predicted, 0.5), 1)
    return {
        "task_id":                payload.task_id,
        "original_estimate_hours": payload.estimated_time,
        "predicted_actual_hours":  predicted,
        "delta_hours":             round(predicted - payload.estimated_time, 1),
        "model":                   backend,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. /predict/bottleneck
# ══════════════════════════════════════════════════════════════════════════════

class BottleneckRequest(BaseModel):
    task_id:              Optional[str] = None
    title:                str           = ""
    description:          str           = ""
    risk_factors:         List[str]     = []
    dependency_count:     int           = 0
    dependency_depth:     int           = 0
    num_downstream_tasks: int           = 0
    task_delay_history:   float         = 0.2
    complexity_label:     str           = "medium"
    dependency_edges:     List[List[str]] = []


@router.post("/bottleneck")
async def predict_bottleneck(payload: BottleneckRequest):
    rf_lower  = [r.lower() for r in payload.risk_factors]
    matched   = [kw for kw in _BOTTLENECK_KEYWORDS if any(kw in rf for rf in rf_lower)]
    risk_score = min(len(matched) * 0.15, 1.0)

    structured = np.array([
        float(payload.dependency_depth),
        float(payload.num_downstream_tasks),
        risk_score,
        float(payload.task_delay_history),
    ], dtype=np.float32)

    task_text = build_task_text(payload.title, payload.description, payload.risk_factors)
    t_emb = _text_emb(task_text if task_text.strip() else "blocked integration task")

    g_feats = _graph_feats(
        [tuple(e) for e in payload.dependency_edges],
        payload.task_id or "task"
    )

    # Bottleneck: structured + text + graph (no sequence — it's structural)
    X = fuse(structured, t_emb, seq_feats=None, graph_feats=g_feats).reshape(1, -1)

    model = get_bottleneck_model()
    if model is not None:
        is_bottleneck = bool(model.predict(X)[0])
        risk_prob     = float(model.predict_proba(X)[0][1])
        backend       = "xgboost+graph+text"
    else:
        risk_prob     = min(payload.dependency_depth / 7 * 0.35
                            + payload.num_downstream_tasks / 11 * 0.25
                            + risk_score * 0.25 + payload.task_delay_history * 0.15, 0.99)
        is_bottleneck = risk_prob > 0.40
        backend       = "heuristic"

    return {
        "task_id":        payload.task_id,
        "is_bottleneck":  is_bottleneck,
        "risk_level":     "HIGH" if risk_prob > 0.6 else "MEDIUM" if risk_prob > 0.3 else "LOW",
        "risk_score":     round(risk_prob, 4),
        "top_reasons":    matched[:3],
        "dependency_risk":payload.dependency_count > 2,
        "model":          backend,
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. /predict/sprint-outcome
# ══════════════════════════════════════════════════════════════════════════════

class SprintTask(BaseModel):
    story_points:      int
    complexity_label:  str   = "medium"
    delay_probability: float = 0.2


class SprintOutcomeRequest(BaseModel):
    tasks:          List[SprintTask]
    sprint_days:    int   = 14
    team_velocity:  float = 20.0
    blocked_tasks:  int   = 0
    # Velocity history for Sequence MLP (last 3 sprints, oldest first)
    past_velocities: List[float] = []


@router.post("/sprint-outcome")
async def predict_sprint_outcome(payload: SprintOutcomeRequest):
    total_sp    = float(sum(t.story_points for t in payload.tasks))
    avg_delay   = (sum(t.delay_probability for t in payload.tasks) / max(len(payload.tasks), 1))
    avg_complex = (sum(_COMPLEXITY_MAP.get(t.complexity_label, 1) for t in payload.tasks)
                   / max(len(payload.tasks), 1))

    # Velocity trend from history
    hist     = payload.past_velocities[-3:] if payload.past_velocities else []
    past_v   = hist + [payload.team_velocity] * (3 - len(hist))  # pad to 3
    vel_trend= payload.team_velocity - past_v[0]

    struct9 = np.array([
        total_sp, avg_delay, payload.team_velocity, float(payload.blocked_tasks),
        avg_complex, float(past_v[0]), float(past_v[1]), float(past_v[2]), vel_trend
    ], dtype=np.float32).reshape(1, -1)

    c_model = get_sprint_completion_model()
    s_model = get_sprint_success_model()
    seq_mlp = get_sprint_sequence_model()

    if c_model is not None:
        completion_pct = float(c_model.predict(struct9)[0])
        backend        = "xgboost"
    else:
        ratio          = min(payload.team_velocity / max(total_sp, 1), 1.5)
        completion_pct = ratio * 100 * (1 - avg_delay * 0.4) - payload.blocked_tasks * 2
        backend        = "heuristic"

    # Blend with Sequence MLP if history available
    if seq_mlp is not None and payload.past_velocities:
        seq_input = np.array([[
            past_v[0], past_v[1], past_v[2], payload.team_velocity,
            vel_trend, total_sp, avg_delay
        ]], dtype=np.float32)
        seq_pct = float(seq_mlp.predict(seq_input)[0])
        # 60% XGB + 40% sequence MLP when history exists
        completion_pct = completion_pct * 0.6 + seq_pct * 0.4
        backend        = "xgboost+sequence_mlp"

    completion_pct = round(max(min(completion_pct, 100), 0), 1)

    if s_model is not None:
        success_prob = float(s_model.predict_proba(struct9)[0][1])
    else:
        success_prob = max(min(completion_pct / 100, 0.99), 0.01)

    outcome = ("ON TRACK" if completion_pct >= 75
               else "AT RISK" if completion_pct >= 45
               else "LIKELY DELAYED")

    at_risk_sp = sum(t.story_points for t in payload.tasks if t.delay_probability > 0.5)
    overshoot  = int(max(total_sp - payload.team_velocity, 0))

    rec = (
        "Sprint looks healthy. Maintain current pace."
        if outcome == "ON TRACK"
        else f"Address {at_risk_sp} at-risk points. Consider descoping ~{overshoot} pts."
        if outcome == "AT RISK"
        else f"Over-committed by ~{overshoot} pts. Descope or extend sprint."
    )

    return {
        "total_story_points":        int(total_sp),
        "team_velocity":             payload.team_velocity,
        "predicted_completion_percent": completion_pct,
        "success_probability":       round(success_prob, 4),
        "sprint_outcome":            outcome,
        "at_risk_story_points":      at_risk_sp,
        "avg_task_delay_probability":round(avg_delay, 4),
        "recommendation":            rec,
        "model":                     backend,
    }
