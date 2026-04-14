from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user_id
from app.schemas.organization import OrganizationCreate, OrganizationOut, OrganizationUpdate, MemberOut
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.get("/", response_model=List[OrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    return await svc.list_for_user(user_id)


@router.post("/", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    return await svc.create(payload, owner_id=user_id)


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    org = await svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.put("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    return await svc.update(org_id, payload)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    await svc.delete(org_id)


@router.get("/{org_id}/members", response_model=List[MemberOut])
async def list_members(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    svc = OrganizationService(db)
    return await svc.list_members(org_id)
