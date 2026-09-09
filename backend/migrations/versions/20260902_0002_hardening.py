"""Harden identity constraints, audit metadata, and refresh-token rotation."""

import sqlalchemy as sa
from alembic import op

revision = "20260902_0002"
down_revision = "20260902_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("clinics", "users", "refresh_tokens", "audit_events"):
        op.add_column(table, sa.Column("created_by", sa.Uuid(), nullable=True))
        op.add_column(table, sa.Column("updated_by", sa.Uuid(), nullable=True))
        op.create_index(f"ix_{table}_created_by", table, ["created_by"])
        op.create_index(f"ix_{table}_updated_by", table, ["updated_by"])

    duplicate_email = op.get_bind().execute(
        sa.text("SELECT email FROM users WHERE deleted_at IS NULL GROUP BY email HAVING count(*) > 1 LIMIT 1")
    ).scalar()
    if duplicate_email:
        raise RuntimeError(
            "Cannot enforce globally unique user emails: resolve duplicate active email "
            f"'{duplicate_email}' before applying migration 20260902_0002."
        )
    op.drop_constraint("uq_users_clinic_email", "users", type_="unique")
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_check_constraint("ck_users_clinic_assignment", "users", "clinic_id IS NOT NULL OR role = 'SUPER_ADMIN'")

    op.add_column("refresh_tokens", sa.Column("family_id", sa.Uuid(), nullable=True))
    op.add_column("refresh_tokens", sa.Column("replaced_by_token_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE refresh_tokens SET family_id = id WHERE family_id IS NULL")
    op.alter_column("refresh_tokens", "family_id", nullable=False)
    op.create_foreign_key("fk_refresh_tokens_replaced_by", "refresh_tokens", "refresh_tokens", ["replaced_by_token_id"], ["id"])
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_audit_events_clinic_created_at", "audit_events", ["clinic_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_clinic_created_at", table_name="audit_events")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_constraint("fk_refresh_tokens_replaced_by", "refresh_tokens", type_="foreignkey")
    op.drop_column("refresh_tokens", "replaced_by_token_id")
    op.drop_column("refresh_tokens", "family_id")
    op.drop_constraint("ck_users_clinic_assignment", "users", type_="check")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.create_unique_constraint("uq_users_clinic_email", "users", ["clinic_id", "email"])
    for table in ("audit_events", "refresh_tokens", "users", "clinics"):
        op.drop_index(f"ix_{table}_updated_by", table_name=table)
        op.drop_index(f"ix_{table}_created_by", table_name=table)
        op.drop_column(table, "updated_by")
        op.drop_column(table, "created_by")
