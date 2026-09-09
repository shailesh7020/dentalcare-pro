from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.models.enterprise import (
    AnnouncementScope,
    AnnouncementType,
    Department,
    EnterpriseAnnouncement,
    EnterpriseAuditLog,
    EnterprisePermission,
    EnterpriseRole,
    InventoryTransfer,
    InventoryTransferStatus,
    Organization,
    PatientSharingMode,
    PatientTransfer,
    Region,
    RolePermissionMapping,
    TransferStatus,
    UserBranchAssignment,
    UserPermissionOverride,
)
from app.models.identity import Clinic
from app.models.inventory import InventoryItem
from app.models.patient import Gender, Patient
from app.repositories.enterprise_repository import EnterpriseRepository
from app.schemas.enterprise import (
    BranchCreate,
    EnterpriseAnnouncementCreate,
    EnterpriseRoleCreate,
    InventoryTransferCreate,
    InventoryTransferStatusUpdateRequest,
    OrganizationCreate,
    OrganizationUpdate,
    PatientTransferActionRequest,
    PatientTransferCreate,
    RegionCreate,
    UserBranchAssignmentCreate,
)
from app.services.enterprise_service import EnterpriseService


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items) if items is not None else []

    def all(self):
        return self._items

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar_one(self):
        return self._items[0] if self._items else 0


class FakeDb:
    def __init__(self):
        self.items = []

    def add(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = uuid4()
        if not hasattr(item, "created_at") or item.created_at is None:
            item.created_at = datetime.now(UTC)
        if not hasattr(item, "updated_at") or item.updated_at is None:
            item.updated_at = datetime.now(UTC)
        if not hasattr(item, "deleted_at"):
            item.deleted_at = None
        if hasattr(item, "is_active") and item.is_active is None:
            item.is_active = True
        if hasattr(item, "is_system") and item.is_system is None:
            item.is_system = False
        self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def delete(self, item):
        if item in self.items:
            self.items.remove(item)

    async def get(self, model_cls, entity_id):
        for it in self.items:
            if isinstance(it, model_cls) and getattr(it, "id", None) == entity_id:
                return it
        return None

    async def execute(self, query):
        stmt = str(query)
        if "enterprise_permissions" in stmt:
            matches = [it for it in self.items if isinstance(it, EnterprisePermission)]
            return FakeScalarResult(matches)
        if "organizations" in stmt:
            matches = [it for it in self.items if isinstance(it, Organization)]
            return FakeScalarResult(matches)
        if "regions" in stmt:
            matches = [it for it in self.items if isinstance(it, Region)]
            return FakeScalarResult(matches)
        if "departments" in stmt:
            matches = [it for it in self.items if isinstance(it, Department)]
            return FakeScalarResult(matches)
        if "clinics" in stmt:
            matches = [it for it in self.items if isinstance(it, Clinic)]
            if "count" in stmt.lower():
                return FakeScalarResult([len(matches)])
            return FakeScalarResult(matches)
        if "enterprise_roles" in stmt:
            matches = [it for it in self.items if isinstance(it, EnterpriseRole)]
            return FakeScalarResult(matches)
        if "role_permission_mappings" in stmt:
            matches = [it for it in self.items if isinstance(it, RolePermissionMapping)]
            return FakeScalarResult(matches)
        if "user_branch_assignments" in stmt:
            matches = [it for it in self.items if isinstance(it, UserBranchAssignment)]
            return FakeScalarResult(matches)
        if "user_permission_overrides" in stmt:
            matches = [it for it in self.items if isinstance(it, UserPermissionOverride)]
            return FakeScalarResult(matches)
        if "patient_transfers" in stmt:
            matches = [it for it in self.items if isinstance(it, PatientTransfer)]
            return FakeScalarResult(matches)
        if "inventory_transfers" in stmt:
            matches = [it for it in self.items if isinstance(it, InventoryTransfer)]
            return FakeScalarResult(matches)
        if "enterprise_announcements" in stmt:
            matches = [it for it in self.items if isinstance(it, EnterpriseAnnouncement)]
            return FakeScalarResult(matches)
        if "enterprise_audit_logs" in stmt:
            matches = [it for it in self.items if isinstance(it, EnterpriseAuditLog)]
            return FakeScalarResult(matches)
        if "patients" in stmt:
            matches = [it for it in self.items if isinstance(it, Patient)]
            return FakeScalarResult(matches)
        if "inventory_items" in stmt:
            matches = [it for it in self.items if isinstance(it, InventoryItem)]
            return FakeScalarResult(matches)
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_organization_and_region_service():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)

    # Seed
    perms = await service.seed_permissions()
    assert len(perms) > 0

    # Org
    org_payload = OrganizationCreate(
        name="Apollo Dental Network",
        code="APOLLO",
        primary_email="corporate@apollo.com",
        phone="+911122334455",
        patient_sharing_mode=PatientSharingMode.SHARED,
    )
    org = await service.create_organization(org_payload, actor_id=uuid4())
    assert org.code == "APOLLO"
    assert org.slug == "apollo"

    # List & Update
    orgs = await service.list_organizations()
    assert len(orgs) == 1

    updated = await service.update_organization(
        org.id, OrganizationUpdate(theme_color="#0284c7")
    )
    assert updated.theme_color == "#0284c7"

    # Region
    reg = await service.create_region(
        RegionCreate(organization_id=org.id, name="West Region", code="REG-WST")
    )
    assert reg.name == "West Region"

    regions = await service.list_regions(org.id)
    assert len(regions) == 1


@pytest.mark.asyncio
async def test_branch_and_permission_service():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)

    org_id = uuid4()
    branch = await service.create_branch(
        BranchCreate(
            organization_id=org_id,
            name="Apex Clinic Mumbai",
            branch_code="B-BOM",
            email="mumbai@apollo.com",
            currency="INR",
            is_main_branch=True,
        )
    )
    assert branch.name == "Apex Clinic Mumbai"
    assert branch.branch_code == "B-BOM"

    # Custom role
    role = await service.create_role(
        EnterpriseRoleCreate(
            organization_id=org_id,
            role_key="AREA_SUPERVISOR",
            name="Area Supervisor",
            description="Supervises regional clinics",
        )
    )
    assert role.role_key == "AREA_SUPERVISOR"

    # Roaming user assignment
    user_id = uuid4()
    assignment = await service.assign_user_branch(
        UserBranchAssignmentCreate(
            user_id=user_id,
            clinic_id=branch.id,
            role_override="AREA_SUPERVISOR",
            is_primary=False,
        )
    )
    assert assignment.clinic_id == branch.id


@pytest.mark.asyncio
async def test_patient_and_inventory_transfers_service():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)

    org_id = uuid4()
    c1 = uuid4()
    c2 = uuid4()

    patient = Patient(
        id=uuid4(),
        clinic_id=c1,
        patient_number="P-100",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        date_of_birth=date(1985, 5, 20),
        mobile_number="9876500000",
    )
    db.add(patient)

    # Initiate patient transfer
    transfer = await service.create_patient_transfer(
        org_id,
        PatientTransferCreate(
            patient_id=patient.id,
            from_clinic_id=c1,
            to_clinic_id=c2,
            transfer_reason="Specialist orthodontic care at central clinic",
        ),
        actor_id=uuid4(),
    )
    assert transfer.status == TransferStatus.PENDING

    # Approve transfer
    approved = await service.handle_patient_transfer(
        transfer.id,
        PatientTransferActionRequest(status=TransferStatus.APPROVED, notes="Confirmed by clinic head"),
        actor_id=uuid4(),
    )
    assert approved.status == TransferStatus.APPROVED
    assert patient.clinic_id == c2

    # Inter-branch inventory transfer
    item = InventoryItem(
        id=uuid4(),
        clinic_id=c1,
        name="Dental Matrix Bands",
        sku="MAT-001",
        unit="box",
        category="CONSUMABLES",
        current_quantity=50,
        selling_price=450.0,
        purchase_price=300.0,
    )
    db.add(item)

    inv_tr = await service.create_inventory_transfer(
        org_id,
        InventoryTransferCreate(
            from_clinic_id=c1,
            to_clinic_id=c2,
            item_id=item.id,
            quantity=10,
            notes="Replenishment for clinic 2",
        ),
        actor_id=uuid4(),
    )
    assert inv_tr.status == InventoryTransferStatus.DRAFT
    assert "TRF-" in inv_tr.transfer_number

    # Dispatch transfer
    disp = await service.update_inventory_transfer_status(
        inv_tr.id,
        InventoryTransferStatusUpdateRequest(
            status=InventoryTransferStatus.DISPATCHED,
            tracking_number="BLUEDART-8899",
        ),
        actor_id=uuid4(),
    )
    assert disp.status == InventoryTransferStatus.DISPATCHED
    assert item.current_quantity == 40


@pytest.mark.asyncio
async def test_announcements_and_financials():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)

    org_id = uuid4()
    ann = await service.create_announcement(
        org_id,
        EnterpriseAnnouncementCreate(
            title="Q3 Clinical Audit Meeting",
            message="All branch heads must attend the corporate clinical audit on Friday.",
            announcement_type=AnnouncementType.BROADCAST,
            target_scope=AnnouncementScope.ALL,
        ),
        actor_id=uuid4(),
    )
    assert ann.title == "Q3 Clinical Audit Meeting"

    anns = await service.list_announcements(org_id)
    assert len(anns) == 1

    # Financials
    fin = await service.get_consolidated_financials(org_id)
    assert fin.organization_id == org_id
    assert fin.total_revenue >= 0.0
