"""Create suppliers, inventory_items, inventory_batches, purchase_orders, purchase_order_items, stock_transactions, and procedure_material_templates tables."""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0009"
down_revision = "20260908_0008"
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid()),
        sa.Column("updated_by", sa.Uuid()),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    ]


def upgrade() -> None:
    # 1. suppliers table
    op.create_table(
        "suppliers",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("contact_person", sa.String(160), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("gst_number", sa.String(30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("payment_terms", sa.String(100), server_default="Net 30", nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), server_default="5.00", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_suppliers_clinic_id", "suppliers", ["clinic_id"])
    op.create_index("ix_suppliers_clinic_name", "suppliers", ["clinic_id", "name"])

    # 2. inventory_items table
    op.create_table(
        "inventory_items",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("generic_name", sa.String(180), nullable=True),
        sa.Column("brand", sa.String(120), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("manufacturer", sa.String(120), nullable=True),
        sa.Column(
            "supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("unit", sa.String(40), server_default="PCS", nullable=False),
        sa.Column("minimum_stock", sa.Integer(), server_default="5", nullable=False),
        sa.Column("maximum_stock", sa.Integer(), server_default="100", nullable=False),
        sa.Column("reorder_level", sa.Integer(), server_default="10", nullable=False),
        sa.Column("current_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("purchase_price", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("selling_price", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0.00", nullable=False),
        sa.Column("batch_number", sa.String(64), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("storage_location", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), server_default="IN_STOCK", nullable=False),
        sa.Column(
            "medicine_catalog_id",
            sa.Uuid(),
            sa.ForeignKey("medicine_catalog.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("clinic_id", "sku", name="uq_inventory_items_clinic_sku"),
    )
    op.create_index("ix_inventory_items_clinic_cat", "inventory_items", ["clinic_id", "category"])
    op.create_index("ix_inventory_items_clinic_status", "inventory_items", ["clinic_id", "status"])
    op.create_index("ix_inventory_items_clinic_name", "inventory_items", ["clinic_id", "name"])
    op.create_index("ix_inventory_items_barcode", "inventory_items", ["clinic_id", "barcode"])

    # 3. inventory_batches table
    op.create_table(
        "inventory_batches",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "item_id", sa.Uuid(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("batch_number", sa.String(64), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("initial_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("purchase_price", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column(
            "supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("purchase_order_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_inventory_batches_clinic_item", "inventory_batches", ["clinic_id", "item_id"])
    op.create_index("ix_inventory_batches_expiry", "inventory_batches", ["clinic_id", "expiry_date"])

    # 4. purchase_orders table
    op.create_table(
        "purchase_orders",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("po_number", sa.String(32), nullable=False),
        sa.Column(
            "supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("grand_total", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column(
            "approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.UniqueConstraint("clinic_id", "po_number", name="uq_purchase_orders_clinic_number"),
    )
    op.create_index("ix_po_clinic_supplier", "purchase_orders", ["clinic_id", "supplier_id"])
    op.create_index("ix_po_clinic_status", "purchase_orders", ["clinic_id", "status"])
    op.create_index("ix_po_clinic_date", "purchase_orders", ["clinic_id", "order_date"])

    # 5. purchase_order_items table
    op.create_table(
        "purchase_order_items",
        *audit_columns(),
        sa.Column(
            "po_id", sa.Uuid(), sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "item_id", sa.Uuid(), sa.ForeignKey("inventory_items.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("quantity_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.String(255), nullable=True),
    )
    op.create_index("ix_po_items_po_id", "purchase_order_items", ["po_id"])

    # 6. stock_transactions table
    op.create_table(
        "stock_transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "item_id", sa.Uuid(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "batch_id", sa.Uuid(), sa.ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("transaction_type", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("previous_quantity", sa.Integer(), nullable=False),
        sa.Column("new_quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column(
            "related_treatment_id",
            sa.Uuid(),
            sa.ForeignKey("treatments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "related_invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "related_po_id",
            sa.Uuid(),
            sa.ForeignKey("purchase_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_stock_tx_clinic_item", "stock_transactions", ["clinic_id", "item_id"])
    op.create_index("ix_stock_tx_clinic_date", "stock_transactions", ["clinic_id", "created_at"])
    op.create_index("ix_stock_tx_treatment", "stock_transactions", ["related_treatment_id"])

    # 7. procedure_material_templates table
    op.create_table(
        "procedure_material_templates",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("procedure_name", sa.String(160), nullable=False),
        sa.Column(
            "item_id", sa.Uuid(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("default_item_name", sa.String(160), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("unit", sa.String(40), server_default="PCS", nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index(
        "ix_proc_mat_templates_clinic",
        "procedure_material_templates",
        ["clinic_id", "procedure_name"],
    )


def downgrade() -> None:
    op.drop_table("procedure_material_templates")
    op.drop_table("stock_transactions")
    op.drop_table("purchase_order_items")
    op.drop_table("purchase_orders")
    op.drop_table("inventory_batches")
    op.drop_table("inventory_items")
    op.drop_table("suppliers")
