from __future__ import annotations

from datetime import date as dt_date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import require_roles
from app.models.identity import Role, User
from app.schemas.inventory import (
    ConsumptionReportItem,
    InventoryDashboardStats,
    InventoryItemCreate,
    InventoryItemDetail,
    InventoryItemRead,
    InventoryItemUpdate,
    MedicineAvailabilityCheck,
    PurchaseOrderCreate,
    PurchaseOrderDetail,
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
    TreatmentConsumptionRequest,
    TreatmentConsumptionResponse,
)
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory & Procurement"])

INVENTORY_READ_ROLES = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
    Role.ASSISTANT,
]

INVENTORY_WRITE_ROLES = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
    Role.DENTIST,
    Role.RECEPTIONIST,
]

INVENTORY_ADMIN_ROLES = [
    Role.SUPER_ADMIN,
    Role.CLINIC_ADMIN,
]


def _get_clinic_id(actor: User) -> UUID:
    if actor.clinic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Clinic context required."
        )
    return actor.clinic_id


# ==========================================
# 1. Dashboard & Alerts
# ==========================================
@router.get(
    "/dashboard/stats",
    response_model=InventoryDashboardStats,
    summary="Inventory dashboard statistics",
)
async def get_dashboard_stats(
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> InventoryDashboardStats:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_dashboard_stats(clinic_id)


@router.get(
    "/alerts",
    response_model=StockAlertSummary,
    summary="Stock and expiry alerts summary",
)
async def get_alerts(
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> StockAlertSummary:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_alerts(clinic_id)


# ==========================================
# 2. Inventory Items
# ==========================================
@router.get(
    "/items",
    response_model=list[InventoryItemRead],
    summary="List inventory items",
)
async def list_items(
    category: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    low_stock: bool = False,
    expiring_days: int | None = None,
    skip: int = 0,
    limit: int = 50,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[InventoryItemRead]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    items, _ = await service.list_items(
        clinic_id=clinic_id,
        category=category,
        status=status_filter,
        search=search,
        low_stock=low_stock,
        expiring_days=expiring_days,
        skip=skip,
        limit=limit,
    )
    return items


@router.post(
    "/items",
    response_model=InventoryItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new inventory item",
)
async def create_item(
    payload: InventoryItemCreate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> InventoryItemRead:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.create_item(clinic_id, payload, actor)


@router.get(
    "/items/{item_id}",
    response_model=InventoryItemDetail,
    summary="Get inventory item details",
)
async def get_item(
    item_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> InventoryItemDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_item_detail(clinic_id, item_id)


@router.patch(
    "/items/{item_id}",
    response_model=InventoryItemRead,
    summary="Update inventory item",
)
async def update_item(
    item_id: UUID,
    payload: InventoryItemUpdate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> InventoryItemRead:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.update_item(clinic_id, item_id, payload, actor)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory item",
)
async def delete_item(
    item_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> None:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    await service.delete_item(clinic_id, item_id, actor)


@router.post(
    "/items/{item_id}/adjust",
    response_model=StockTransactionRead,
    summary="Adjust inventory stock balance",
)
async def adjust_stock(
    item_id: UUID,
    payload: StockAdjustmentCreate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> StockTransactionRead:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.adjust_stock(clinic_id, item_id, payload, actor)


# ==========================================
# 3. Suppliers
# ==========================================
@router.get(
    "/suppliers",
    response_model=list[SupplierRead],
    summary="List suppliers",
)
async def list_suppliers(
    is_active: bool | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[SupplierRead]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    suppliers, _ = await service.list_suppliers(
        clinic_id=clinic_id, is_active=is_active, search=search, skip=skip, limit=limit
    )
    return suppliers


@router.post(
    "/suppliers",
    response_model=SupplierDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create supplier",
)
async def create_supplier(
    payload: SupplierCreate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SupplierDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.create_supplier(clinic_id, payload, actor)


@router.get(
    "/suppliers/{supplier_id}",
    response_model=SupplierDetail,
    summary="Get supplier detail",
)
async def get_supplier(
    supplier_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SupplierDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_supplier_detail(clinic_id, supplier_id)


@router.patch(
    "/suppliers/{supplier_id}",
    response_model=SupplierDetail,
    summary="Update supplier",
)
async def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> SupplierDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.update_supplier(clinic_id, supplier_id, payload, actor)


# ==========================================
# 4. Purchase Orders & Goods Receipt
# ==========================================
@router.get(
    "/purchase-orders",
    response_model=list[PurchaseOrderRead],
    summary="List purchase orders",
)
async def list_purchase_orders(
    status_filter: str | None = None,
    supplier_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[PurchaseOrderRead]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    pos, _ = await service.list_purchase_orders(
        clinic_id=clinic_id,
        status=status_filter,
        supplier_id=supplier_id,
        skip=skip,
        limit=limit,
    )
    return pos


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create purchase order",
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.create_purchase_order(clinic_id, payload, actor)


@router.get(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderDetail,
    summary="Get purchase order detail",
)
async def get_purchase_order(
    po_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_purchase_order_detail(clinic_id, po_id)


@router.patch(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderDetail,
    summary="Update purchase order",
)
async def update_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderUpdate,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.update_purchase_order(clinic_id, po_id, payload, actor)


@router.get(
    "/purchase-orders/{po_id}/pdf",
    summary="Download purchase order PDF",
    response_class=Response,
)
async def get_purchase_order_pdf(
    po_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> Response:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    pdf_bytes = await service.generate_po_pdf(clinic_id, po_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="PO_{po_id}.pdf"'},
    )


@router.post(
    "/purchase-orders/{po_id}/receive",
    response_model=PurchaseOrderDetail,
    summary="Receive goods against purchase order",
)
async def receive_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderReceive,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.receive_purchase_order(clinic_id, po_id, payload, actor)


@router.post(
    "/purchase-orders/{po_id}/cancel",
    response_model=PurchaseOrderDetail,
    summary="Cancel purchase order",
)
async def cancel_purchase_order(
    po_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_ADMIN_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> PurchaseOrderDetail:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.cancel_purchase_order(clinic_id, po_id, actor)


# ==========================================
# 5. Treatment Material Consumption & History
# ==========================================
@router.post(
    "/treatments/{treatment_id}/consume",
    response_model=TreatmentConsumptionResponse,
    summary="Consume inventory materials for treatment",
)
async def consume_treatment_materials(
    treatment_id: UUID,
    payload: TreatmentConsumptionRequest | None = None,
    actor: User = Depends(require_roles(*INVENTORY_WRITE_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> TreatmentConsumptionResponse:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.consume_treatment_materials(clinic_id, treatment_id, payload, actor)


@router.get(
    "/treatments/{treatment_id}/consumption",
    response_model=TreatmentConsumptionResponse,
    summary="Get materials consumed for a treatment",
)
async def get_treatment_consumption(
    treatment_id: UUID,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> TreatmentConsumptionResponse:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_treatment_consumed_materials(clinic_id, treatment_id)


# ==========================================
# 6. Prescription Medicine Availability
# ==========================================
@router.get(
    "/medicines/availability",
    response_model=list[MedicineAvailabilityCheck],
    summary="Check real-time stock availability for medications",
)
async def check_medicine_availability(
    names: list[str] = Query(..., description="Medicine names or generic names to check"),
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[MedicineAvailabilityCheck]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.check_medicine_availability(clinic_id, names)


# ==========================================
# 7. Stock Transactions & Ledger
# ==========================================
@router.get(
    "/transactions",
    response_model=list[StockTransactionRead],
    summary="List stock movement transactions",
)
async def list_transactions(
    item_id: UUID | None = None,
    treatment_id: UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[StockTransactionRead]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    txs = await service.repo.list_transactions(
        clinic_id=clinic_id, item_id=item_id, treatment_id=treatment_id, skip=skip, limit=limit
    )
    return [
        StockTransactionRead(
            id=t.id,
            clinic_id=t.clinic_id,
            item_id=t.item_id,
            item_name=t.item.name if t.item else None,
            item_sku=t.item.sku if t.item else None,
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


# ==========================================
# 8. Reports
# ==========================================
@router.get(
    "/reports/valuation",
    response_model=StockValuationReport,
    summary="Inventory stock valuation report",
)
async def get_valuation_report(
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> StockValuationReport:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_valuation_report(clinic_id)


@router.get(
    "/reports/consumption",
    response_model=list[ConsumptionReportItem],
    summary="Inventory consumption report by procedure/item",
)
async def get_consumption_report(
    start_date: dt_date | None = None,
    end_date: dt_date | None = None,
    actor: User = Depends(require_roles(*INVENTORY_READ_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[ConsumptionReportItem]:
    clinic_id = _get_clinic_id(actor)
    service = InventoryService(db)
    return await service.get_consumption_report(clinic_id, start_date=start_date, end_date=end_date)
