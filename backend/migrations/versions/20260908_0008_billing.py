"""Create invoices, invoice_items, and payments tables."""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0008"
down_revision = "20260908_0007"
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
    # 1. invoices table
    op.create_table(
        "invoices",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "dentist_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("invoice_number", sa.String(32), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), server_default="UNPAID", nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("discount_type", sa.String(20), server_default="FIXED", nullable=False),
        sa.Column("discount_value", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("grand_total", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("balance_due", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("clinic_id", "invoice_number", name="uq_invoices_clinic_number"),
    )
    op.create_index("ix_invoices_clinic_patient", "invoices", ["clinic_id", "patient_id"])
    op.create_index("ix_invoices_clinic_date", "invoices", ["clinic_id", "date"])
    op.create_index("ix_invoices_clinic_status", "invoices", ["clinic_id", "status"])

    # 2. invoice_items table
    op.create_table(
        "invoice_items",
        *audit_columns(),
        sa.Column(
            "invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("item_type", sa.String(40), server_default="PROCEDURE", nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), server_default="0.00", nullable=False),
        sa.Column("tax_amount", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("total", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("procedure_id", sa.Uuid(), nullable=True),
    )
    op.create_index("ix_invoice_items_invoice_id", "invoice_items", ["invoice_id"])

    # 3. payments table
    op.create_table(
        "payments",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "invoice_id", sa.Uuid(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("receipt_number", sa.String(32), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("method", sa.String(30), server_default="CASH", nullable=False),
        sa.Column("transaction_reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("received_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(30), server_default="COMPLETED", nullable=False),
        sa.Column("refund_amount", sa.Numeric(12, 2), server_default="0.00", nullable=False),
        sa.Column("refund_reason", sa.Text(), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("clinic_id", "receipt_number", name="uq_payments_clinic_receipt"),
    )
    op.create_index("ix_payments_clinic_date", "payments", ["clinic_id", "payment_date"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
