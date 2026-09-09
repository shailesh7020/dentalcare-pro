from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import inventory as inventory_api
from app.models.identity import Clinic, Role, User
from app.models.inventory import (
    BatchStatus,
    InventoryBatch,
    InventoryCategory,
    InventoryItem,
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
    InventoryItemUpdate,
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderReceive,
    PurchaseOrderReceiveItem,
    PurchaseOrderUpdate,
    StockAdjustmentCreate,
    SupplierCreate,
    SupplierUpdate,
    TreatmentConsumptionRequest,
    TreatmentMaterialConsumeItem,
)


class FakeApiDb:
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
            if hasattr(statement, "compile"):
                try:
                    params = statement.compile().params
                    matching_id = [p for p in pos if p.id in params.values()]
                    if matching_id:
                        pos = matching_id
                except (AttributeError, KeyError, ValueError):
                    pass
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
def api_setup():
    clinic_id = uuid4()
    clinic = Clinic(
        id=clinic_id,
        name="Apollo Dental Care",
        slug="apollo",
        email="contact@apollodental.com",
        phone="+91 44 2829 0000",
    )
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@apollodental.com",
        first_name="Pooja",
        last_name="Iyer",
        role=Role.CLINIC_ADMIN,
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dentist@apollodental.com",
        first_name="Dr. Suresh",
        last_name="Menon",
        role=Role.DENTIST,
    )
    db = FakeApiDb([clinic, admin, dentist])
    return clinic_id, admin, dentist, db


@pytest.mark.asyncio
async def test_dashboard_and_alerts_endpoints(api_setup):
    _clinic_id, admin, _dentist, db = api_setup

    stats = await inventory_api.get_dashboard_stats(actor=admin, db=db)
    assert stats.total_items == 0
    assert stats.total_valuation == 0.0

    alerts = await inventory_api.get_alerts(actor=admin, db=db)
    assert alerts.pending_orders_count == 0


@pytest.mark.asyncio
async def test_supplier_api_endpoints(api_setup):
    _clinic_id, admin, dentist, db = api_setup

    # Create supplier
    s_create = SupplierCreate(
        name="MedPlus Wholesale Dist",
        contact_person="Ramesh Gupta",
        phone="+91 98400 12345",
        email="sales@medplus.in",
        rating=4.7,
    )
    sup = await inventory_api.create_supplier(s_create, actor=admin, db=db)
    assert sup.name == "MedPlus Wholesale Dist"

    # List suppliers
    sups = await inventory_api.list_suppliers(actor=dentist, db=db)
    assert len(sups) >= 1

    # Get supplier detail
    detail = await inventory_api.get_supplier(sup.id, actor=dentist, db=db)
    assert detail.id == sup.id

    # Update supplier
    up = await inventory_api.update_supplier(
        sup.id, SupplierUpdate(rating=4.9), actor=admin, db=db
    )
    assert up.rating == 4.9


@pytest.mark.asyncio
async def test_inventory_items_and_adjustment_endpoints(api_setup):
    _clinic_id, admin, dentist, db = api_setup

    # Create item
    item_payload = InventoryItemCreate(
        name="Alginate Impression Material",
        category=InventoryCategory.PROSTHODONTIC,
        unit="PACK",
        minimum_stock=10,
        reorder_level=20,
        purchase_price=400.00,
        selling_price=650.00,
        initial_quantity=30,
        initial_batch_number="ALG-2026-01",
    )
    item = await inventory_api.create_item(item_payload, actor=admin, db=db)
    assert item.name == "Alginate Impression Material"
    assert item.current_quantity == 30

    # List items
    items = await inventory_api.list_items(actor=dentist, db=db)
    assert len(items) >= 1

    # Get item detail
    detail = await inventory_api.get_item(item.id, actor=dentist, db=db)
    assert detail.id == item.id
    assert detail.current_quantity == 30

    # Update item
    updated = await inventory_api.update_item(
        item.id, InventoryItemUpdate(reorder_level=25), actor=admin, db=db
    )
    assert updated.reorder_level == 25

    # Adjust stock
    adj_payload = StockAdjustmentCreate(
        adjustment_type=StockTransactionType.ADJUSTMENT,
        quantity=5,
        reason="Stock audit correction",
    )
    tx = await inventory_api.adjust_stock(item.id, adj_payload, actor=admin, db=db)
    assert tx.quantity == 5
    assert tx.new_quantity == 35

    # Delete item
    await inventory_api.delete_item(item.id, actor=admin, db=db)
    # Re-fetch shows marked deleted
    db_item = await db.get(InventoryItem, item.id)
    assert db_item.deleted_at is not None


@pytest.mark.asyncio
async def test_purchase_orders_api_endpoints(api_setup):
    clinic_id, admin, dentist, db = api_setup

    supplier = Supplier(id=uuid4(), clinic_id=clinic_id, name="OrthoLine Supplies")
    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-ORT-0001",
        name="Orthodontic Brackets 0.022",
        category=InventoryCategory.ORTHODONTIC.value,
        unit="SET",
        purchase_price=1200.00,
        current_quantity=5,
    )
    db.items.extend([supplier, item])

    today = datetime.now(UTC).date()

    # Create PO
    po_create = PurchaseOrderCreate(
        supplier_id=supplier.id,
        order_date=today,
        items=[
            PurchaseOrderItemCreate(
                item_id=item.id,
                quantity_ordered=10,
                unit_price=1200.00,
                tax_rate=18.0,
            )
        ],
    )
    po = await inventory_api.create_purchase_order(po_create, actor=admin, db=db)
    assert po.po_number.startswith("PO-")

    # List POs
    pos = await inventory_api.list_purchase_orders(actor=dentist, db=db)
    assert len(pos) >= 1

    # Get PO Detail
    detail = await inventory_api.get_purchase_order(po.id, actor=dentist, db=db)
    assert detail.id == po.id

    # Update PO
    updated_po = await inventory_api.update_purchase_order(
        po.id, PurchaseOrderUpdate(notes="Standard delivery"), actor=admin, db=db
    )
    assert updated_po.notes == "Standard delivery"

    # Download PO PDF
    pdf_resp = await inventory_api.get_purchase_order_pdf(po.id, actor=dentist, db=db)
    assert pdf_resp.media_type == "application/pdf"
    assert pdf_resp.body.startswith(b"%PDF-")

    # Receive Goods
    rcv = PurchaseOrderReceive(
        items=[
            PurchaseOrderReceiveItem(
                po_item_id=po.items[0].id,
                quantity_to_receive=10,
                batch_number="BRK-2026-10",
                expiry_date=today + timedelta(days=1000),
            )
        ]
    )
    rcv_po = await inventory_api.receive_purchase_order(po.id, rcv, actor=admin, db=db)
    assert rcv_po.status == PurchaseOrderStatus.RECEIVED.value

    # Cancel a draft PO
    draft_po_create = PurchaseOrderCreate(
        supplier_id=supplier.id,
        order_date=today,
        items=[
            PurchaseOrderItemCreate(
                item_id=item.id,
                quantity_ordered=2,
                unit_price=1200.00,
            )
        ],
    )
    draft_po = await inventory_api.create_purchase_order(draft_po_create, actor=admin, db=db)
    cancelled = await inventory_api.cancel_purchase_order(draft_po.id, actor=admin, db=db)
    assert cancelled.status == PurchaseOrderStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_treatment_consumption_and_reports_api_endpoints(api_setup):
    clinic_id, _admin, dentist, db = api_setup

    today = datetime.now(UTC).date()

    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-CON-0088",
        name="Prophylaxis Paste Spearmint",
        category=InventoryCategory.CONSUMABLES.value,
        unit="GM",
        purchase_price=20.00,
        current_quantity=50,
    )
    batch = InventoryBatch(
        id=uuid4(),
        clinic_id=clinic_id,
        item_id=item.id,
        batch_number="PROPHY-1",
        expiry_date=today + timedelta(days=365),
        quantity=50,
        initial_quantity=50,
        purchase_price=20.00,
        received_date=today,
        status=BatchStatus.ACTIVE.value,
    )
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0088",
        diagnosis="Gingivitis",
        status=TreatmentStatus.IN_PROGRESS,
    )
    proc = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment.id,
        procedure_name="Scaling & Polishing",
        quantity=1,
    )
    treatment.procedures = [proc]
    db.items.extend([item, batch, treatment, proc])

    # Consume materials
    consume_res = await inventory_api.consume_treatment_materials(
        treatment.id,
        TreatmentConsumptionRequest(
            items=[TreatmentMaterialConsumeItem(item_id=item.id, quantity=2)],
            notes="Scaling paste usage",
        ),
        actor=dentist,
        db=db,
    )
    assert len(consume_res.consumed_items) == 1
    assert consume_res.consumed_items[0].quantity == 2

    # Get consumption
    history = await inventory_api.get_treatment_consumption(treatment.id, actor=dentist, db=db)
    assert len(history.consumed_items) == 1

    # Transactions ledger
    txs = await inventory_api.list_transactions(treatment_id=treatment.id, actor=dentist, db=db)
    assert len(txs) >= 1

    # Valuation report
    val = await inventory_api.get_valuation_report(actor=dentist, db=db)
    assert val.total_items >= 1

    # Consumption report
    cons_rep = await inventory_api.get_consumption_report(actor=dentist, db=db)
    assert len(cons_rep) >= 1

    # Check clinic context validation
    no_clinic_user = User(
        id=uuid4(),
        clinic_id=None,
        email="noclinc@test.com",
        first_name="No",
        last_name="Clinic",
        role=Role.SUPER_ADMIN,
    )
    with pytest.raises(HTTPException) as exc:
        await inventory_api.get_dashboard_stats(actor=no_clinic_user, db=db)
    assert exc.value.status_code == 400
