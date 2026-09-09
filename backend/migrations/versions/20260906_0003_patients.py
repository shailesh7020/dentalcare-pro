"""Create clinic-scoped patient management tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "20260906_0003"
down_revision = "20260902_0002"
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.Uuid()), sa.Column("updated_by", sa.Uuid()),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    ]


def upgrade() -> None:
    gender = pg.ENUM("FEMALE", "MALE", "NON_BINARY", "PREFER_NOT_TO_SAY", name="patient_gender", create_type=False)
    blood_group = pg.ENUM("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN", name="blood_group", create_type=False)
    gender.create(op.get_bind(), checkfirst=True); blood_group.create(op.get_bind(), checkfirst=True)
    op.create_table("patients", *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False), sa.Column("patient_number", sa.String(32), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False), sa.Column("middle_name", sa.String(80)), sa.Column("last_name", sa.String(80), nullable=False), sa.Column("gender", gender, nullable=False), sa.Column("date_of_birth", sa.Date(), nullable=False), sa.Column("blood_group", blood_group), sa.Column("marital_status", sa.String(40)), sa.Column("occupation", sa.String(100)), sa.Column("aadhaar_number", sa.String(12)), sa.Column("email", sa.String(255)), sa.Column("mobile_number", sa.String(15), nullable=False), sa.Column("alternate_mobile", sa.String(15)), sa.Column("address", sa.Text()), sa.Column("city", sa.String(80)), sa.Column("state", sa.String(80)), sa.Column("country", sa.String(80), nullable=False, server_default="India"), sa.Column("pin_code", sa.String(6)), sa.Column("emergency_contact_name", sa.String(160)), sa.Column("emergency_contact_number", sa.String(15)), sa.Column("emergency_contact_relation", sa.String(60)), sa.Column("insurance_provider", sa.String(160)), sa.Column("insurance_policy_number", sa.String(100)), sa.Column("preferred_language", sa.String(40), nullable=False, server_default="English"), sa.Column("photo_url", sa.String(500)), sa.Column("notes", sa.Text()),
        sa.UniqueConstraint("clinic_id", "patient_number", name="uq_patients_clinic_number"))
    op.create_index("ix_patients_clinic_id", "patients", ["clinic_id"]); op.create_index("ix_patients_clinic_active_name", "patients", ["clinic_id", "deleted_at", "last_name", "first_name"]); op.create_index("ix_patients_clinic_email", "patients", ["clinic_id", "email"]); op.create_index("ix_patients_clinic_aadhaar", "patients", ["clinic_id", "aadhaar_number"]); op.create_index("uq_patients_clinic_mobile_active", "patients", ["clinic_id", "mobile_number"], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))
    for name, columns in (("medical_histories", [sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("diabetes", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("hypertension", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("cardiac_disease", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("thyroid", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("asthma", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("epilepsy", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("pregnancy", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("allergies", sa.Text()), sa.Column("current_medications", sa.Text()), sa.Column("smoking", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("tobacco", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("alcohol", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("previous_surgeries", sa.Text()), sa.Column("infectious_diseases", sa.Text()), sa.Column("physician_name", sa.String(160)), sa.Column("physician_contact", sa.String(15)), sa.Column("additional_notes", sa.Text())]), ("dental_histories", [sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, unique=True), sa.Column("chief_complaint", sa.Text()), sa.Column("previous_dental_treatments", sa.Text()), sa.Column("brushing_frequency", sa.String(40)), sa.Column("flossing_habit", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("tobacco_habit", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("grinding", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("jaw_pain", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("tmj_disorder", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("sensitivity", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("bleeding_gums", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("last_dental_visit", sa.Date()), sa.Column("dental_notes", sa.Text())])):
        op.create_table(name, *audit_columns(), *columns)
        op.create_index(f"ix_{name}_patient_id", name, ["patient_id"])
    op.create_table("patient_timeline_events", *audit_columns(), sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False), sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("description", sa.Text()), sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")))
    op.create_index("ix_patient_timeline_patient_created", "patient_timeline_events", ["patient_id", "created_at"]); op.create_index("ix_patient_timeline_clinic_id", "patient_timeline_events", ["clinic_id"])
    op.create_table("patient_documents", *audit_columns(), sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False), sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id"), nullable=False), sa.Column("file_name", sa.String(255), nullable=False), sa.Column("content_type", sa.String(120), nullable=False), sa.Column("storage_key", sa.String(500), nullable=False, unique=True), sa.Column("document_type", sa.String(60), nullable=False, server_default="DOCUMENT"))
    op.create_index("ix_patient_documents_patient_id", "patient_documents", ["patient_id"]); op.create_index("ix_patient_documents_clinic_id", "patient_documents", ["clinic_id"])


def downgrade() -> None:
    for table in ("patient_documents", "patient_timeline_events", "dental_histories", "medical_histories", "patients"): op.drop_table(table)
    sa.Enum(name="blood_group").drop(op.get_bind(), checkfirst=True); sa.Enum(name="patient_gender").drop(op.get_bind(), checkfirst=True)
