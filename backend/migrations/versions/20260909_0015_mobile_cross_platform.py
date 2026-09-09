"""Create mobile devices, sync queues, digital signatures, and clinical media tables.

Revision ID: 20260909_0015
Revises: 20260909_0014
Create Date: 2026-09-09 00:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0015"
down_revision = "20260909_0014"
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
    # 1. mobile_devices
    op.create_table(
        "mobile_devices",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_token", sa.String(length=512), nullable=False),
        sa.Column("device_type", sa.String(length=32), nullable=False),
        sa.Column("device_name", sa.String(length=128), nullable=True),
        sa.Column("device_os_version", sa.String(length=64), nullable=True),
        sa.Column("app_version", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("biometric_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_mobile_devices_user_id", "mobile_devices", ["user_id"])
    op.create_index("ix_mobile_devices_device_token", "mobile_devices", ["device_token"])

    # 2. mobile_sync_queues
    op.create_table(
        "mobile_sync_queues",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Uuid(), sa.ForeignKey("mobile_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sync_type", sa.String(length=16), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("client_mutation_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="APPLIED", nullable=False),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_mobile_sync_queues_user_id", "mobile_sync_queues", ["user_id"])
    op.create_index("ix_mobile_sync_queues_client_mutation_id", "mobile_sync_queues", ["client_mutation_id"])

    # 3. mobile_digital_signatures
    op.create_table(
        "mobile_digital_signatures",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signer_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signature_type", sa.String(length=64), nullable=False),
        sa.Column("target_entity_type", sa.String(length=64), nullable=False),
        sa.Column("target_entity_id", sa.Uuid(), nullable=False),
        sa.Column("signature_image_url", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mobile_signatures_signer_id", "mobile_digital_signatures", ["signer_id"])
    op.create_index("ix_mobile_signatures_target_entity", "mobile_digital_signatures", ["target_entity_type", "target_entity_id"])

    # 4. mobile_clinical_media
    op.create_table(
        "mobile_clinical_media",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("captured_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("tooth_number", sa.Integer(), nullable=True),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("compression_ratio", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_mobile_media_patient_id", "mobile_clinical_media", ["patient_id"])
    op.create_index("ix_mobile_media_treatment_id", "mobile_clinical_media", ["treatment_id"])


def downgrade() -> None:
    op.drop_table("mobile_clinical_media")
    op.drop_table("mobile_digital_signatures")
    op.drop_table("mobile_sync_queues")
    op.drop_table("mobile_devices")
