"""Create medicine_catalog, prescription_templates, prescriptions, and prescription_items tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260908_0007"
down_revision = "20260908_0006"
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
    # 1. medicine_catalog table
    op.create_table(
        "medicine_catalog",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("generic_name", sa.String(160), nullable=False),
        sa.Column("brand_name", sa.String(160), nullable=False),
        sa.Column("strength", sa.String(80), nullable=False),
        sa.Column("form", sa.String(50), server_default="TABLET", nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("standard_dosage", sa.String(120), nullable=True),
        sa.Column("default_route", sa.String(50), server_default="Oral", nullable=True),
        sa.Column("default_frequency", sa.String(30), server_default="BD", nullable=True),
        sa.Column("default_duration", sa.String(50), server_default="5 days", nullable=True),
        sa.Column("default_instructions", sa.String(255), server_default="After food", nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index(
        "ix_medicine_catalog_generic", "medicine_catalog", ["generic_name"]
    )
    op.create_index(
        "ix_medicine_catalog_brand", "medicine_catalog", ["brand_name"]
    )
    op.create_index(
        "ix_medicine_catalog_clinic", "medicine_catalog", ["clinic_id"]
    )

    # 2. prescription_templates table
    op.create_table(
        "prescription_templates",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("diagnosis_template", sa.Text(), nullable=True),
        sa.Column("instructions_template", sa.Text(), nullable=True),
        sa.Column("default_items", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index(
        "ix_prescription_templates_clinic", "prescription_templates", ["clinic_id"]
    )
    op.create_index(
        "ix_prescription_templates_category", "prescription_templates", ["category"]
    )

    # 3. prescriptions table
    op.create_table(
        "prescriptions",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("prescription_number", sa.String(32), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "superseded_by_id", sa.Uuid(), sa.ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True
        ),
        sa.UniqueConstraint("clinic_id", "prescription_number", name="uq_prescriptions_clinic_number"),
    )
    op.create_index(
        "ix_prescriptions_clinic_patient", "prescriptions", ["clinic_id", "patient_id"]
    )
    op.create_index(
        "ix_prescriptions_clinic_treatment", "prescriptions", ["clinic_id", "treatment_id"]
    )
    op.create_index(
        "ix_prescriptions_clinic_appointment", "prescriptions", ["clinic_id", "appointment_id"]
    )
    op.create_index(
        "ix_prescriptions_clinic_status", "prescriptions", ["clinic_id", "status"]
    )
    op.create_index(
        "ix_prescriptions_clinic_date", "prescriptions", ["clinic_id", "date"]
    )

    # 4. prescription_items table
    op.create_table(
        "prescription_items",
        *audit_columns(),
        sa.Column(
            "prescription_id", sa.Uuid(), sa.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("medicine_name", sa.String(160), nullable=False),
        sa.Column("generic_name", sa.String(160), nullable=True),
        sa.Column("brand_name", sa.String(160), nullable=True),
        sa.Column("strength", sa.String(80), nullable=False),
        sa.Column("form", sa.String(50), server_default="TABLET", nullable=False),
        sa.Column("dosage", sa.String(80), nullable=False),
        sa.Column("route", sa.String(50), server_default="Oral", nullable=False),
        sa.Column("frequency", sa.String(30), nullable=False),
        sa.Column("duration", sa.String(50), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="10", nullable=False),
        sa.Column("timing", sa.String(100), nullable=True),
        sa.Column("food_instructions", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_prescription_items_prescription_id", "prescription_items", ["prescription_id"]
    )


def downgrade() -> None:
    op.drop_table("prescription_items")
    op.drop_table("prescriptions")
    op.drop_table("prescription_templates")
    op.drop_table("medicine_catalog")
