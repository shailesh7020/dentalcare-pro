from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from app.models.enterprise import (
    EnterprisePermission,
    InventoryTransferStatus,
    TransferStatus,
)
from app.models.inventory import InventoryItem
from app.repositories.enterprise_repository import EnterpriseRepository
from app.schemas.enterprise import (
    BranchCreate,
    BranchResponse,
    BranchUpdate,
    ConsolidatedFinancialsResponse,
    ConsolidatedInventoryItem,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DuplicatePatientMatch,
    EffectiveUserPermissionsResponse,
    EnterpriseAnnouncementCreate,
    EnterpriseAnnouncementResponse,
    EnterpriseAnnouncementUpdate,
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
    RegionCreate,
    RegionResponse,
    RegionUpdate,
    UserBranchAssignmentCreate,
    UserBranchAssignmentResponse,
    UserPermissionOverrideCreate,
    UserPermissionOverrideResponse,
)


class EnterpriseService:
    def __init__(self, repo: EnterpriseRepository):
        self.repo = repo

    # -----------------------------------------------------------------------
    # System Setup
    # -----------------------------------------------------------------------
    async def seed_permissions(self) -> list[EnterprisePermissionResponse]:
        perms = await self.repo.seed_system_permissions()
        return [EnterprisePermissionResponse.model_validate(p) for p in perms]

    # -----------------------------------------------------------------------
    # Organizations
    # -----------------------------------------------------------------------
    async def create_organization(self, payload: OrganizationCreate, actor_id: UUID | None = None) -> OrganizationResponse:
        slug = payload.code.lower().replace(" ", "-")
        org_data = payload.model_dump()
        org_data["slug"] = slug
        org = await self.repo.create_organization(org_data)

        # Audit log
        await self.repo.create_audit_log(
            {
                "organization_id": org.id,
                "actor_id": actor_id,
                "action": "ORGANIZATION_CREATED",
                "resource_type": "organization",
                "resource_id": str(org.id),
                "details_json": json.dumps({"name": org.name, "code": org.code}),
            }
        )
        return OrganizationResponse.model_validate(org)

    async def get_organization(self, org_id: UUID) -> OrganizationResponse | None:
        org = await self.repo.get_organization(org_id)
        return OrganizationResponse.model_validate(org) if org else None

    async def list_organizations(self, skip: int = 0, limit: int = 50) -> list[OrganizationResponse]:
        orgs = await self.repo.list_organizations(skip=skip, limit=limit)
        return [OrganizationResponse.model_validate(o) for o in orgs]

    async def update_organization(
        self, org_id: UUID, payload: OrganizationUpdate, actor_id: UUID | None = None
    ) -> OrganizationResponse | None:
        updated = await self.repo.update_organization(org_id, payload.model_dump(exclude_unset=True))
        if not updated:
            return None
        await self.repo.create_audit_log(
            {
                "organization_id": org_id,
                "actor_id": actor_id,
                "action": "ORGANIZATION_UPDATED",
                "resource_type": "organization",
                "resource_id": str(org_id),
                "details_json": json.dumps(payload.model_dump(exclude_unset=True, mode="json")),
            }
        )
        return OrganizationResponse.model_validate(updated)

    # -----------------------------------------------------------------------
    # Regions
    # -----------------------------------------------------------------------
    async def create_region(self, payload: RegionCreate) -> RegionResponse:
        region = await self.repo.create_region(payload.model_dump())
        return RegionResponse.model_validate(region)

    async def list_regions(self, org_id: UUID) -> list[RegionResponse]:
        regions = await self.repo.list_regions(org_id)
        responses = []
        for r in regions:
            count = await self.repo.count_branches_in_region(r.id)
            resp = RegionResponse.model_validate(r)
            resp.branch_count = count
            responses.append(resp)
        return responses

    async def update_region(self, region_id: UUID, payload: RegionUpdate) -> RegionResponse | None:
        region = await self.repo.update_region(region_id, payload.model_dump(exclude_unset=True))
        if not region:
            return None
        count = await self.repo.count_branches_in_region(region.id)
        resp = RegionResponse.model_validate(region)
        resp.branch_count = count
        return resp

    # -----------------------------------------------------------------------
    # Branches (Clinics)
    # -----------------------------------------------------------------------
    async def create_branch(self, payload: BranchCreate, actor_id: UUID | None = None) -> BranchResponse:
        slug = f"{payload.name.lower().replace(' ', '-')}-{payload.branch_code.lower()}"
        branch_data = payload.model_dump()
        branch_data["slug"] = slug
        branch = await self.repo.create_branch(branch_data)

        await self.repo.create_audit_log(
            {
                "organization_id": payload.organization_id,
                "clinic_id": branch.id,
                "actor_id": actor_id,
                "action": "BRANCH_CREATED",
                "resource_type": "clinic",
                "resource_id": str(branch.id),
                "details_json": json.dumps({"name": branch.name, "code": branch.branch_code}),
            }
        )
        return BranchResponse.model_validate(branch)

    async def list_branches(
        self,
        org_id: UUID,
        region_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[BranchResponse]:
        branches = await self.repo.list_branches(
            org_id=org_id, region_id=region_id, is_active=is_active, search=search
        )
        return [BranchResponse.model_validate(b) for b in branches]

    async def get_branch(self, branch_id: UUID) -> BranchResponse | None:
        branch = await self.repo.get_branch(branch_id)
        return BranchResponse.model_validate(branch) if branch else None

    async def update_branch(
        self, branch_id: UUID, payload: BranchUpdate, actor_id: UUID | None = None
    ) -> BranchResponse | None:
        branch = await self.repo.update_branch(branch_id, payload.model_dump(exclude_unset=True))
        if not branch:
            return None
        if branch.organization_id:
            await self.repo.create_audit_log(
                {
                    "organization_id": branch.organization_id,
                    "clinic_id": branch.id,
                    "actor_id": actor_id,
                    "action": "BRANCH_UPDATED",
                    "resource_type": "clinic",
                    "resource_id": str(branch.id),
                    "details_json": json.dumps(payload.model_dump(exclude_unset=True, mode="json")),
                }
            )
        return BranchResponse.model_validate(branch)

    # -----------------------------------------------------------------------
    # Departments
    # -----------------------------------------------------------------------
    async def create_department(self, payload: DepartmentCreate) -> DepartmentResponse:
        dept = await self.repo.create_department(payload.model_dump())
        return DepartmentResponse.model_validate(dept)

    async def list_departments(self, clinic_id: UUID) -> list[DepartmentResponse]:
        depts = await self.repo.list_departments(clinic_id)
        return [DepartmentResponse.model_validate(d) for d in depts]

    async def update_department(self, dept_id: UUID, payload: DepartmentUpdate) -> DepartmentResponse | None:
        dept = await self.repo.update_department(dept_id, payload.model_dump(exclude_unset=True))
        return DepartmentResponse.model_validate(dept) if dept else None

    # -----------------------------------------------------------------------
    # Enterprise Roles & Permissions
    # -----------------------------------------------------------------------
    async def list_permissions(self) -> list[EnterprisePermissionResponse]:
        perms = await self.repo.list_permissions()
        return [EnterprisePermissionResponse.model_validate(p) for p in perms]

    async def create_role(self, payload: EnterpriseRoleCreate) -> EnterpriseRoleResponse:
        role_data = payload.model_dump(exclude={"permission_ids"})
        role = await self.repo.create_role(role_data, payload.permission_ids)
        perms = await self.repo.get_role_permissions(role.id)
        resp = EnterpriseRoleResponse.model_validate(role)
        resp.permissions = [EnterprisePermissionResponse.model_validate(p) for p in perms]
        return resp

    async def list_roles(self, org_id: UUID | None = None) -> list[EnterpriseRoleResponse]:
        roles = await self.repo.list_roles(org_id)
        results = []
        for r in roles:
            perms = await self.repo.get_role_permissions(r.id)
            resp = EnterpriseRoleResponse.model_validate(r)
            resp.permissions = [EnterprisePermissionResponse.model_validate(p) for p in perms]
            results.append(resp)
        return results

    async def assign_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        await self.repo.assign_role_permissions(role_id, permission_ids)

    async def assign_user_branch(self, payload: UserBranchAssignmentCreate) -> UserBranchAssignmentResponse:
        assignment = await self.repo.assign_user_branch(payload.model_dump())
        return UserBranchAssignmentResponse.model_validate(assignment)

    async def get_user_branch_assignments(self, user_id: UUID) -> list[UserBranchAssignmentResponse]:
        assignments = await self.repo.get_user_branch_assignments(user_id)
        return [UserBranchAssignmentResponse.model_validate(a) for a in assignments]

    async def set_user_permission_override(
        self, payload: UserPermissionOverrideCreate
    ) -> UserPermissionOverrideResponse:
        override = await self.repo.set_user_permission_override(
            payload.user_id, payload.permission_id, payload.is_granted
        )
        perm = await self.repo.db.get(EnterprisePermission, payload.permission_id)
        return UserPermissionOverrideResponse(
            user_id=override.user_id,
            permission_id=override.permission_id,
            permission_key=perm.permission_key if perm else "",
            is_granted=override.is_granted,
        )

    async def resolve_user_permissions(self, user_id: UUID) -> EffectiveUserPermissionsResponse:
        roles, clinics, perms = await self.repo.resolve_effective_permissions(user_id)
        return EffectiveUserPermissionsResponse(
            user_id=user_id,
            roles=roles,
            assigned_clinics=clinics,
            permissions=perms,
        )

    # -----------------------------------------------------------------------
    # Cross-Branch Patient Transfers & Merges
    # -----------------------------------------------------------------------
    async def create_patient_transfer(
        self, org_id: UUID, payload: PatientTransferCreate, actor_id: UUID | None = None
    ) -> PatientTransferResponse:
        transfer_data = payload.model_dump()
        transfer_data["organization_id"] = org_id
        transfer_data["initiated_by"] = actor_id
        transfer_data["status"] = TransferStatus.PENDING

        transfer = await self.repo.create_patient_transfer(transfer_data)
        await self.repo.create_audit_log(
            {
                "organization_id": org_id,
                "clinic_id": payload.from_clinic_id,
                "actor_id": actor_id,
                "action": "PATIENT_TRANSFER_INITIATED",
                "resource_type": "patient_transfer",
                "resource_id": str(transfer.id),
                "details_json": json.dumps({"patient_id": str(payload.patient_id), "to_clinic_id": str(payload.to_clinic_id)}),
            }
        )
        return PatientTransferResponse.model_validate(transfer)

    async def handle_patient_transfer(
        self, transfer_id: UUID, payload: PatientTransferActionRequest, actor_id: UUID | None = None
    ) -> PatientTransferResponse | None:
        updated = await self.repo.update_patient_transfer_status(
            transfer_id=transfer_id,
            status=payload.status,
            approved_by=actor_id,
            notes=payload.notes,
        )
        if not updated:
            return None

        await self.repo.create_audit_log(
            {
                "organization_id": updated.organization_id,
                "clinic_id": updated.to_clinic_id,
                "actor_id": actor_id,
                "action": f"PATIENT_TRANSFER_{payload.status}",
                "resource_type": "patient_transfer",
                "resource_id": str(transfer_id),
                "details_json": json.dumps({"status": payload.status.value, "notes": payload.notes}),
            }
        )
        return PatientTransferResponse.model_validate(updated)

    async def list_patient_transfers(
        self, org_id: UUID, clinic_id: UUID | None = None, status: TransferStatus | None = None
    ) -> list[PatientTransferResponse]:
        transfers = await self.repo.list_patient_transfers(org_id, clinic_id=clinic_id, status=status)
        return [PatientTransferResponse.model_validate(t) for t in transfers]

    async def find_duplicate_patients(
        self, org_id: UUID, name: str | None = None, phone: str | None = None, email: str | None = None
    ) -> list[DuplicatePatientMatch]:
        raw_matches = await self.repo.find_duplicate_patients(org_id, name=name, phone=phone, email=email)
        return [DuplicatePatientMatch(**m) for m in raw_matches]

    async def merge_patients(
        self, org_id: UUID, payload: PatientMergeRequest, actor_id: UUID | None = None
    ) -> PatientMergeResponse:
        record = await self.repo.merge_patients(
            org_id=org_id,
            primary_id=payload.primary_patient_id,
            duplicate_id=payload.duplicate_patient_id,
            merged_by=actor_id,
            reason=payload.merge_reason,
        )
        counts = json.loads(record.merged_data_snapshot_json or "{}")

        await self.repo.create_audit_log(
            {
                "organization_id": org_id,
                "actor_id": actor_id,
                "action": "PATIENT_MERGE_COMPLETED",
                "resource_type": "patient",
                "resource_id": str(payload.primary_patient_id),
                "details_json": json.dumps(
                    {"duplicate_id": str(payload.duplicate_patient_id), "migrated": counts}
                ),
            }
        )
        return PatientMergeResponse(
            id=record.id,
            organization_id=record.organization_id,
            primary_patient_id=record.primary_patient_id,
            duplicate_patient_id=record.duplicate_patient_id,
            merged_by=record.merged_by,
            merge_reason=record.merge_reason,
            records_migrated=counts,
            created_at=record.created_at,
        )

    # -----------------------------------------------------------------------
    # Inter-Branch Inventory Transfers
    # -----------------------------------------------------------------------
    async def create_inventory_transfer(
        self, org_id: UUID, payload: InventoryTransferCreate, actor_id: UUID | None = None
    ) -> InventoryTransferResponse:
        timestamp_str = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        transfer_number = f"TRF-{timestamp_str}"

        # Fetch unit cost
        item = await self.repo.db.get(InventoryItem, payload.item_id)
        unit_cost = float(item.purchase_price or 0.0) if item else 0.0
        transfer_data = payload.model_dump()
        transfer_data["organization_id"] = org_id
        transfer_data["transfer_number"] = transfer_number
        transfer_data["unit_cost"] = unit_cost
        transfer_data["status"] = InventoryTransferStatus.DRAFT

        transfer = await self.repo.create_inventory_transfer(transfer_data)
        await self.repo.create_audit_log(
            {
                "organization_id": org_id,
                "clinic_id": payload.from_clinic_id,
                "actor_id": actor_id,
                "action": "INVENTORY_TRANSFER_CREATED",
                "resource_type": "inventory_transfer",
                "resource_id": str(transfer.id),
                "details_json": json.dumps(
                    {"transfer_number": transfer_number, "quantity": payload.quantity}
                ),
            }
        )
        return InventoryTransferResponse.model_validate(transfer)

    async def update_inventory_transfer_status(
        self,
        transfer_id: UUID,
        payload: InventoryTransferStatusUpdateRequest,
        actor_id: UUID | None = None,
    ) -> InventoryTransferResponse | None:
        updated = await self.repo.update_inventory_transfer_status(
            transfer_id=transfer_id,
            status=payload.status,
            actor_id=actor_id,
            tracking_number=payload.tracking_number,
            notes=payload.notes,
        )
        if not updated:
            return None

        await self.repo.create_audit_log(
            {
                "organization_id": updated.organization_id,
                "clinic_id": updated.from_clinic_id,
                "actor_id": actor_id,
                "action": f"INVENTORY_TRANSFER_{payload.status}",
                "resource_type": "inventory_transfer",
                "resource_id": str(transfer_id),
                "details_json": json.dumps(
                    {"status": payload.status.value, "tracking_number": payload.tracking_number}
                ),
            }
        )
        return InventoryTransferResponse.model_validate(updated)

    async def list_inventory_transfers(
        self, org_id: UUID, clinic_id: UUID | None = None, status: InventoryTransferStatus | None = None
    ) -> list[InventoryTransferResponse]:
        transfers = await self.repo.list_inventory_transfers(org_id, clinic_id=clinic_id, status=status)
        return [InventoryTransferResponse.model_validate(t) for t in transfers]

    async def get_consolidated_inventory(self, org_id: UUID) -> list[ConsolidatedInventoryItem]:
        data = await self.repo.get_consolidated_inventory(org_id)
        return [ConsolidatedInventoryItem(**d) for d in data]

    # -----------------------------------------------------------------------
    # Consolidated Financials
    # -----------------------------------------------------------------------
    async def get_consolidated_financials(self, org_id: UUID) -> ConsolidatedFinancialsResponse:
        data = await self.repo.get_consolidated_financials(org_id)
        return ConsolidatedFinancialsResponse(**data)

    # -----------------------------------------------------------------------
    # Announcements & Audits
    # -----------------------------------------------------------------------
    async def create_announcement(
        self, org_id: UUID, payload: EnterpriseAnnouncementCreate, actor_id: UUID | None = None
    ) -> EnterpriseAnnouncementResponse:
        ann_data = payload.model_dump()
        ann_data["organization_id"] = org_id
        ann = await self.repo.create_announcement(ann_data)
        await self.repo.create_audit_log(
            {
                "organization_id": org_id,
                "actor_id": actor_id,
                "action": "ANNOUNCEMENT_PUBLISHED",
                "resource_type": "announcement",
                "resource_id": str(ann.id),
                "details_json": json.dumps({"title": ann.title, "type": ann.announcement_type.value}),
            }
        )
        return EnterpriseAnnouncementResponse.model_validate(ann)

    async def list_announcements(
        self, org_id: UUID, active_only: bool = True
    ) -> list[EnterpriseAnnouncementResponse]:
        anns = await self.repo.list_announcements(org_id, active_only=active_only)
        return [EnterpriseAnnouncementResponse.model_validate(a) for a in anns]

    async def update_announcement(
        self, announcement_id: UUID, payload: EnterpriseAnnouncementUpdate
    ) -> EnterpriseAnnouncementResponse | None:
        ann = await self.repo.update_announcement(announcement_id, payload.model_dump(exclude_unset=True))
        return EnterpriseAnnouncementResponse.model_validate(ann) if ann else None

    async def list_audit_logs(self, org_id: UUID, limit: int = 100) -> list[EnterpriseAuditLogResponse]:
        logs = await self.repo.list_audit_logs(org_id, limit=limit)
        return [EnterpriseAuditLogResponse.model_validate(l) for l in logs]
