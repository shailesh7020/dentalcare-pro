"""Create enterprise multi-branch tables, organization hierarchy, permissions, and cross-branch transfers.

Revision ID: 20260908_0013
Revises: 20260908_0012
Create Date: 2026-09-08 23:50:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0013"
down_revision = "20260908_0012"
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
    # 1. organizations
    op.create_table(
        "organizations",
        *audit_columns(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(80), unique=True, index=True, nullable=False),
        sa.Column("code", sa.String(40), unique=True, index=True, nullable=False),
        sa.Column("tax_id", sa.String(80), nullable=True),
        sa.Column("legal_name", sa.String(200), nullable=True),
        sa.Column("subscription_tier", sa.String(40), server_default="ENTERPRISE", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("logo_url", sa.String(255), nullable=True),
        sa.Column("theme_color", sa.String(40), server_default="#0d9488", nullable=False),
        sa.Column("primary_email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("patient_sharing_mode", sa.String(40), server_default="SHARED", nullable=False),
        sa.Column("settings_json", sa.Text(), nullable=True),
    )

    # 2. regions
    op.create_table(
        "regions",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("regional_manager_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_regions_org_id", "regions", ["organization_id"])

    # 3. Alter clinics to add enterprise branch columns
    op.add_column("clinics", sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.add_column("clinics", sa.Column("region_id", sa.Uuid(), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True))
    op.add_column("clinics", sa.Column("branch_code", sa.String(40), nullable=True))
    op.add_column("clinics", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("clinics", sa.Column("working_hours", sa.Text(), nullable=True))
    op.add_column("clinics", sa.Column("currency", sa.String(10), server_default="INR", nullable=False))
    op.add_column("clinics", sa.Column("tax_configuration", sa.Text(), nullable=True))
    op.add_column("clinics", sa.Column("is_main_branch", sa.Boolean(), server_default="false", nullable=False))
    op.create_index("ix_clinics_organization_id", "clinics", ["organization_id"])
    op.create_index("ix_clinics_region_id", "clinics", ["region_id"])

    # 4. Alter users to add organization_id
    op.add_column("users", sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    # 5. departments
    op.create_table(
        "departments",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("head_dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_departments_clinic_id", "departments", ["clinic_id"])

    # 6. enterprise_roles
    op.create_table(
        "enterprise_roles",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role_key", sa.String(60), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_enterprise_roles_org_key", "enterprise_roles", ["organization_id", "role_key"])

    # 7. enterprise_permissions
    op.create_table(
        "enterprise_permissions",
        *audit_columns(),
        sa.Column("permission_key", sa.String(80), unique=True, index=True, nullable=False),
        sa.Column("module", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # 8. role_permission_mappings
    op.create_table(
        "role_permission_mappings",
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("enterprise_roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Uuid(), sa.ForeignKey("enterprise_permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    # 9. user_branch_assignments
    op.create_table(
        "user_branch_assignments",
        *audit_columns(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_override", sa.String(60), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("working_days_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_user_branch_user_clinic", "user_branch_assignments", ["user_id", "clinic_id"])

    # 10. user_permission_overrides
    op.create_table(
        "user_permission_overrides",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Uuid(), sa.ForeignKey("enterprise_permissions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_granted", sa.Boolean(), nullable=False),
    )

    # 11. patient_transfers
    op.create_table(
        "patient_transfers",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiated_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(40), server_default="PENDING", nullable=False),
        sa.Column("transfer_reason", sa.Text(), nullable=False),
        sa.Column("records_included_json", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_patient_transfers_org", "patient_transfers", ["organization_id"])
    op.create_index("ix_patient_transfers_patient", "patient_transfers", ["patient_id"])

    # 12. patient_merge_records
    op.create_table(
        "patient_merge_records",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("primary_patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duplicate_patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merged_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("merge_reason", sa.Text(), nullable=True),
        sa.Column("merged_data_snapshot_json", sa.Text(), nullable=True),
    )

    # 13. inventory_transfers
    op.create_table(
        "inventory_transfers",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transfer_number", sa.String(60), unique=True, index=True, nullable=False),
        sa.Column("from_clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Uuid(), sa.ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatched_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_inventory_transfers_org", "inventory_transfers", ["organization_id"])

    # 14. enterprise_announcements
    op.create_table(
        "enterprise_announcements",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("announcement_type", sa.String(40), server_default="BROADCAST", nullable=False),
        sa.Column("target_scope", sa.String(40), server_default="ALL", nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_enterprise_announcements_org", "enterprise_announcements", ["organization_id"])

    # 15. enterprise_audit_logs
    op.create_table(
        "enterprise_audit_logs",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
    )
    op.create_index("ix_ent_audit_org_id", "enterprise_audit_logs", ["organization_id"])


def downgrade() -> None:
    op.drop_table("enterprise_audit_logs")
    op.drop_table("enterprise_announcements")
    op.drop_table("inventory_transfers")
    op.drop_table("patient_merge_records")
    op.drop_table("patient_transfers")
    op.drop_table("user_permission_overrides")
    op.drop_table("user_branch_assignments")
    op.drop_table("role_permission_mappings")
    op.drop_table("enterprise_permissions")
    op.drop_table("enterprise_roles")
    op.drop_table("departments")
    op.drop_column("users", "organization_id")
    op.drop_column("clinics", "is_main_branch")
    op.drop_column("clinics", "tax_configuration")
    op.drop_column("clinics", "currency")
    op.drop_column("clinics", "working_hours")
    op.drop_column("clinics", "address")
    op.drop_column("clinics", "branch_code")
    op.drop_column("clinics", "region_id")
    op.drop_column("clinics", "organization_id")
    op.drop_table("regions")
    op.drop_table("organizations")
