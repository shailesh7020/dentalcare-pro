"""Create notifications, notification_templates, clinic_notification_settings, conversations, conversation_participants, messages, form_templates, patient_forms, and consent_records tables. Add patient_id to users."""

from alembic import op
import sqlalchemy as sa

revision = "20260908_0010"
down_revision = "20260908_0009"
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
    # 0. Alter users: add patient_id for patient portal accounts
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
        )
        batch_op.create_index("ix_users_patient_id", ["patient_id"])

    # 1. notifications table
    op.create_table(
        "notifications",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notification_type", sa.String(60), nullable=False),
        sa.Column("priority", sa.String(20), server_default="NORMAL", nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("delivery_channel", sa.String(20), server_default="IN_APP", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("data_json", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_clinic_id", "notifications", ["clinic_id"])
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_patient_id", "notifications", ["patient_id"])
    op.create_index("ix_notifications_status", "notifications", ["clinic_id", "status"])
    op.create_index("ix_notifications_type", "notifications", ["clinic_id", "notification_type"])

    # 2. notification_templates table
    op.create_table(
        "notification_templates",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("template_code", sa.String(80), nullable=False),
        sa.Column("channel", sa.String(20), server_default="EMAIL", nullable=False),
        sa.Column("subject_template", sa.String(255), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_notification_templates_clinic_id", "notification_templates", ["clinic_id"])
    op.create_index("ix_notification_templates_code", "notification_templates", ["template_code"])

    # 3. clinic_notification_settings table
    op.create_table(
        "clinic_notification_settings",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("enable_email", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("enable_sms", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("enable_whatsapp", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("reminder_intervals_hours", sa.String(100), server_default="168,72,24,2", nullable=False),
        sa.Column("sender_email", sa.String(120), nullable=True),
        sa.Column("sender_phone", sa.String(40), nullable=True),
    )
    op.create_index("ix_clinic_notification_settings_clinic_id", "clinic_notification_settings", ["clinic_id"])

    # 4. conversations table
    op.create_table(
        "conversations",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("conversation_type", sa.String(40), server_default="PATIENT_CLINIC", nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_conversations_clinic_id", "conversations", ["clinic_id"])
    op.create_index("ix_conversations_patient_id", "conversations", ["patient_id"])

    # 5. conversation_participants table
    op.create_table(
        "conversation_participants",
        *audit_columns(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=True),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_muted", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_conv_part_conversation_id", "conversation_participants", ["conversation_id"])
    op.create_index("ix_conv_part_user_id", "conversation_participants", ["user_id"])
    op.create_index("ix_conv_part_patient_id", "conversation_participants", ["patient_id"])

    # 6. messages table
    op.create_table(
        "messages",
        *audit_columns(),
        sa.Column("conversation_id", sa.Uuid(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sender_patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("attachments_json", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])

    # 7. form_templates table
    op.create_table(
        "form_templates",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("form_type", sa.String(50), server_default="CUSTOM", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("schema_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.create_index("ix_form_templates_clinic_id", "form_templates", ["clinic_id"])
    op.create_index("ix_form_templates_type", "form_templates", ["clinic_id", "form_type"])

    # 8. patient_forms table
    op.create_table(
        "patient_forms",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", sa.Uuid(), sa.ForeignKey("form_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_patient_forms_clinic_id", "patient_forms", ["clinic_id"])
    op.create_index("ix_patient_forms_patient_id", "patient_forms", ["patient_id"])
    op.create_index("ix_patient_forms_status", "patient_forms", ["clinic_id", "status"])

    # 9. consent_records table
    op.create_table(
        "consent_records",
        *audit_columns(),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_id", sa.Uuid(), sa.ForeignKey("treatments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("consent_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("patient_signature", sa.Text(), nullable=False),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("witness_name", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("expires_at", sa.Date(), nullable=True),
    )
    op.create_index("ix_consent_records_clinic_id", "consent_records", ["clinic_id"])
    op.create_index("ix_consent_records_patient_id", "consent_records", ["patient_id"])
    op.create_index("ix_consent_records_treatment_id", "consent_records", ["treatment_id"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("patient_forms")
    op.drop_table("form_templates")
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
    op.drop_table("clinic_notification_settings")
    op.drop_table("notification_templates")
    op.drop_table("notifications")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_patient_id")
        batch_op.drop_column("patient_id")
