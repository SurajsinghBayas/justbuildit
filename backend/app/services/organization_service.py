from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.membership import Membership
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> List[Organization]:
        """Return all organizations where the user is a member or owner."""
        # Get orgs via membership
        result = await self.db.execute(
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id)
            .where(Organization.is_deleted == False)
        )
        return list(result.scalars().all())

    async def get(self, org_id: str) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id, Organization.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create(self, payload: OrganizationCreate, owner_id: str) -> Organization:
        from fastapi import HTTPException
        # Check slug uniqueness
        existing = await self.get_by_slug(payload.slug)
        if existing:
            raise HTTPException(status_code=400, detail="Organization slug already taken")

        org = Organization(**payload.model_dump(), owner_id=owner_id)
        self.db.add(org)
        await self.db.flush()  # Get the org.id before creating membership

        # Auto-create membership for owner
        membership = Membership(user_id=owner_id, organization_id=org.id, role="OWNER")
        self.db.add(membership)

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def update(self, org_id: str, payload: OrganizationUpdate) -> Organization:
        from fastapi import HTTPException
        org = await self.get(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(org, field, value)
        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def delete(self, org_id: str) -> None:
        org = await self.get(org_id)
        if org:
            org.is_deleted = True
            await self.db.commit()

    async def list_members(self, org_id: str) -> List[Membership]:
        result = await self.db.execute(
            select(Membership).where(Membership.organization_id == org_id)
        )
        return list(result.scalars().all())

    async def add_member(self, org_id: str, user_id: str, role: str = "MEMBER") -> Membership:
        membership = Membership(user_id=user_id, organization_id=org_id, role=role)
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership
