# DentalCare Pro - Complete REST API Reference (v1.0.0)

## 1. Overview & Headers
- **Base URL**: `https://api.dentalcarepro.com/api/v1`
- **Authentication**: Bearer JWT (`Authorization: Bearer <access_token>`)
- **Multi-Tenancy**: Mandatory `X-Clinic-ID: <clinic_uuid>` header on all tenant-scoped requests.

---

## 2. Core API Endpoints

### 2.1 Authentication (`/auth`)
- `POST /auth/login`: Authenticate credentials, returns access & refresh tokens.
- `POST /auth/refresh`: Exchange valid refresh token for a new access token.
- `POST /auth/logout`: Revoke active session tokens.

### 2.2 Patients (`/patients`)
- `GET /patients`: List patients (supports search by name, mobile, Aadhaar).
- `POST /patients`: Register new patient intake record.
- `GET /patients/{id}`: Retrieve detailed patient demographic & medical history.
- `PUT /patients/{id}`: Update patient details.
- `DELETE /patients/{id}`: Soft-delete patient record.

### 2.3 Appointments (`/appointments`)
- `GET /appointments`: Query appointment roster by date, dentist, or status.
- `POST /appointments`: Book new chairside appointment.
- `PUT /appointments/{id}/status`: Transition appointment state (`CHECKED_IN`, `IN_TREATMENT`, `COMPLETED`, `CANCELLED`).
- `PUT /appointments/{id}/reschedule`: Update appointment timing with slot conflict verification.

### 2.4 Interactive Odontogram (`/patients/{id}/odontogram`)
- `GET /patients/{id}/odontogram`: Retrieve current state of all 32 teeth and surfaces.
- `POST /patients/{id}/odontogram/findings`: Record clinical finding on a specific tooth/surface.
- `POST /patients/{id}/odontogram/reset`: Archive current chart and reset dentition.

### 2.5 Treatments (`/treatments`)
- `POST /treatments`: Create clinical treatment record with SOAP notes.
- `POST /treatments/{id}/procedures`: Record completed CDT dental procedure.
- `PUT /treatments/{id}/complete`: Finalize treatment, record actual cost, mark appointment complete.

### 2.6 Prescriptions (`/prescriptions`)
- `POST /prescriptions`: Issue new prescription with medication catalog validation.
- `GET /prescriptions/{id}`: Retrieve prescription details and downloadable PDF link.

### 2.7 Billing & Invoicing (`/billing`)
- `POST /billing/invoices`: Create itemized dental invoice.
- `POST /billing/payments`: Record card, UPI, cash, or insurance payment against an invoice.
- `GET /billing/reports/revenue`: Aggregate revenue reports across custom date ranges.

### 2.8 Telemetry & Health Probes (Root Level)
- `GET /health/live`: Kubernetes liveness probe (200 OK).
- `GET /health/ready`: Kubernetes readiness probe (validates DB & Redis connectivity).
- `GET /metrics`: Prometheus text metrics export for request latency, status codes, and DB pool depth.
