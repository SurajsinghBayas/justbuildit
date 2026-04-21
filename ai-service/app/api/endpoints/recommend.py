"""
Recommendation endpoints — Siamese MLP (assignee) + LightGBM Ranker (next-task).

Assignee flow:
  task text → TextEncoder → task_emb (32)
  dev skills → TextEncoder → dev_emb (32)
  cosine_sim = dot(task_emb, dev_emb)
  X = [task_emb | dev_emb | |task-dev| | cosine_sim | dev_struct(3)]  → MLP

Next-task flow:
  [(task text → emb, cosine_sim with user_emb) for each task]
  + structured task features + sequence features + graph features
  → LightGBM Ranker → sorted scores
"""
import numpy as np
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.utils.model_loader import get_text_encoder, get_assignee_model, get_next_task_model
from app.encoders.text_encoder import build_task_text, build_skill_text
from app.encoders.sequence_encoder import SequenceEncoder, SEQ_DIM
from app.encoders.graph_encoder import GraphEncoder, GRAPH_DIM

router = APIRouter()

_seq_enc   = SequenceEncoder()
_graph_enc = GraphEncoder()

_COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
_PRIORITY_MAP   = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


# ══════════════════════════════════════════════════════════════════════════════
# 4. /recommend/assignee  — Siamese MLP
# ══════════════════════════════════════════════════════════════════════════════

class TeamMember(BaseModel):
    id:                  str
    name:                str
    skills:              List[str] = []
    open_tasks:          int       = 0
    past_success_rate:   float     = 0.75
    avg_completion_speed:float     = 1.0


class AssigneeRequest(BaseModel):
    task_id:          Optional[str] = None
    title:            str           = ""
    description:      str           = ""
    required_skills:  List[str]     = []
    tags:             List[str]     = []
    complexity_label: str           = "medium"
    team_members:     List[TeamMember] = []


@router.post("/assignee")
async def recommend_assignee(payload: AssigneeRequest):
    if not payload.team_members:
        return {"task_id": payload.task_id, "assignee_id": None,
                "name": None, "reason": "No team members provided", "score": 0}

    enc = get_text_encoder()
    model = get_assignee_model()

    task_text = build_task_text(payload.title, payload.description,
                                payload.required_skills + payload.tags)
    task_emb  = (enc.encode(task_text if task_text.strip() else "engineering task")
                 .ravel() if enc.pipeline else np.zeros(32, dtype=np.float32))

    complexity = float(_COMPLEXITY_MAP.get(payload.complexity_label, 1))
    query_skills = set(s.lower() for s in payload.required_skills + payload.tags)

    scored = []
    for member in payload.team_members:
        dev_text = build_skill_text(member.skills)
        dev_emb  = (enc.encode(dev_text if dev_text else "developer")
                    .ravel() if enc.pipeline else np.zeros(32, dtype=np.float32))

        # Siamese feature vector
        cosine_sim = float(np.dot(task_emb, dev_emb))  # both L2-normed
        diff       = np.abs(task_emb - dev_emb)
        dev_struct = np.array([float(member.open_tasks),
                               float(member.past_success_rate),
                               float(member.avg_completion_speed)], dtype=np.float32)

        X = np.concatenate([task_emb, dev_emb, diff, [cosine_sim], dev_struct]).reshape(1, -1)

        if model is not None:
            score = float(model.predict_proba(X)[0][1])
            backend = "siamese_mlp"
        else:
            # Fallback: cosine similarity + workload penalty
            member_skills = set(s.lower() for s in member.skills)
            skill_match   = (len(member_skills & query_skills) / max(len(query_skills), 1))
            score = (skill_match * 0.45 + member.past_success_rate * 0.30
                     + member.avg_completion_speed / 2 * 0.15
                     - member.open_tasks / 15 * 0.20)
            backend = "heuristic"

        member_skills_set = set(s.lower() for s in member.skills)
        matched = member_skills_set & query_skills
        scored.append((score, member, matched))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best, matched_skills = scored[0]

    reason = (
        f"Best text similarity + skill match ({len(matched_skills)}/{max(len(query_skills),1)} skills)"
        if matched_skills
        else f"Highest Siamese MLP success probability ({round(best_score*100)}%)"
    )

    return {
        "task_id":       payload.task_id,
        "assignee_id":   best.id,
        "name":          best.name,
        "score":         round(best_score, 4),
        "matched_skills":list(matched_skills),
        "open_tasks":    best.open_tasks,
        "reason":        reason,
        "model":         backend,
        "all_scores": [
            {"id": m.id, "name": m.name, "score": round(s, 4)}
            for s, m, _ in scored
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 5. /recommend/next-task  — LightGBM Ranker
# ══════════════════════════════════════════════════════════════════════════════

class NextTaskItem(BaseModel):
    id:                 str
    title:              str           = ""
    priority:           str           = "MEDIUM"
    status:             str           = "TODO"
    required_skills:    List[str]     = []
    tags:               List[str]     = []
    story_points:       int           = 3
    complexity_label:   str           = "medium"
    dependency_blocked: bool          = False
    created_at:         Optional[str] = None
    # Optional enrichment
    status_events:      List[dict]    = []
    dependency_edges:   List[List[str]] = []


class NextTaskRequest(BaseModel):
    user_id:              str
    user_skills:          List[str]         = []
    project_tasks:        List[NextTaskItem] = []
    dependency_edges:     List[List[str]]   = []   # global edge list for the sprint


@router.post("/next-task")
async def recommend_next_task(payload: NextTaskRequest):
    candidates = [t for t in payload.project_tasks
                  if t.status in ("TODO", "IN_PROGRESS")]

    if not candidates:
        return {"task_id": None, "title": None,
                "reason": "No available tasks", "ranked_tasks": []}

    enc   = get_text_encoder()
    model = get_next_task_model()

    # User skill embedding
    user_text = build_skill_text(payload.user_skills)
    user_emb  = (enc.encode(user_text if user_text else "developer")
                 .ravel() if enc.pipeline else np.zeros(32, dtype=np.float32))

    # Build shared graph for all project tasks (once)
    all_edges = [tuple(e) for e in payload.dependency_edges]
    graph_map: dict = {}
    if all_edges:
        graph_map = _graph_enc.encode_all(all_edges, [t.id for t in candidates])

    now = datetime.now(timezone.utc)

    all_rows = []
    for task in candidates:
        task_text = build_task_text(task.title, tags=task.required_skills + task.tags)
        task_emb  = (enc.encode(task_text if task_text else "engineering task")
                     .ravel() if enc.pipeline else np.zeros(32, dtype=np.float32))

        cosine_sim = float(np.dot(task_emb, user_emb))

        priority   = float(_PRIORITY_MAP.get(task.priority, 1))
        blocked    = float(task.dependency_blocked)
        complexity = float(_COMPLEXITY_MAP.get(task.complexity_label, 1))
        sp         = float(task.story_points)

        days_created = 0.0
        if task.created_at:
            try:
                created     = datetime.fromisoformat(task.created_at.replace("Z", "+00:00"))
                days_created= max((now - created).days, 0)
            except Exception:
                pass

        struct6 = np.array([priority, cosine_sim, blocked, complexity,
                             sp, min(days_created, 30)], dtype=np.float32)

        seq_feats   = _seq_enc.encode(task.status_events)                     # (10,)
        graph_feats = graph_map.get(task.id, np.zeros(GRAPH_DIM, dtype=np.float32))

        row = np.concatenate([struct6, seq_feats, graph_feats])               # (26,)
        all_rows.append(row)

    X = np.vstack(all_rows)  # (n_tasks, 26)

    if model is not None:
        scores  = model.predict(X)
        backend = "lightgbm_ranker"
    else:
        scores  = np.array([
            r[0] / 3 * 0.40 + r[1] * 0.30 - r[2] * 0.20 - r[3] / 2 * 0.05
            for r in X
        ])
        backend = "heuristic"

    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    best_score, best = ranked[0]

    return {
        "task_id":          best.id,
        "title":            best.title,
        "priority":         best.priority,
        "complexity_label": best.complexity_label,
        "story_points":     best.story_points,
        "score":            round(float(best_score), 4),
        "reason":           "LightGBM ranker: priority × skill match × sequence × graph",
        "model":            backend,
        "ranked_tasks": [
            {"id": t.id, "title": t.title, "score": round(float(s), 4)}
            for s, t in ranked[:5]
        ],
    }
