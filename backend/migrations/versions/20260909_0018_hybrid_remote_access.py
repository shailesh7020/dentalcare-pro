"""Create tables for Phase 18: Hybrid Local + Secure Remote Access.

Revision ID: 20260909_0018
Revises: 20260909_0017
Create Date: 2026-09-09 16:30:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0018"
down_revision = "20260909_0017"
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
    # 1. clinic_remote_configs
    op.create_table(
        "clinic_remote_configs",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_remote_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "allowed_roles_json",
            sa.Text(),
            server_default='["SUPER_ADMIN", "CLINIC_ADMIN", "DENTIST", "RECEPTIONIST"]',
            nullable=False,
        ),
        sa.Column("require_2fa", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("session_timeout_minutes", sa.Integer(), server_default="480", nullable=False),
        sa.Column("tunnel_provider", sa.String(length=40), server_default="cloudflare", nullable=False),
        sa.Column("tunnel_hostname", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("clinic_id", name="uq_clinic_remote_config_clinic"),
    )
    op.create_index("ix_clinic_remote_configs_clinic_id", "clinic_remote_configs", ["clinic_id"])

    # 2. two_factor_secrets
    op.create_table(
        "two_factor_secrets",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("secret_base32", sa.String(length=64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("backup_codes_json", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", name="uq_two_factor_secret_user"),
    )
    op.create_index("ix_two_factor_secrets_user_id", "two_factor_secrets", ["user_id"])

    # 3. remote_sessions
    op.create_table(
        "remote_sessions",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_token_hash", sa.String(length=128), unique=True, nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=False),
        sa.Column("device_type", sa.String(length=30), server_default="MOBILE", nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_2fa_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_remote_sessions_user_id", "remote_sessions", ["user_id"])
    op.create_index("ix_remote_sessions_clinic_id", "remote_sessions", ["clinic_id"])
    op.create_index("ix_remote_sessions_token_hash", "remote_sessions", ["session_token_hash"])
    op.create_index("ix_remote_sessions_expires", "remote_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("remote_sessions")
    op.drop_table("two_factor_secrets")
    op.drop_table("clinic_remote_configs")
