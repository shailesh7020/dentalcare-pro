from __future__ import annotations

import json
from datetime import date as dt_date
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import AuditEvent, Clinic, User
from app.models.inventory import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderStatus,
    StockTransactionType,
)
from app.models.treatment import Treatment
from app.repositories.inventory_repository import InventoryRepository
from app.schemas.inventory import (
    ConsumptionReportItem,
    InventoryBatchRead,
    InventoryDashboardStats,
    InventoryItemCreate,
    InventoryItemDetail,
    InventoryItemRead,
    InventoryItemUpdate,
    MedicineAvailabilityCheck,
    PurchaseOrderCreate,
    PurchaseOrderDetail,
    PurchaseOrderItemRead,
    PurchaseOrderRead,
    PurchaseOrderReceive,
    PurchaseOrderUpdate,
    StockAdjustmentCreate,
    StockAlertSummary,
    StockTransactionRead,
    StockValuationReport,
    SupplierCreate,
    SupplierDetail,
    SupplierRead,
    SupplierUpdate,
    TreatmentConsumedItemRead,
    TreatmentConsumptionRequest,
    TreatmentConsumptionResponse,
)
from app.services.inventory_pdf_service import InventoryPDFService

# Standard clinical consumption recipes for dental procedures
DEFAULT_PROCEDURE_RECIPES: dict[str, list[dict]] = {
    "root canal": [
        {"name": "Endodontic Rotary Files (Protaper)", "quantity": 1, "unit": "PACK"},
        {"name": "Gutta Percha Points 4%", "quantity": 3, "unit": "PCS"},
        {"name": "Sodium Hypochlorite 3% Irrigation", "quantity": 10, "unit": "ML"},
        {"name": "Cavit Temporary Restoration", "quantity": 1, "unit": "GM"},
        {"name": "Disposable Latex Gloves", "quantity": 2, "unit": "PAIR"},
        {"name": "Disposable Surgical Face Mask", "quantity": 2, "unit": "PCS"},
        {"name": "Saliva Ejector Suction Tip", "quantity": 2, "unit": "PCS"},
    ],
    "extraction": [
        {"name": "Lignocaine 2% with Adrenaline Cartridge", "quantity": 2, "unit": "CARTRIDGE"},
        {"name": "Dental Disposable Syringe Needle 27G", "quantity": 2, "unit": "PCS"},
        {"name": "Sterile Gauze Swabs 2x2", "quantity": 4, "unit": "PCS"},
        {"name": "Braided Silk Suture 3-0", "quantity": 1, "unit": "PCS"},
        {"name": "Disposable Latex Gloves", "quantity": 2, "unit": "PAIR"},
        {"name": "Disposable Surgical Face Mask", "quantity": 2, "unit": "PCS"},
    ],
    "scaling": [
        {"name": "Ultrasonic Scaler Tip G1", "quantity": 1, "unit": "PCS"},
        {"name": "Prophylaxis Paste Spearmint", "quantity": 2, "unit": "GM"},
        {"name": "Saliva Ejector Suction Tip", "quantity": 1, "unit": "PCS"},
        {"name": "Disposable Latex Gloves", "quantity": 2, "unit": "PAIR"},
        {"name": "Disposable Surgical Face Mask", "quantity": 2, "unit": "PCS"},
    ],
    "composite restoration": [
        {"name": "Composite Restorative Resin Universal (A2)", "quantity": 1, "unit": "CAPSULE"},
        {"name": "Dental Etch & Bond Adhesive Agent", "quantity": 1, "unit": "DROP"},
        {"name": "Microbrush Applicators Regular", "quantity": 2, "unit": "PCS"},
        {"name": "Celluloid Matrix Strips", "quantity": 1, "unit": "PCS"},
        {"name": "Disposable Latex Gloves", "quantity": 2, "unit": "PAIR"},
    ],
}


class InventoryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InventoryRepository(db)

    # ==========================================
    # Supplier Business Logic
    # ==========================================
    async def create_supplier(
        self, clinic_id: UUID, payload: SupplierCreate, actor: User
    ) -> SupplierDetail:
        supplier = await self.repo.create_supplier(clinic_id, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="SUPPLIER",
                entity_id=str(supplier.id),
                metadata_json=json.dumps({"name": supplier.name, "phone": supplier.phone}),
            )
        )
        await self.db.commit()
        return await self.repo.get_supplier_detail(clinic_id, supplier)

    async def update_supplier(
        self, clinic_id: UUID, supplier_id: UUID, payload: SupplierUpdate, actor: User
    ) -> SupplierDetail:
        supplier = await self.repo.get_supplier(clinic_id, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")
        updated = await self.repo.update_supplier(supplier, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="SUPPLIER",
                entity_id=str(supplier.id),
                metadata_json=json.dumps({"name": updated.name}),
            )
        )
        await self.db.commit()
        return await self.repo.get_supplier_detail(clinic_id, updated)

    async def get_supplier_detail(self, clinic_id: UUID, supplier_id: UUID) -> SupplierDetail:
        supplier = await self.repo.get_supplier(clinic_id, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")
        return await self.repo.get_supplier_detail(clinic_id, supplier)

    async def list_suppliers(
        self,
        clinic_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[SupplierRead], int]:
        suppliers, total = await self.repo.list_suppliers(
            clinic_id, is_active=is_active, search=search, skip=skip, limit=limit
        )
        return [SupplierRead.model_validate(s) for s in suppliers], total

    # ==========================================
    # Inventory Items Business Logic
    # ==========================================
    async def create_item(
        self, clinic_id: UUID, payload: InventoryItemCreate, actor: User
    ) -> InventoryItemRead:
        if payload.sku:
            existing = await self.repo.get_item_by_sku(clinic_id, payload.sku)
            if existing:
                raise HTTPException(status_code=400, detail=f"SKU '{payload.sku}' already exists.")

        if payload.supplier_id:
            supplier = await self.repo.get_supplier(clinic_id, payload.supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Selected supplier does not exist.")

        item = await self.repo.create_item(clinic_id, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="CREATE",
                entity_type="INVENTORY_ITEM",
                entity_id=str(item.id),
                metadata_json=json.dumps({
                    "sku": item.sku,
                    "name": item.name,
                    "quantity": item.current_quantity,
                }),
            )
        )
        await self.db.commit()
        return InventoryItemRead.model_validate(item)

    async def update_item(
        self, clinic_id: UUID, item_id: UUID, payload: InventoryItemUpdate, actor: User
    ) -> InventoryItemRead:
        item = await self.repo.get_item(clinic_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")

        if payload.supplier_id:
            supplier = await self.repo.get_supplier(clinic_id, payload.supplier_id)
            if not supplier:
                raise HTTPException(status_code=404, detail="Selected supplier does not exist.")

        updated = await self.repo.update_item(item, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="INVENTORY_ITEM",
                entity_id=str(item.id),
                metadata_json=json.dumps({"sku": updated.sku, "name": updated.name}),
            )
        )
        await self.db.commit()
        return InventoryItemRead.model_validate(updated)

    async def delete_item(self, clinic_id: UUID, item_id: UUID, actor: User) -> None:
        item = await self.repo.get_item(clinic_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")
        await self.repo.delete_item(item, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="DELETE",
                entity_type="INVENTORY_ITEM",
                entity_id=str(item.id),
                metadata_json=json.dumps({"sku": item.sku, "name": item.name}),
            )
        )
        await self.db.commit()

    async def get_item_detail(self, clinic_id: UUID, item_id: UUID) -> InventoryItemDetail:
        item = await self.repo.get_item(clinic_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")

        if not item.supplier and item.supplier_id:
            item.supplier = await self.repo.get_supplier(clinic_id, item.supplier_id)
        supplier_read = SupplierRead.model_validate(item.supplier) if item.supplier else None
        active_batches = [
            InventoryBatchRead.model_validate(b)
            for b in (item.batches or [])
            if b.deleted_at is None
        ]
        txs = await self.repo.list_transactions(clinic_id, item_id=item_id, limit=20)
        recent_txs = [
            StockTransactionRead(
                id=t.id,
                clinic_id=t.clinic_id,
                item_id=t.item_id,
                item_name=item.name,
                item_sku=item.sku,
                batch_id=t.batch_id,
                batch_number=t.batch.batch_number if t.batch else None,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                previous_quantity=t.previous_quantity,
                new_quantity=t.new_quantity,
                unit_cost=float(t.unit_cost),
                total_cost=float(t.total_cost),
                reason=t.reason,
                related_treatment_id=t.related_treatment_id,
                related_invoice_id=t.related_invoice_id,
                related_po_id=t.related_po_id,
                actor_id=t.actor_id,
                actor_name=f"{t.actor.first_name} {t.actor.last_name}" if t.actor else None,
                notes=t.notes,
                created_at=t.created_at,
            )
            for t in txs
        ]

        item_dict = InventoryItemRead.model_validate(item).model_dump()
        return InventoryItemDetail(
            **item_dict,
            supplier=supplier_read,
            batches=active_batches,
            recent_transactions=recent_txs,
        )

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
    ) -> tuple[list[InventoryItemRead], int]:
        items, total = await self.repo.list_items(
            clinic_id,
            category=category,
            status=status,
            search=search,
            low_stock=low_stock,
            expiring_days=expiring_days,
            skip=skip,
            limit=limit,
        )
        return [InventoryItemRead.model_validate(i) for i in items], total

    # ==========================================
    # Stock Adjustments Business Logic
    # ==========================================
    async def adjust_stock(
        self, clinic_id: UUID, item_id: UUID, payload: StockAdjustmentCreate, actor: User
    ) -> StockTransactionRead:
        item = await self.repo.get_item(clinic_id, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found.")

        # Non-Negative Stock Rule
        if payload.quantity < 0 and (item.current_quantity + payload.quantity) < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reduce stock below zero. Current quantity is {item.current_quantity}, attempted reduction is {abs(payload.quantity)}.",
            )

        tx = await self.repo.record_adjustment(clinic_id, item, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="STOCK_ADJUSTED",
                entity_type="INVENTORY_ITEM",
                entity_id=str(item.id),
                metadata_json=json.dumps({
                    "delta": payload.quantity,
                    "previous_quantity": tx.previous_quantity,
                    "new_quantity": tx.new_quantity,
                    "reason": payload.reason,
                    "type": payload.adjustment_type.value,
                }),
            )
        )
        await self.db.commit()

        return StockTransactionRead(
            id=tx.id,
            clinic_id=tx.clinic_id,
            item_id=tx.item_id,
            item_name=item.name,
            item_sku=item.sku,
            batch_id=tx.batch_id,
            transaction_type=tx.transaction_type,
            quantity=tx.quantity,
            previous_quantity=tx.previous_quantity,
            new_quantity=tx.new_quantity,
            unit_cost=float(tx.unit_cost),
            total_cost=float(tx.total_cost),
            reason=tx.reason,
            actor_id=tx.actor_id,
            actor_name=f"{actor.first_name} {actor.last_name}",
            notes=tx.notes,
            created_at=tx.created_at,
        )

    # ==========================================
    # Purchase Order Business Logic
    # ==========================================
    async def create_purchase_order(
        self, clinic_id: UUID, payload: PurchaseOrderCreate, actor: User
    ) -> PurchaseOrderDetail:
        supplier = await self.repo.get_supplier(clinic_id, payload.supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found.")

        # Validate item existence
        for it in payload.items:
            item = await self.repo.get_item(clinic_id, it.item_id)
            if not item:
                raise HTTPException(status_code=404, detail=f"Item {it.item_id} not found.")

        po = await self.repo.create_purchase_order(clinic_id, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="PO_CREATED",
                entity_type="PURCHASE_ORDER",
                entity_id=str(po.id),
                metadata_json=json.dumps({
                    "po_number": po.po_number,
                    "supplier_id": str(supplier.id),
                    "grand_total": float(po.grand_total),
                }),
            )
        )
        await self.db.commit()
        full_po = await self.repo.get_purchase_order(clinic_id, po.id)
        return self._to_po_detail(full_po or po)

    async def update_purchase_order(
        self, clinic_id: UUID, po_id: UUID, payload: PurchaseOrderUpdate, actor: User
    ) -> PurchaseOrderDetail:
        po = await self.repo.get_purchase_order(clinic_id, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        if po.status in (PurchaseOrderStatus.RECEIVED.value, PurchaseOrderStatus.CANCELLED.value):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify purchase order in '{po.status}' state.",
            )

        updated = await self.repo.update_purchase_order(po, payload, actor.id)
        await self.db.commit()
        full_po = await self.repo.get_purchase_order(clinic_id, updated.id)
        return self._to_po_detail(full_po or updated)

    async def receive_purchase_order(
        self, clinic_id: UUID, po_id: UUID, payload: PurchaseOrderReceive, actor: User
    ) -> PurchaseOrderDetail:
        po = await self.repo.get_purchase_order(clinic_id, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        if po.status in (PurchaseOrderStatus.RECEIVED.value, PurchaseOrderStatus.CANCELLED.value):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot receive goods for purchase order in '{po.status}' state.",
            )

        received_po = await self.repo.receive_goods(po, payload, actor.id)
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="GOODS_RECEIVED",
                entity_type="PURCHASE_ORDER",
                entity_id=str(po.id),
                metadata_json=json.dumps({
                    "po_number": po.po_number,
                    "items_received_count": len(payload.items),
                    "new_status": received_po.status,
                }),
            )
        )
        await self.db.commit()
        full_po = await self.repo.get_purchase_order(clinic_id, received_po.id)
        return self._to_po_detail(full_po or received_po)

    async def cancel_purchase_order(
        self, clinic_id: UUID, po_id: UUID, actor: User
    ) -> PurchaseOrderDetail:
        po = await self.repo.get_purchase_order(clinic_id, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        if po.status in (PurchaseOrderStatus.RECEIVED.value, PurchaseOrderStatus.PARTIALLY_RECEIVED.value):
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel purchase order that has already received items.",
            )

        po.status = PurchaseOrderStatus.CANCELLED.value
        po.updated_by = actor.id
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="PO_CANCELLED",
                entity_type="PURCHASE_ORDER",
                entity_id=str(po.id),
                metadata_json=json.dumps({"po_number": po.po_number}),
            )
        )
        await self.db.commit()
        full_po = await self.repo.get_purchase_order(clinic_id, po.id)
        return self._to_po_detail(full_po or po)

    async def get_purchase_order_detail(
        self, clinic_id: UUID, po_id: UUID
    ) -> PurchaseOrderDetail:
        po = await self.repo.get_purchase_order(clinic_id, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found.")
        return self._to_po_detail(po)

    async def list_purchase_orders(
        self,
        clinic_id: UUID,
        status: str | None = None,
        supplier_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrderRead], int]:
        pos, total = await self.repo.list_purchase_orders(
            clinic_id, status=status, supplier_id=supplier_id, skip=skip, limit=limit
        )
        reads = []
        for p in pos:
            r = PurchaseOrderRead.model_validate(p)
            if p.supplier:
                r.supplier_name = p.supplier.name
            reads.append(r)
        return reads, total

    async def generate_po_pdf(self, clinic_id: UUID, po_id: UUID) -> bytes:
        po = await self.repo.get_purchase_order(clinic_id, po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found.")

        clinic_q = select(Clinic).where(Clinic.id == clinic_id)
        clinic = (await self.db.execute(clinic_q)).scalar_one_or_none()

        clinic_name = getattr(clinic, "name", "DentalCare Pro Clinic") if clinic else "DentalCare Pro Clinic"
        clinic_addr = getattr(clinic, "address", "Healthcare Plaza, Suite 400") if clinic else "Healthcare Plaza, Suite 400"
        clinic_phone = getattr(clinic, "phone", "+91 98765 43210") if clinic else "+91 98765 43210"
        clinic_email = getattr(clinic, "email", "procurement@dentalcarepro.in") if clinic else "procurement@dentalcarepro.in"

        return InventoryPDFService.generate_purchase_order_pdf(
            po=po,
            clinic_name=clinic_name,
            clinic_address=clinic_addr,
            clinic_phone=clinic_phone,
            clinic_email=clinic_email,
        )

    def _to_po_detail(self, po: PurchaseOrder) -> PurchaseOrderDetail:
        supplier_read = SupplierRead.model_validate(po.supplier) if po.supplier else None
        item_reads = []
        for i in po.items or []:
            ir = PurchaseOrderItemRead(
                id=i.id,
                po_id=i.po_id,
                item_id=i.item_id,
                item_name=i.item.name if i.item else "",
                item_sku=i.item.sku if i.item else "",
                quantity_ordered=i.quantity_ordered,
                quantity_received=i.quantity_received,
                unit_price=float(i.unit_price),
                tax_rate=float(i.tax_rate),
                tax_amount=float(i.tax_amount),
                total=float(i.total),
                notes=i.notes,
            )
            item_reads.append(ir)

        base_read = PurchaseOrderRead.model_validate(po)
        if po.supplier:
            base_read.supplier_name = po.supplier.name

        return PurchaseOrderDetail(
            **base_read.model_dump(),
            supplier=supplier_read,
            items=item_reads,
            notes=po.notes,
            terms=po.terms,
            approved_by=po.approved_by,
        )

    # ==========================================
    # Treatment Material Consumption Logic
    # ==========================================
    async def consume_treatment_materials(
        self,
        clinic_id: UUID,
        treatment_id: UUID,
        payload: TreatmentConsumptionRequest | None,
        actor: User,
    ) -> TreatmentConsumptionResponse:
        treatment_q = select(Treatment).where(
            Treatment.clinic_id == clinic_id,
            Treatment.id == treatment_id,
            Treatment.deleted_at.is_(None),
        ).options(selectinload(Treatment.procedures))
        treatment = (await self.db.execute(treatment_q)).scalar_one_or_none()
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        warnings: list[str] = []
        consumed_records: list[TreatmentConsumedItemRead] = []
        total_cost = 0.0

        # Case A: Explicit items provided in payload
        if payload and payload.items and len(payload.items) > 0:
            for c_item in payload.items:
                item = await self.repo.get_item(clinic_id, c_item.item_id)
                if not item:
                    warnings.append(f"Item {c_item.item_id} not found; skipped.")
                    continue

                req_qty = c_item.quantity
                avail_qty = item.current_quantity
                if avail_qty < req_qty:
                    warnings.append(
                        f"Insufficient stock for {item.name}: available {avail_qty}, requested {req_qty}. Consuming {max(0, avail_qty)}."
                    )
                    qty_to_take = max(0, avail_qty)
                else:
                    qty_to_take = req_qty

                if qty_to_take > 0:
                    txs = await self.repo.deduct_fifo(
                        clinic_id=clinic_id,
                        item=item,
                        quantity=qty_to_take,
                        transaction_type=StockTransactionType.CONSUMPTION.value,
                        reason=payload.notes or f"Clinical consumption for Treatment #{treatment.treatment_number}",
                        actor_id=actor.id,
                        treatment_id=treatment.id,
                    )
                    for t in txs:
                        consumed_records.append(
                            TreatmentConsumedItemRead(
                                transaction_id=t.id,
                                item_id=item.id,
                                item_name=item.name,
                                item_sku=item.sku,
                                quantity=abs(t.quantity),
                                unit=item.unit,
                                unit_cost=float(t.unit_cost),
                                total_cost=float(t.total_cost),
                                created_at=t.created_at,
                            )
                        )
                        total_cost += float(t.total_cost)

        # Case B: Auto-detect from treatment procedures using recipes
        else:
            for proc in treatment.procedures or []:
                proc_name = proc.procedure_name.lower()
                matched_recipe: list[dict] | None = None
                for recipe_key, recipe_items in DEFAULT_PROCEDURE_RECIPES.items():
                    if recipe_key in proc_name:
                        matched_recipe = recipe_items
                        break

                if not matched_recipe:
                    # Check custom procedure templates from database
                    db_templates = await self.repo.get_templates_for_procedure(clinic_id, proc.procedure_name)
                    if db_templates:
                        matched_recipe = [
                            {"name": t.default_item_name, "quantity": t.quantity, "item_id": t.item_id}
                            for t in db_templates
                        ]

                if matched_recipe:
                    for r_item in matched_recipe:
                        target_item: InventoryItem | None = None
                        if r_item.get("item_id"):
                            target_item = await self.repo.get_item(clinic_id, r_item["item_id"])
                        if not target_item:
                            # Search by name match in clinic inventory
                            srch_q = select(InventoryItem).where(
                                InventoryItem.clinic_id == clinic_id,
                                InventoryItem.deleted_at.is_(None),
                                InventoryItem.name.ilike(f"%{r_item['name'].split()[0]}%"),
                            ).limit(1)
                            target_item = (await self.db.execute(srch_q)).scalar_one_or_none()

                        if not target_item:
                            continue

                        req_qty = r_item.get("quantity", 1) * (proc.quantity or 1)
                        avail_qty = target_item.current_quantity
                        if avail_qty < req_qty:
                            warnings.append(
                                f"Insufficient stock for {target_item.name}: available {avail_qty}, needed {req_qty}. Consumed {max(0, avail_qty)}."
                            )
                            qty_to_take = max(0, avail_qty)
                        else:
                            qty_to_take = req_qty

                        if qty_to_take > 0:
                            txs = await self.repo.deduct_fifo(
                                clinic_id=clinic_id,
                                item=target_item,
                                quantity=qty_to_take,
                                transaction_type=StockTransactionType.CONSUMPTION.value,
                                reason=f"Procedure: {proc.procedure_name} (Treatment #{treatment.treatment_number})",
                                actor_id=actor.id,
                                treatment_id=treatment.id,
                            )
                            for t in txs:
                                consumed_records.append(
                                    TreatmentConsumedItemRead(
                                        transaction_id=t.id,
                                        item_id=target_item.id,
                                        item_name=target_item.name,
                                        item_sku=target_item.sku,
                                        quantity=abs(t.quantity),
                                        unit=target_item.unit,
                                        unit_cost=float(t.unit_cost),
                                        total_cost=float(t.total_cost),
                                        created_at=t.created_at,
                                    )
                                )
                                total_cost += float(t.total_cost)

        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="MATERIALS_CONSUMED",
                entity_type="TREATMENT",
                entity_id=str(treatment.id),
                metadata_json=json.dumps({
                    "treatment_number": treatment.treatment_number,
                    "total_cost": round(total_cost, 2),
                    "items_count": len(consumed_records),
                    "warnings_count": len(warnings),
                }),
            )
        )
        await self.db.commit()

        return TreatmentConsumptionResponse(
            treatment_id=treatment.id,
            treatment_number=treatment.treatment_number,
            consumed_items=consumed_records,
            total_material_cost=round(total_cost, 2),
            warnings=warnings,
        )

    async def get_treatment_consumed_materials(
        self, clinic_id: UUID, treatment_id: UUID
    ) -> TreatmentConsumptionResponse:
        treatment_q = select(Treatment).where(
            Treatment.clinic_id == clinic_id,
            Treatment.id == treatment_id,
            Treatment.deleted_at.is_(None),
        )
        treatment = (await self.db.execute(treatment_q)).scalar_one_or_none()
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment record not found.")

        txs = await self.repo.list_transactions(clinic_id, treatment_id=treatment_id, limit=200)
        consumed_records = []
        total_cost = 0.0

        for t in txs:
            item = t.item or await self.repo.get_item(clinic_id, t.item_id)
            if item:
                consumed_records.append(
                    TreatmentConsumedItemRead(
                        transaction_id=t.id,
                        item_id=t.item_id,
                        item_name=item.name,
                        item_sku=item.sku,
                        quantity=abs(t.quantity),
                        unit=item.unit,
                        unit_cost=float(t.unit_cost),
                        total_cost=float(t.total_cost),
                        created_at=t.created_at,
                    )
                )
                total_cost += float(t.total_cost)

        return TreatmentConsumptionResponse(
            treatment_id=treatment.id,
            treatment_number=treatment.treatment_number,
            consumed_items=consumed_records,
            total_material_cost=round(total_cost, 2),
            warnings=[],
        )

    # ==========================================
    # Prescription Medicine Availability Logic
    # ==========================================
    async def check_medicine_availability(
        self, clinic_id: UUID, terms: list[str]
    ) -> list[MedicineAvailabilityCheck]:
        return await self.repo.check_medicine_availability(clinic_id, terms)

    # ==========================================
    # Reports & Dashboards
    # ==========================================
    async def get_dashboard_stats(self, clinic_id: UUID) -> InventoryDashboardStats:
        return await self.repo.get_dashboard_stats(clinic_id)

    async def get_alerts(self, clinic_id: UUID) -> StockAlertSummary:
        return await self.repo.get_alerts(clinic_id)

    async def get_valuation_report(self, clinic_id: UUID) -> StockValuationReport:
        return await self.repo.get_valuation_report(clinic_id)

    async def get_consumption_report(
        self, clinic_id: UUID, start_date: dt_date | None = None, end_date: dt_date | None = None
    ) -> list[ConsumptionReportItem]:
        return await self.repo.get_consumption_report(clinic_id, start_date=start_date, end_date=end_date)
