from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDAuditMixin

if TYPE_CHECKING:
    from app.models.identity import Clinic, User
    from app.models.treatment import Treatment


class InventoryCategory(StrEnum):
    DENTAL_MATERIALS = "DENTAL_MATERIALS"
    INSTRUMENTS = "INSTRUMENTS"
    CONSUMABLES = "CONSUMABLES"
    MEDICINES = "MEDICINES"
    LABORATORY = "LABORATORY"
    SURGICAL = "SURGICAL"
    ORTHODONTIC = "ORTHODONTIC"
    ENDODONTIC = "ENDODONTIC"
    PROSTHODONTIC = "PROSTHODONTIC"
    IMPLANTS = "IMPLANTS"
    CLEANING = "CLEANING"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"


class InventoryStatus(StrEnum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    EXPIRED = "EXPIRED"
    DISCONTINUED = "DISCONTINUED"


class BatchStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEPLETED = "DEPLETED"
    EXPIRED = "EXPIRED"
    QUARANTINED = "QUARANTINED"


class PurchaseOrderStatus(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class StockTransactionType(StrEnum):
    PURCHASE = "PURCHASE"
    CONSUMPTION = "CONSUMPTION"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"
    RETURN = "RETURN"
    EXPIRED = "EXPIRED"
    DAMAGED = "DAMAGED"
    OPENING_BALANCE = "OPENING_BALANCE"


class Supplier(Base, UUIDAuditMixin):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("ix_suppliers_clinic_id", "clinic_id"),
        Index("ix_suppliers_clinic_name", "clinic_id", "name"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(120))
    gst_number: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(Text)
    payment_terms: Mapped[str | None] = mapped_column(String(100), default="Net 30")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=5.00, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped[Clinic] = relationship("Clinic")
    items: Mapped[list[InventoryItem]] = relationship("InventoryItem", back_populates="supplier")
    purchase_orders: Mapped[list[PurchaseOrder]] = relationship("PurchaseOrder", back_populates="supplier")


class InventoryItem(Base, UUIDAuditMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("clinic_id", "sku", name="uq_inventory_items_clinic_sku"),
        Index("ix_inventory_items_clinic_cat", "clinic_id", "category"),
        Index("ix_inventory_items_clinic_status", "clinic_id", "status"),
        Index("ix_inventory_items_clinic_name", "clinic_id", "name"),
        Index("ix_inventory_items_barcode", "clinic_id", "barcode"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    generic_name: Mapped[str | None] = mapped_column(String(180))
    brand: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(50), default=InventoryCategory.CONSUMABLES.value, nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    supplier_id: Mapped[UUID | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    unit: Mapped[str] = mapped_column(String(40), default="PCS", nullable=False)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    maximum_stock: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    selling_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    batch_number: Mapped[str | None] = mapped_column(String(64))
    expiry_date: Mapped[date | None] = mapped_column(Date)
    storage_location: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default=InventoryStatus.IN_STOCK.value, nullable=False)
    medicine_catalog_id: Mapped[UUID | None] = mapped_column(ForeignKey("medicine_catalog.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    clinic: Mapped[Clinic] = relationship("Clinic")
    supplier: Mapped[Supplier | None] = relationship("Supplier", back_populates="items")
    batches: Mapped[list[InventoryBatch]] = relationship(
        "InventoryBatch", back_populates="item", cascade="all, delete-orphan", order_by="InventoryBatch.expiry_date.asc()"
    )
    transactions: Mapped[list[StockTransaction]] = relationship(
        "StockTransaction", back_populates="item", cascade="all, delete-orphan", order_by="StockTransaction.created_at.desc()"
    )


class InventoryBatch(Base, UUIDAuditMixin):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        Index("ix_inventory_batches_clinic_item", "clinic_id", "item_id"),
        Index("ix_inventory_batches_expiry", "clinic_id", "expiry_date"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id", ondelete="CASCADE"), index=True, nullable=False)
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    initial_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[UUID | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    purchase_order_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=BatchStatus.ACTIVE.value, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="batches")
    supplier: Mapped[Supplier | None] = relationship("Supplier")


class PurchaseOrder(Base, UUIDAuditMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("clinic_id", "po_number", name="uq_purchase_orders_clinic_number"),
        Index("ix_po_clinic_supplier", "clinic_id", "supplier_id"),
        Index("ix_po_clinic_status", "clinic_id", "status"),
        Index("ix_po_clinic_date", "clinic_id", "order_date"),
    )

    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False)
    po_number: Mapped[str] = mapped_column(String(32), nullable=False)
    supplier_id: Mapped[UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default=PurchaseOrderStatus.DRAFT.value, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    grand_total: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    terms: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    clinic: Mapped[Clinic] = relationship("Clinic")
    supplier: Mapped[Supplier] = relationship("Supplier", back_populates="purchase_orders")
    approver: Mapped[User | None] = relationship("User", foreign_keys=[approved_by])
    items: Mapped[list[PurchaseOrderItem]] = relationship(
        "PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan", order_by="PurchaseOrderItem.created_at.asc()"
    )


class PurchaseOrderItem(Base, UUIDAuditMixin):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        Index("ix_po_items_po_id", "po_id"),
    )

    po_id: Mapped[UUID] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    purchase_order: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="items")
    item: Mapped[InventoryItem] = relationship("InventoryItem")


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    __table_args__ = (
        Index("ix_stock_tx_clinic_item", "clinic_id", "item_id"),
        Index("ix_stock_tx_clinic_date", "clinic_id", "created_at"),
        Index("ix_stock_tx_treatment", "related_treatment_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), index=True, nullable=False)
    item_id: Mapped[UUID] = mapped_column(ForeignKey("inventory_items.id", ondelete="CASCADE"), index=True, nullable=False)
    batch_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0.00, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    related_treatment_id: Mapped[UUID | None] = mapped_column(ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True)
    related_invoice_id: Mapped[UUID | None] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    related_po_id: Mapped[UUID | None] = mapped_column(ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="transactions")
    batch: Mapped[InventoryBatch | None] = relationship("InventoryBatch")
    treatment: Mapped[Treatment | None] = relationship("Treatment")
    actor: Mapped[User | None] = relationship("User", foreign_keys=[actor_id])


class ProcedureMaterialTemplate(Base, UUIDAuditMixin):
    __tablename__ = "procedure_material_templates"
    __table_args__ = (
        Index("ix_proc_mat_templates_clinic", "clinic_id", "procedure_name"),
    )

    clinic_id: Mapped[UUID | None] = mapped_column(ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True)
    procedure_name: Mapped[str] = mapped_column(String(160), nullable=False)
    item_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=True)
    default_item_name: Mapped[str] = mapped_column(String(160), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="PCS", nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    item: Mapped[InventoryItem | None] = relationship("InventoryItem")
