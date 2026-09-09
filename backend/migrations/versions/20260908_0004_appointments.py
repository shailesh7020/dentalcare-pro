"""Create appointment, chair, dentist schedule, and appointment timeline tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20260908_0004"
down_revision = "20260906_0003"
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
    appointment_status = pg.ENUM(
        "SCHEDULED",
        "CONFIRMED",
        "CHECKED_IN",
        "IN_TREATMENT",
        "COMPLETED",
        "CANCELLED",
        "NO_SHOW",
        "RESCHEDULED",
        name="appointment_status",
        create_type=False,
    )
    visit_type = pg.ENUM(
        "CONSULTATION",
        "EMERGENCY",
        "FOLLOW_UP",
        "CLEANING",
        "ROOT_CANAL",
        "EXTRACTION",
        "CROWN",
        "IMPLANT",
        "SURGERY",
        "ORTHODONTICS",
        "PEDIATRIC",
        "OTHER",
        name="appointment_visit_type",
        create_type=False,
    )
    chair_status = pg.ENUM("ACTIVE", "MAINTENANCE", "INACTIVE", name="chair_status", create_type=False)

    appointment_status.create(op.get_bind(), checkfirst=True)
    visit_type.create(op.get_bind(), checkfirst=True)
    chair_status.create(op.get_bind(), checkfirst=True)

    # 2. Chairs table
    op.create_table(
        "chairs",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("room_number", sa.String(40)),
        sa.Column("status", chair_status, nullable=False, server_default="ACTIVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text()),
        sa.UniqueConstraint("clinic_id", "name", name="uq_chairs_clinic_name"),
    )
    op.create_index("ix_chairs_clinic_id", "chairs", ["clinic_id"])

    # 3. Dentist working hours
    op.create_table(
        "dentist_working_hours",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("dentist_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_start", sa.Time()),
        sa.Column("break_end", sa.Time()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint(
            "clinic_id", "dentist_id", "day_of_week", name="uq_dentist_working_hour"
        ),
    )
    op.create_index("ix_dentist_working_hours_clinic_id", "dentist_working_hours", ["clinic_id"])
    op.create_index("ix_dentist_working_hours_dentist_id", "dentist_working_hours", ["dentist_id"])

    # 4. Dentist blocked times / leaves
    op.create_table(
        "dentist_blocked_times",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("dentist_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("block_type", sa.String(60), nullable=False, server_default="LEAVE"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text()),
    )
    op.create_index("ix_dentist_blocked_clinic_id", "dentist_blocked_times", ["clinic_id"])
    op.create_index("ix_dentist_blocked_dentist_id", "dentist_blocked_times", ["dentist_id"])

    # 5. Appointments table
    op.create_table(
        "appointments",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("dentist_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("chair_id", sa.Uuid(), sa.ForeignKey("chairs.id"), nullable=False),
        sa.Column("appointment_number", sa.String(32), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("start_datetime", sa.DateTime(timezone=True)),
        sa.Column("end_datetime", sa.DateTime(timezone=True)),
        sa.Column("status", appointment_status, nullable=False, server_default="SCHEDULED"),
        sa.Column("visit_type", visit_type, nullable=False, server_default="CONSULTATION"),
        sa.Column("chief_complaint", sa.Text()),
        sa.Column("priority", sa.String(20), nullable=False, server_default="NORMAL"),
        sa.Column("notes", sa.Text()),
        sa.Column("cancellation_reason", sa.Text()),
        sa.Column("rescheduled_from_id", sa.Uuid(), sa.ForeignKey("appointments.id")),
        sa.Column(
            "is_emergency_override", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.UniqueConstraint("clinic_id", "appointment_number", name="uq_appointments_clinic_number"),
    )
    op.create_index("ix_appointments_clinic_id", "appointments", ["clinic_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_dentist_id", "appointments", ["dentist_id"])
    op.create_index("ix_appointments_chair_id", "appointments", ["chair_id"])
    op.create_index(
        "ix_appointments_clinic_dentist_date", "appointments", ["clinic_id", "dentist_id", "date"]
    )
    op.create_index(
        "ix_appointments_clinic_chair_date", "appointments", ["clinic_id", "chair_id", "date"]
    )
    op.create_index(
        "ix_appointments_clinic_patient_date", "appointments", ["clinic_id", "patient_id", "date"]
    )
    op.create_index(
        "ix_appointments_clinic_date_status", "appointments", ["clinic_id", "date", "status"]
    )

    # 6. Appointment Timeline Events
    op.create_table(
        "appointment_timeline_events",
        *audit_columns(),
        sa.Column(
            "appointment_id",
            sa.Uuid(),
            sa.ForeignKey("appointments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False),
        sa.Column("from_status", sa.String(40)),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")),
    )
    op.create_index(
        "ix_apt_timeline_appointment_created",
        "appointment_timeline_events",
        ["appointment_id", "created_at"],
    )
    op.create_index(
        "ix_apt_timeline_clinic_id", "appointment_timeline_events", ["clinic_id"]
    )


def downgrade() -> None:
    for table in (
        "appointment_timeline_events",
        "appointments",
        "dentist_blocked_times",
        "dentist_working_hours",
        "chairs",
    ):
        op.drop_table(table)
    sa.Enum(name="chair_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="appointment_visit_type").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="appointment_status").drop(op.get_bind(), checkfirst=True)
