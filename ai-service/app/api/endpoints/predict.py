"""
XGBoost-backed prediction endpoints.
Falls back to calibrated heuristics when model files are not yet trained.
API contracts are unchanged from the heuristic version.
"""
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter

from app.utils.model_loader import (
    get_delay_model, get_duration_model, get_bottleneck_model,
    get_sprint_completion_model, get_sprint_success_model,
)

router = APIRouter()

# ── Encoding maps (must match training.py exactly) ─────────────────────────────
_COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
_COMPLEXITY_MULTIPLIER = {"easy": 0.8, "medium": 1.1, "hard": 1.5}
_TASK_TYPE_MAP = {"frontend": 0, "backend": 1, "devops": 2, "testing": 3, "bug": 4}
_HIGH_RISK_KEYWORDS = [
    "third-party", "external api", "payment", "oauth", "auth",
    "migration", "legacy", "no test coverage", "untested",
    "dependency", "integration", "webhook", "rate limit",
]


# ══════════════════════════════════════════════════════════════════════════════
# 1. /predict/delay
# ══════════════════════════════════════════════════════════════════════════════

class DelayPredictRequest(BaseModel):
    task_id: Optional[str] = None
    complexity_label: str = "medium"
    risk_factors: List[str] = []
    subtask_count: int = 0
    days_remaining: Optional[float] = None
    assignee_load: int = 0
    story_points: int = 3
    estimated_time: float = 4.0
    past_delay_rate_assignee: float = 0.2    # historical assignee delay rate


@router.post("/delay")
async def predict_delay(payload: DelayPredictRequest):
    """
    Binary delay classification + probability via XGBoostClassifier.
    Features: complexity, num_subtasks, risk_count, assignee_load,
              deadline_squeeze_ratio, dependency_count, past_delay_rate_assignee
    """
    complexity = _COMPLEXITY_MAP.get(payload.complexity_label, 1)
    risk_count = len(payload.risk_factors)
    squeeze = (
        max(payload.story_points - payload.days_remaining, 0) / max(payload.story_points, 1)
        if payload.days_remaining is not None else 0.5
    )

    features = np.array([[
        complexity,
        payload.subtask_count,
        risk_count,
        payload.assignee_load,
        squeeze,
        0,   # dependency_count (not in request yet — default 0)
        payload.past_delay_rate_assignee,
    ]])

    model = get_delay_model()
    if model is not None:
        prob = float(model.predict_proba(features)[0][1])
        will_delay = bool(model.predict(features)[0])
    else:
        # Calibrated heuristic fallback
        prob = min(
            complexity / 2 * 0.35
            + risk_count / 5 * 0.30
            + min(payload.assignee_load / 15, 1) * 0.15
            + squeeze * 0.10
            + payload.past_delay_rate_assignee * 0.10,
            0.99,
        )
        will_delay = prob > 0.45

    risk_level = "HIGH" if prob > 0.65 else "MEDIUM" if prob > 0.35 else "LOW"

    return {
        "task_id": payload.task_id,
        "will_delay": will_delay,
        "probability": round(prob, 4),
        "risk_level": risk_level,
        "confidence": round(abs(prob - 0.5) * 2, 4),
        "model": "xgboost" if model is not None else "heuristic",
        "top_risk_factors": payload.risk_factors[:3],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 2. /predict/duration
# ══════════════════════════════════════════════════════════════════════════════

class DurationPredictRequest(BaseModel):
    task_id: Optional[str] = None
    complexity_label: str = "medium"
    subtask_count: int = 0
    story_points: int = 3
    estimated_time: float = 4.0
    task_type: str = "backend"
    assignee_speed: float = 1.0    # multiplier: >1 = faster, <1 = slower


@router.post("/duration")
async def predict_duration(payload: DurationPredictRequest):
    """
    Regression: predicted actual hours via XGBoostRegressor.
    Features: complexity, story_points, num_subtasks, task_type, assignee_speed
    """
    complexity = _COMPLEXITY_MAP.get(payload.complexity_label, 1)
    task_type = _TASK_TYPE_MAP.get(payload.task_type, 1)

    features = np.array([[
        float(complexity),
        float(payload.story_points),
        float(payload.subtask_count),
        float(task_type),
        float(payload.assignee_speed),
    ]])

    model = get_duration_model()
    if model is not None:
        predicted_hours = float(model.predict(features)[0])
    else:
        mult = _COMPLEXITY_MULTIPLIER.get(payload.complexity_label, 1.1)
        predicted_hours = payload.estimated_time * mult + payload.subtask_count * 0.5

    predicted_hours = round(max(predicted_hours, 0.5), 1)

    return {
        "task_id": payload.task_id,
        "original_estimate_hours": payload.estimated_time,
        "predicted_actual_hours": predicted_hours,
        "delta_hours": round(predicted_hours - payload.estimated_time, 1),
        "model": "xgboost" if model is not None else "heuristic",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 3. /predict/bottleneck
# ══════════════════════════════════════════════════════════════════════════════

class BottleneckRequest(BaseModel):
    task_id: Optional[str] = None
    risk_factors: List[str] = []
    dependency_count: int = 0
    dependency_depth: int = 0
    num_downstream_tasks: int = 0
    task_delay_history: float = 0.2   # historical delay rate for this task type
    complexity_label: str = "medium"
    subtask_count: int = 0


@router.post("/bottleneck")
async def predict_bottleneck(payload: BottleneckRequest):
    """
    Binary bottleneck classification via XGBoostClassifier.
    Features: dependency_depth, num_downstream_tasks, risk_score, task_delay_history
    """
    # Derive risk_score from keyword matching
    risk_factors_lower = [r.lower() for r in payload.risk_factors]
    matched = [kw for kw in _HIGH_RISK_KEYWORDS if any(kw in rf for rf in risk_factors_lower)]
    risk_score = min(len(matched) * 0.15, 1.0)

    features = np.array([[
        float(payload.dependency_depth),
        float(payload.num_downstream_tasks),
        risk_score,
        float(payload.task_delay_history),
    ]])

    model = get_bottleneck_model()
    if model is not None:
        is_bottleneck = bool(model.predict(features)[0])
        risk_prob = float(model.predict_proba(features)[0][1])
    else:
        risk_prob = min(
            payload.dependency_depth / 7 * 0.35
            + payload.num_downstream_tasks / 11 * 0.25
            + risk_score * 0.25
            + payload.task_delay_history * 0.15,
            0.99,
        )
        is_bottleneck = risk_prob > 0.40

    risk_level = "HIGH" if risk_prob > 0.6 else "MEDIUM" if risk_prob > 0.3 else "LOW"

    return {
        "task_id": payload.task_id,
        "is_bottleneck": is_bottleneck,
        "risk_level": risk_level,
        "risk_score": round(risk_prob, 4),
        "top_reasons": matched[:3],
        "dependency_risk": payload.dependency_count > 2,
        "model": "xgboost" if model is not None else "heuristic",
    }


# ══════════════════════════════════════════════════════════════════════════════
# 4. /predict/sprint-outcome
# ══════════════════════════════════════════════════════════════════════════════

class SprintTask(BaseModel):
    story_points: int
    complexity_label: str = "medium"
    delay_probability: float = 0.2


class SprintOutcomeRequest(BaseModel):
    tasks: List[SprintTask]
    sprint_days: int = 14
    team_velocity: float = 20.0
    blocked_tasks: int = 0


@router.post("/sprint-outcome")
async def predict_sprint_outcome(payload: SprintOutcomeRequest):
    """
    Dual output: completion % (XGBRegressor) + success probability (XGBClassifier).
    Features: total_story_points, avg_delay_prob, team_velocity, blocked_tasks, avg_complexity
    """
    total_sp = sum(t.story_points for t in payload.tasks)
    avg_delay = (
        sum(t.delay_probability for t in payload.tasks) / len(payload.tasks)
        if payload.tasks else 0.2
    )
    avg_complexity = (
        sum(_COMPLEXITY_MAP.get(t.complexity_label, 1) for t in payload.tasks) / max(len(payload.tasks), 1)
    )

    features = np.array([[
        float(total_sp),
        float(avg_delay),
        float(payload.team_velocity),
        float(payload.blocked_tasks),
        avg_complexity,
    ]])

    completion_model = get_sprint_completion_model()
    success_model = get_sprint_success_model()

    if completion_model is not None:
        completion_pct = float(completion_model.predict(features)[0])
    else:
        ratio = min(payload.team_velocity / max(total_sp, 1), 1.5)
        completion_pct = ratio * 100 * (1 - avg_delay * 0.4) - payload.blocked_tasks * 2

    completion_pct = round(max(min(completion_pct, 100), 0), 1)

    if success_model is not None:
        success_prob = float(success_model.predict_proba(features)[0][1])
    else:
        success_prob = max(min(completion_pct / 100, 0.99), 0.01)

    outcome = (
        "ON TRACK" if completion_pct >= 75
        else "AT RISK" if completion_pct >= 45
        else "LIKELY DELAYED"
    )
    at_risk_sp = sum(t.story_points for t in payload.tasks if t.delay_probability > 0.5)

    rec = (
        "Sprint looks healthy. Maintain current pace."
        if outcome == "ON TRACK"
        else f"Address {at_risk_sp} at-risk story points. Consider descoping {int(max(total_sp - payload.team_velocity, 0))} pts."
        if outcome == "AT RISK"
        else f"Sprint over-committed by ~{int(max(total_sp - payload.team_velocity, 0))} pts. Descope or extend."
    )

    return {
        "total_story_points": total_sp,
        "team_velocity": payload.team_velocity,
        "predicted_completion_percent": completion_pct,
        "success_probability": round(success_prob, 4),
        "sprint_outcome": outcome,
        "at_risk_story_points": at_risk_sp,
        "avg_task_delay_probability": round(avg_delay, 4),
        "recommendation": rec,
        "model": "xgboost" if completion_model is not None else "heuristic",
    }
