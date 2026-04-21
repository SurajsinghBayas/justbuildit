from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.membership import Membership
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: str) -> List[Organization]:
        """Return all organizations where the user is a member or owner."""
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

    async def get_user_role(self, org_id: str, user_id: str) -> Optional[str]:
        """Return the role of a user in an org, or None if not a member."""
        result = await self.db.execute(
            select(Membership.role).where(
                Membership.organization_id == org_id,
                Membership.user_id == user_id,
            )
        )
        row = result.scalar_one_or_none()
        return row

    async def create(self, payload: OrganizationCreate, owner_id: str) -> Organization:
        from fastapi import HTTPException
        import re, random, string

        # Auto-generate slug from name if not provided
        raw_slug = payload.slug or payload.name
        slug = re.sub(r'[^a-z0-9]+', '-', raw_slug.lower()).strip('-')
        base_slug = slug
        for _ in range(10):
            existing = await self.get_by_slug(slug)
            if not existing:
                break
            slug = base_slug + '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        else:
            raise HTTPException(status_code=400, detail="Could not generate a unique slug")

        org = Organization(name=payload.name, slug=slug, logo_url=payload.logo_url, owner_id=owner_id)
        self.db.add(org)
        await self.db.flush()

        # Auto-create OWNER membership
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

    async def list_members_with_details(self, org_id: str) -> list:
        """Return memberships joined with user details (name, email, avatar)."""
        result = await self.db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id)
            .order_by(Membership.joined_at)
        )
        rows = result.all()
        members = []
        for membership, user in rows:
            members.append({
                "user_id": membership.user_id,
                "organization_id": membership.organization_id,
                "role": membership.role,
                "joined_at": membership.joined_at,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
            })
        return members

    async def add_member(self, org_id: str, user_id: str, role: str = "MEMBER") -> Membership:
        membership = Membership(user_id=user_id, organization_id=org_id, role=role)
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def add_member_by_email(self, org_id: str, email: str, role: str = "MEMBER") -> dict:
        from fastapi import HTTPException
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"No user found with email: {email}")
        existing = await self.db.execute(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
        membership = Membership(user_id=user.id, organization_id=org_id, role=role)
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)

        # Notify via email (fire and forget)
        try:
            from app.core.email import notify_added_to_org
            org = await self.get(org_id)
            # Find inviter name (caller of this method)
            # For now we use a generic placeholder or could pass it in. 
            # Let's assume we don't have inviter name easily here without extra query.
            # I will just use "A team member" for now or find it if user_id is passed.
            await notify_added_to_org(user.email, org.name if org else "the organization", "A team member")
        except:
            pass

        return {
            "user_id": user.id,
            "organization_id": org_id,
            "role": role,
            "joined_at": membership.joined_at,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
        }

    async def remove_member(self, org_id: str, user_id: str) -> None:
        result = await self.db.execute(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership:
            if membership.role == "OWNER":
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="Cannot remove the organization owner")
            await self.db.delete(membership)
            await self.db.commit()

    async def update_member_role(self, org_id: str, user_id: str, role: str) -> dict:
        from fastapi import HTTPException
        result = await self.db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id, Membership.user_id == user_id)
        )
        row = result.one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail="Member not found")
        
        membership, user = row
        if membership.role == "OWNER":
            raise HTTPException(status_code=400, detail="Cannot change the role of the organization owner")
            
        membership.role = role
        await self.db.commit()
        await self.db.refresh(membership)
        return {
            "user_id": user.id,
            "organization_id": org_id,
            "role": role,
            "joined_at": membership.joined_at,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
        }

