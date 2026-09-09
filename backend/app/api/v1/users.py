from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models import AuditEvent, Role, User
from app.schemas.auth import UserCreate, UserRead
from app.security.passwords import hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List clinic staff",
    description="Lists active staff in the current clinic; super administrators may view all staff.",
    responses={
        401: {"description": "Authentication required."},
        403: {"description": "Administrator role required."},
    },
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    actor: User = Depends(require_roles(Role.CLINIC_ADMIN, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    query = select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
    if actor.role != Role.SUPER_ADMIN:
        query = query.where(User.clinic_id == actor.clinic_id)
    return list((await db.scalars(query.order_by(User.created_at.desc()))).all())


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a clinic staff member",
    description="Creates a staff account in the authenticated administrator's clinic using the password policy.",
    responses={
        401: {"description": "Authentication required."},
        403: {"description": "Administrator role required."},
        409: {"description": "Email is already registered."},
    },
)
async def create_user(
    payload: UserCreate,
    actor: User = Depends(require_roles(Role.CLINIC_ADMIN, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> User:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="A clinic context is required"
        )
    if payload.role == Role.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create a super admin in clinic context",
        )
    existing = await db.scalar(
        select(User).where(
            User.email == payload.email,
            User.deleted_at.is_(None),
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists"
        )
    user = User(
        clinic_id=actor.clinic_id,
        email=str(payload.email),
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
    )
    db.add(user)
    db.add(
        AuditEvent(
            clinic_id=actor.clinic_id,
            actor_id=actor.id,
            action="CREATE",
            entity_type="USER",
            entity_id=str(user.id),
        )
    )
    await db.commit()
    await db.refresh(user)
    return user
