"""Create Phase 1 clinic identity tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20260902_0001"
down_revision = None
branch_labels = None
depends_on = None


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    ]


def upgrade() -> None:
    role = pg.ENUM("SUPER_ADMIN", "CLINIC_ADMIN", "DENTIST", "RECEPTIONIST", "ASSISTANT", name="user_role", create_type=False)
    role.create(op.get_bind(), checkfirst=True)
    op.create_table("clinics", *audit_columns(), sa.Column("name", sa.String(160), nullable=False), sa.Column("slug", sa.String(80), nullable=False), sa.Column("email", sa.String(255), nullable=False), sa.Column("phone", sa.String(32)), sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Kolkata"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.UniqueConstraint("slug"))
    op.create_index("ix_clinics_slug", "clinics", ["slug"])
    op.create_table("users", *audit_columns(), sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id")), sa.Column("email", sa.String(255), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("first_name", sa.String(80), nullable=False), sa.Column("last_name", sa.String(80), nullable=False), sa.Column("role", role, nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("clinic_id", "email", name="uq_users_clinic_email"))
    op.create_index("ix_users_clinic_id", "users", ["clinic_id"]); op.create_index("ix_users_email", "users", ["email"])
    op.create_table("refresh_tokens", *audit_columns(), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_hash", sa.String(128), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("token_hash")); op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table("audit_events", *audit_columns(), sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id")), sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id")), sa.Column("action", sa.String(100), nullable=False), sa.Column("entity_type", sa.String(100), nullable=False), sa.Column("entity_id", sa.String(64)), sa.Column("metadata_json", sa.Text())); op.create_index("ix_audit_events_clinic_id", "audit_events", ["clinic_id"]); op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])


def downgrade() -> None:
    op.drop_table("audit_events"); op.drop_table("refresh_tokens"); op.drop_table("users"); op.drop_table("clinics"); sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
