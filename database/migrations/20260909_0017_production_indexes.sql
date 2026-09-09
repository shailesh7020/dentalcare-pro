-- =====================================================================
-- DentalCare Pro - Enterprise Production Database Indexes & Optimization
-- Phase 17: Query Acceleration, Multi-Tenant Partitioning & Autovacuum
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. High-Frequency Clinical & Patient Search Indexes
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_clinic_name_search
    ON patients (clinic_id, last_name, first_name)
    WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_mobile_active
    ON patients (clinic_id, mobile_number)
    WHERE deleted_at IS NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_aadhaar_active
    ON patients (clinic_id, aadhaar_number)
    WHERE aadhaar_number IS NOT NULL AND deleted_at IS NULL;

-- ---------------------------------------------------------------------
-- 2. Appointment Scheduling & Operatory Roster Indexes
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_clinic_date_status
    ON appointments (clinic_id, date, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_dentist_schedule
    ON appointments (clinic_id, dentist_id, date, start_time);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_appointments_chair_timeline
    ON appointments (clinic_id, chair_id, date, start_time, end_time);

-- ---------------------------------------------------------------------
-- 3. Odontogram & 32-Tooth FDI Quadrant Charting
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_teeth_patient_quadrant
    ON teeth (clinic_id, patient_id, quadrant, tooth_number);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tooth_surfaces_tooth_lookup
    ON tooth_surfaces (tooth_id, surface, condition);

-- ---------------------------------------------------------------------
-- 4. Clinical Treatments & Procedure Records
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_treatments_clinic_patient_date
    ON treatments (clinic_id, patient_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_treatment_procedures_perf
    ON treatment_procedures (treatment_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_treatment_followups_active
    ON treatment_follow_ups (clinic_id, follow_up_date, status)
    WHERE status = 'SCHEDULED';

-- ---------------------------------------------------------------------
-- 5. Financial Ledger, Invoicing & POS Payments
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_invoices_outstanding_balance
    ON invoices (clinic_id, balance_due, status)
    WHERE balance_due > 0 AND status != 'CANCELLED';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_payments_clinic_reconciliation
    ON payments (clinic_id, payment_date DESC, method);

-- ---------------------------------------------------------------------
-- 6. Insurance Claims & Adjudication Pipeline
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_insurance_claims_processing
    ON insurance_claims (clinic_id, status, submission_date DESC);

-- ---------------------------------------------------------------------
-- 7. Inventory Stock & Automatic Reorder Alerts
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_low_stock_alert
    ON inventory_items (clinic_id, current_quantity, reorder_level)
    WHERE current_quantity <= reorder_level;

-- ---------------------------------------------------------------------
-- 8. Workforce Management & Shift Attendance
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_attendance_records_daily
    ON attendance_records (clinic_id, date, employee_id, status);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leave_requests_approval
    ON leave_requests (clinic_id, status, start_date)
    WHERE status = 'SUBMITTED';

-- ---------------------------------------------------------------------
-- 9. HIPAA Immutable Audit Log Stream
-- ---------------------------------------------------------------------
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_tenant_timestamp
    ON audit_events (clinic_id, created_at DESC);

-- ---------------------------------------------------------------------
-- 10. Autovacuum Table-Level Tuning for High-Volume Tables
-- ---------------------------------------------------------------------
ALTER TABLE patients SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE appointments SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE treatments SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE invoices SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE payments SET (
    autovacuum_vacuum_scale_factor = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ANALYZE VERBOSE patients;
ANALYZE VERBOSE appointments;
ANALYZE VERBOSE treatments;
ANALYZE VERBOSE teeth;
ANALYZE VERBOSE invoices;
ANALYZE VERBOSE payments;
