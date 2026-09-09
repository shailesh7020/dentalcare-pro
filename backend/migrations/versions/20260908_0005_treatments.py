"""Create treatment, treatment procedure, and treatment follow-up tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "20260908_0005"
down_revision = "20260908_0004"
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
    # 1. Enums
    treatment_status = pg.ENUM(
        "PLANNED",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
        "ON_HOLD",
        name="treatment_status",
        create_type=False,
    )
    follow_up_status = pg.ENUM(
        "SCHEDULED",
        "COMPLETED",
        "CANCELLED",
        name="treatment_follow_up_status",
        create_type=False,
    )

    bind = op.get_bind()
    treatment_status.create(bind, checkfirst=True)
    follow_up_status.create(bind, checkfirst=True)

    # 2. treatments table
    op.create_table(
        "treatments",
        *audit_columns(),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "appointment_id",
            sa.Uuid(),
            sa.ForeignKey("appointments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("treatment_number", sa.String(32), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=False),
        sa.Column("chief_complaint", sa.Text()),
        sa.Column("clinical_findings", sa.Text()),
        sa.Column("treatment_plan", sa.Text()),
        sa.Column("procedure_performed", sa.Text()),
        sa.Column("local_anaesthesia_used", sa.String(255)),
        sa.Column("medicines_used", sa.Text()),
        sa.Column("clinical_notes", sa.Text()),
        sa.Column("soap_subjective", sa.Text()),
        sa.Column("soap_objective", sa.Text()),
        sa.Column("soap_assessment", sa.Text()),
        sa.Column("soap_plan", sa.Text()),
        sa.Column("follow_up_instructions", sa.Text()),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column(
            "status",
            treatment_status,
            server_default="IN_PROGRESS",
            nullable=False,
        ),
        sa.Column("is_override", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("clinic_id", "treatment_number", name="uq_treatments_clinic_number"),
    )
    op.create_index("ix_treatments_clinic_patient", "treatments", ["clinic_id", "patient_id"])
    op.create_index("ix_treatments_clinic_date", "treatments", ["clinic_id", "created_at"])
    op.create_index("ix_treatments_clinic_status", "treatments", ["clinic_id", "status"])
    op.create_index("ix_treatments_appointment_id", "treatments", ["appointment_id"])
    op.create_index("ix_treatments_dentist_id", "treatments", ["dentist_id"])

    # 3. treatment_procedures table
    op.create_table(
        "treatment_procedures",
        *audit_columns(),
        sa.Column(
            "treatment_id",
            sa.Uuid(),
            sa.ForeignKey("treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("procedure_name", sa.String(160), nullable=False),
        sa.Column("tooth_number", sa.String(20)),
        sa.Column("quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("cost", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("duration", sa.Integer(), server_default="30", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(40), server_default="COMPLETED", nullable=False),
    )
    op.create_index(
        "ix_treatment_procedures_treatment_id", "treatment_procedures", ["treatment_id"]
    )

    # 4. treatment_follow_ups table
    op.create_table(
        "treatment_follow_ups",
        *audit_columns(),
        sa.Column(
            "treatment_id",
            sa.Uuid(),
            sa.ForeignKey("treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("follow_up_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("instructions", sa.Text()),
        sa.Column(
            "status",
            follow_up_status,
            server_default="SCHEDULED",
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_treatment_follow_ups_treatment_id", "treatment_follow_ups", ["treatment_id"]
    )
    op.create_index(
        "ix_treatment_follow_ups_clinic_date",
        "treatment_follow_ups",
        ["clinic_id", "follow_up_date"],
    )


def downgrade() -> None:
    op.drop_table("treatment_follow_ups")
    op.drop_table("treatment_procedures")
    op.drop_table("treatments")

    bind = op.get_bind()
    sa.Enum(name="treatment_follow_up_status").drop(bind, checkfirst=True)
    sa.Enum(name="treatment_status").drop(bind, checkfirst=True)
