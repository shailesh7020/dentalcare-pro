from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.enterprise import (
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
    TransferStatus,
)
from app.models.identity import Clinic
from app.models.inventory import InventoryItem
from app.models.patient import Patient
from app.repositories.enterprise_repository import EnterpriseRepository


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
        self.deleted = []

    def add(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = uuid4()
        if not hasattr(item, "created_at") or item.created_at is None:
            item.created_at = datetime.now(UTC)
        if not hasattr(item, "updated_at") or item.updated_at is None:
            item.updated_at = datetime.now(UTC)
        if not hasattr(item, "deleted_at"):
            item.deleted_at = None
        self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def delete(self, item):
        self.deleted.append(item)
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
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_seed_permissions_and_organizations():
    db = FakeDb()
    repo = EnterpriseRepository(db)

    perms = await repo.seed_system_permissions()
    assert len(perms) > 0
    assert any(p.permission_key == "enterprise:view" for p in perms)

    org_data = {
        "name": "DentalCorp Global",
        "slug": "dentalcorp-global",
        "code": "DCG",
        "primary_email": "admin@dentalcorp.com",
        "phone": "+919876543210",
        "theme_color": "#0d9488",
        "patient_sharing_mode": PatientSharingMode.SHARED,
    }
    org = await repo.create_organization(org_data)
    assert org.id is not None
    assert org.name == "DentalCorp Global"

    retrieved = await repo.get_organization(org.id)
    assert retrieved is not None
    assert retrieved.name == "DentalCorp Global"

    updated = await repo.update_organization(org.id, {"theme_color": "#14b8a6"})
    assert updated.theme_color == "#14b8a6"


@pytest.mark.asyncio
async def test_region_and_branch_crud():
    db = FakeDb()
    repo = EnterpriseRepository(db)

    org_id = uuid4()
    reg = await repo.create_region(
        {"organization_id": org_id, "name": "North Region", "code": "REG-NTH"}
    )
    assert reg.name == "North Region"

    branch = await repo.create_branch(
        {
            "organization_id": org_id,
            "region_id": reg.id,
            "name": "Downtown Branch",
            "slug": "downtown-branch",
            "branch_code": "BR-001",
            "email": "downtown@dentalcorp.com",
            "currency": "INR",
            "is_main_branch": True,
        }
    )
    assert branch.name == "Downtown Branch"
    assert branch.is_main_branch is True

    dept = await repo.create_department(
        {"clinic_id": branch.id, "name": "Orthodontics", "code": "ORTHO"}
    )
    assert dept.name == "Orthodontics"


@pytest.mark.asyncio
async def test_patient_transfers_and_inventory():
    db = FakeDb()
    repo = EnterpriseRepository(db)
    org_id = uuid4()
    c1 = uuid4()
    c2 = uuid4()
    from datetime import date

    from app.models.patient import Gender
    patient = Patient(
        id=uuid4(),
        clinic_id=c1,
        patient_number="P-001",
        first_name="John",
        last_name="Doe",
        gender=Gender.MALE,
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
    )
    db.add(patient)

    # Patient transfer
    transfer = await repo.create_patient_transfer(
        {
            "organization_id": org_id,
            "patient_id": patient.id,
            "from_clinic_id": c1,
            "to_clinic_id": c2,
            "transfer_reason": "Patient relocated to new city",
        }
    )
    assert transfer.status == TransferStatus.PENDING

    updated_tr = await repo.update_patient_transfer_status(
        transfer.id, TransferStatus.APPROVED, approved_by=uuid4(), notes="Approved by manager"
    )
    assert updated_tr.status == TransferStatus.APPROVED
    assert patient.clinic_id == c2

    # Inventory transfer
    item = InventoryItem(
        id=uuid4(),
        clinic_id=c1,
        name="Composite Resin A2",
        sku="RESIN-A2",
        unit="syringe",
        category="CONSUMABLES",
        current_quantity=20,
        selling_price=1200.0,
        purchase_price=800.0,
    )
    db.add(item)

    inv_tr = await repo.create_inventory_transfer(
        {
            "organization_id": org_id,
            "transfer_number": "TRF-TEST-001",
            "from_clinic_id": c1,
            "to_clinic_id": c2,
            "item_id": item.id,
            "quantity": 5,
        }
    )
    assert inv_tr.status == InventoryTransferStatus.DRAFT

    # Dispatch
    disp_tr = await repo.update_inventory_transfer_status(
        inv_tr.id, InventoryTransferStatus.DISPATCHED, actor_id=uuid4()
    )
    assert disp_tr.status == InventoryTransferStatus.DISPATCHED
    assert item.current_quantity == 15

    # Receive
    rec_tr = await repo.update_inventory_transfer_status(
        inv_tr.id, InventoryTransferStatus.RECEIVED, actor_id=uuid4()
    )
    assert rec_tr.status == InventoryTransferStatus.RECEIVED
