from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "ACTIVE"
    organization_id: Optional[str] = None  # auto-resolved from user's first org if not provided


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectOut(ProjectBase):
    id: str
    organization_id: str
    created_by: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

