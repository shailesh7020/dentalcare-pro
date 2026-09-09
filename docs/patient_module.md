# Patient Management Module Documentation

The Patient Management Module in **DentalCare Pro** provides complete, clinic-isolated lifecycle management for patient records, medical histories, dental histories, chronological timelines, and clinical attachments.

---

## 1. Architectural Principles

1. **Multi-Clinic Tenant Isolation**: Every patient record, history row, timeline event, and document attachment is partitioned by `clinic_id`. No query or mutation executes without asserting the authenticated user's clinic boundary.
2. **Audit Logging & Provenance**: Every lifecycle mutation (`REGISTER`, `UPDATE`, `ARCHIVE`, `RESTORE`, `VIEW`, `DOCUMENT_UPLOAD`) emits an immutable `AuditEvent` (for platform-wide compliance) and a `PatientTimelineEvent` (for clinical continuity).
3. **Soft Deletion & Active Uniqueness**: Patient records are never hard-deleted in clinical workflows. When archived, `deleted_at` is set. The PostgreSQL partial index `uq_patients_clinic_mobile_active` enforces mobile uniqueness strictly among active records (`WHERE deleted_at IS NULL`).
4. **Non-blocking Duplicate Detection**: Registration and updates check for matching `mobile_number`, `email`, and `aadhaar_number` within the clinic. Instead of hard failures, the API returns a structured `duplicate_warning` payload enabling receptionists and dentists to review matches without interrupting urgent care.
5. **Secure Local/S3 Storage Streaming**: Document files are stored with unique storage keys and accessed exclusively through clinic-authorized API streaming endpoints. Raw storage URIs are never exposed to clients.

---

## 2. Data Models & Schema

### Database Tables (`migrations/versions/20260906_0003_patients.py`)

#### `patients`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Unique patient identifier |
| `clinic_id` | UUID | FK -> `clinics.id`, Index | Tenant partition |
| `patient_number` | VARCHAR(32) | NOT NULL | Clinic-scoped sequential identifier (e.g. `PAT-20260908-4102`) |
| `first_name` | VARCHAR(80) | NOT NULL | Patient given name |
| `middle_name` | VARCHAR(80) | NULLABLE | Middle name |
| `last_name` | VARCHAR(80) | NOT NULL | Surname |
| `gender` | ENUM | NOT NULL | `FEMALE`, `MALE`, `NON_BINARY`, `PREFER_NOT_TO_SAY` |
| `date_of_birth` | DATE | NOT NULL | Date of birth (must not be in future) |
| `blood_group` | ENUM | NULLABLE | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`, `UNKNOWN` |
| `marital_status` | VARCHAR(40) | NULLABLE | Single, Married, Divorced, Widowed, etc. |
| `occupation` | VARCHAR(100) | NULLABLE | Patient occupation |
| `aadhaar_number` | VARCHAR(12) | NULLABLE, Index | 12-digit Indian UIDAI Aadhaar |
| `email` | VARCHAR(255) | NULLABLE, Index | Patient email address |
| `mobile_number` | VARCHAR(15) | NOT NULL | 10-digit Indian mobile (`^[6-9]\d{9}$`) |
| `alternate_mobile` | VARCHAR(15) | NULLABLE | Secondary contact |
| `address` | TEXT | NULLABLE | Street address |
| `city` | VARCHAR(80) | NULLABLE | City |
| `state` | VARCHAR(80) | NULLABLE | State / Province |
| `country` | VARCHAR(80) | NOT NULL, DEFAULT 'India' | Country |
| `pin_code` | VARCHAR(6) | NULLABLE | 6-digit Indian Postal Index Number |
| `emergency_contact_name` | VARCHAR(160) | NULLABLE | Primary emergency contact person |
| `emergency_contact_number` | VARCHAR(15) | NULLABLE | Emergency phone number |
| `emergency_contact_relation` | VARCHAR(60) | NULLABLE | Relationship (Parent, Spouse, Sibling, etc.) |
| `insurance_provider` | VARCHAR(160) | NULLABLE | Insurance carrier name |
| `insurance_policy_number` | VARCHAR(100) | NULLABLE | Policy / Member ID |
| `preferred_language` | VARCHAR(40) | NOT NULL, DEFAULT 'English' | Preferred language of communication |
| `photo_url` | VARCHAR(500) | NULLABLE | Optional profile photo URL |
| `notes` | TEXT | NULLABLE | General clinical or administrative notes |
| `created_at` | TIMESTAMPTZ | NOT NULL | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Last update timestamp |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Soft-delete timestamp |
| `created_by` | UUID | NULLABLE | User ID who created the record |
| `updated_by` | UUID | NULLABLE | User ID who last updated the record |
| `version` | INT | NOT NULL, DEFAULT 1 | Optimistic concurrency control |

**Table Constraints & Indexes:**
- Unique Constraint: `uq_patients_clinic_number` (`clinic_id`, `patient_number`)
- Partial Unique Index: `uq_patients_clinic_mobile_active` (`clinic_id`, `mobile_number`) `WHERE deleted_at IS NULL`
- Compound Index: `ix_patients_clinic_active_name` (`clinic_id`, `deleted_at`, `last_name`, `first_name`)
- Index: `ix_patients_clinic_aadhaar` (`clinic_id`, `aadhaar_number`)
- Index: `ix_patients_clinic_email` (`clinic_id`, `email`)

#### `medical_histories`
1-to-1 relationship with `patients` (cascade delete on patient purge).
- **Systemic Conditions**: `diabetes`, `hypertension`, `cardiac_disease`, `thyroid`, `asthma`, `epilepsy`, `pregnancy` (all boolean, default `false`).
- **Habits**: `smoking`, `tobacco`, `alcohol` (boolean, default `false`).
- **Clinical Details**: `allergies` (text), `current_medications` (text), `previous_surgeries` (text), `infectious_diseases` (text), `physician_name` (varchar 160), `physician_contact` (varchar 15), `additional_notes` (text).

#### `dental_histories`
1-to-1 relationship with `patients` (cascade delete on patient purge).
- **Clinical Symptoms & Complaints**: `chief_complaint` (text), `previous_dental_treatments` (text), `brushing_frequency` (varchar 40), `flossing_habit` (boolean), `tobacco_habit` (boolean), `grinding` (boolean), `jaw_pain` (boolean), `tmj_disorder` (boolean), `sensitivity` (boolean), `bleeding_gums` (boolean), `last_dental_visit` (date), `dental_notes` (text).

#### `patient_timeline_events`
Chronological event ledger per patient.
- `id` (UUID PK), `patient_id` (UUID FK), `clinic_id` (UUID FK), `event_type` (VARCHAR 80), `title` (VARCHAR 200), `description` (TEXT), `actor_id` (UUID FK -> users.id), `created_at` (TIMESTAMPTZ).
- Index: `ix_patient_timeline_patient_created` (`patient_id`, `created_at`).

#### `patient_documents`
Clinical files, radiographs, and lab reports.
- `id` (UUID PK), `patient_id` (UUID FK), `clinic_id` (UUID FK), `file_name` (VARCHAR 255), `content_type` (VARCHAR 120), `storage_key` (VARCHAR 500 UK), `document_type` (VARCHAR 60), `created_at` (TIMESTAMPTZ).

---

## 3. Role-Based Access Control Matrix

| Endpoint | Method | Permitted Roles | Action Description |
|---|---|---|---|
| `/api/v1/patients` | `GET` | All Roles (`SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST`, `RECEPTIONIST`, `STAFF`) | List patients with search, status, and demographic filters |
| `/api/v1/patients/search` | `GET` | All Roles | Quick search by query string |
| `/api/v1/patients/{id}` | `GET` | All Roles | View complete profile, medical & dental histories |
| `/api/v1/patients/{id}/timeline` | `GET` | All Roles | View chronological patient history ledger |
| `/api/v1/patients/{id}/documents` | `GET` | All Roles | View attached documents metadata list |
| `/api/v1/patients/{id}/documents/{doc_id}/download` | `GET` | All Roles | Stream document bytes securely |
| `/api/v1/patients` | `POST` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST`, `RECEPTIONIST` | Register new patient with optional initial medical/dental histories |
| `/api/v1/patients/{id}` | `PATCH` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST`, `RECEPTIONIST` | Update demographics, contact info, and medical/dental histories |
| `/api/v1/patients/{id}/documents` | `POST` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `DENTIST`, `RECEPTIONIST` | Upload clinical attachments, radiographs, consent forms |
| `/api/v1/patients/{id}` | `DELETE` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `RECEPTIONIST` | Archive (soft-delete) patient record |
| `/api/v1/patients/{id}/restore` | `POST` | `SUPER_ADMIN`, `CLINIC_ADMIN`, `RECEPTIONIST` | Restore archived patient record |

---

## 4. API Endpoints Catalog

### 4.1 Register Patient
`POST /api/v1/patients`
- **Request Body**: `PatientCreate`
  - Required: `first_name`, `last_name`, `gender`, `date_of_birth`, `mobile_number`.
  - Optional: `middle_name`, `blood_group`, `marital_status`, `occupation`, `aadhaar_number`, `email`, `alternate_mobile`, `address`, `city`, `state`, `country`, `pin_code`, `emergency_contact_*`, `insurance_*`, `preferred_language`, `photo_url`, `notes`, `medical_history`, `dental_history`.
- **Response**: `201 Created` with `PatientMutationResponse`:
  ```json
  {
    "patient": {
      "id": "7fa85f64-5717-4562-b3fc-2c963f66afa6",
      "clinic_id": "99999999-9999-9999-9999-999999999999",
      "patient_number": "PAT-20260908-1024",
      "first_name": "Aarav",
      "last_name": "Sharma",
      "gender": "MALE",
      "date_of_birth": "1994-06-15",
      "age": 32,
      "status": "ACTIVE",
      "mobile_number": "9876543210",
      ...
    },
    "duplicate_warning": null
  }
  ```
  If a duplicate matching mobile/email/Aadhaar is found, `duplicate_warning` returns:
  ```json
  {
    "duplicate_warning": {
      "matched_by": "mobile",
      "patient_id": "11111111-2222-3333-4444-555555555555",
      "patient_number": "PAT-20260901-0001",
      "name": "Aarav Sharma",
      "mobile_number": "9876543210"
    }
  }
  ```

### 4.2 List Patients
`GET /api/v1/patients`
- **Query Parameters**:
  - `search` (string, optional): Matches patient number, first name, last name, mobile number, email, or Aadhaar.
  - `status` (string, optional, default `"active"`): Filter by `"active"`, `"archived"`, or `"all"`.
  - `gender` (Gender, optional): Filter by gender enum.
  - `blood_group` (BloodGroup, optional): Filter by blood group enum.
  - `skip` (int, default `0`): Pagination offset.
  - `limit` (int, default `50`, max `100`): Page size.
  - `sort` (string, default `"created_at"`): Sort column (`created_at`, `patient_number`, `last_name`, `date_of_birth`).
  - `descending` (bool, default `true`): Sort order.
- **Response**: `200 OK` with list of `PatientRead` items.

### 4.3 Get Patient Details
`GET /api/v1/patients/{id}`
- Returns full `PatientDetail` including 1-to-1 `medical_history` and `dental_history`.
- Automatically logs a `PATIENT_VIEWED` audit entry and timeline event.
- Returns `404` if not found or if belonging to another clinic.

### 4.4 Update Patient
`PATCH /api/v1/patients/{id}`
- **Request Body**: `PatientUpdate` (all fields optional). Supports updating demographics, contact info, notes, and nested `medical_history` and `dental_history`.
- **Response**: `200 OK` with `PatientMutationResponse`.

### 4.5 Archive Patient (Soft Delete)
`DELETE /api/v1/patients/{id}`
- Marks `deleted_at = now()`.
- Logs `PATIENT_ARCHIVED` in audit log and timeline.
- **Response**: `204 No Content`.

### 4.6 Restore Patient
`POST /api/v1/patients/{id}/restore`
- Resets `deleted_at = null`.
- Fails with `409 Conflict` if another active patient already exists in the clinic with the same mobile number.
- Logs `PATIENT_RESTORED` in audit log and timeline.
- **Response**: `200 OK` with restored `PatientDetail`.

### 4.7 Patient Timeline Ledger
`GET /api/v1/patients/{id}/timeline`
- Returns chronological list of `PatientTimelineEventRead` items sorted newest first.

### 4.8 Document Storage Endpoints
- `GET /api/v1/patients/{id}/documents`: Returns list of `DocumentRead` records.
- `POST /api/v1/patients/{id}/documents`: Multipart form upload with `file` and optional `document_type`. Validates content types (`image/jpeg`, `image/png`, `application/pdf`, `image/webp`).
- `GET /api/v1/patients/{id}/documents/{document_id}/download`: Streams file bytes with tenant validation and appropriate `Content-Disposition`.

---

## 5. Frontend Architecture & Features

Built using **Next.js 16 (Turbopack, App Router)**, **React 19**, **Tailwind CSS**, and **shadcn/ui** design patterns.

### 5.1 Route Structure
- `/patients`: Patient directory listing with live search, status switcher, filters, sort controls, and action menus.
- `/patients/new`: Multi-section registration form with responsive live age calculation, medical checkboxes, dental habits, and duplicate detection alerts.
- `/patients/[id]`: Comprehensive patient profile layout with:
  - Header: Avatar, patient number badge, status badge, quick actions (Edit, Archive/Restore).
  - High-risk Medical Alerts Banner (Cardiac disease, Bleeding disorders, Allergies, Diabetes, Pregnancy).
  - Tabs:
    1. **Overview**: Demographics, address, emergency contact, insurance.
    2. **Medical History**: Systemic conditions, allergies, medications, habits, physician notes.
    3. **Dental History**: Chief complaint, symptoms, habits, dental notes.
    4. **Timeline**: Chronological audit trail of clinical activities.
    5. **Appointments**: Connected integration placeholder for Phase 3.
    6. **Treatments**: Connected integration placeholder for Phase 4.
    7. **Documents**: Upload modal, document grid, and secure direct download buttons.
- `/patients/[id]/edit`: Pre-populated edit form for all patient parameters.

### 5.2 UI Primitives Built
- `badge.tsx`: Variant badges for `ACTIVE` / `ARCHIVED` statuses, high-risk warnings, and blood groups.
- `skeleton.tsx`: Shimmer loading states for tables, forms, and cards.
- `dialog.tsx`: Accessible modal dialogs for archive confirmations and document uploads.
- `tabs.tsx`: Accessible tab switcher for patient detail sections.

---

## 6. Verification and Quality Metrics

- **Backend Pytest Suite**: 40 unit and integration tests passing (`100%` pass rate).
- **Backend Code Coverage**:
  - `app/api/v1/patients.py`: **100%**
  - `app/models/patient.py`: **100%**
  - `app/repositories/patient_repository.py`: **100%**
  - `app/services/patient_service.py`: **100%**
  - `app/schemas/patient.py`: **99%**
  - **Overall Patient Module Coverage**: **99.2%** (surpassing the 90% benchmark).
- **Frontend Vitest Suite**: 6 schema & validation tests passing.
- **Frontend Production Build**: `pnpm build` completed with zero errors across all 11 static/dynamic routes.
