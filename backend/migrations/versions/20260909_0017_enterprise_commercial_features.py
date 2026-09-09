"""Create clinician signatures and backup records tables for Phase 17.

Revision ID: 20260909_0017
Revises: 20260909_0016
Create Date: 2026-09-09 14:15:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0017"
down_revision = "20260909_0016"
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
    # 1. clinician_signatures
    op.create_table(
        "clinician_signatures",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signature_data", sa.Text(), nullable=False),
        sa.Column("signature_type", sa.String(length=32), server_default="DRAWN", nullable=False),
        sa.Column("verification_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.create_index("ix_clinician_signatures_user_id", "clinician_signatures", ["user_id"], unique=True)
    op.create_index("ix_clinician_signatures_verification_hash", "clinician_signatures", ["verification_hash"])

    # 2. backup_records
    op.create_table(
        "backup_records",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_encrypted", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("destination_type", sa.String(length=32), server_default="LOCAL", nullable=False),
        sa.Column("backup_type", sa.String(length=32), server_default="MANUAL", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="COMPLETED", nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_backup_records_clinic_id", "backup_records", ["clinic_id"])


def downgrade() -> None:
    op.drop_index("ix_backup_records_clinic_id", table_name="backup_records", if_exists=True)
    op.drop_table("backup_records")
    op.drop_index("ix_clinician_signatures_verification_hash", table_name="clinician_signatures", if_exists=True)
    op.drop_index("ix_clinician_signatures_user_id", table_name="clinician_signatures", if_exists=True)
    op.drop_table("clinician_signatures")
