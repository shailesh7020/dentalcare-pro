from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.enterprise import InventoryTransferStatus, TransferStatus
from app.models.identity import Role, User
from app.repositories.enterprise_repository import EnterpriseRepository
from app.schemas.enterprise import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    ConsolidatedFinancialsResponse,
    ConsolidatedInventoryItem,
    DepartmentBase,
    DepartmentCreate,
    DepartmentResponse,
    DuplicatePatientMatch,
    EffectiveUserPermissionsResponse,
    EnterpriseAIAnalyticsResponse,
    EnterpriseAnnouncementCreate,
    EnterpriseAnnouncementResponse,
    EnterpriseAuditLogResponse,
    EnterprisePermissionResponse,
    EnterpriseRoleCreate,
    EnterpriseRoleResponse,
    InventoryTransferCreate,
    InventoryTransferResponse,
    InventoryTransferStatusUpdateRequest,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    PatientMergeRequest,
    PatientMergeResponse,
    PatientTransferActionRequest,
    PatientTransferCreate,
    PatientTransferResponse,
    RegionBase,
    RegionCreate,
    RegionResponse,
    RegionUpdate,
    RolePermissionAssignRequest,
    UserBranchAssignmentCreate,
    UserBranchAssignmentResponse,
    UserPermissionOverrideCreate,
    UserPermissionOverrideResponse,
)
from app.services.ai.enterprise_analytics_service import EnterpriseAnalyticsService
from app.services.enterprise_service import EnterpriseService

router = APIRouter(prefix="/enterprise", tags=["Enterprise Multi-Branch Administration"])

ENTERPRISE_ADMIN_ROLES = (
    Role.SUPER_ADMIN,
    Role.ORGANIZATION_ADMIN,
    Role.REGIONAL_MANAGER,
    Role.BRANCH_MANAGER,
    Role.CLINIC_ADMIN,
)

ENTERPRISE_STAFF_ROLES = (
    Role.SUPER_ADMIN,
    Role.ORGANIZATION_ADMIN,
    Role.REGIONAL_MANAGER,
    Role.BRANCH_MANAGER,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.HYGIENIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
    Role.ACCOUNTANT,
    Role.INVENTORY_MANAGER,
)


def get_enterprise_service(db: Annotated[AsyncSession, Depends(get_db)]) -> EnterpriseService:
    return EnterpriseService(EnterpriseRepository(db))


def get_analytics_service(db: Annotated[AsyncSession, Depends(get_db)]) -> EnterpriseAnalyticsService:
    return EnterpriseAnalyticsService(db, EnterpriseRepository(db))


def check_org_access(user: User, org_id: UUID) -> None:
    if user.role != Role.SUPER_ADMIN and user.organization_id is not None and user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: user cannot access resources outside their organization.",
        )


# ---------------------------------------------------------------------------
# Permissions & Seed
# ---------------------------------------------------------------------------
@router.get("/permissions", response_model=list[EnterprisePermissionResponse])
async def list_permissions(
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[EnterprisePermissionResponse]:
    return await service.list_permissions()


@router.post("/permissions/seed", response_model=list[EnterprisePermissionResponse])
async def seed_permissions(
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[EnterprisePermissionResponse]:
    return await service.seed_permissions()


# ---------------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------------
@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> OrganizationResponse:
    return await service.create_organization(payload, actor_id=current_user.id)


@router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations(
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[OrganizationResponse]:
    return await service.list_organizations(skip=skip, limit=limit)


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> OrganizationResponse:
    check_org_access(current_user, org_id)
    org = await service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    payload: OrganizationUpdate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> OrganizationResponse:
    check_org_access(current_user, org_id)
    updated = await service.update_organization(org_id, payload, actor_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return updated


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------
@router.post("/organizations/{org_id}/regions", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_region(
    org_id: UUID,
    payload: RegionBase,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN, Role.REGIONAL_MANAGER))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> RegionResponse:
    check_org_access(current_user, org_id)
    full_payload = RegionCreate(**payload.model_dump(), organization_id=org_id)
    return await service.create_region(full_payload)


@router.get("/organizations/{org_id}/regions", response_model=list[RegionResponse])
async def list_regions(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[RegionResponse]:
    check_org_access(current_user, org_id)
    return await service.list_regions(org_id)


@router.patch("/organizations/{org_id}/regions/{region_id}", response_model=RegionResponse)
async def update_region(
    org_id: UUID,
    region_id: UUID,
    payload: RegionUpdate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN, Role.REGIONAL_MANAGER))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> RegionResponse:
    check_org_access(current_user, org_id)
    updated = await service.update_region(region_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return updated


# ---------------------------------------------------------------------------
# Branches (Clinics)
# ---------------------------------------------------------------------------
@router.post("/organizations/{org_id}/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    org_id: UUID,
    payload: BranchCreate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN, Role.REGIONAL_MANAGER))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> BranchResponse:
    check_org_access(current_user, org_id)
    if payload.organization_id != org_id:
        payload.organization_id = org_id
    return await service.create_branch(payload, actor_id=current_user.id)


@router.get("/organizations/{org_id}/branches", response_model=list[BranchResponse])
async def list_branches(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    region_id: UUID | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> list[BranchResponse]:
    check_org_access(current_user, org_id)
    return await service.list_branches(org_id=org_id, region_id=region_id, is_active=is_active, search=search)


@router.get("/branches/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> BranchResponse:
    branch = await service.get_branch(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch clinic not found")
    return branch


@router.patch("/branches/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    payload: BranchUpdate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN, Role.BRANCH_MANAGER, Role.CLINIC_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> BranchResponse:
    updated = await service.update_branch(branch_id, payload, actor_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch clinic not found")
    return updated


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------
@router.post("/branches/{branch_id}/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    branch_id: UUID,
    payload: DepartmentBase,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> DepartmentResponse:
    full_payload = DepartmentCreate(**payload.model_dump(), clinic_id=branch_id)
    return await service.create_department(full_payload)


@router.get("/branches/{branch_id}/departments", response_model=list[DepartmentResponse])
async def list_departments(
    branch_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[DepartmentResponse]:
    return await service.list_departments(branch_id)


# ---------------------------------------------------------------------------
# Roles & Permissions
# ---------------------------------------------------------------------------
@router.post("/roles", response_model=EnterpriseRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: EnterpriseRoleCreate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> EnterpriseRoleResponse:
    return await service.create_role(payload)


@router.get("/roles", response_model=list[EnterpriseRoleResponse])
async def list_roles(
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    org_id: UUID | None = None,
) -> list[EnterpriseRoleResponse]:
    return await service.list_roles(org_id=org_id)


@router.post("/roles/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def assign_role_permissions(
    role_id: UUID,
    payload: RolePermissionAssignRequest,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> dict[str, str]:
    await service.assign_role_permissions(role_id, payload.permission_ids)
    return {"message": "Role permissions assigned successfully"}


@router.post("/users/assign-branch", response_model=UserBranchAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_branch(
    payload: UserBranchAssignmentCreate,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> UserBranchAssignmentResponse:
    return await service.assign_user_branch(payload)


@router.get("/users/{user_id}/branches", response_model=list[UserBranchAssignmentResponse])
async def get_user_branch_assignments(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[UserBranchAssignmentResponse]:
    return await service.get_user_branch_assignments(user_id)


@router.post("/users/permission-override", response_model=UserPermissionOverrideResponse)
async def set_user_permission_override(
    payload: UserPermissionOverrideCreate,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> UserPermissionOverrideResponse:
    return await service.set_user_permission_override(payload)


@router.get("/users/{user_id}/effective-permissions", response_model=EffectiveUserPermissionsResponse)
async def get_effective_user_permissions(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> EffectiveUserPermissionsResponse:
    return await service.resolve_user_permissions(user_id)


# ---------------------------------------------------------------------------
# Patient Transfers & Merges
# ---------------------------------------------------------------------------
@router.post("/organizations/{org_id}/transfers/patients", response_model=PatientTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_transfer(
    org_id: UUID,
    payload: PatientTransferCreate,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> PatientTransferResponse:
    return await service.create_patient_transfer(org_id, payload, actor_id=current_user.id)


@router.get("/organizations/{org_id}/transfers/patients", response_model=list[PatientTransferResponse])
async def list_patient_transfers(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    clinic_id: UUID | None = None,
    status: TransferStatus | None = None,
) -> list[PatientTransferResponse]:
    return await service.list_patient_transfers(org_id, clinic_id=clinic_id, status=status)


@router.post("/organizations/{org_id}/transfers/patients/{transfer_id}/action", response_model=PatientTransferResponse)
async def handle_patient_transfer(
    org_id: UUID,
    transfer_id: UUID,
    payload: PatientTransferActionRequest,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> PatientTransferResponse:
    updated = await service.handle_patient_transfer(transfer_id, payload, actor_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient transfer not found")
    return updated


@router.get("/organizations/{org_id}/patients/duplicates", response_model=list[DuplicatePatientMatch])
async def search_duplicate_patients(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> list[DuplicatePatientMatch]:
    return await service.find_duplicate_patients(org_id, name=name, phone=phone, email=email)


@router.post("/organizations/{org_id}/patients/merge", response_model=PatientMergeResponse)
async def merge_patients(
    org_id: UUID,
    payload: PatientMergeRequest,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> PatientMergeResponse:
    try:
        return await service.merge_patients(org_id, payload, actor_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Inter-Branch Inventory Transfers
# ---------------------------------------------------------------------------
@router.post("/organizations/{org_id}/transfers/inventory", response_model=InventoryTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_transfer(
    org_id: UUID,
    payload: InventoryTransferCreate,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> InventoryTransferResponse:
    return await service.create_inventory_transfer(org_id, payload, actor_id=current_user.id)


@router.get("/organizations/{org_id}/transfers/inventory", response_model=list[InventoryTransferResponse])
async def list_inventory_transfers(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    clinic_id: UUID | None = None,
    status: InventoryTransferStatus | None = None,
) -> list[InventoryTransferResponse]:
    return await service.list_inventory_transfers(org_id, clinic_id=clinic_id, status=status)


@router.post("/organizations/{org_id}/transfers/inventory/{transfer_id}/status", response_model=InventoryTransferResponse)
async def update_inventory_transfer_status(
    org_id: UUID,
    transfer_id: UUID,
    payload: InventoryTransferStatusUpdateRequest,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> InventoryTransferResponse:
    try:
        updated = await service.update_inventory_transfer_status(
            transfer_id, payload, actor_id=current_user.id
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory transfer not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{org_id}/inventory/consolidated", response_model=list[ConsolidatedInventoryItem])
async def get_consolidated_inventory(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> list[ConsolidatedInventoryItem]:
    return await service.get_consolidated_inventory(org_id)


# ---------------------------------------------------------------------------
# Consolidated Financials
# ---------------------------------------------------------------------------
@router.get("/organizations/{org_id}/financials/consolidated", response_model=ConsolidatedFinancialsResponse)
async def get_consolidated_financials(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES, Role.ACCOUNTANT))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> ConsolidatedFinancialsResponse:
    return await service.get_consolidated_financials(org_id)


# ---------------------------------------------------------------------------
# AI Enterprise Analytics
# ---------------------------------------------------------------------------
@router.get("/organizations/{org_id}/analytics", response_model=EnterpriseAIAnalyticsResponse)
async def get_enterprise_analytics(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    analytics_service: Annotated[EnterpriseAnalyticsService, Depends(get_analytics_service)],
) -> EnterpriseAIAnalyticsResponse:
    return await analytics_service.generate_enterprise_analytics(org_id)


# ---------------------------------------------------------------------------
# Announcements & Audit Logs
# ---------------------------------------------------------------------------
@router.post("/organizations/{org_id}/announcements", response_model=EnterpriseAnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    org_id: UUID,
    payload: EnterpriseAnnouncementCreate,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_ADMIN_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
) -> EnterpriseAnnouncementResponse:
    return await service.create_announcement(org_id, payload, actor_id=current_user.id)


@router.get("/organizations/{org_id}/announcements", response_model=list[EnterpriseAnnouncementResponse])
async def list_announcements(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(*ENTERPRISE_STAFF_ROLES))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    active_only: Annotated[bool, Query()] = True,
) -> list[EnterpriseAnnouncementResponse]:
    return await service.list_announcements(org_id, active_only=active_only)


@router.get("/organizations/{org_id}/audit-logs", response_model=list[EnterpriseAuditLogResponse])
async def list_audit_logs(
    org_id: UUID,
    current_user: Annotated[User, Depends(require_roles(Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN))],
    service: Annotated[EnterpriseService, Depends(get_enterprise_service)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EnterpriseAuditLogResponse]:
    return await service.list_audit_logs(org_id, limit=limit)
