from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None


class OrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str] = None
    owner_id: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Simple membership (just IDs)
class MemberOut(BaseModel):
    user_id: str
    organization_id: str
    role: str
    joined_at: datetime

    model_config = {"from_attributes": True}


# Rich membership — includes user details (name + email)
class MemberDetailOut(BaseModel):
    user_id: str
    organization_id: str
    role: str
    joined_at: datetime
    # User details
    name: str
    email: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}
