from __future__ import annotations

from datetime import date as dt_date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory import (
    BatchStatus,
    InventoryCategory,
    PurchaseOrderStatus,
    StockTransactionType,
)


# ==========================================
# 1. Supplier Schemas
# ==========================================
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    contact_person: str | None = Field(None, max_length=160)
    phone: str | None = Field(None, max_length=40)
    email: str | None = Field(None, max_length=120)
    gst_number: str | None = Field(None, max_length=30)
    address: str | None = None
    payment_terms: str | None = Field("Net 30", max_length=100)
    is_active: bool = True
    rating: float = Field(5.00, ge=1.0, le=5.0)
    notes: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=160)
    contact_person: str | None = Field(None, max_length=160)
    phone: str | None = Field(None, max_length=40)
    email: str | None = Field(None, max_length=120)
    gst_number: str | None = Field(None, max_length=30)
    address: str | None = None
    payment_terms: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    rating: float | None = Field(None, ge=1.0, le=5.0)
    notes: str | None = None


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    created_at: datetime
    updated_at: datetime


class SupplierDetail(SupplierRead):
    item_count: int = 0
    active_po_count: int = 0


# ==========================================
# 2. Inventory Batch Schemas
# ==========================================
class InventoryBatchBase(BaseModel):
    batch_number: str = Field(..., min_length=1, max_length=64)
    expiry_date: dt_date
    quantity: int = Field(0, ge=0)
    purchase_price: float = Field(0.00, ge=0)
    received_date: dt_date
    supplier_id: UUID | None = None
    status: BatchStatus = BatchStatus.ACTIVE
    notes: str | None = None


class InventoryBatchCreate(InventoryBatchBase):
    pass


class InventoryBatchRead(InventoryBatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    item_id: UUID
    initial_quantity: int
    purchase_order_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 3. Inventory Item Schemas
# ==========================================
class InventoryItemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=180)
    sku: str | None = Field(None, max_length=64)
    barcode: str | None = Field(None, max_length=64)
    generic_name: str | None = Field(None, max_length=180)
    brand: str | None = Field(None, max_length=120)
    category: InventoryCategory = InventoryCategory.CONSUMABLES
    manufacturer: str | None = Field(None, max_length=120)
    supplier_id: UUID | None = None
    unit: str = Field("PCS", max_length=40)
    minimum_stock: int = Field(5, ge=0)
    maximum_stock: int = Field(100, ge=1)
    reorder_level: int = Field(10, ge=0)
    purchase_price: float = Field(0.00, ge=0)
    selling_price: float = Field(0.00, ge=0)
    tax_rate: float = Field(0.00, ge=0, le=100)
    storage_location: str | None = Field(None, max_length=100)
    medicine_catalog_id: UUID | None = None
    notes: str | None = None


class InventoryItemCreate(InventoryItemBase):
    initial_quantity: int = Field(0, ge=0)
    initial_batch_number: str | None = Field(None, max_length=64)
    initial_expiry_date: dt_date | None = None


class InventoryItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=180)
    barcode: str | None = Field(None, max_length=64)
    generic_name: str | None = Field(None, max_length=180)
    brand: str | None = Field(None, max_length=120)
    category: InventoryCategory | None = None
    manufacturer: str | None = Field(None, max_length=120)
    supplier_id: UUID | None = None
    unit: str | None = Field(None, max_length=40)
    minimum_stock: int | None = Field(None, ge=0)
    maximum_stock: int | None = Field(None, ge=1)
    reorder_level: int | None = Field(None, ge=0)
    purchase_price: float | None = Field(None, ge=0)
    selling_price: float | None = Field(None, ge=0)
    tax_rate: float | None = Field(None, ge=0, le=100)
    storage_location: str | None = Field(None, max_length=100)
    medicine_catalog_id: UUID | None = None
    notes: str | None = None


class InventoryItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    sku: str
    barcode: str | None = None
    name: str
    generic_name: str | None = None
    brand: str | None = None
    category: str
    manufacturer: str | None = None
    supplier_id: UUID | None = None
    unit: str
    minimum_stock: int
    maximum_stock: int
    reorder_level: int
    current_quantity: int
    purchase_price: float
    selling_price: float
    tax_rate: float
    batch_number: str | None = None
    expiry_date: dt_date | None = None
    storage_location: str | None = None
    status: str
    medicine_catalog_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 4. Stock Transaction & Adjustment Schemas
# ==========================================
class StockAdjustmentCreate(BaseModel):
    adjustment_type: StockTransactionType = StockTransactionType.ADJUSTMENT
    quantity: int = Field(..., description="Quantity delta (positive to increase, negative to decrease)")
    batch_id: UUID | None = None
    batch_number: str | None = None
    expiry_date: dt_date | None = None
    reason: str = Field(..., min_length=3, max_length=255)
    unit_cost: float | None = Field(None, ge=0)
    notes: str | None = None


class StockTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    item_id: UUID
    item_name: str | None = None
    item_sku: str | None = None
    batch_id: UUID | None = None
    batch_number: str | None = None
    transaction_type: str
    quantity: int
    previous_quantity: int
    new_quantity: int
    unit_cost: float
    total_cost: float
    reason: str | None = None
    related_treatment_id: UUID | None = None
    related_invoice_id: UUID | None = None
    related_po_id: UUID | None = None
    actor_id: UUID | None = None
    actor_name: str | None = None
    notes: str | None = None
    created_at: datetime


class InventoryItemDetail(InventoryItemRead):
    supplier: SupplierRead | None = None
    batches: list[InventoryBatchRead] = []
    recent_transactions: list[StockTransactionRead] = []


# ==========================================
# 5. Purchase Order Schemas
# ==========================================
class PurchaseOrderItemCreate(BaseModel):
    item_id: UUID
    quantity_ordered: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(0.00, ge=0, le=100)
    notes: str | None = Field(None, max_length=255)


class PurchaseOrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    item_id: UUID
    item_name: str = ""
    item_sku: str = ""
    quantity_ordered: int
    quantity_received: int
    unit_price: float
    tax_rate: float
    tax_amount: float
    total: float
    notes: str | None = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID
    order_date: dt_date
    expected_delivery_date: dt_date | None = None
    discount_amount: float = Field(0.00, ge=0)
    notes: str | None = None
    terms: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    order_date: dt_date | None = None
    expected_delivery_date: dt_date | None = None
    discount_amount: float | None = Field(None, ge=0)
    notes: str | None = None
    terms: str | None = None
    status: PurchaseOrderStatus | None = None


class PurchaseOrderReceiveItem(BaseModel):
    po_item_id: UUID
    quantity_to_receive: int = Field(..., gt=0)
    batch_number: str = Field(..., min_length=1, max_length=64)
    expiry_date: dt_date
    purchase_price: float | None = Field(None, ge=0)


class PurchaseOrderReceive(BaseModel):
    items: list[PurchaseOrderReceiveItem] = Field(..., min_length=1)
    notes: str | None = None


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: UUID
    po_number: str
    supplier_id: UUID
    supplier_name: str = ""
    order_date: dt_date
    expected_delivery_date: dt_date | None = None
    status: str
    subtotal: float
    tax_amount: float
    discount_amount: float
    grand_total: float
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetail(PurchaseOrderRead):
    supplier: SupplierRead | None = None
    items: list[PurchaseOrderItemRead] = []
    notes: str | None = None
    terms: str | None = None
    approved_by: UUID | None = None


# ==========================================
# 6. Treatment Material Consumption Schemas
# ==========================================
class TreatmentMaterialConsumeItem(BaseModel):
    item_id: UUID
    quantity: int = Field(1, gt=0)
    notes: str | None = None


class TreatmentConsumptionRequest(BaseModel):
    items: list[TreatmentMaterialConsumeItem] | None = None
    notes: str | None = None


class TreatmentConsumedItemRead(BaseModel):
    transaction_id: UUID
    item_id: UUID
    item_name: str
    item_sku: str
    quantity: int
    unit: str
    unit_cost: float
    total_cost: float
    created_at: datetime


class TreatmentConsumptionResponse(BaseModel):
    treatment_id: UUID
    treatment_number: str
    consumed_items: list[TreatmentConsumedItemRead]
    total_material_cost: float
    warnings: list[str] = []


# ==========================================
# 7. Medicine Stock Availability Schemas
# ==========================================
class MedicineAvailabilityCheck(BaseModel):
    medicine_name: str
    generic_name: str | None = None
    form: str | None = None
    is_available: bool
    stock_status: str
    current_quantity: int
    earliest_expiry: dt_date | None = None
    unit: str | None = None


# ==========================================
# 8. Reports & Analytics Schemas
# ==========================================
class InventoryDashboardStats(BaseModel):
    total_items: int
    total_valuation: float
    low_stock_count: int
    out_of_stock_count: int
    near_expiry_count: int
    expired_count: int
    pending_po_count: int


class StockAlertItem(BaseModel):
    item_id: UUID
    name: str
    sku: str
    category: str
    current_quantity: int
    reorder_level: int
    alert_type: str
    expiry_date: dt_date | None = None
    days_until_expiry: int | None = None


class StockAlertSummary(BaseModel):
    low_stock_alerts: list[StockAlertItem]
    expiry_alerts: list[StockAlertItem]
    pending_orders_count: int


class StockValuationItem(BaseModel):
    category: str
    item_count: int
    total_quantity: int
    total_cost_value: float
    total_selling_value: float


class StockValuationReport(BaseModel):
    total_items: int
    total_inventory_value: float
    valuation_by_category: list[StockValuationItem]


class ConsumptionReportItem(BaseModel):
    item_id: UUID
    item_name: str
    sku: str
    category: str
    total_consumed_quantity: int
    total_cost: float
    procedure_names: list[str] = []
