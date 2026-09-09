from __future__ import annotations

from datetime import UTC, datetime, timedelta
from datetime import date as dt_date
from types import SimpleNamespace
from uuid import uuid4

import pytest

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
from app.repositories.inventory_repository import InventoryRepository
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
)


class FakeInventoryDb:
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
                except (AttributeError, KeyError):
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

        # Stock transactions query
        if "from stock_transactions" in text:
            txs = [i for i in self.items if isinstance(i, StockTransaction)]
            first = txs[0] if txs else None
            return SimpleNamespace(
                scalar_one_or_none=lambda: first,
                scalars=lambda: SimpleNamespace(all=lambda: txs),
            )

        # Procedure material templates
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


def today_date() -> dt_date:
    return datetime.now(UTC).date()


@pytest.mark.asyncio
async def test_sku_and_po_number_generation():
    clinic_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    sku = await repo.generate_sku(clinic_id, "CONSUMABLES")
    assert sku.startswith("SKU-CON-")

    po_num = await repo.generate_po_number(clinic_id, dt_date(2026, 9, 8))
    assert po_num.startswith("PO-20260908-")


@pytest.mark.asyncio
async def test_supplier_crud():
    clinic_id = uuid4()
    actor_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    # 1. Create Supplier
    payload = SupplierCreate(
        name="DentSupply India Pvt Ltd",
        contact_person="Rajesh Sharma",
        phone="+91 98765 11223",
        email="orders@dentsupply.in",
        gst_number="27AABCS1429B1Z8",
        address="Bandra West, Mumbai",
        payment_terms="Net 30",
        rating=4.8,
    )
    supplier = await repo.create_supplier(clinic_id, payload, actor_id)
    assert supplier.name == "DentSupply India Pvt Ltd"
    assert supplier.clinic_id == clinic_id

    # 2. Get Supplier
    fetched = await repo.get_supplier(clinic_id, supplier.id)
    assert fetched is not None
    assert fetched.name == "DentSupply India Pvt Ltd"

    # 3. Update Supplier
    up_payload = SupplierUpdate(phone="+91 98765 99999", rating=4.9)
    updated = await repo.update_supplier(supplier, up_payload, actor_id)
    assert updated.phone == "+91 98765 99999"
    assert updated.rating == 4.9

    # 4. List Suppliers
    suppliers, count = await repo.list_suppliers(clinic_id)
    assert count >= 1
    assert any(s.id == supplier.id for s in suppliers)

    # 5. Detail view
    detail = await repo.get_supplier_detail(clinic_id, supplier)
    assert detail.name == "DentSupply India Pvt Ltd"
    assert detail.item_count == 0


@pytest.mark.asyncio
async def test_inventory_item_crud_with_opening_stock():
    clinic_id = uuid4()
    actor_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    # Create Item with opening stock
    payload = InventoryItemCreate(
        name="Composite Resin A2 Universal",
        category=InventoryCategory.DENTAL_MATERIALS,
        unit="CAPSULE",
        minimum_stock=10,
        maximum_stock=200,
        reorder_level=20,
        purchase_price=120.00,
        selling_price=250.00,
        tax_rate=12.0,
        initial_quantity=50,
        initial_batch_number="BATCH-CR-001",
        initial_expiry_date=today_date() + timedelta(days=365),
    )
    item = await repo.create_item(clinic_id, payload, actor_id)
    assert item.name == "Composite Resin A2 Universal"
    assert item.current_quantity == 50
    assert item.status == InventoryStatus.IN_STOCK.value

    # Verify opening balance batch & stock transaction
    batch = next((b for b in db.items if isinstance(b, InventoryBatch) and b.item_id == item.id), None)
    assert batch is not None
    assert batch.batch_number == "BATCH-CR-001"
    assert batch.quantity == 50

    tx = next((t for t in db.items if isinstance(t, StockTransaction) and t.item_id == item.id), None)
    assert tx is not None
    assert tx.transaction_type == StockTransactionType.OPENING_BALANCE.value
    assert tx.quantity == 50

    # Update item
    up_payload = InventoryItemUpdate(reorder_level=25, notes="Frequently used in operatories")
    updated = await repo.update_item(item, up_payload, actor_id)
    assert updated.reorder_level == 25
    assert updated.notes == "Frequently used in operatories"

    # Soft delete item
    await repo.delete_item(item, actor_id)
    assert item.deleted_at is not None


@pytest.mark.asyncio
async def test_fifo_batch_deduction():
    clinic_id = uuid4()
    actor_id = uuid4()
    treatment_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    # Create item
    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-MAT-0001",
        name="Dental Anaesthetic Cartridges",
        category=InventoryCategory.MEDICINES.value,
        unit="CARTRIDGE",
        minimum_stock=5,
        reorder_level=10,
        current_quantity=20,
        purchase_price=45.00,
        selling_price=90.00,
        status=InventoryStatus.IN_STOCK.value,
    )
    db.items.append(item)

    # Batch 1: Expiring in 10 days (qty 5)
    b1 = InventoryBatch(
        id=uuid4(),
        clinic_id=clinic_id,
        item_id=item.id,
        batch_number="B-EXP-SOON",
        expiry_date=today_date() + timedelta(days=10),
        quantity=5,
        initial_quantity=5,
        purchase_price=40.00,
        received_date=today_date(),
        status=BatchStatus.ACTIVE.value,
    )
    # Batch 2: Expiring in 60 days (qty 15)
    b2 = InventoryBatch(
        id=uuid4(),
        clinic_id=clinic_id,
        item_id=item.id,
        batch_number="B-EXP-LATER",
        expiry_date=today_date() + timedelta(days=60),
        quantity=15,
        initial_quantity=15,
        purchase_price=45.00,
        received_date=today_date(),
        status=BatchStatus.ACTIVE.value,
    )
    db.items.extend([b1, b2])

    # Deduct 8 cartridges: should completely deplete B1 (5) and take 3 from B2
    txs = await repo.deduct_fifo(
        clinic_id=clinic_id,
        item=item,
        quantity=8,
        transaction_type=StockTransactionType.CONSUMPTION.value,
        reason="Extraction Procedure",
        actor_id=actor_id,
        treatment_id=treatment_id,
    )

    assert len(txs) == 2
    assert b1.quantity == 0
    assert b1.status == BatchStatus.DEPLETED.value
    assert b2.quantity == 12
    assert item.current_quantity == 12
    assert item.status == InventoryStatus.IN_STOCK.value


@pytest.mark.asyncio
async def test_purchase_order_lifecycle_and_goods_receipt():
    clinic_id = uuid4()
    actor_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    # Setup Supplier and Item
    supplier = Supplier(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Global Dental Logistics",
        is_active=True,
    )
    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-CON-0042",
        name="Sterile Surgical Gloves (M)",
        category=InventoryCategory.CONSUMABLES.value,
        unit="BOX",
        current_quantity=10,
        reorder_level=15,
        purchase_price=250.00,
        status=InventoryStatus.LOW_STOCK.value,
    )
    db.items.extend([supplier, item])

    # 1. Create Purchase Order (Order 20 boxes at ₹250 + 12% GST)
    po_create = PurchaseOrderCreate(
        supplier_id=supplier.id,
        order_date=today_date(),
        discount_amount=100.00,
        items=[
            PurchaseOrderItemCreate(
                item_id=item.id,
                quantity_ordered=20,
                unit_price=250.00,
                tax_rate=12.0,
            )
        ],
    )
    po = await repo.create_purchase_order(clinic_id, po_create, actor_id)
    assert po.po_number.startswith("PO-")
    assert po.status == PurchaseOrderStatus.DRAFT.value
    assert float(po.subtotal) == 5000.00
    assert float(po.tax_amount) == 600.00
    assert float(po.grand_total) == 5500.00  # 5000 + 600 - 100

    # 2. Update Purchase Order
    up_po = PurchaseOrderUpdate(notes="Urgent operatory supply")
    updated_po = await repo.update_purchase_order(po, up_po, actor_id)
    assert updated_po.notes == "Urgent operatory supply"

    # 3. Goods Receipt: Receive 10 boxes (Partial)
    po_item = po.items[0]
    rcv_payload = PurchaseOrderReceive(
        items=[
            PurchaseOrderReceiveItem(
                po_item_id=po_item.id,
                quantity_to_receive=10,
                batch_number="GLV-2026-B1",
                expiry_date=today_date() + timedelta(days=730),
            )
        ],
        notes="Partial delivery received by front desk",
    )
    po = await repo.receive_goods(po, rcv_payload, actor_id)
    assert po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED.value
    assert po_item.quantity_received == 10
    assert item.current_quantity == 20  # 10 existing + 10 received
    assert item.status == InventoryStatus.IN_STOCK.value

    # 4. Goods Receipt: Receive remaining 10 boxes (Full)
    rcv_payload_2 = PurchaseOrderReceive(
        items=[
            PurchaseOrderReceiveItem(
                po_item_id=po_item.id,
                quantity_to_receive=10,
                batch_number="GLV-2026-B2",
                expiry_date=today_date() + timedelta(days=730),
            )
        ]
    )
    po = await repo.receive_goods(po, rcv_payload_2, actor_id)
    assert po.status == PurchaseOrderStatus.RECEIVED.value
    assert po_item.quantity_received == 20
    assert item.current_quantity == 30


@pytest.mark.asyncio
async def test_stock_adjustments_and_reports():
    clinic_id = uuid4()
    actor_id = uuid4()
    db = FakeInventoryDb()
    repo = InventoryRepository(db)

    item = InventoryItem(
        id=uuid4(),
        clinic_id=clinic_id,
        sku="SKU-SUR-0010",
        name="Disposable Scalpel Blades #15",
        category=InventoryCategory.SURGICAL.value,
        unit="BOX",
        current_quantity=20,
        reorder_level=10,
        purchase_price=300.00,
        selling_price=450.00,
        status=InventoryStatus.IN_STOCK.value,
    )
    db.items.append(item)

    # Positive adjustment
    adj_pos = StockAdjustmentCreate(
        adjustment_type=StockTransactionType.ADJUSTMENT,
        quantity=5,
        batch_number="SCALPEL-ADJ-1",
        reason="Physical audit stock surplus",
    )
    tx_pos = await repo.record_adjustment(clinic_id, item, adj_pos, actor_id)
    assert tx_pos.quantity == 5
    assert tx_pos.new_quantity == 25
    assert item.current_quantity == 25

    # Negative adjustment (damaged)
    adj_neg = StockAdjustmentCreate(
        adjustment_type=StockTransactionType.DAMAGED,
        quantity=-2,
        reason="Water damaged packaging during rain",
    )
    tx_neg = await repo.record_adjustment(clinic_id, item, adj_neg, actor_id)
    assert tx_neg.quantity == -2
    assert tx_neg.new_quantity == 23
    assert item.current_quantity == 23

    # Dashboard stats
    stats = await repo.get_dashboard_stats(clinic_id)
    assert stats.total_items == 1
    assert stats.total_valuation == 23 * 300.00

    # Alerts
    alerts = await repo.get_alerts(clinic_id)
    assert alerts.pending_orders_count == 0

    # Valuation report
    val_report = await repo.get_valuation_report(clinic_id)
    assert val_report.total_items == 1
    assert len(val_report.valuation_by_category) == 1
    assert val_report.valuation_by_category[0].category == InventoryCategory.SURGICAL.value

    # Medicine availability
    med_avail = await repo.check_medicine_availability(clinic_id, ["Scalpel", "Amoxicillin"])
    assert len(med_avail) == 2
    assert med_avail[1].is_available is False
    assert med_avail[1].stock_status == "OUT_OF_STOCK"
