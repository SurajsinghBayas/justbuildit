from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter

from app.services.recommendation_service import RecommendationService

router = APIRouter()
svc = RecommendationService()


class TeamMember(BaseModel):
    id: str
    name: str
    open_tasks: int = 0


class RecommendAssigneeRequest(BaseModel):
    task: dict
    team: List[TeamMember]


class RecommendPriorityRequest(BaseModel):
    task_id: Optional[str] = None
    days_until_due: int = 99
    has_blockers: bool = False


@router.post("/assignee")
async def recommend_assignee(payload: RecommendAssigneeRequest):
    team = [m.model_dump() for m in payload.team]
    return svc.recommend_assignee(payload.task, team)


@router.post("/priority")
async def recommend_priority(payload: RecommendPriorityRequest):
    return svc.recommend_priority(payload.model_dump())
