"""Create teeth, tooth_surfaces, and tooth_history tables for Odontogram module."""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0006"
down_revision = "20260908_0005"
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
    # 1. teeth table
    op.create_table(
        "teeth",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("tooth_number", sa.String(10), nullable=False),
        sa.Column("universal_number", sa.String(10), nullable=False),
        sa.Column("palmer_notation", sa.String(10), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("dentition_type", sa.String(20), server_default="ADULT", nullable=False),
        sa.Column("arch", sa.String(20), nullable=False),
        sa.Column("quadrant", sa.Integer(), nullable=False),
        sa.Column("tooth_type", sa.String(30), nullable=False),
        sa.Column("primary_status", sa.String(40), server_default="HEALTHY", nullable=False),
        sa.Column("color", sa.String(30), server_default="#10B981", nullable=False),
        sa.Column("is_missing", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_extracted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_impacted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_root_canal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_crown", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_implant", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("has_bridge", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("mobility_grade", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.UniqueConstraint(
            "clinic_id", "patient_id", "tooth_number", name="uq_teeth_clinic_patient_tooth"
        ),
    )
    op.create_index("ix_teeth_clinic_patient", "teeth", ["clinic_id", "patient_id"])
    op.create_index("ix_teeth_patient_tooth", "teeth", ["patient_id", "tooth_number"])
    op.create_index("ix_teeth_clinic_status", "teeth", ["clinic_id", "primary_status"])

    # 2. tooth_surfaces table
    op.create_table(
        "tooth_surfaces",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "tooth_id", sa.Uuid(), sa.ForeignKey("teeth.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("surface", sa.String(20), nullable=False),
        sa.Column("condition", sa.String(60), server_default="HEALTHY", nullable=False),
        sa.Column("treatment", sa.String(60), server_default="NONE", nullable=False),
        sa.Column("color", sa.String(30), server_default="#10B981", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "last_modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.UniqueConstraint("tooth_id", "surface", name="uq_tooth_surfaces_tooth_surface"),
    )
    op.create_index("ix_tooth_surfaces_tooth_id", "tooth_surfaces", ["tooth_id"])
    op.create_index("ix_tooth_surfaces_clinic", "tooth_surfaces", ["clinic_id"])

    # 3. tooth_history table
    op.create_table(
        "tooth_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "tooth_id", sa.Uuid(), sa.ForeignKey("teeth.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("previous_state", sa.Text(), nullable=True),
        sa.Column("new_state", sa.Text(), nullable=True),
        sa.Column("affected_surfaces", sa.String(100), nullable=True),
        sa.Column(
            "treatment_id",
            sa.Uuid(),
            sa.ForeignKey("treatments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "treatment_procedure_id",
            sa.Uuid(),
            sa.ForeignKey("treatment_procedures.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "appointment_id",
            sa.Uuid(),
            sa.ForeignKey("appointments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_tooth_history_patient", "tooth_history", ["clinic_id", "patient_id"])
    op.create_index("ix_tooth_history_tooth", "tooth_history", ["clinic_id", "tooth_id"])
    op.create_index("ix_tooth_history_created_at", "tooth_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("tooth_history")
    op.drop_table("tooth_surfaces")
    op.drop_table("teeth")
