from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment
from app.models.billing import Invoice
from app.models.enterprise import (
    Department,
    EnterpriseAnnouncement,
    EnterpriseAuditLog,
    EnterprisePermission,
    EnterpriseRole,
    InventoryTransfer,
    InventoryTransferStatus,
    Organization,
    PatientMergeRecord,
    PatientTransfer,
    Region,
    RolePermissionMapping,
    TransferStatus,
    UserBranchAssignment,
    UserPermissionOverride,
)
from app.models.identity import Clinic, Role, User
from app.models.insurance import InsurancePaymentReconciliation
from app.models.inventory import (
    InventoryItem,
    StockTransaction,
    StockTransactionType,
)
from app.models.patient import DentalHistory, MedicalHistory, Patient
from app.models.prescription import Prescription
from app.models.treatment import Treatment

DEFAULT_PERMISSIONS = [
    ("enterprise:view", "enterprise", "View enterprise organization and hierarchy"),
    ("enterprise:manage", "enterprise", "Manage enterprise settings, branding and regions"),
    ("branch:view", "branch", "View branch clinics"),
    ("branch:manage", "branch", "Create and manage branch clinics and departments"),
    ("user:assign", "user", "Assign users and roaming dentists across branches"),
    ("permission:manage", "user", "Configure enterprise roles and permission overrides"),
    ("patient:transfer", "patient", "Initiate and approve cross-branch patient transfers"),
    ("patient:merge", "patient", "Detect and merge duplicate patient profiles"),
    ("patient:cross_view", "patient", "View patient records across all network branches"),
    ("inventory:transfer", "inventory", "Initiate, dispatch, and receive inter-branch stock"),
    ("inventory:consolidated_view", "inventory", "View consolidated enterprise inventory valuation"),
    ("financials:consolidated_view", "financials", "View consolidated financials and regional rollups"),
    ("reports:comparative_view", "reports", "View comparative multi-branch benchmark analytics"),
    ("announcement:broadcast", "announcement", "Publish organization-wide announcements and alerts"),
    ("audit:view", "audit", "View enterprise compliance and audit logs"),
]


def _clean_limit_offset(limit: object, offset: object = 0, default_limit: int = 50) -> tuple[int, int]:
    try:
        clean_limit = int(getattr(limit, "default", limit) or default_limit)
    except (TypeError, ValueError):
        clean_limit = default_limit
    try:
        clean_offset = int(getattr(offset, "default", offset) or 0)
    except (TypeError, ValueError):
        clean_offset = 0
    return clean_limit, clean_offset


class EnterpriseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # System Seed
    # -----------------------------------------------------------------------
    async def seed_system_permissions(self) -> list[EnterprisePermission]:
        result = await self.db.execute(select(EnterprisePermission))
        existing = {p.permission_key: p for p in result.scalars().all()}
        created = []
        for key, module, desc in DEFAULT_PERMISSIONS:
            if key not in existing:
                perm = EnterprisePermission(permission_key=key, module=module, description=desc)
                self.db.add(perm)
                created.append(perm)
        if created:
            await self.db.flush()
        result = await self.db.execute(select(EnterprisePermission))
        return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Organizations
    # -----------------------------------------------------------------------
    async def create_organization(self, data: dict) -> Organization:
        org = Organization(**data)
        self.db.add(org)
        await self.db.flush()
        return org

    async def get_organization(self, org_id: UUID) -> Organization | None:
        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.regions))
            .where(Organization.id == org_id, Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_organization_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug, Organization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_organizations(self, skip: int = 0, limit: int = 50) -> list[Organization]:
        clean_limit, clean_offset = _clean_limit_offset(limit, skip)
        result = await self.db.execute(
            select(Organization)
            .where(Organization.deleted_at.is_(None))
            .order_by(Organization.name.asc())
            .offset(clean_offset)
            .limit(clean_limit)
        )
        return list(result.scalars().all())

    async def update_organization(self, org_id: UUID, data: dict) -> Organization | None:
        org = await self.get_organization(org_id)
        if not org:
            return None
        for k, v in data.items():
            if v is not None and hasattr(org, k):
                setattr(org, k, v)
        await self.db.flush()
        return org

    # -----------------------------------------------------------------------
    # Regions
    # -----------------------------------------------------------------------
    async def create_region(self, data: dict) -> Region:
        region = Region(**data)
        self.db.add(region)
        await self.db.flush()
        return region

    async def get_region(self, region_id: UUID) -> Region | None:
        result = await self.db.execute(
            select(Region).where(Region.id == region_id, Region.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_regions(self, org_id: UUID) -> list[Region]:
        result = await self.db.execute(
            select(Region)
            .where(Region.organization_id == org_id, Region.deleted_at.is_(None))
            .order_by(Region.name.asc())
        )
        return list(result.scalars().all())

    async def count_branches_in_region(self, region_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Clinic.id)).where(Clinic.region_id == region_id, Clinic.deleted_at.is_(None))
        )
        return result.scalar_one() or 0

    async def update_region(self, region_id: UUID, data: dict) -> Region | None:
        region = await self.get_region(region_id)
        if not region:
            return None
        for k, v in data.items():
            if v is not None and hasattr(region, k):
                setattr(region, k, v)
        await self.db.flush()
        return region

    # -----------------------------------------------------------------------
    # Branches (Clinics)
    # -----------------------------------------------------------------------
    async def create_branch(self, data: dict) -> Clinic:
        branch = Clinic(**data)
        self.db.add(branch)
        await self.db.flush()
        return branch

    async def get_branch(self, branch_id: UUID) -> Clinic | None:
        result = await self.db.execute(
            select(Clinic).where(Clinic.id == branch_id, Clinic.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_branches(
        self,
        org_id: UUID,
        region_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Clinic]:
        query = select(Clinic).where(
            Clinic.organization_id == org_id,
            Clinic.deleted_at.is_(None),
        )
        if region_id:
            query = query.where(Clinic.region_id == region_id)
        if is_active is not None:
            query = query.where(Clinic.is_active == is_active)
        if search:
            s = f"%{search}%"
            query = query.where(
                or_(Clinic.name.ilike(s), Clinic.branch_code.ilike(s), Clinic.email.ilike(s))
            )
        result = await self.db.execute(query.order_by(Clinic.name.asc()))
        return list(result.scalars().all())

    async def update_branch(self, branch_id: UUID, data: dict) -> Clinic | None:
        branch = await self.get_branch(branch_id)
        if not branch:
            return None
        for k, v in data.items():
            if v is not None and hasattr(branch, k):
                setattr(branch, k, v)
        await self.db.flush()
        return branch

    # -----------------------------------------------------------------------
    # Departments
    # -----------------------------------------------------------------------
    async def create_department(self, data: dict) -> Department:
        dept = Department(**data)
        self.db.add(dept)
        await self.db.flush()
        return dept

    async def get_department(self, dept_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.id == dept_id, Department.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_departments(self, clinic_id: UUID) -> list[Department]:
        result = await self.db.execute(
            select(Department)
            .where(Department.clinic_id == clinic_id, Department.deleted_at.is_(None))
            .order_by(Department.name.asc())
        )
        return list(result.scalars().all())

    async def update_department(self, dept_id: UUID, data: dict) -> Department | None:
        dept = await self.get_department(dept_id)
        if not dept:
            return None
        for k, v in data.items():
            if v is not None and hasattr(dept, k):
                setattr(dept, k, v)
        await self.db.flush()
        return dept

    # -----------------------------------------------------------------------
    # Roles & Permissions
    # -----------------------------------------------------------------------
    async def list_permissions(self) -> list[EnterprisePermission]:
        result = await self.db.execute(select(EnterprisePermission).order_by(EnterprisePermission.module.asc()))
        return list(result.scalars().all())

    async def create_role(self, data: dict, permission_ids: list[UUID] | None = None) -> EnterpriseRole:
        role = EnterpriseRole(**data)
        self.db.add(role)
        await self.db.flush()
        if permission_ids:
            for pid in permission_ids:
                self.db.add(RolePermissionMapping(role_id=role.id, permission_id=pid))
            await self.db.flush()
        return role

    async def get_role(self, role_id: UUID) -> EnterpriseRole | None:
        result = await self.db.execute(
            select(EnterpriseRole).where(EnterpriseRole.id == role_id, EnterpriseRole.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_roles(self, org_id: UUID | None = None) -> list[EnterpriseRole]:
        query = select(EnterpriseRole).where(EnterpriseRole.deleted_at.is_(None))
        if org_id:
            query = query.where(or_(EnterpriseRole.organization_id == org_id, EnterpriseRole.is_system.is_(True)))
        result = await self.db.execute(query.order_by(EnterpriseRole.name.asc()))
        return list(result.scalars().all())

    async def get_role_permissions(self, role_id: UUID) -> list[EnterprisePermission]:
        result = await self.db.execute(
            select(EnterprisePermission)
            .join(RolePermissionMapping, RolePermissionMapping.permission_id == EnterprisePermission.id)
            .where(RolePermissionMapping.role_id == role_id)
        )
        return list(result.scalars().all())

    async def assign_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        # Delete existing mappings
        existing = await self.db.execute(
            select(RolePermissionMapping).where(RolePermissionMapping.role_id == role_id)
        )
        for row in existing.scalars().all():
            await self.db.delete(row)
        for pid in permission_ids:
            self.db.add(RolePermissionMapping(role_id=role_id, permission_id=pid))
        await self.db.flush()

    # -----------------------------------------------------------------------
    # User Branch Assignments & Overrides
    # -----------------------------------------------------------------------
    async def assign_user_branch(self, data: dict) -> UserBranchAssignment:
        assignment = UserBranchAssignment(**data)
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_user_branch_assignments(self, user_id: UUID) -> list[UserBranchAssignment]:
        result = await self.db.execute(
            select(UserBranchAssignment)
            .where(UserBranchAssignment.user_id == user_id, UserBranchAssignment.deleted_at.is_(None))
            .order_by(UserBranchAssignment.is_primary.desc())
        )
        return list(result.scalars().all())

    async def set_user_permission_override(
        self, user_id: UUID, permission_id: UUID, is_granted: bool
    ) -> UserPermissionOverride:
        result = await self.db.execute(
            select(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user_id,
                UserPermissionOverride.permission_id == permission_id,
            )
        )
        override = result.scalar_one_or_none()
        if override:
            override.is_granted = is_granted
        else:
            override = UserPermissionOverride(
                user_id=user_id, permission_id=permission_id, is_granted=is_granted
            )
            self.db.add(override)
        await self.db.flush()
        return override

    async def get_user_permission_overrides(self, user_id: UUID) -> list[tuple[UserPermissionOverride, str]]:
        result = await self.db.execute(
            select(UserPermissionOverride, EnterprisePermission.permission_key)
            .join(EnterprisePermission, EnterprisePermission.id == UserPermissionOverride.permission_id)
            .where(UserPermissionOverride.user_id == user_id)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def resolve_effective_permissions(self, user_id: UUID) -> tuple[list[str], list[UUID], list[str]]:
        user = await self.db.get(User, user_id)
        if not user:
            return [], [], []

        roles = [user.role.value]
        assigned_clinics = []
        if user.clinic_id:
            assigned_clinics.append(user.clinic_id)

        # Additional branch assignments
        assignments = await self.get_user_branch_assignments(user_id)
        for a in assignments:
            if a.clinic_id not in assigned_clinics:
                assigned_clinics.append(a.clinic_id)
            if a.role_override and a.role_override not in roles:
                roles.append(a.role_override)

        # Base permissions granted by role
        granted_permissions: set[str] = set()
        if user.role in (Role.SUPER_ADMIN, Role.ORGANIZATION_ADMIN):
            # Admin roles get all permissions
            all_perms = await self.db.execute(select(EnterprisePermission.permission_key))
            granted_permissions.update(all_perms.scalars().all())
        else:
            # Query enterprise roles matching role keys
            result = await self.db.execute(
                select(EnterprisePermission.permission_key)
                .join(RolePermissionMapping, RolePermissionMapping.permission_id == EnterprisePermission.id)
                .join(EnterpriseRole, EnterpriseRole.id == RolePermissionMapping.role_id)
                .where(EnterpriseRole.role_key.in_(roles))
            )
            granted_permissions.update(result.scalars().all())

        # Apply overrides
        overrides = await self.get_user_permission_overrides(user_id)
        for _, perm_key in overrides:
            pass
        # Check explicitly granted vs revoked
        for override, perm_key in overrides:
            if override.is_granted:
                granted_permissions.add(perm_key)
            else:
                granted_permissions.discard(perm_key)

        return roles, assigned_clinics, sorted(granted_permissions)

    # -----------------------------------------------------------------------
    # Cross-Branch Patient Transfers
    # -----------------------------------------------------------------------
    async def create_patient_transfer(self, data: dict) -> PatientTransfer:
        if "status" not in data:
            data["status"] = TransferStatus.PENDING
        transfer = PatientTransfer(**data)
        self.db.add(transfer)
        await self.db.flush()
        return transfer

    async def get_patient_transfer(self, transfer_id: UUID) -> PatientTransfer | None:
        result = await self.db.execute(
            select(PatientTransfer).where(
                PatientTransfer.id == transfer_id, PatientTransfer.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def list_patient_transfers(
        self,
        org_id: UUID,
        clinic_id: UUID | None = None,
        status: TransferStatus | None = None,
    ) -> list[PatientTransfer]:
        query = select(PatientTransfer).where(
            PatientTransfer.organization_id == org_id,
            PatientTransfer.deleted_at.is_(None),
        )
        if clinic_id:
            query = query.where(
                or_(
                    PatientTransfer.from_clinic_id == clinic_id,
                    PatientTransfer.to_clinic_id == clinic_id,
                )
            )
        if status:
            query = query.where(PatientTransfer.status == status)
        result = await self.db.execute(query.order_by(PatientTransfer.created_at.desc()))
        return list(result.scalars().all())

    async def update_patient_transfer_status(
        self,
        transfer_id: UUID,
        status: TransferStatus,
        approved_by: UUID | None = None,
        notes: str | None = None,
    ) -> PatientTransfer | None:
        transfer = await self.get_patient_transfer(transfer_id)
        if not transfer:
            return None
        transfer.status = status
        if approved_by:
            transfer.approved_by = approved_by
        if notes:
            transfer.notes = (transfer.notes or "") + f"\n[{status}] {notes}"
        if status == TransferStatus.COMPLETED or status == TransferStatus.APPROVED:
            # Transfer patient primary clinic_id
            patient = await self.db.get(Patient, transfer.patient_id)
            if patient:
                patient.clinic_id = transfer.to_clinic_id
        await self.db.flush()
        return transfer

    # -----------------------------------------------------------------------
    # Duplicate Patient Search & Merge
    # -----------------------------------------------------------------------
    async def find_duplicate_patients(
        self,
        org_id: UUID,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> list[dict]:
        # Find all clinics in org
        clinics_res = await self.db.execute(
            select(Clinic.id, Clinic.name).where(Clinic.organization_id == org_id, Clinic.deleted_at.is_(None))
        )
        clinic_map = {row[0]: row[1] for row in clinics_res.all()}
        if not clinic_map:
            return []

        query = select(Patient).where(
            Patient.clinic_id.in_(clinic_map.keys()),
            Patient.deleted_at.is_(None),
        )
        conditions = []
        if phone:
            conditions.append(Patient.mobile_number.ilike(f"%{phone[-10:]}%"))
        if email:
            conditions.append(Patient.email.ilike(email.strip()))
        if name:
            conditions.append(
                or_(
                    Patient.first_name.ilike(f"%{name}%"),
                    Patient.last_name.ilike(f"%{name}%"),
                )
            )
        if conditions:
            query = query.where(or_(*conditions))

        res = await self.db.execute(query.limit(20))
        matched = res.scalars().all()
        results = []
        for p in matched:
            matched_fields = []
            score = 0.0
            if phone and p.mobile_number and phone[-10:] in p.mobile_number:
                matched_fields.append("phone")
                score += 0.5
            if email and p.email and email.lower() == p.email.lower():
                matched_fields.append("email")
                score += 0.4
            if name and (name.lower() in p.first_name.lower() or name.lower() in p.last_name.lower()):
                matched_fields.append("name")
                score += 0.3
            results.append(
                {
                    "patient_id": p.id,
                    "clinic_id": p.clinic_id,
                    "clinic_name": clinic_map.get(p.clinic_id, "Unknown"),
                    "full_name": f"{p.first_name} {p.last_name}",
                    "phone": p.mobile_number,
                    "email": p.email,
                    "date_of_birth": str(p.date_of_birth) if p.date_of_birth else None,
                    "similarity_score": min(1.0, score),
                    "matched_fields": matched_fields,
                }
            )
        return sorted(results, key=lambda x: x["similarity_score"], reverse=True)

    async def merge_patients(
        self,
        org_id: UUID,
        primary_id: UUID,
        duplicate_id: UUID,
        merged_by: UUID | None,
        reason: str | None = None,
    ) -> PatientMergeRecord:
        primary = await self.db.get(Patient, primary_id)
        duplicate = await self.db.get(Patient, duplicate_id)
        if not primary or not duplicate:
            raise ValueError("Primary or duplicate patient not found.")

        counts: dict[str, int] = {}
        # 1. Reassign Appointments
        appts = await self.db.execute(select(Appointment).where(Appointment.patient_id == duplicate_id))
        appts_list = appts.scalars().all()
        for a in appts_list:
            a.patient_id = primary_id
        counts["appointments"] = len(appts_list)

        # 2. Reassign Treatments
        treatments = await self.db.execute(select(Treatment).where(Treatment.patient_id == duplicate_id))
        treatments_list = treatments.scalars().all()
        for t in treatments_list:
            t.patient_id = primary_id
        counts["treatments"] = len(treatments_list)

        # 3. Reassign Invoices
        invoices = await self.db.execute(select(Invoice).where(Invoice.patient_id == duplicate_id))
        invoices_list = invoices.scalars().all()
        for inv in invoices_list:
            inv.patient_id = primary_id
        counts["invoices"] = len(invoices_list)

        # 4. Reassign Prescriptions
        prescriptions = await self.db.execute(select(Prescription).where(Prescription.patient_id == duplicate_id))
        prescriptions_list = prescriptions.scalars().all()
        for rx in prescriptions_list:
            rx.patient_id = primary_id
        counts["prescriptions"] = len(prescriptions_list)

        # 5. Dental and Medical histories
        dh_res = await self.db.execute(select(DentalHistory).where(DentalHistory.patient_id == duplicate_id))
        for dh in dh_res.scalars().all():
            dh.patient_id = primary_id
        mh_res = await self.db.execute(select(MedicalHistory).where(MedicalHistory.patient_id == duplicate_id))
        for mh in mh_res.scalars().all():
            mh.patient_id = primary_id

        # Mark duplicate patient as inactive or soft-deleted
        duplicate.is_active = False
        duplicate.notes = (duplicate.notes or "") + f" [MERGED into {primary_id}]"

        import json

        record = PatientMergeRecord(
            organization_id=org_id,
            primary_patient_id=primary_id,
            duplicate_patient_id=duplicate_id,
            merged_by=merged_by,
            merge_reason=reason,
            merged_data_snapshot_json=json.dumps(counts),
        )
        self.db.add(record)
        await self.db.flush()
        return record

    # -----------------------------------------------------------------------
    # Inter-Branch Inventory Transfers
    # -----------------------------------------------------------------------
    async def create_inventory_transfer(self, data: dict) -> InventoryTransfer:
        if "status" not in data:
            data["status"] = InventoryTransferStatus.DRAFT
        transfer = InventoryTransfer(**data)
        self.db.add(transfer)
        await self.db.flush()
        return transfer

    async def get_inventory_transfer(self, transfer_id: UUID) -> InventoryTransfer | None:
        result = await self.db.execute(
            select(InventoryTransfer).where(
                InventoryTransfer.id == transfer_id, InventoryTransfer.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def list_inventory_transfers(
        self,
        org_id: UUID,
        clinic_id: UUID | None = None,
        status: InventoryTransferStatus | None = None,
    ) -> list[InventoryTransfer]:
        query = select(InventoryTransfer).where(
            InventoryTransfer.organization_id == org_id,
            InventoryTransfer.deleted_at.is_(None),
        )
        if clinic_id:
            query = query.where(
                or_(
                    InventoryTransfer.from_clinic_id == clinic_id,
                    InventoryTransfer.to_clinic_id == clinic_id,
                )
            )
        if status:
            query = query.where(InventoryTransfer.status == status)
        result = await self.db.execute(query.order_by(InventoryTransfer.created_at.desc()))
        return list(result.scalars().all())

    async def update_inventory_transfer_status(
        self,
        transfer_id: UUID,
        status: InventoryTransferStatus,
        actor_id: UUID | None = None,
        tracking_number: str | None = None,
        notes: str | None = None,
    ) -> InventoryTransfer | None:
        transfer = await self.get_inventory_transfer(transfer_id)
        if not transfer:
            return None

        now = datetime.now(UTC)
        transfer.status = status
        if tracking_number:
            transfer.tracking_number = tracking_number
        if notes:
            transfer.notes = (transfer.notes or "") + f"\n[{status}] {notes}"

        source_item = await self.db.get(InventoryItem, transfer.item_id)
        if not source_item:
            raise ValueError("Inventory item not found.")

        if status == InventoryTransferStatus.DISPATCHED:
            transfer.dispatched_at = now
            transfer.dispatched_by = actor_id
            # Deduct stock from source clinic
            prev_qty = source_item.current_quantity
            source_item.current_quantity -= transfer.quantity
            new_qty = source_item.current_quantity
            self.db.add(
                StockTransaction(
                    clinic_id=transfer.from_clinic_id,
                    item_id=source_item.id,
                    transaction_type=StockTransactionType.TRANSFER.value,
                    quantity=-transfer.quantity,
                    previous_quantity=prev_qty,
                    new_quantity=new_qty,
                    actor_id=actor_id,
                    unit_cost=float(source_item.purchase_price or 0.0),
                    total_cost=float(source_item.purchase_price or 0.0) * transfer.quantity,
                    notes=f"Dispatched via transfer {transfer.transfer_number}",
                )
            )
        elif status == InventoryTransferStatus.RECEIVED:
            transfer.received_at = now
            transfer.received_by = actor_id
            # Find or create corresponding item at destination clinic
            dest_item_res = await self.db.execute(
                select(InventoryItem).where(
                    InventoryItem.clinic_id == transfer.to_clinic_id,
                    or_(
                        InventoryItem.name == source_item.name,
                        InventoryItem.sku == source_item.sku,
                    ),
                    InventoryItem.deleted_at.is_(None),
                )
            )
            dest_item = dest_item_res.scalar_one_or_none()
            if not dest_item:
                dest_item = InventoryItem(
                    clinic_id=transfer.to_clinic_id,
                    category=source_item.category,
                    name=source_item.name,
                    sku=f"{source_item.sku}-dest",
                    unit=source_item.unit,
                    selling_price=source_item.selling_price,
                    purchase_price=source_item.purchase_price,
                    current_quantity=transfer.quantity,
                    minimum_stock=source_item.minimum_stock,
                    maximum_stock=source_item.maximum_stock,
                    reorder_level=source_item.reorder_level,
                )
                self.db.add(dest_item)
                await self.db.flush()
                prev_qty = 0
                new_qty = transfer.quantity
            else:
                prev_qty = dest_item.current_quantity
                dest_item.current_quantity += transfer.quantity
                new_qty = dest_item.current_quantity

            self.db.add(
                StockTransaction(
                    clinic_id=transfer.to_clinic_id,
                    item_id=dest_item.id,
                    transaction_type=StockTransactionType.TRANSFER.value,
                    quantity=transfer.quantity,
                    previous_quantity=prev_qty,
                    new_quantity=new_qty,
                    actor_id=actor_id,
                    unit_cost=float(dest_item.purchase_price or 0.0),
                    total_cost=float(dest_item.purchase_price or 0.0) * transfer.quantity,
                    notes=f"Received via transfer {transfer.transfer_number}",
                )
            )

        await self.db.flush()
        return transfer

    async def get_consolidated_inventory(self, org_id: UUID) -> list[dict]:
        clinics_res = await self.db.execute(
            select(Clinic.id, Clinic.name).where(Clinic.organization_id == org_id, Clinic.deleted_at.is_(None))
        )
        clinic_map = {row[0]: row[1] for row in clinics_res.all()}
        if not clinic_map:
            return []

        items_res = await self.db.execute(
            select(InventoryItem)
            .where(InventoryItem.clinic_id.in_(clinic_map.keys()), InventoryItem.deleted_at.is_(None))
        )
        items = items_res.scalars().all()

        # Group by item name
        grouped: dict[str, dict] = {}
        for it in items:
            key = it.name.strip().lower()
            val = float(it.purchase_price or 0.0) * it.current_quantity
            if key not in grouped:
                grouped[key] = {
                    "item_id": it.id,
                    "item_name": it.name,
                    "category": it.category,
                    "unit_of_measure": it.unit,
                    "total_stock": 0,
                    "total_valuation": 0.0,
                    "clinic_breakdown": [],
                }
            grouped[key]["total_stock"] += it.current_quantity
            grouped[key]["total_valuation"] += val
            grouped[key]["clinic_breakdown"].append(
                {
                    "clinic_id": str(it.clinic_id),
                    "clinic_name": clinic_map.get(it.clinic_id, "Unknown"),
                    "stock": it.current_quantity,
                    "valuation": round(val, 2),
                }
            )

        return list(grouped.values())

    # -----------------------------------------------------------------------
    # Consolidated Financials
    # -----------------------------------------------------------------------
    async def get_consolidated_financials(self, org_id: UUID) -> dict:
        clinics_res = await self.db.execute(
            select(Clinic).where(Clinic.organization_id == org_id, Clinic.deleted_at.is_(None))
        )
        clinics = list(clinics_res.scalars().all())
        clinic_map = {c.id: c for c in clinics}

        regions_res = await self.db.execute(
            select(Region).where(Region.organization_id == org_id, Region.deleted_at.is_(None))
        )
        regions = list(regions_res.scalars().all())

        if not clinics:
            return {
                "organization_id": org_id,
                "currency": "INR",
                "total_revenue": 0.0,
                "total_collected": 0.0,
                "total_outstanding": 0.0,
                "total_insurance_settled": 0.0,
                "total_tax": 0.0,
                "branch_summaries": [],
                "region_summaries": [],
            }

        clinic_ids = [c.id for c in clinics]

        # 1. Invoices rollup
        inv_res = await self.db.execute(
            select(
                Invoice.clinic_id,
                func.sum(Invoice.grand_total).label("total_invoiced"),
                func.sum(Invoice.amount_paid).label("total_collected"),
                func.sum(Invoice.tax_amount).label("total_tax"),
                func.count(Invoice.id).label("invoice_count"),
            )
            .where(Invoice.clinic_id.in_(clinic_ids), Invoice.deleted_at.is_(None))
            .group_by(Invoice.clinic_id)
        )
        inv_data = {
            row.clinic_id: {
                "total_invoiced": float(row.total_invoiced or 0.0),
                "total_collected": float(row.total_collected or 0.0),
                "total_tax": float(row.total_tax or 0.0),
                "invoice_count": int(row.invoice_count or 0),
            }
            for row in inv_res.all()
        }

        # 2. Insurance reconciliations rollup
        recon_res = await self.db.execute(
            select(
                InsurancePaymentReconciliation.clinic_id,
                func.sum(InsurancePaymentReconciliation.settled_amount).label("insurance_settled"),
            )
            .where(
                InsurancePaymentReconciliation.clinic_id.in_(clinic_ids),
                InsurancePaymentReconciliation.deleted_at.is_(None),
            )
            .group_by(InsurancePaymentReconciliation.clinic_id)
        )
        recon_data = {
            row.clinic_id: float(row.insurance_settled or 0.0) for row in recon_res.all()
        }

        # Build branch summaries
        branch_summaries = []
        total_rev = 0.0
        total_coll = 0.0
        total_out = 0.0
        total_ins = 0.0
        total_tx = 0.0

        for c in clinics:
            idata = inv_data.get(c.id, {"total_invoiced": 0.0, "total_collected": 0.0, "total_tax": 0.0, "invoice_count": 0})
            ins_settled = recon_data.get(c.id, 0.0)
            invoiced = idata["total_invoiced"]
            collected = idata["total_collected"]
            tax = idata["total_tax"]
            outstanding = max(0.0, invoiced - collected)

            total_rev += invoiced
            total_coll += collected
            total_out += outstanding
            total_ins += ins_settled
            total_tx += tax

            branch_summaries.append(
                {
                    "clinic_id": c.id,
                    "clinic_name": c.name,
                    "total_invoiced": round(invoiced, 2),
                    "total_collected": round(collected, 2),
                    "insurance_collected": round(ins_settled, 2),
                    "outstanding_balance": round(outstanding, 2),
                    "tax_amount": round(tax, 2),
                    "invoice_count": idata["invoice_count"],
                }
            )

        # Build region summaries
        region_summaries = []
        for r in regions:
            reg_branches = [b for b in branch_summaries if clinic_map.get(b["clinic_id"]) and clinic_map[b["clinic_id"]].region_id == r.id]
            reg_invoiced = sum(b["total_invoiced"] for b in reg_branches)
            reg_collected = sum(b["total_collected"] for b in reg_branches)
            reg_out = sum(b["outstanding_balance"] for b in reg_branches)
            region_summaries.append(
                {
                    "region_id": r.id,
                    "region_name": r.name,
                    "total_invoiced": round(reg_invoiced, 2),
                    "total_collected": round(reg_collected, 2),
                    "outstanding_balance": round(reg_out, 2),
                    "branches": reg_branches,
                }
            )

        return {
            "organization_id": org_id,
            "currency": clinics[0].currency if clinics else "INR",
            "total_revenue": round(total_rev, 2),
            "total_collected": round(total_coll, 2),
            "total_outstanding": round(total_out, 2),
            "total_insurance_settled": round(total_ins, 2),
            "total_tax": round(total_tx, 2),
            "branch_summaries": branch_summaries,
            "region_summaries": region_summaries,
        }

    # -----------------------------------------------------------------------
    # Announcements & Audits
    # -----------------------------------------------------------------------
    async def create_announcement(self, data: dict) -> EnterpriseAnnouncement:
        ann = EnterpriseAnnouncement(**data)
        self.db.add(ann)
        await self.db.flush()
        return ann

    async def list_announcements(self, org_id: UUID, active_only: bool = True) -> list[EnterpriseAnnouncement]:
        query = select(EnterpriseAnnouncement).where(
            EnterpriseAnnouncement.organization_id == org_id,
            EnterpriseAnnouncement.deleted_at.is_(None),
        )
        if active_only:
            query = query.where(EnterpriseAnnouncement.is_active.is_(True))
        result = await self.db.execute(query.order_by(EnterpriseAnnouncement.created_at.desc()))
        return list(result.scalars().all())

    async def update_announcement(self, announcement_id: UUID, data: dict) -> EnterpriseAnnouncement | None:
        result = await self.db.execute(
            select(EnterpriseAnnouncement).where(
                EnterpriseAnnouncement.id == announcement_id,
                EnterpriseAnnouncement.deleted_at.is_(None),
            )
        )
        ann = result.scalar_one_or_none()
        if not ann:
            return None
        for k, v in data.items():
            if v is not None and hasattr(ann, k):
                setattr(ann, k, v)
        await self.db.flush()
        return ann

    async def create_audit_log(self, data: dict) -> EnterpriseAuditLog:
        log = EnterpriseAuditLog(**data)
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_audit_logs(self, org_id: UUID, limit: int = 100) -> list[EnterpriseAuditLog]:
        clean_limit, _ = _clean_limit_offset(limit, 0, default_limit=100)
        result = await self.db.execute(
            select(EnterpriseAuditLog)
            .where(EnterpriseAuditLog.organization_id == org_id)
            .order_by(EnterpriseAuditLog.created_at.desc())
            .limit(clean_limit)
        )
        return list(result.scalars().all())
