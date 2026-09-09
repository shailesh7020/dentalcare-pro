from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user, require_roles
from app.models import Clinic, Role, User
from app.schemas.clinic import ClinicCreate, ClinicRead

router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.post(
    "",
    response_model=ClinicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a clinic",
    description="Creates a clinic. Only super administrators can create clinic tenants.",
    responses={
        403: {"description": "Super administrator role required."},
        409: {"description": "Clinic slug already exists."},
    },
)
async def create_clinic(
    payload: ClinicCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(Role.SUPER_ADMIN)),
) -> Clinic:
    if await db.scalar(select(Clinic).where(Clinic.slug == payload.slug)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Clinic slug already exists"
        )
    clinic = Clinic(**payload.model_dump())
    db.add(clinic)
    await db.commit()
    await db.refresh(clinic)
    return clinic


@router.get(
    "/current",
    response_model=ClinicRead,
    summary="Get the current clinic",
    description="Returns the clinic bound to the authenticated staff member.",
    responses={
        401: {"description": "Authentication required."},
        404: {"description": "Clinic assignment not found."},
    },
)
async def get_current_clinic(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> Clinic:
    if user.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not assigned to a clinic"
        )
    clinic = await db.get(Clinic, user.clinic_id)
    if clinic is None or not clinic.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    return clinic
