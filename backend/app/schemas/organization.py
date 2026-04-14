from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    slug: str
    logo_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationOut(OrganizationBase):
    id: str
    owner_id: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    user_id: str
    organization_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}
