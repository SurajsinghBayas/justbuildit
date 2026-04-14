from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    deadline: Optional[datetime] = None
    estimated_time: Optional[float] = None
    actual_time: Optional[float] = None
    tags: List[str] = []


class TaskCreate(TaskBase):
    project_id: str
    organization_id: str
    assigned_to: Optional[str] = None
    created_by: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[datetime] = None
    actual_time: Optional[float] = None
    tags: Optional[List[str]] = None


class TaskStatusUpdate(BaseModel):
    status: str


class TaskOut(TaskBase):
    id: str
    project_id: str
    organization_id: str
    assigned_to: Optional[str] = None
    created_by: str
    github_issue_number: Optional[int] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
