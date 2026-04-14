from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter

from app.services.prediction_service import PredictionService

router = APIRouter()
svc = PredictionService()


class PredictRequest(BaseModel):
    task_id: Optional[str] = None
    complexity: float = 3.0       # 1-5 scale
    assignee_load: float = 5.0    # number of open tasks on assignee
    days_remaining: float = 7.0   # days until due date
    open_blockers: int = 0
    team_velocity: float = 10.0   # tasks completed per sprint


@router.post("/delay")
async def predict_delay(payload: PredictRequest):
    result = svc.predict_delay(payload.model_dump())
    return {"task_id": payload.task_id, **result}
