from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.identity import Clinic, Role, User
from app.models.inventory import (
    BatchStatus,
    InventoryBatch,
    InventoryCategory,
    InventoryItem,
    InventoryStatus,
    ProcedureMaterialTemplate,
    PurchaseOrder,
    PurchaseOrderStatus,
    StockTransaction,
    StockTransactionType,
    Supplier,
)
from app.models.treatment import Treatment, TreatmentProcedure, TreatmentStatus
from app.schemas.inventory import (
    InventoryItemCreate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderReceive,
    PurchaseOrderReceiveItem,
    StockAdjustmentCreate,
    SupplierCreate,
    SupplierUpdate,
    TreatmentConsumptionRequest,
    TreatmentMaterialConsumeItem,
)
from app.services.inventory_service import InventoryService


class FakeServiceDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def delete(self, item: object) -> None:
        if item in self.items:
            self.items.remove(item)

    async def flush(self) -> None:
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
            if getattr(item, "created_at", None) is None:
                item.created_at = datetime.now(UTC)
            if getattr(item, "updated_at", None) is None:
                item.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def get(self, model: type, id_: object) -> object | None:
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, statement: object) -> object:
        text = str(statement).lower()

        # Count queries
        if "count(" in text:
            if "from suppliers" in text:
                matching = [i for i in self.items if isinstance(i, Supplier) and i.deleted_at is None]
                return SimpleNamespace(scalar=lambda: len(matching))
            if "from inventory_items" in text:
                matching = [i for i in self.items if isinstance(i, InventoryItem) and i.deleted_at is None]
                return SimpleNamespace(scalar=lambda: len(matching))
            if "from purchase_orders" in text:
                matching = [i for i in self.items if isinstance(i, PurchaseOrder) and i.deleted_at is None]
                return SimpleNamespace(scalar=lambda: len(matching))

        # Clinic query
        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic) and i.deleted_at is None]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        # Suppliers query
        if "from suppliers" in text:
            suppliers = [i for i in self.items if isinstance(i, Supplier) and i.deleted_at is None]
            first = suppliers[0] if suppliers else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: suppliers),
            )

        # Inventory items query
        if "from inventory_items" in text:
            items = [i for i in self.items if isinstance(i, InventoryItem) and i.deleted_at is None]
            if hasattr(statement, "compile"):
                try:
                    params = statement.compile().params
                    for val in params.values():
                        if val == InventoryCategory.MEDICINES.value:
                            items = [i for i in items if i.category == InventoryCategory.MEDICINES.value]
                        elif isinstance(val, str) and val.startswith("%") and val.endswith("%"):
                            term = val[1:-1].lower()
                            items = [
                                i
                                for i in items
                                if term in (i.name or "").lower()
                                or term in (i.generic_name or "").lower()
                            ]
                except (AttributeError, KeyError, ValueError):
                    pass
            first = items[0] if items else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: items),
            )

        # Inventory batches query
        if "from inventory_batches" in text:
            batches = [i for i in self.items if isinstance(i, InventoryBatch) and i.deleted_at is None]
            first = batches[0] if batches else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: batches),
            )

        # Purchase orders query
        if "from purchase_orders" in text:
            pos = [i for i in self.items if isinstance(i, PurchaseOrder) and i.deleted_at is None]
            first = pos[0] if pos else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: pos),
            )

        # Treatment query
        if "from treatments" in text:
            treatments = [i for i in self.items if isinstance(i, Treatment) and i.deleted_at is None]
            first = treatments[0] if treatments else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: treatments),
            )

        # Stock transactions query
        if "from stock_transactions" in text:
            txs = [i for i in self.items if isinstance(i, StockTransaction)]
            first = txs[0] if txs else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: txs),
            )

        # Procedure material templates query
        if "from procedure_material_templates" in text:
            tmpls = [i for i in self.items if isinstance(i, ProcedureMaterialTemplate) and i.deleted_at is None]
            first = tmpls[0] if tmpls else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: tmpls),
            )

        return SimpleNamespace(
            scalar=lambda: None,
            scalar_one_or_none=lambda: None,
            scalars=lambda: SimpleNamespace(all=list),
        )


@pytest.fixture
def test_setup():
    clinic_id = uuid4()
    clinic = Clinic(
        id=clinic_id,
        name="Apex Dental Hospital",
        slug="apex",
        email="info@apexdental.com",
        phone="+91 22 2840 0000",
    )
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@apexdental.com",
        first_name="Anita",
        last_name="Desai",
        role=Role.CLINIC_ADMIN,
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@apexdental.com",
        first_name="Dr. Rohit",
        last_name="Verma",
        role=Role.DENTIST,
    )
    db = FakeServiceDb([clinic, admin, dentist])
    service = InventoryService(db)
    return clinic_id, admin, dentist, db, service


@pytest.mark.asyncio
async def test_supplier_and_item_service_workflow(test_setup):
    clinic_id, admin, _dentist, _db, service = test_setup

    # 1. Create Supplier
    s_create = SupplierCreate(
        name="Prime Dental Supplies Ltd",
        contact_person="Vikas Khanna",
        phone="+91 99887 76655",
        email="vikas@primedental.com",
        payment_terms="Net 15",
    )
    supplier = await service.create_supplier(clinic_id, s_create, admin)
    assert supplier.name == "Prime Dental Supplies Ltd"

    # 2. Update Supplier
    supplier_up = await service.update_supplier(
        clinic_id, supplier.id, SupplierUpdate(notes="Preferred vendor for endodontic files"), admin
    )
    assert supplier_up.notes == "Preferred vendor for endodontic files"

    # 3. Create Item
    itm_create = InventoryItemCreate(
        name="Endodontic K-Files #15-40",
        category=InventoryCategory.ENDODONTIC,
        supplier_id=supplier.id,
        unit="PACK",
        minimum_stock=5,
        reorder_level=12,
        purchase_price=350.00,
        selling_price=550.00,
        initial_quantity=20,
    )
    item = await service.create_item(clinic_id, itm_create, admin)
    assert item.name == "Endodontic K-Files #15-40"
    assert item.current_quantity == 20

    # 4. Item Detail
    detail = await service.get_item_detail(clinic_id, item.id)
    assert detail.id == item.id
    assert detail.supplier is not None
    assert detail.supplier.name == "Prime Dental Supplies Ltd"

    # 5. List items
    items, total = await service.list_items(clinic_id)
    assert total >= 1
    assert any(i.id == item.id for i in items)


@pytest.mark.asyncio
async def test_non_negative_stock_enforcement(test_setup):
    clinic_id, admin, _dentist, db, service = test_setup

    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-SUR-0001",
        name="Surgical Blades #15",
        category=InventoryCategory.SURGICAL.value,
        unit="BOX",
        current_quantity=10,
        reorder_level=5,
        purchase_price=250.00,
        status=InventoryStatus.IN_STOCK.value,
    )
    db.items.append(item)

    # 1. Valid reduction to 0
    adj_valid = StockAdjustmentCreate(
        adjustment_type=StockTransactionType.ADJUSTMENT,
        quantity=-10,
        reason="Damaged in transit",
    )
    res_valid = await service.adjust_stock(clinic_id, item.id, adj_valid, admin)
    assert res_valid.new_quantity == 0
    assert item.current_quantity == 0

    # 2. Reduction below 0 MUST raise 400 Bad Request
    adj_invalid = StockAdjustmentCreate(
        adjustment_type=StockTransactionType.ADJUSTMENT,
        quantity=-5,
        reason="Further deduction impossible",
    )
    with pytest.raises(HTTPException) as exc:
        await service.adjust_stock(clinic_id, item.id, adj_invalid, admin)
    assert exc.value.status_code == 400
    assert "Cannot reduce stock below zero" in exc.value.detail


@pytest.mark.asyncio
async def test_purchase_order_and_pdf_generation(test_setup):
    clinic_id, admin, _dentist, db, service = test_setup

    supplier = Supplier(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Apex Diagnostics & Medical Supplies",
        is_active=True,
    )
    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-MED-0001",
        name="Amoxicillin 500mg Capsules",
        category=InventoryCategory.MEDICINES.value,
        unit="BOX",
        current_quantity=10,
        reorder_level=20,
        purchase_price=90.00,
        status=InventoryStatus.LOW_STOCK.value,
    )
    db.items.extend([supplier, item])

    today = datetime.now(UTC).date()

    # 1. Create Purchase Order
    po_create = PurchaseOrderCreate(
        supplier_id=supplier.id,
        order_date=today,
        terms="Payment within 30 days upon receipt",
        items=[
            PurchaseOrderItemCreate(
                item_id=item.id,
                quantity_ordered=50,
                unit_price=90.00,
                tax_rate=5.0,
            )
        ],
    )
    po = await service.create_purchase_order(clinic_id, po_create, admin)
    assert po.po_number.startswith("PO-")
    assert len(po.items) == 1
    assert float(po.grand_total) > 0

    # 2. Generate PDF
    pdf_bytes = await service.generate_po_pdf(clinic_id, po.id)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 1000

    # 3. Receive Goods
    rcv_payload = PurchaseOrderReceive(
        items=[
            PurchaseOrderReceiveItem(
                po_item_id=po.items[0].id,
                quantity_to_receive=50,
                batch_number="AMX-2026-99",
                expiry_date=today + timedelta(days=700),
            )
        ]
    )
    rcv_po = await service.receive_purchase_order(clinic_id, po.id, rcv_payload, admin)
    assert rcv_po.status == PurchaseOrderStatus.RECEIVED.value
    assert item.current_quantity == 60


@pytest.mark.asyncio
async def test_treatment_material_consumption_workflow(test_setup):
    clinic_id, _admin, dentist, db, service = test_setup

    today = datetime.now(UTC).date()

    # Items for Root Canal
    endo_file = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-END-0001",
        name="Endodontic Rotary Files (Protaper)",
        category=InventoryCategory.ENDODONTIC.value,
        unit="PACK",
        current_quantity=10,
        reorder_level=5,
        purchase_price=800.00,
        status=InventoryStatus.IN_STOCK.value,
    )
    gloves = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-CON-0001",
        name="Disposable Latex Gloves",
        category=InventoryCategory.CONSUMABLES.value,
        unit="PAIR",
        current_quantity=100,
        reorder_level=20,
        purchase_price=15.00,
        status=InventoryStatus.IN_STOCK.value,
    )
    db.items.extend([endo_file, gloves])

    # Active batches
    b1 = InventoryBatch(
        id=uuid4(),
        clinic_id=clinic_id,
        item_id=endo_file.id,
        batch_number="B-ENDO-1",
        expiry_date=today + timedelta(days=365),
        quantity=10,
        initial_quantity=10,
        purchase_price=800.00,
        received_date=today,
        status=BatchStatus.ACTIVE.value,
    )
    b2 = InventoryBatch(
        id=uuid4(),
        clinic_id=clinic_id,
        item_id=gloves.id,
        batch_number="B-GLV-1",
        expiry_date=today + timedelta(days=500),
        quantity=100,
        initial_quantity=100,
        purchase_price=15.00,
        received_date=today,
        status=BatchStatus.ACTIVE.value,
    )
    db.items.extend([b1, b2])

    # Treatment with Root Canal procedure
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Irreversible Pulpitis #46",
        status=TreatmentStatus.IN_PROGRESS,
    )
    proc = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment.id,
        procedure_name="Root Canal Therapy",
        quantity=1,
    )
    treatment.procedures = [proc]
    db.items.extend([treatment, proc])

    # 1. Automatic procedural consumption using default Root Canal recipe
    res_auto = await service.consume_treatment_materials(clinic_id, treatment.id, None, dentist)
    assert res_auto.treatment_id == treatment.id
    assert len(res_auto.consumed_items) >= 1
    assert res_auto.total_material_cost > 0

    # 2. View consumed materials for treatment
    consumed_view = await service.get_treatment_consumed_materials(clinic_id, treatment.id)
    assert consumed_view.treatment_id == treatment.id
    assert len(consumed_view.consumed_items) == len(res_auto.consumed_items)

    # 3. Explicit consumption
    res_explicit = await service.consume_treatment_materials(
        clinic_id,
        treatment.id,
        TreatmentConsumptionRequest(
            items=[TreatmentMaterialConsumeItem(item_id=gloves.id, quantity=4)],
            notes="Additional operator gloves",
        ),
        dentist,
    )
    assert len(res_explicit.consumed_items) == 1
    assert res_explicit.consumed_items[0].quantity == 4
