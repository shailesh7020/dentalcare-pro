# DentalCare Pro – Treatment Management Module (Phase 4 Specification)

## 1. Executive Summary & Clinical Purpose

The **Treatment Management Module** transforms DentalCare Pro from a patient directory and appointment scheduler into a **commercial-grade Clinical Electronic Health Record (EHR)** system (comparable to Dentrix, OpenDental, and Denticon).

Every completed or in-progress clinical visit transitions into a structured, longitudinal clinical treatment record that:
- Captures chief complaints, clinical diagnoses, and intraoral findings.
- Dynamically breaks down care into discrete dental procedures with tooth numbers (FDI / Universal notation prep for Phase 5 Odontogram) and monetary fees (prep for Phase 6 Billing & Invoicing).
- Documents structured SOAP notes (Subjective, Objective, Assessment, Plan).
- Enforces strict multi-clinic data isolation (`clinic_id`).
- Synchronizes appointment lifecycle state (initiating treatment advances appointment to `IN_CHAIR`/`IN_TREATMENT`; completing treatment can auto-finalize visit).
- Protects legal and clinical integrity through **Completed Record Immutability**.
- Maintains dual longitudinal audit trails (system-wide `AuditEvent` and patient-facing `PatientTimelineEvent`).

---

## 2. Database Schema & Relational Design

The module is implemented in PostgreSQL through Alembic migration `20260908_0005_treatments.py`.

### 2.1 Table: `treatments`

Primary clinical record for a patient treatment session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Globally unique record ID |
| `clinic_id` | `UUID` | `NOT NULL, FK(clinics.id)` | Tenant partition boundary |
| `patient_id` | `UUID` | `NOT NULL, FK(patients.id)` | Patient receiving care |
| `appointment_id` | `UUID` | `NOT NULL, FK(appointments.id)` | Linked clinical visit session |
| `dentist_id` | `UUID` | `NOT NULL, FK(users.id)` | Attending clinician |
| `treatment_number` | `VARCHAR(32)` | `NOT NULL` | Sequential identifier (e.g. `TRT-20260908-0001`) |
| `diagnosis` | `VARCHAR(500)` | `NOT NULL` | Primary clinical diagnosis |
| `chief_complaint` | `TEXT` | `NULLABLE` | Patient-reported primary complaint |
| `clinical_findings` | `TEXT` | `NULLABLE` | Intraoral and diagnostic examination findings |
| `treatment_plan` | `TEXT` | `NULLABLE` | Multi-step or staged clinical plan |
| `procedure_performed` | `TEXT` | `NULLABLE` | Narrative summary of procedures done |
| `local_anaesthesia_used` | `VARCHAR(255)` | `NULLABLE` | Anaesthetic agent, vasoconstrictor, volume |
| `medicines_used` | `VARCHAR(500)` | `NULLABLE` | Prescribed and in-clinic pharmaceuticals |
| `clinical_notes` | `TEXT` | `NULLABLE` | Detailed markdown clinical notes |
| `soap_subjective` | `TEXT` | `NULLABLE` | Patient history and subjective symptoms |
| `soap_objective` | `TEXT` | `NULLABLE` | Objective clinical exam & diagnostic tests |
| `soap_assessment` | `TEXT` | `NULLABLE` | Clinician diagnosis, pulpal/periodontal staging |
| `soap_plan` | `TEXT` | `NULLABLE` | Proposed treatment steps and prescriptions |
| `follow_up_instructions` | `TEXT` | `NULLABLE` | Post-operative home care instructions |
| `cancellation_reason` | `TEXT` | `NULLABLE` | Reason if treatment is cancelled |
| `status` | `ENUM` | `NOT NULL, DEFAULT 'IN_PROGRESS'` | `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `is_override` | `BOOLEAN` | `NOT NULL, DEFAULT FALSE` | True if created via Admin Override |
| `completed_at` | `TIMESTAMPTZ` | `NULLABLE` | Timestamp when treatment was finalized |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL, DEFAULT now()` | Last update timestamp |
| `deleted_at` | `TIMESTAMPTZ` | `NULLABLE` | Soft delete timestamp |
| `created_by` | `UUID` | `NULLABLE, FK(users.id)` | User who created record |
| `updated_by` | `UUID` | `NULLABLE, FK(users.id)` | User who last modified record |
| `version` | `INTEGER` | `NOT NULL, DEFAULT 1` | Optimistic locking counter |

**Indexes & Constraints**:
- `uq_treatments_clinic_number`: Unique constraint on `(clinic_id, treatment_number)`.
- `ix_treatments_clinic_status`: Compound index on `(clinic_id, status)`.
- `ix_treatments_clinic_patient`: Compound index on `(clinic_id, patient_id)`.
- `ix_treatments_clinic_appointment`: Compound index on `(clinic_id, appointment_id)`.
- `ix_treatments_clinic_dentist`: Compound index on `(clinic_id, dentist_id)`.
- `ix_treatments_clinic_created_at`: Compound index on `(clinic_id, created_at)`.

---

### 2.2 Table: `treatment_procedures`

Discrete procedure line items performed during the treatment session.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Procedure row ID |
| `treatment_id` | `UUID` | `NOT NULL, FK(treatments.id, CASCADE)` | Parent treatment session |
| `procedure_name` | `VARCHAR(160)` | `NOT NULL` | Name of procedure (e.g. Root Canal Stage 1) |
| `tooth_number` | `VARCHAR(20)` | `NULLABLE` | Tooth identifier (e.g. `46`, `11-21`, `Upper Arch`) |
| `quantity` | `INTEGER` | `NOT NULL, DEFAULT 1` | Number of units/teeth treated |
| `cost` | `NUMERIC(10, 2)`| `NOT NULL, DEFAULT 0.00` | Unit procedure cost |
| `duration` | `INTEGER` | `NOT NULL, DEFAULT 30` | Duration in minutes |
| `notes` | `TEXT` | `NULLABLE` | Procedure-specific notes (canals, shades) |
| `status` | `VARCHAR(40)` | `NOT NULL, DEFAULT 'COMPLETED'` | `COMPLETED`, `IN_PROGRESS`, `PLANNED` |

---

### 2.3 Table: `treatment_follow_ups`

Scheduled clinical follow-up visits resulting from the treatment.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | `PRIMARY KEY` | Follow-up record ID |
| `treatment_id` | `UUID` | `NOT NULL, FK(treatments.id, CASCADE)` | Source treatment record |
| `clinic_id` | `UUID` | `NOT NULL, FK(clinics.id)` | Multi-clinic tenant boundary |
| `patient_id` | `UUID` | `NOT NULL, FK(patients.id)` | Patient for follow-up |
| `follow_up_date` | `DATE` | `NOT NULL` | Scheduled date of follow-up |
| `reason` | `VARCHAR(255)` | `NOT NULL` | Clinical objective of follow-up |
| `instructions` | `TEXT` | `NULLABLE` | Special instructions for patient |
| `status` | `ENUM` | `NOT NULL, DEFAULT 'SCHEDULED'` | `SCHEDULED`, `COMPLETED`, `MISSED`, `CANCELLED` |
| `completed_at` | `TIMESTAMPTZ` | `NULLABLE` | Completion timestamp |

---

## 3. Clinical Business Rules & State Machine

### 3.1 Single Active Treatment & Administrative Override
1. An appointment can only have **one active treatment** (`status != CANCELLED` and `deleted_at IS NULL`) at a time.
2. If a non-override request is submitted for an appointment with an existing active treatment, the API rejects it with:
   `HTTP 400 Bad Request: Active treatment #TRT-YYYYMMDD-XXXX already exists for this appointment. Enable is_override to proceed.`
3. If `is_override = true`, the request is permitted **only** if the actor is `CLINIC_ADMIN` or `SUPER_ADMIN`. Regular clinicians attempting an override receive:
   `HTTP 403 Forbidden: Only clinic administrators can override and create multiple active treatments.`

### 3.2 Appointment Lifecycle Synchrony
- Creating a treatment automatically advances the associated appointment from `SCHEDULED` or `CHECKED_IN` to `IN_TREATMENT` (`IN_CHAIR`).
- Sets `start_datetime = now()`.
- Logs an `AppointmentTimelineEvent` (`TREATMENT_STARTED`).
- Completing a treatment with `complete_appointment = true` automatically updates the appointment to `COMPLETED` and sets `end_datetime = now()`.

### 3.3 Completed Record Immutability
- Completed clinical records (`status = COMPLETED`) are **permanently locked**.
- Attempting to update (`PATCH`), cancel (`POST /cancel`), or delete (`DELETE`) a completed treatment is strictly blocked:
  `HTTP 400 Bad Request: Completed treatments are permanently locked and cannot be edited.`

### 3.4 Follow-up Chronological Validation
- The `follow_up_date` cannot precede the treatment / appointment date.
- Any attempt to schedule a follow-up in the past triggers:
  `HTTP 400 Bad Request: Follow-up date cannot be before the treatment date.`

---

## 4. REST API Endpoints

All routes are mounted under `/api/v1/treatments` and require authentication and clinic context.

| Method | Path | Required Roles | Description |
|---|---|---|---|
| `POST` | `/treatments` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST` | Create new clinical treatment |
| `GET` | `/treatments` | All authenticated roles | Searchable, filterable directory |
| `GET` | `/treatments/dashboard/stats` | All authenticated roles | KPI statistics (planned, in progress, completed, follow-ups due) |
| `GET` | `/treatments/{id}` | All authenticated roles | Full treatment detail with procedures and SOAP |
| `PATCH` | `/treatments/{id}` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST` | Update uncompleted treatment |
| `DELETE` | `/treatments/{id}` | `SUPER_ADMIN`, `CLINIC_ADMIN` | Soft-delete treatment (Admin only) |
| `POST` | `/treatments/{id}/complete` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST` | Complete and permanently lock record |
| `POST` | `/treatments/{id}/cancel` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST` | Cancel treatment with clinical reason |
| `GET` | `/treatments/patient/{id}` | All authenticated roles | All treatments for a patient |
| `GET` | `/treatments/appointment/{id}` | All authenticated roles | Treatment for an appointment |
| `GET` | `/patients/{id}/treatments` | All authenticated roles | Route alias on patients router |
| `GET` | `/appointments/{id}/treatment`| All authenticated roles | Route alias on appointments router |

---

## 5. Structured SOAP Notes Architecture

Each clinical record includes dedicated storage and UI fields for the four components of SOAP documentation:

```
[S] Subjective:
- Patient symptoms and chief complaints in their own words.
- Pain scale (1-10), aggravating/relieving factors, onset and duration.

[O] Objective:
- Intraoral physical findings: probing depth, bleeding on probing (BOP), tooth mobility.
- Diagnostic vitality tests (electric pulp test, cold test, percussion, palpation).
- Radiographic observations (periapical radiolucency, bone loss).

[A] Assessment:
- Clinical diagnosis (e.g., Symptomatic Irreversible Pulpitis, Generalized Periodontitis Stage III).
- Differential diagnoses.

[P] Plan:
- Clinical procedures scheduled or completed (e.g., Endodontic therapy, composite restoration).
- Pharmacological prescriptions (analgesics, antibiotics, mouthwashes).
- Patient education and next recall schedule.
```

---

## 6. Frontend Architecture & Views

The frontend is implemented in Next.js 16 (App Router), React 19, and Tailwind CSS:

1. **Treatments Hub (`/treatments`)**:
   - Practice KPI metrics (Total, In Progress, Planned, Completed, Follow-ups Due).
   - Search bar across patient name, treatment number, phone, and diagnosis.
   - Status tab pills (All, In Progress, Planned, Completed, Cancelled).
   - Interactive directory table with procedure counts, costs, and quick actions.

2. **Clinical Treatment Form (`/treatments/new`)**:
   - Pre-fills patient and appointment context when navigated from appointments queue or patient profile.
   - Displays patient medical alerts (Cardiac disease, Allergies, Hypertension, etc.) in real time.
   - Dynamic Procedure Builder with row addition/deletion, tooth numbering, and live cost calculation.
   - Dedicated 4-field SOAP clinical notes editor.
   - Follow-up visit scheduler with chronological validation.
   - Admin override toggle with authorization notices.

3. **Treatment Detail View (`/treatments/[id]`)**:
   - Header with status badges and permanent record locks.
   - Patient card with medical alerts and appointment linkage.
   - Itemized procedure table with individual and total costs.
   - 4-card longitudinal SOAP notes panel.
   - Pharmacology, local anaesthesia, and clinical notes card.
   - Post-op home care and follow-up schedule.
   - Finalization modals: Complete Treatment (with appointment auto-complete), Cancel Treatment (with mandatory reason), Soft-Delete (admin only).

4. **Treatment Edit View (`/treatments/[id]/edit`)**:
   - Pre-populates all editable fields for open records.
   - Enforces permanent read-only lock if treatment is `COMPLETED`.

5. **Cross-Module Integrations**:
   - **Patient Profile (`/patients/[id]`)**: Tab 6 replaced with real treatments list and "+ Start New Treatment" trigger.
   - **Appointment Dialog (`AppointmentDetailDialog`)**: Added "+ Start Treatment" and "Open Clinical Record" direct CTAs.
   - **Main Navigation (`page.tsx`)**: Connected top-level Treatments link and Quick Actions button to `/treatments`.

---

## 7. Verification & Coverage Results

- **Backend Pytest Suite**:
  - `tests/test_treatment_repository.py`: 6 tests, **99%** coverage.
  - `tests/test_treatment_service.py`: 6 tests, **92%** coverage.
  - `tests/test_treatment_api.py`: 4 tests, **100%** coverage.
  - Total Treatment Module Statements: 512, Tested: 494 (**96.5% overall**).
- **Frontend Vitest Suite**:
  - `apps/web/src/app/treatments/treatment.spec.ts`: 8 tests, **100% passing**.
- **Production Build**:
  - `next build` with Turbopack succeeded with **zero errors**.
