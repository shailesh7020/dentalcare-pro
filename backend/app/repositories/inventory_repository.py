from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from datetime import date as dt_date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.inventory import (
    BatchStatus,
    InventoryBatch,
    InventoryCategory,
    InventoryItem,
    InventoryStatus,
    ProcedureMaterialTemplate,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderStatus,
    StockTransaction,
    StockTransactionType,
    Supplier,
)
from app.schemas.inventory import (
    ConsumptionReportItem,
    InventoryDashboardStats,
    InventoryItemCreate,
    InventoryItemUpdate,
    MedicineAvailabilityCheck,
    PurchaseOrderCreate,
    PurchaseOrderReceive,
    PurchaseOrderUpdate,
    StockAdjustmentCreate,
    StockAlertItem,
    StockAlertSummary,
    StockValuationItem,
    StockValuationReport,
    SupplierCreate,
    SupplierDetail,
    SupplierRead,
    SupplierUpdate,
)


class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================
    # Sequence Generators
    # ==========================================
    async def generate_sku(self, clinic_id: UUID, category: str) -> str:
        cat_code = category[:3].upper() if category else "ITM"
        prefix = f"SKU-{cat_code}"
        query = select(func.count(InventoryItem.id)).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.sku.like(f"{prefix}-%"),
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        candidate = f"{prefix}-{(count + 1):04d}"

        # Collision guard
        exists_q = select(InventoryItem.id).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.sku == candidate,
        )
        if (await self.db.execute(exists_q)).scalar_one_or_none():
            rand_suffix = random.randint(1000, 9999)
            candidate = f"{prefix}-{rand_suffix}"
        return candidate

    async def generate_po_number(self, clinic_id: UUID, order_date: dt_date) -> str:
        date_str = order_date.strftime("%Y%m%d")
        prefix = f"PO-{date_str}"
        query = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.clinic_id == clinic_id,
            PurchaseOrder.po_number.like(f"{prefix}-%"),
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        candidate = f"{prefix}-{(count + 1):04d}"

        exists_q = select(PurchaseOrder.id).where(
            PurchaseOrder.clinic_id == clinic_id,
            PurchaseOrder.po_number == candidate,
        )
        if (await self.db.execute(exists_q)).scalar_one_or_none():
            rand_suffix = random.randint(1000, 9999)
            candidate = f"{prefix}-{rand_suffix}"
        return candidate

    # ==========================================
    # Supplier Management
    # ==========================================
    async def get_supplier(self, clinic_id: UUID, supplier_id: UUID) -> Supplier | None:
        query = select(Supplier).where(
            Supplier.clinic_id == clinic_id,
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_suppliers(
        self,
        clinic_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Supplier], int]:
        query = select(Supplier).where(
            Supplier.clinic_id == clinic_id,
            Supplier.deleted_at.is_(None),
        )
        if is_active is not None:
            query = query.where(Supplier.is_active == is_active)
        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Supplier.name.ilike(s),
                    Supplier.contact_person.ilike(s),
                    Supplier.phone.ilike(s),
                    Supplier.email.ilike(s),
                    Supplier.gst_number.ilike(s),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(Supplier.name.asc()).offset(skip).limit(limit)
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def create_supplier(
        self, clinic_id: UUID, payload: SupplierCreate, actor_id: UUID | None
    ) -> Supplier:
        supplier = Supplier(
            clinic_id=clinic_id,
            name=payload.name,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=payload.email,
            gst_number=payload.gst_number,
            address=payload.address,
            payment_terms=payload.payment_terms,
            is_active=payload.is_active,
            rating=payload.rating,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(supplier)
        await self.db.flush()
        return supplier

    async def update_supplier(
        self, supplier: Supplier, payload: SupplierUpdate, actor_id: UUID | None
    ) -> Supplier:
        data = payload.model_dump(exclude_unset=True)
        for field, val in data.items():
            setattr(supplier, field, val)
        supplier.updated_by = actor_id
        await self.db.flush()
        return supplier

    async def get_supplier_detail(self, clinic_id: UUID, supplier: Supplier) -> SupplierDetail:
        # Count items
        items_count_q = select(func.count(InventoryItem.id)).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.supplier_id == supplier.id,
            InventoryItem.deleted_at.is_(None),
        )
        item_count = (await self.db.execute(items_count_q)).scalar() or 0

        # Count active POs
        active_po_q = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.clinic_id == clinic_id,
            PurchaseOrder.supplier_id == supplier.id,
            PurchaseOrder.status.in_([PurchaseOrderStatus.DRAFT.value, PurchaseOrderStatus.SENT.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value]),
            PurchaseOrder.deleted_at.is_(None),
        )
        active_po_count = (await self.db.execute(active_po_q)).scalar() or 0

        detail_dict = SupplierRead.model_validate(supplier).model_dump()
        return SupplierDetail(
            **detail_dict,
            item_count=item_count,
            active_po_count=active_po_count,
        )

    # ==========================================
    # Inventory Items Master
    # ==========================================
    def _base_item_query(self, clinic_id: UUID):
        return (
            select(InventoryItem)
            .where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.deleted_at.is_(None),
            )
            .options(
                selectinload(InventoryItem.supplier),
                selectinload(InventoryItem.batches),
            )
        )

    async def get_item(self, clinic_id: UUID, item_id: UUID) -> InventoryItem | None:
        query = self._base_item_query(clinic_id).where(InventoryItem.id == item_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_item_by_sku(self, clinic_id: UUID, sku: str) -> InventoryItem | None:
        query = self._base_item_query(clinic_id).where(InventoryItem.sku == sku)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_items(
        self,
        clinic_id: UUID,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        low_stock: bool = False,
        expiring_days: int | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[InventoryItem], int]:
        query = self._base_item_query(clinic_id)

        if category:
            query = query.where(InventoryItem.category == category)
        if status:
            query = query.where(InventoryItem.status == status)
        if low_stock:
            query = query.where(InventoryItem.current_quantity <= InventoryItem.reorder_level)
        if expiring_days is not None:
            today = datetime.now(UTC).date()
            cutoff = today + timedelta(days=expiring_days)
            query = query.where(
                InventoryItem.expiry_date.isnot(None),
                InventoryItem.expiry_date <= cutoff,
            )
        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryItem.name.ilike(s),
                    InventoryItem.sku.ilike(s),
                    InventoryItem.barcode.ilike(s),
                    InventoryItem.generic_name.ilike(s),
                    InventoryItem.brand.ilike(s),
                    InventoryItem.storage_location.ilike(s),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(InventoryItem.name.asc()).offset(skip).limit(limit)
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    def _determine_item_status(self, item: InventoryItem) -> str:
        if item.status == InventoryStatus.DISCONTINUED.value:
            return InventoryStatus.DISCONTINUED.value
        today = datetime.now(UTC).date()
        if item.expiry_date and item.expiry_date < today and item.current_quantity > 0:
            return InventoryStatus.EXPIRED.value
        if item.current_quantity <= 0:
            return InventoryStatus.OUT_OF_STOCK.value
        reorder = item.reorder_level if item.reorder_level is not None else 0
        if item.current_quantity <= reorder:
            return InventoryStatus.LOW_STOCK.value
        return InventoryStatus.IN_STOCK.value

    async def create_item(
        self, clinic_id: UUID, payload: InventoryItemCreate, actor_id: UUID | None
    ) -> InventoryItem:
        sku = payload.sku or await self.generate_sku(clinic_id, payload.category.value)
        status = InventoryStatus.IN_STOCK.value
        if payload.initial_quantity <= 0:
            status = InventoryStatus.OUT_OF_STOCK.value
        elif payload.initial_quantity <= payload.reorder_level:
            status = InventoryStatus.LOW_STOCK.value

        item = InventoryItem(
            clinic_id=clinic_id,
            sku=sku,
            barcode=payload.barcode,
            name=payload.name,
            generic_name=payload.generic_name,
            brand=payload.brand,
            category=payload.category.value,
            manufacturer=payload.manufacturer,
            supplier_id=payload.supplier_id,
            unit=payload.unit,
            minimum_stock=payload.minimum_stock,
            maximum_stock=payload.maximum_stock,
            reorder_level=payload.reorder_level,
            current_quantity=payload.initial_quantity,
            purchase_price=payload.purchase_price,
            selling_price=payload.selling_price,
            tax_rate=payload.tax_rate,
            batch_number=payload.initial_batch_number,
            expiry_date=payload.initial_expiry_date,
            storage_location=payload.storage_location,
            status=status,
            medicine_catalog_id=payload.medicine_catalog_id,
            notes=payload.notes,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(item)
        await self.db.flush()

        # If opening stock > 0, create batch and opening balance transaction
        if payload.initial_quantity > 0:
            batch_num = payload.initial_batch_number or f"BATCH-{sku}-INIT"
            exp_date = payload.initial_expiry_date or (datetime.now(UTC).date() + timedelta(days=365))
            batch = InventoryBatch(
                clinic_id=clinic_id,
                item_id=item.id,
                batch_number=batch_num,
                expiry_date=exp_date,
                quantity=payload.initial_quantity,
                initial_quantity=payload.initial_quantity,
                purchase_price=payload.purchase_price,
                received_date=datetime.now(UTC).date(),
                supplier_id=payload.supplier_id,
                status=BatchStatus.ACTIVE.value,
                notes="Initial opening stock",
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(batch)
            await self.db.flush()

            tx = StockTransaction(
                clinic_id=clinic_id,
                item_id=item.id,
                batch_id=batch.id,
                transaction_type=StockTransactionType.OPENING_BALANCE.value,
                quantity=payload.initial_quantity,
                previous_quantity=0,
                new_quantity=payload.initial_quantity,
                unit_cost=payload.purchase_price,
                total_cost=float(payload.purchase_price) * payload.initial_quantity,
                reason="Initial inventory setup",
                actor_id=actor_id,
                notes=payload.notes,
            )
            self.db.add(tx)
            await self.db.flush()

        return item

    async def update_item(
        self, item: InventoryItem, payload: InventoryItemUpdate, actor_id: UUID | None
    ) -> InventoryItem:
        data = payload.model_dump(exclude_unset=True)
        for field, val in data.items():
            if field == "category" and val is not None:
                setattr(item, field, val.value if hasattr(val, "value") else str(val))
            else:
                setattr(item, field, val)

        item.status = self._determine_item_status(item)
        item.updated_by = actor_id
        await self.db.flush()
        return item

    async def delete_item(self, item: InventoryItem, actor_id: UUID | None) -> None:
        item.deleted_at = datetime.now(UTC)
        item.updated_by = actor_id
        await self.db.flush()

    # ==========================================
    # Batches & FIFO Deduction
    # ==========================================
    async def get_active_batches(self, clinic_id: UUID, item_id: UUID) -> list[InventoryBatch]:
        query = (
            select(InventoryBatch)
            .where(
                InventoryBatch.clinic_id == clinic_id,
                InventoryBatch.item_id == item_id,
                InventoryBatch.deleted_at.is_(None),
                InventoryBatch.status == BatchStatus.ACTIVE.value,
                InventoryBatch.quantity > 0,
            )
            .order_by(InventoryBatch.expiry_date.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def deduct_fifo(
        self,
        clinic_id: UUID,
        item: InventoryItem,
        quantity: int,
        transaction_type: str,
        reason: str,
        actor_id: UUID | None,
        treatment_id: UUID | None = None,
        invoice_id: UUID | None = None,
    ) -> list[StockTransaction]:
        """
        Deducts quantity from earliest expiring active batches (FIFO / FEFO).
        Creates corresponding StockTransactions and updates item stock and status.
        """
        if quantity <= 0:
            return []

        active_batches = await self.get_active_batches(clinic_id, item.id)
        remaining = quantity
        transactions: list[StockTransaction] = []

        for batch in active_batches:
            if remaining <= 0:
                break
            deduct_qty = min(batch.quantity, remaining)
            batch.quantity -= deduct_qty
            remaining -= deduct_qty
            if batch.quantity == 0:
                batch.status = BatchStatus.DEPLETED.value

            tx = StockTransaction(
                clinic_id=clinic_id,
                item_id=item.id,
                batch_id=batch.id,
                transaction_type=transaction_type,
                quantity=-deduct_qty,
                previous_quantity=item.current_quantity,
                new_quantity=max(0, item.current_quantity - deduct_qty),
                unit_cost=batch.purchase_price,
                total_cost=float(batch.purchase_price) * deduct_qty,
                reason=reason,
                related_treatment_id=treatment_id,
                related_invoice_id=invoice_id,
                actor_id=actor_id,
            )
            item.current_quantity = max(0, item.current_quantity - deduct_qty)
            self.db.add(tx)
            transactions.append(tx)

        # Discrepancy / unbatched stock fallback
        if remaining > 0 and item.current_quantity > 0:
            unbatched_deduct = min(item.current_quantity, remaining)
            tx = StockTransaction(
                clinic_id=clinic_id,
                item_id=item.id,
                batch_id=None,
                transaction_type=transaction_type,
                quantity=-unbatched_deduct,
                previous_quantity=item.current_quantity,
                new_quantity=item.current_quantity - unbatched_deduct,
                unit_cost=item.purchase_price,
                total_cost=float(item.purchase_price) * unbatched_deduct,
                reason=f"{reason} (Unbatched stock)",
                related_treatment_id=treatment_id,
                related_invoice_id=invoice_id,
                actor_id=actor_id,
            )
            item.current_quantity -= unbatched_deduct
            self.db.add(tx)
            transactions.append(tx)

        # Refresh earliest active batch expiry on item
        remaining_active = [b for b in active_batches if b.quantity > 0]
        if remaining_active:
            item.expiry_date = remaining_active[0].expiry_date
            item.batch_number = remaining_active[0].batch_number

        item.status = self._determine_item_status(item)
        item.updated_by = actor_id
        await self.db.flush()
        return transactions

    # ==========================================
    # Stock Adjustments & Movement Ledger
    # ==========================================
    async def record_adjustment(
        self,
        clinic_id: UUID,
        item: InventoryItem,
        payload: StockAdjustmentCreate,
        actor_id: UUID | None,
    ) -> StockTransaction:
        prev_qty = item.current_quantity
        qty_delta = payload.quantity
        new_qty = max(0, prev_qty + qty_delta)
        cost = payload.unit_cost if payload.unit_cost is not None else float(item.purchase_price)

        batch_id = payload.batch_id

        # If adding stock and batch info provided, create or increment batch
        if qty_delta > 0 and payload.batch_number:
            exp_date = payload.expiry_date or (datetime.now(UTC).date() + timedelta(days=365))
            batch = InventoryBatch(
                clinic_id=clinic_id,
                item_id=item.id,
                batch_number=payload.batch_number,
                expiry_date=exp_date,
                quantity=qty_delta,
                initial_quantity=qty_delta,
                purchase_price=cost,
                received_date=datetime.now(UTC).date(),
                status=BatchStatus.ACTIVE.value,
                notes=payload.notes,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(batch)
            await self.db.flush()
            batch_id = batch.id
            if not item.expiry_date or exp_date < item.expiry_date:
                item.expiry_date = exp_date
                item.batch_number = payload.batch_number
        elif qty_delta < 0 and batch_id:
            # Deduct from specific batch
            b_query = select(InventoryBatch).where(
                InventoryBatch.clinic_id == clinic_id,
                InventoryBatch.id == batch_id,
            )
            b = (await self.db.execute(b_query)).scalar_one_or_none()
            if b:
                b.quantity = max(0, b.quantity + qty_delta)
                if b.quantity == 0:
                    b.status = BatchStatus.DEPLETED.value

        item.current_quantity = new_qty
        item.status = self._determine_item_status(item)
        item.updated_by = actor_id

        tx = StockTransaction(
            clinic_id=clinic_id,
            item_id=item.id,
            batch_id=batch_id,
            transaction_type=payload.adjustment_type.value,
            quantity=qty_delta,
            previous_quantity=prev_qty,
            new_quantity=new_qty,
            unit_cost=cost,
            total_cost=cost * abs(qty_delta),
            reason=payload.reason,
            actor_id=actor_id,
            notes=payload.notes,
        )
        self.db.add(tx)
        await self.db.flush()
        return tx

    async def list_transactions(
        self,
        clinic_id: UUID,
        item_id: UUID | None = None,
        treatment_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[StockTransaction]:
        query = (
            select(StockTransaction)
            .where(StockTransaction.clinic_id == clinic_id)
            .options(
                selectinload(StockTransaction.item),
                selectinload(StockTransaction.batch),
                selectinload(StockTransaction.actor),
            )
        )
        if item_id:
            query = query.where(StockTransaction.item_id == item_id)
        if treatment_id:
            query = query.where(StockTransaction.related_treatment_id == treatment_id)

        query = query.order_by(StockTransaction.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==========================================
    # Purchase Orders & Goods Receipt
    # ==========================================
    def _base_po_query(self, clinic_id: UUID):
        return (
            select(PurchaseOrder)
            .where(
                PurchaseOrder.clinic_id == clinic_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .options(
                selectinload(PurchaseOrder.supplier),
                selectinload(PurchaseOrder.items).selectinload(PurchaseOrderItem.item),
                selectinload(PurchaseOrder.approver),
                selectinload(PurchaseOrder.clinic),
            )
        )

    async def get_purchase_order(self, clinic_id: UUID, po_id: UUID) -> PurchaseOrder | None:
        query = self._base_po_query(clinic_id).where(PurchaseOrder.id == po_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_purchase_orders(
        self,
        clinic_id: UUID,
        status: str | None = None,
        supplier_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrder], int]:
        query = self._base_po_query(clinic_id)
        if status:
            query = query.where(PurchaseOrder.status == status)
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def create_purchase_order(
        self, clinic_id: UUID, payload: PurchaseOrderCreate, actor_id: UUID | None
    ) -> PurchaseOrder:
        po_number = await self.generate_po_number(clinic_id, payload.order_date)

        subtotal = 0.0
        tax_amount = 0.0

        po = PurchaseOrder(
            clinic_id=clinic_id,
            po_number=po_number,
            supplier_id=payload.supplier_id,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            status=PurchaseOrderStatus.DRAFT.value,
            subtotal=0.0,
            tax_amount=0.0,
            discount_amount=payload.discount_amount,
            grand_total=0.0,
            notes=payload.notes,
            terms=payload.terms,
            created_by=actor_id,
            updated_by=actor_id,
        )
        po.items = []
        self.db.add(po)
        await self.db.flush()

        for item_in in payload.items:
            line_sub = float(item_in.unit_price) * item_in.quantity_ordered
            line_tax = line_sub * (float(item_in.tax_rate) / 100.0)
            line_total = line_sub + line_tax

            subtotal += line_sub
            tax_amount += line_tax

            po_item = PurchaseOrderItem(
                po_id=po.id,
                item_id=item_in.item_id,
                quantity_ordered=item_in.quantity_ordered,
                quantity_received=0,
                unit_price=item_in.unit_price,
                tax_rate=item_in.tax_rate,
                tax_amount=round(line_tax, 2),
                total=round(line_total, 2),
                notes=item_in.notes,
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(po_item)
            po.items.append(po_item)

        po.subtotal = round(subtotal, 2)
        po.tax_amount = round(tax_amount, 2)
        po.grand_total = max(0.0, round(subtotal + tax_amount - payload.discount_amount, 2))
        await self.db.flush()
        return po

    async def update_purchase_order(
        self, po: PurchaseOrder, payload: PurchaseOrderUpdate, actor_id: UUID | None
    ) -> PurchaseOrder:
        data = payload.model_dump(exclude_unset=True)
        for field, val in data.items():
            if field == "status" and val is not None:
                setattr(po, field, val.value if hasattr(val, "value") else str(val))
            elif field == "discount_amount" and val is not None:
                po.discount_amount = val
                po.grand_total = max(0.0, round(float(po.subtotal) + float(po.tax_amount) - float(val), 2))
            else:
                setattr(po, field, val)

        po.updated_by = actor_id
        await self.db.flush()
        return po

    async def receive_goods(
        self, po: PurchaseOrder, payload: PurchaseOrderReceive, actor_id: UUID | None
    ) -> PurchaseOrder:
        """
        Receives items against a purchase order:
        - Increments quantity_received on line items
        - Creates new InventoryBatch
        - Increments InventoryItem.current_quantity
        - Creates StockTransaction (PURCHASE)
        - Updates PO status (PARTIALLY_RECEIVED or RECEIVED)
        """
        for r_item in payload.items:
            # Find PO item
            line = next((i for i in po.items if i.id == r_item.po_item_id), None)
            if not line:
                continue

            qty_rcv = r_item.quantity_to_receive
            line.quantity_received += qty_rcv

            # Find inventory item
            item = await self.get_item(po.clinic_id, line.item_id)
            if not item:
                continue

            cost = r_item.purchase_price if r_item.purchase_price is not None else float(line.unit_price)

            # Create batch
            batch = InventoryBatch(
                clinic_id=po.clinic_id,
                item_id=item.id,
                batch_number=r_item.batch_number,
                expiry_date=r_item.expiry_date,
                quantity=qty_rcv,
                initial_quantity=qty_rcv,
                purchase_price=cost,
                received_date=datetime.now(UTC).date(),
                supplier_id=po.supplier_id,
                purchase_order_id=po.id,
                status=BatchStatus.ACTIVE.value,
                notes=payload.notes or f"Received from PO {po.po_number}",
                created_by=actor_id,
                updated_by=actor_id,
            )
            self.db.add(batch)
            await self.db.flush()

            # Increment item quantity & update earliest expiry
            prev_qty = item.current_quantity
            item.current_quantity += qty_rcv
            if not item.expiry_date or r_item.expiry_date < item.expiry_date:
                item.expiry_date = r_item.expiry_date
                item.batch_number = r_item.batch_number
            item.status = self._determine_item_status(item)
            item.purchase_price = cost

            # Create StockTransaction
            tx = StockTransaction(
                clinic_id=po.clinic_id,
                item_id=item.id,
                batch_id=batch.id,
                transaction_type=StockTransactionType.PURCHASE.value,
                quantity=qty_rcv,
                previous_quantity=prev_qty,
                new_quantity=item.current_quantity,
                unit_cost=cost,
                total_cost=cost * qty_rcv,
                reason=f"Goods Receipt PO #{po.po_number}",
                related_po_id=po.id,
                actor_id=actor_id,
                notes=payload.notes,
            )
            self.db.add(tx)

        # Check total fulfillment
        all_fulfilled = all(line.quantity_received >= line.quantity_ordered for line in po.items)
        if all_fulfilled:
            po.status = PurchaseOrderStatus.RECEIVED.value
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED.value

        po.updated_by = actor_id
        await self.db.flush()
        return po

    # ==========================================
    # Procedure Material Templates & Consumption
    # ==========================================
    async def get_templates_for_procedure(
        self, clinic_id: UUID, procedure_name: str
    ) -> list[ProcedureMaterialTemplate]:
        query = select(ProcedureMaterialTemplate).where(
            or_(
                ProcedureMaterialTemplate.clinic_id == clinic_id,
                ProcedureMaterialTemplate.clinic_id.is_(None),
            ),
            ProcedureMaterialTemplate.procedure_name.ilike(f"%{procedure_name.strip()}%"),
            ProcedureMaterialTemplate.deleted_at.is_(None),
        ).options(selectinload(ProcedureMaterialTemplate.item))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ==========================================
    # Reports & Dashboard Analytics
    # ==========================================
    async def get_dashboard_stats(self, clinic_id: UUID) -> InventoryDashboardStats:
        today = datetime.now(UTC).date()
        cutoff_30 = today + timedelta(days=30)

        # Items query
        items_q = select(InventoryItem).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.deleted_at.is_(None),
        )
        items = (await self.db.execute(items_q)).scalars().all()

        total_items = len(items)
        total_valuation = sum(float(i.purchase_price or 0.0) * i.current_quantity for i in items)
        low_stock_count = sum(1 for i in items if 0 < i.current_quantity <= i.reorder_level)
        out_of_stock_count = sum(1 for i in items if i.current_quantity <= 0)
        expired_count = sum(1 for i in items if i.expiry_date and i.expiry_date < today and i.current_quantity > 0)
        near_expiry_count = sum(
            1 for i in items if i.expiry_date and today <= i.expiry_date <= cutoff_30 and i.current_quantity > 0
        )

        # Pending POs
        po_q = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.clinic_id == clinic_id,
            PurchaseOrder.status.in_([
                PurchaseOrderStatus.DRAFT.value,
                PurchaseOrderStatus.SENT.value,
                PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
            ]),
            PurchaseOrder.deleted_at.is_(None),
        )
        pending_po_count = (await self.db.execute(po_q)).scalar() or 0

        return InventoryDashboardStats(
            total_items=total_items,
            total_valuation=round(total_valuation, 2),
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            near_expiry_count=near_expiry_count,
            expired_count=expired_count,
            pending_po_count=pending_po_count,
        )

    async def get_alerts(self, clinic_id: UUID) -> StockAlertSummary:
        today = datetime.now(UTC).date()

        items_q = select(InventoryItem).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.deleted_at.is_(None),
        )
        items = (await self.db.execute(items_q)).scalars().all()

        low_stock_alerts: list[StockAlertItem] = []
        expiry_alerts: list[StockAlertItem] = []

        for itm in items:
            if itm.current_quantity <= 0:
                low_stock_alerts.append(
                    StockAlertItem(
                        item_id=itm.id,
                        name=itm.name,
                        sku=itm.sku,
                        category=itm.category,
                        current_quantity=itm.current_quantity,
                        reorder_level=itm.reorder_level,
                        alert_type="OUT_OF_STOCK",
                    )
                )
            elif itm.current_quantity <= itm.reorder_level:
                low_stock_alerts.append(
                    StockAlertItem(
                        item_id=itm.id,
                        name=itm.name,
                        sku=itm.sku,
                        category=itm.category,
                        current_quantity=itm.current_quantity,
                        reorder_level=itm.reorder_level,
                        alert_type="LOW_STOCK",
                    )
                )

            if itm.expiry_date and itm.current_quantity > 0:
                days = (itm.expiry_date - today).days
                if days < 0:
                    expiry_alerts.append(
                        StockAlertItem(
                            item_id=itm.id,
                            name=itm.name,
                            sku=itm.sku,
                            category=itm.category,
                            current_quantity=itm.current_quantity,
                            reorder_level=itm.reorder_level,
                            alert_type="EXPIRED",
                            expiry_date=itm.expiry_date,
                            days_until_expiry=days,
                        )
                    )
                elif days <= 60:
                    expiry_alerts.append(
                        StockAlertItem(
                            item_id=itm.id,
                            name=itm.name,
                            sku=itm.sku,
                            category=itm.category,
                            current_quantity=itm.current_quantity,
                            reorder_level=itm.reorder_level,
                            alert_type="NEAR_EXPIRY",
                            expiry_date=itm.expiry_date,
                            days_until_expiry=days,
                        )
                    )

        # Pending POs
        po_q = select(func.count(PurchaseOrder.id)).where(
            PurchaseOrder.clinic_id == clinic_id,
            PurchaseOrder.status.in_([
                PurchaseOrderStatus.DRAFT.value,
                PurchaseOrderStatus.SENT.value,
                PurchaseOrderStatus.PARTIALLY_RECEIVED.value,
            ]),
            PurchaseOrder.deleted_at.is_(None),
        )
        pending_orders_count = (await self.db.execute(po_q)).scalar() or 0

        return StockAlertSummary(
            low_stock_alerts=low_stock_alerts,
            expiry_alerts=expiry_alerts,
            pending_orders_count=pending_orders_count,
        )

    async def get_valuation_report(self, clinic_id: UUID) -> StockValuationReport:
        items_q = select(InventoryItem).where(
            InventoryItem.clinic_id == clinic_id,
            InventoryItem.deleted_at.is_(None),
        )
        items = (await self.db.execute(items_q)).scalars().all()

        cats: dict[str, dict] = {}
        for itm in items:
            c = itm.category
            if c not in cats:
                cats[c] = {
                    "count": 0,
                    "quantity": 0,
                    "cost_val": 0.0,
                    "sell_val": 0.0,
                }
            cats[c]["count"] += 1
            cats[c]["quantity"] += itm.current_quantity
            cats[c]["cost_val"] += float(itm.purchase_price or 0.0) * itm.current_quantity
            cats[c]["sell_val"] += float(itm.selling_price or 0.0) * itm.current_quantity

        val_list = [
            StockValuationItem(
                category=k,
                item_count=v["count"],
                total_quantity=v["quantity"],
                total_cost_value=round(v["cost_val"], 2),
                total_selling_value=round(v["sell_val"], 2),
            )
            for k, v in sorted(cats.items())
        ]
        total_val = sum(v["cost_val"] for v in cats.values())

        return StockValuationReport(
            total_items=len(items),
            total_inventory_value=round(total_val, 2),
            valuation_by_category=val_list,
        )

    async def get_consumption_report(
        self, clinic_id: UUID, start_date: dt_date | None = None, end_date: dt_date | None = None
    ) -> list[ConsumptionReportItem]:
        query = (
            select(StockTransaction)
            .where(
                StockTransaction.clinic_id == clinic_id,
                StockTransaction.transaction_type == StockTransactionType.CONSUMPTION.value,
            )
            .options(selectinload(StockTransaction.item))
        )
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
            query = query.where(StockTransaction.created_at >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=UTC)
            query = query.where(StockTransaction.created_at <= end_dt)

        txs = (await self.db.execute(query)).scalars().all()

        grouped: dict[UUID, dict] = {}
        for tx in txs:
            item = tx.item or await self.get_item(clinic_id, tx.item_id)
            if not item:
                continue
            iid = tx.item_id
            if iid not in grouped:
                grouped[iid] = {
                    "item_id": item.id,
                    "item_name": item.name,
                    "sku": item.sku,
                    "category": item.category,
                    "total_consumed_quantity": 0,
                    "total_cost": 0.0,
                    "procedures": set(),
                }
            grouped[iid]["total_consumed_quantity"] += abs(tx.quantity)
            grouped[iid]["total_cost"] += float(tx.total_cost)
            if tx.reason:
                grouped[iid]["procedures"].add(tx.reason)

        return [
            ConsumptionReportItem(
                item_id=v["item_id"],
                item_name=v["item_name"],
                sku=v["sku"],
                category=v["category"],
                total_consumed_quantity=v["total_consumed_quantity"],
                total_cost=round(v["total_cost"], 2),
                procedure_names=list(v["procedures"]),
            )
            for v in grouped.values()
        ]

    async def check_medicine_availability(
        self, clinic_id: UUID, search_terms: list[str]
    ) -> list[MedicineAvailabilityCheck]:
        results: list[MedicineAvailabilityCheck] = []
        today = datetime.now(UTC).date()

        for term in search_terms:
            t = f"%{term.strip()}%"
            query = select(InventoryItem).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.category == InventoryCategory.MEDICINES.value,
                InventoryItem.deleted_at.is_(None),
                or_(
                    InventoryItem.name.ilike(t),
                    InventoryItem.generic_name.ilike(t),
                    InventoryItem.brand.ilike(t),
                ),
            ).order_by(InventoryItem.current_quantity.desc()).limit(1)

            item = (await self.db.execute(query)).scalar_one_or_none()
            if not item:
                results.append(
                    MedicineAvailabilityCheck(
                        medicine_name=term,
                        is_available=False,
                        stock_status="OUT_OF_STOCK",
                        current_quantity=0,
                    )
                )
            else:
                is_expired = item.expiry_date and item.expiry_date < today
                status = "EXPIRED" if is_expired else ("IN_STOCK" if item.current_quantity > 0 else "OUT_OF_STOCK")
                if not is_expired and 0 < item.current_quantity <= item.reorder_level:
                    status = "LOW_STOCK"

                results.append(
                    MedicineAvailabilityCheck(
                        medicine_name=item.name,
                        generic_name=item.generic_name,
                        is_available=(item.current_quantity > 0 and not is_expired),
                        stock_status=status,
                        current_quantity=item.current_quantity,
                        earliest_expiry=item.expiry_date,
                        unit=item.unit,
                    )
                )

        return results
