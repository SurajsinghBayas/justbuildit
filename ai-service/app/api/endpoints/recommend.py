"""
XGBoost-backed recommendation endpoints.
Falls back to calibrated heuristics when models are not yet trained.
"""
import numpy as np
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter

from app.utils.model_loader import get_assignee_model, get_next_task_model

router = APIRouter()

_COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
_PRIORITY_MAP = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


# ══════════════════════════════════════════════════════════════════════════════
# 4. /recommend/assignee
# ══════════════════════════════════════════════════════════════════════════════

class TeamMember(BaseModel):
    id: str
    name: str
    skills: List[str] = []
    open_tasks: int = 0
    past_success_rate: float = 0.75    # 0–1
    avg_completion_speed: float = 1.0  # multiplier vs estimate


class AssigneeRequest(BaseModel):
    task_id: Optional[str] = None
    required_skills: List[str] = []
    tags: List[str] = []
    complexity_label: str = "medium"
    team_members: List[TeamMember] = []


@router.post("/assignee")
async def recommend_assignee(payload: AssigneeRequest):
    """
    Ranks each team member using XGBoostClassifier success probability.
    Features: skill_match_score, dev_load, past_success_rate,
              avg_completion_speed, complexity
    """
    if not payload.team_members:
        return {
            "task_id": payload.task_id,
            "assignee_id": None, "name": None,
            "reason": "No team members provided", "score": 0,
        }

    query_skills = set(s.lower() for s in payload.required_skills + payload.tags)
    complexity = float(_COMPLEXITY_MAP.get(payload.complexity_label, 1))
    model = get_assignee_model()

    scores = []
    for member in payload.team_members:
        member_skills = set(s.lower() for s in member.skills)
        skill_match = (
            len(member_skills & query_skills) / len(query_skills)
            if query_skills else 0.5
        )

        features = np.array([[
            skill_match,
            float(member.open_tasks),
            float(member.past_success_rate),
            float(member.avg_completion_speed),
            complexity,
        ]])

        if model is not None:
            score = float(model.predict_proba(features)[0][1])  # P(success)
        else:
            score = (
                skill_match * 0.45
                + member.past_success_rate * 0.30
                + member.avg_completion_speed / 2 * 0.15
                - member.open_tasks / 15 * 0.20
                - complexity / 2 * 0.10
            )

        matched = member_skills & query_skills
        scores.append((score, member, matched))

    scores.sort(key=lambda x: x[0], reverse=True)
    best_score, best, matched_skills = scores[0]

    reason = (
        f"Best skill match ({len(matched_skills)}/{max(len(query_skills),1)} skills: {', '.join(list(matched_skills)[:3])})"
        if matched_skills
        else f"Highest predicted success rate ({round(best_score*100)}%)"
    )

    return {
        "task_id": payload.task_id,
        "assignee_id": best.id,
        "name": best.name,
        "score": round(best_score, 4),
        "matched_skills": list(matched_skills),
        "open_tasks": best.open_tasks,
        "reason": reason,
        "model": "xgboost" if model is not None else "heuristic",
        "all_scores": [
            {"id": m.id, "name": m.name, "score": round(s, 4)}
            for s, m, _ in scores
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. /recommend/next-task
# ══════════════════════════════════════════════════════════════════════════════

class NextTaskItem(BaseModel):
    id: str
    title: str
    priority: str = "MEDIUM"
    status: str = "TODO"
    required_skills: List[str] = []
    story_points: int = 3
    complexity_label: str = "medium"
    dependency_blocked: bool = False
    created_at: Optional[str] = None  # ISO string


class NextTaskRequest(BaseModel):
    user_id: str
    user_skills: List[str] = []
    project_tasks: List[NextTaskItem] = []


@router.post("/next-task")
async def recommend_next_task(payload: NextTaskRequest):
    """
    Ranks available tasks using XGBoostClassifier pick-probability.
    Features: priority, skill_match, dep_blocked, complexity, story_points, days_since_created
    """
    candidates = [
        t for t in payload.project_tasks
        if t.status in ("TODO", "IN_PROGRESS")
    ]

    if not candidates:
        return {"task_id": None, "title": None, "reason": "No available tasks"}

    user_skills = set(s.lower() for s in payload.user_skills)
    model = get_next_task_model()
    now = datetime.now(timezone.utc)

    scored = []
    for task in candidates:
        required = set(s.lower() for s in task.required_skills)
        skill_match = (
            len(user_skills & required) / len(required)
            if required else 0.5
        )
        priority_num = float(_PRIORITY_MAP.get(task.priority, 1))
        complexity_num = float(_COMPLEXITY_MAP.get(task.complexity_label, 1))
        blocked = float(task.dependency_blocked)

        # Days since created
        days_created = 0.0
        if task.created_at:
            try:
                created = datetime.fromisoformat(task.created_at.replace("Z", "+00:00"))
                days_created = max((now - created).days, 0)
            except Exception:
                pass

        features = np.array([[
            priority_num,
            skill_match,
            blocked,
            complexity_num,
            float(task.story_points),
            float(min(days_created, 30)),
        ]])

        if model is not None:
            score = float(model.predict_proba(features)[0][1])
        else:
            score = (
                priority_num / 3 * 0.40
                + skill_match * 0.30
                - blocked * 0.20
                - complexity_num / 2 * 0.05
                + min(days_created, 30) / 30 * 0.05
            )

        scored.append((score, task))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]

    return {
        "task_id": best.id,
        "title": best.title,
        "priority": best.priority,
        "complexity_label": best.complexity_label,
        "story_points": best.story_points,
        "score": round(best_score, 4),
        "reason": "Highest ML pick-probability based on priority, skill match, and dependencies",
        "model": "xgboost" if model is not None else "heuristic",
        "ranked_tasks": [
            {"id": t.id, "title": t.title, "score": round(s, 4)}
            for s, t in scored[:5]
        ],
    }
