from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.api.v1 import enterprise as ep_api
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
from app.models.identity import Clinic, Role, User
from app.models.inventory import InventoryItem
from app.models.patient import Gender, Patient
from app.repositories.enterprise_repository import EnterpriseRepository
from app.schemas.enterprise import (
    BranchCreate,
    DepartmentBase,
    EnterpriseAnnouncementCreate,
    EnterpriseRoleCreate,
    InventoryTransferCreate,
    InventoryTransferStatusUpdateRequest,
    OrganizationCreate,
    OrganizationUpdate,
    PatientTransferActionRequest,
    PatientTransferCreate,
    RegionBase,
    RolePermissionAssignRequest,
)
from app.services.ai.enterprise_analytics_service import EnterpriseAnalyticsService
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


def make_admin():
    return User(
        id=uuid4(),
        first_name="Admin",
        last_name="User",
        email="superadmin@dentalcorp.com",
        role=Role.SUPER_ADMIN,
        password_hash="fake",
    )


@pytest.mark.asyncio
async def test_api_permissions_and_organizations():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)
    user = make_admin()

    # Seed permissions
    perms = await ep_api.seed_permissions(current_user=user, service=service)
    assert len(perms) > 0

    list_perms = await ep_api.list_permissions(current_user=user, service=service)
    assert len(list_perms) > 0

    # Create Org
    org_payload = OrganizationCreate(
        name="Global Dental Systems",
        code="GDS",
        primary_email="info@gds.com",
        patient_sharing_mode=PatientSharingMode.SHARED,
    )
    org = await ep_api.create_organization(payload=org_payload, current_user=user, service=service)
    assert org.name == "Global Dental Systems"

    # List Orgs
    orgs = await ep_api.list_organizations(current_user=user, service=service)
    assert len(orgs) == 1

    # Get Org
    retrieved = await ep_api.get_organization(org_id=org.id, current_user=user, service=service)
    assert retrieved.code == "GDS"

    # Update Org
    updated = await ep_api.update_organization(
        org_id=org.id,
        payload=OrganizationUpdate(website="https://gds.com"),
        current_user=user,
        service=service,
    )
    assert updated.website == "https://gds.com"


@pytest.mark.asyncio
async def test_api_regions_branches_departments():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)
    user = make_admin()
    org_id = uuid4()

    # Region
    reg = await ep_api.create_region(
        org_id=org_id,
        payload=RegionBase(name="South Hub", code="REG-STH"),
        current_user=user,
        service=service,
    )
    assert reg.name == "South Hub"

    regs = await ep_api.list_regions(org_id=org_id, current_user=user, service=service)
    assert len(regs) == 1

    # Branch
    branch = await ep_api.create_branch(
        org_id=org_id,
        payload=BranchCreate(
            organization_id=org_id,
            region_id=reg.id,
            name="Bangalore Flagship",
            branch_code="BR-BLR",
            email="blr@gds.com",
            is_main_branch=True,
        ),
        current_user=user,
        service=service,
    )
    assert branch.name == "Bangalore Flagship"

    branches = await ep_api.list_branches(org_id=org_id, current_user=user, service=service)
    assert len(branches) == 1

    b_retrieved = await ep_api.get_branch(branch_id=branch.id, current_user=user, service=service)
    assert b_retrieved.branch_code == "BR-BLR"

    # Department
    dept = await ep_api.create_department(
        branch_id=branch.id,
        payload=DepartmentBase(name="Periodontics", code="PERIO"),
        current_user=user,
        service=service,
    )
    assert dept.name == "Periodontics"

    depts = await ep_api.list_departments(branch_id=branch.id, current_user=user, service=service)
    assert len(depts) == 1


@pytest.mark.asyncio
async def test_api_roles_and_transfers():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)
    user = make_admin()
    org_id = uuid4()
    c1 = uuid4()
    c2 = uuid4()

    # Role
    role = await ep_api.create_role(
        payload=EnterpriseRoleCreate(
            organization_id=org_id,
            role_key="REGIONAL_CLINICAL_DIRECTOR",
            name="Regional Clinical Director",
        ),
        current_user=user,
        service=service,
    )
    assert role.role_key == "REGIONAL_CLINICAL_DIRECTOR"

    perm_id = uuid4()
    resp_map = await ep_api.assign_role_permissions(
        role_id=role.id,
        payload=RolePermissionAssignRequest(permission_ids=[perm_id]),
        current_user=user,
        service=service,
    )
    assert resp_map["message"] == "Role permissions assigned successfully"

    # Patient Transfer
    patient = Patient(
        id=uuid4(), clinic_id=c1, patient_number="PT-99", first_name="Tom", last_name="Hanks",
        gender=Gender.MALE, date_of_birth=date(1970, 7, 9), mobile_number="9988776655",
    )
    db.add(patient)

    tr = await ep_api.create_patient_transfer(
        org_id=org_id,
        payload=PatientTransferCreate(
            patient_id=patient.id,
            from_clinic_id=c1,
            to_clinic_id=c2,
            transfer_reason="Transfer for cosmetic surgery",
        ),
        current_user=user,
        service=service,
    )
    assert tr.status == TransferStatus.PENDING

    tr_action = await ep_api.handle_patient_transfer(
        org_id=org_id,
        transfer_id=tr.id,
        payload=PatientTransferActionRequest(status=TransferStatus.APPROVED, notes="Approved"),
        current_user=user,
        service=service,
    )
    assert tr_action.status == TransferStatus.APPROVED

    # Inventory Transfer
    item = InventoryItem(
        id=uuid4(), clinic_id=c1, name="Bonding Agent", sku="BOND-01",
        unit="bottle", category="CONSUMABLES", current_quantity=25,
        selling_price=800.0, purchase_price=500.0,
    )
    db.add(item)

    inv_tr = await ep_api.create_inventory_transfer(
        org_id=org_id,
        payload=InventoryTransferCreate(
            from_clinic_id=c1, to_clinic_id=c2, item_id=item.id, quantity=5,
        ),
        current_user=user,
        service=service,
    )
    assert inv_tr.status == InventoryTransferStatus.DRAFT

    inv_tr_up = await ep_api.update_inventory_transfer_status(
        org_id=org_id,
        transfer_id=inv_tr.id,
        payload=InventoryTransferStatusUpdateRequest(status=InventoryTransferStatus.DISPATCHED),
        current_user=user,
        service=service,
    )
    assert inv_tr_up.status == InventoryTransferStatus.DISPATCHED


@pytest.mark.asyncio
async def test_api_analytics_announcements_financials():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    service = EnterpriseService(repo)
    analytics_service = EnterpriseAnalyticsService(db, repo)
    user = make_admin()
    org_id = uuid4()

    # Financials
    fin = await ep_api.get_consolidated_financials(org_id=org_id, current_user=user, service=service)
    assert fin.organization_id == org_id

    # Analytics
    analytics = await ep_api.get_enterprise_analytics(
        org_id=org_id, current_user=user, analytics_service=analytics_service
    )
    assert analytics.organization_id == org_id
    assert isinstance(analytics.strategic_recommendations, list)

    # Announcements
    ann = await ep_api.create_announcement(
        org_id=org_id,
        payload=EnterpriseAnnouncementCreate(
            title="System Maintenance Notice",
            message="Server upgrade scheduled at 2 AM.",
            announcement_type=AnnouncementType.BRANCH_ALERT,
            target_scope=AnnouncementScope.ALL,
        ),
        current_user=user,
        service=service,
    )
    assert ann.title == "System Maintenance Notice"

    anns = await ep_api.list_announcements(org_id=org_id, current_user=user, service=service)
    assert len(anns) == 1

    # Audit logs
    logs = await ep_api.list_audit_logs(org_id=org_id, current_user=user, service=service)
    assert isinstance(logs, list)
