"""Create ai_configurations, ai_prompt_templates, ai_audit_logs, and ai_recommendations tables.

Revision ID: 20260908_0011
Revises: 20260908_0010
Create Date: 2026-09-08 20:25:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "20260908_0011"
down_revision = "20260908_0010"
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
    # 1. ai_configurations
    op.create_table(
        "ai_configurations",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("provider_type", sa.String(40), server_default="MOCK", nullable=False),
        sa.Column("model_name", sa.String(120), server_default="mock-dental-llm", nullable=False),
        sa.Column("api_base_url", sa.String(255), nullable=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Float(), server_default="0.2", nullable=False),
        sa.Column("max_tokens", sa.Integer(), server_default="2048", nullable=False),
        sa.Column("clinical_guardrails_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_ai_configurations_clinic", "ai_configurations", ["clinic_id"])

    # 2. ai_prompt_templates
    op.create_table(
        "ai_prompt_templates",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("template_key", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt_template", sa.Text(), nullable=False),
        sa.Column("variables_schema", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_ai_prompt_templates_clinic", "ai_prompt_templates", ["clinic_id"])
    op.create_index("ix_ai_prompt_templates_key", "ai_prompt_templates", ["template_key"])

    # 3. ai_audit_logs
    op.create_table(
        "ai_audit_logs",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task_type", sa.String(60), nullable=False),
        sa.Column("provider_type", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("tokens_prompt", sa.Integer(), server_default="0", nullable=False),
        sa.Column("tokens_completion", sa.Integer(), server_default="0", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("anonymized_prompt_summary", sa.Text(), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("safety_flags", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("request_id", sa.String(80), nullable=False),
    )
    op.create_index("ix_ai_audit_logs_clinic", "ai_audit_logs", ["clinic_id"])
    op.create_index("ix_ai_audit_logs_task", "ai_audit_logs", ["task_type"])
    op.create_index("ix_ai_audit_logs_req", "ai_audit_logs", ["request_id"])

    # 4. ai_recommendations
    op.create_table(
        "ai_recommendations",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dentist_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appointment_id", sa.Uuid(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommendation_type", sa.String(60), nullable=False),
        sa.Column("input_context_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("generated_output_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("status", sa.String(40), server_default="PENDING_REVIEW", nullable=False),
        sa.Column("reviewed_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clinician_feedback", sa.Text(), nullable=True),
        sa.Column("final_content", sa.Text(), nullable=True),
    )
    op.create_index("ix_ai_recommendations_clinic", "ai_recommendations", ["clinic_id"])
    op.create_index("ix_ai_recommendations_patient", "ai_recommendations", ["patient_id"])
    op.create_index("ix_ai_recommendations_status", "ai_recommendations", ["status"])


def downgrade() -> None:
    op.drop_table("ai_recommendations")
    op.drop_table("ai_audit_logs")
    op.drop_table("ai_prompt_templates")
    op.drop_table("ai_configurations")
