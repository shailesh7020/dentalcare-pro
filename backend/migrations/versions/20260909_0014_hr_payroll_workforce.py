"""Create HR, payroll, attendance, leave, performance, training, recruitment, and document management tables.

Revision ID: 20260909_0014
Revises: 20260908_0013
Create Date: 2026-09-09 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260909_0014"
down_revision = "20260908_0013"
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
    # 1. employees
    op.create_table(
        "employees",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True),
        sa.Column("employee_code", sa.String(40), index=True, nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("email", sa.String(255), index=True, nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("gender", sa.String(20), server_default="OTHER", nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("profile_photo_url", sa.String(255), nullable=True),
        sa.Column("emergency_contact_name", sa.String(120), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("emergency_contact_relation", sa.String(60), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("qualification", sa.String(120), nullable=True),
        sa.Column("specialization", sa.String(120), nullable=True),
        sa.Column("license_number", sa.String(80), index=True, nullable=True),
        sa.Column("license_expiry_date", sa.Date(), nullable=True),
        sa.Column("department_id", sa.Uuid(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("designation", sa.String(100), nullable=False),
        sa.Column("employment_type", sa.String(40), server_default="FULL_TIME", nullable=False),
        sa.Column("reporting_manager_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(40), server_default="ACTIVE", nullable=False),
        sa.Column("base_salary", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("bank_name", sa.String(120), nullable=True),
        sa.Column("bank_account_number", sa.String(60), nullable=True),
        sa.Column("bank_ifsc_or_routing", sa.String(40), nullable=True),
        sa.Column("tax_id_number", sa.String(60), nullable=True),
    )
    op.create_index("ix_employees_org_clinic", "employees", ["organization_id", "clinic_id"])

    # 2. work_shifts
    op.create_table(
        "work_shifts",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("shift_type", sa.String(40), server_default="REGULAR", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )

    # 3. staff_schedules
    op.create_table(
        "staff_schedules",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shift_id", sa.Uuid(), sa.ForeignKey("work_shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chair_id", sa.Uuid(), sa.ForeignKey("chairs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("schedule_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_split_shift", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("split_start_time", sa.Time(), nullable=True),
        sa.Column("split_end_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(40), server_default="SCHEDULED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_staff_schedules_emp_date", "staff_schedules", ["employee_id", "schedule_date"])
    op.create_index("ix_staff_schedules_clinic_date", "staff_schedules", ["clinic_id", "schedule_date"])

    # 4. attendance_records
    op.create_table(
        "attendance_records",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("check_in_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entry_method", sa.String(40), server_default="MANUAL", nullable=False),
        sa.Column("status", sa.String(40), server_default="PRESENT", nullable=False),
        sa.Column("break_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_late", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("late_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_early_departure", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("early_departure_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_attendance_emp_date", "attendance_records", ["employee_id", "date"])

    # 5. leave_allocations
    op.create_table(
        "leave_allocations",
        *audit_columns(),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("leave_type", sa.String(40), nullable=False),
        sa.Column("total_days", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("used_days", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("pending_days", sa.Float(), server_default="0.0", nullable=False),
    )
    op.create_index("ix_leave_allocations_emp_year", "leave_allocations", ["employee_id", "year"])

    # 6. leave_requests
    op.create_table(
        "leave_requests",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type", sa.String(40), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("days_count", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("manager_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("manager_notes", sa.Text(), nullable=True),
        sa.Column("manager_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hr_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hr_notes", sa.Text(), nullable=True),
        sa.Column("hr_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_leave_requests_emp", "leave_requests", ["employee_id"])

    # 7. payroll_runs
    op.create_table(
        "payroll_runs",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("run_number", sa.String(60), unique=True, index=True, nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
        sa.Column("total_gross", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_deductions", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_net", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_employees", sa.Integer(), server_default="0", nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # 8. payslips
    op.create_table(
        "payslips",
        *audit_columns(),
        sa.Column("payroll_run_id", sa.Uuid(), sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("basic_salary", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("hra_allowance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("special_allowance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("medical_allowance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("other_allowance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("incentive_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("overtime_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("bonus_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("gross_earnings", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("pf_deduction", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("professional_tax", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("tds_tax", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("insurance_deduction", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("unpaid_leave_deduction", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("other_deductions", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("total_deductions", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("net_salary", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(40), server_default="GENERATED", nullable=False),
        sa.Column("payment_method", sa.String(40), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_payslips_run_emp", "payslips", ["payroll_run_id", "employee_id"])

    # 9. employee_incentives
    op.create_table(
        "employee_incentives",
        *audit_columns(),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("criterion_type", sa.String(40), nullable=False),
        sa.Column("target_value", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("achieved_value", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("rate_or_percentage", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("calculated_amount", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(40), server_default="PENDING", nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # 10. performance_reviews
    op.create_table(
        "performance_reviews",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("review_cycle", sa.String(40), server_default="QUARTERLY", nullable=False),
        sa.Column("review_period", sa.String(40), nullable=False),
        sa.Column("clinical_skills_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("patient_satisfaction_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("punctuality_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("teamwork_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("protocol_adherence_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("overall_rating", sa.Float(), server_default="5.0", nullable=False),
        sa.Column("kpi_details_json", sa.Text(), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("areas_of_improvement", sa.Text(), nullable=True),
        sa.Column("goals_next_period", sa.Text(), nullable=True),
        sa.Column("training_needs", sa.Text(), nullable=True),
        sa.Column("employee_feedback", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), server_default="DRAFT", nullable=False),
    )

    # 11. training_courses
    op.create_table(
        "training_courses",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("provider", sa.String(160), nullable=False),
        sa.Column("course_type", sa.String(60), server_default="CONTINUING_EDUCATION", nullable=False),
        sa.Column("credits_hours", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("validity_months", sa.Integer(), server_default="12", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # 12. employee_training_records
    op.create_table(
        "employee_training_records",
        *audit_columns(),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("training_courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("course_title", sa.String(200), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("certificate_number", sa.String(100), nullable=True),
        sa.Column("certificate_url", sa.String(255), nullable=True),
        sa.Column("status", sa.String(40), server_default="COMPLETED", nullable=False),
    )

    # 13. job_openings
    op.create_table(
        "job_openings",
        *audit_columns(),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("clinic_id", sa.Uuid(), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", sa.Uuid(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("employment_type", sa.String(40), server_default="FULL_TIME", nullable=False),
        sa.Column("open_positions", sa.Integer(), server_default="1", nullable=False),
        sa.Column("experience_years_min", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(40), server_default="OPEN", nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements", sa.Text(), nullable=True),
    )

    # 14. job_applicants
    op.create_table(
        "job_applicants",
        *audit_columns(),
        sa.Column("job_opening_id", sa.Uuid(), sa.ForeignKey("job_openings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("resume_url", sa.String(255), nullable=True),
        sa.Column("qualification", sa.String(120), nullable=True),
        sa.Column("experience_years", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("current_stage", sa.String(40), server_default="APPLIED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # 15. interview_schedules
    op.create_table(
        "interview_schedules",
        *audit_columns(),
        sa.Column("applicant_id", sa.Uuid(), sa.ForeignKey("job_applicants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interviewer_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interview_type", sa.String(40), server_default="TECHNICAL", nullable=False),
        sa.Column("feedback_notes", sa.Text(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("result", sa.String(40), server_default="PENDING", nullable=False),
    )

    # 16. employee_documents
    op.create_table(
        "employee_documents",
        *audit_columns(),
        sa.Column("employee_id", sa.Uuid(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("file_url", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mime_type", sa.String(80), server_default="application/pdf", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_table("employee_documents")
    op.drop_table("interview_schedules")
    op.drop_table("job_applicants")
    op.drop_table("job_openings")
    op.drop_table("employee_training_records")
    op.drop_table("training_courses")
    op.drop_table("performance_reviews")
    op.drop_table("employee_incentives")
    op.drop_table("payslips")
    op.drop_table("payroll_runs")
    op.drop_table("leave_requests")
    op.drop_table("leave_allocations")
    op.drop_table("attendance_records")
    op.drop_table("staff_schedules")
    op.drop_table("work_shifts")
    op.drop_table("employees")
