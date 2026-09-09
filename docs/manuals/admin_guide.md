# DentalCare Pro - System Administrator & Practice Manager Guide

## Overview
This guide provides technical administration instructions for managing multi-branch clinics, user provisioning, security policies, and financial configuration in DentalCare Pro.

---

## 1. User Provisioning & Role-Based Access Control (RBAC)

DentalCare Pro implements strict separation of duties across predefined organizational roles:

| System Role | Permissions & Operational Scope |
| :--- | :--- |
| **Superadmin** | Full global platform administration, tenant provisioning, system configurations |
| **Organization Admin** | Corporate-wide administrative control across all regional clinic branches |
| **Regional Manager** | Multi-branch oversight within an assigned geographical region |
| **Clinic Admin** | Branch-level administration, staff scheduling, local inventory and billing oversight |
| **Dentist** | Clinical records, 32-tooth odontogram charting, SOAP notes, prescriptions |
| **Hygienist** | Preventive cleanings, periodontal scoring, medical history intake |
| **Receptionist** | Patient intake, scheduling, waiting room queues, POS payment processing |
| **Accountant** | Financial ledger audits, tax reports, insurance claims reconciliation |
| **HR Manager** | Staff recruitment, attendance, shift scheduling, payroll runs, appraisals |

### Creating a New Staff Account
1. Navigate to **Settings -> User Management -> Add User**.
2. Provide the employee's corporate email, designated branch, and primary role.
3. The system generates an activation link enforcing mandatory Multi-Factor Authentication (MFA) setup upon first login.

---

## 2. Multi-Branch & Corporate Management

1. **Regional Grouping**: Organize branches under distinct regions (e.g. Metro Flagships vs Suburban Practices).
2. **Inter-Branch Patient Record Sharing**:
   - `SHARED`: Clinicians across all corporate branches can review clinical history upon patient check-in.
   - `ISOLATED`: Strict silo; records never leave the registered clinic.
   - `TRANSFER_ONLY`: Explicit branch transfer authorization required.
3. **Inter-Clinic Inventory Requisition**:
   - Practice managers can initiate stock transfer requests from central warehouse depots to satellite operatory locations.

---

## 3. Financial & Tax Configuration

1. **Currency Settings**: Default currency and rounding precision per clinic.
2. **Tax Schedules**: Configure GST, VAT, or Sales Tax rates applied to procedural codes or dental supplies.
3. **Insurance Payer Profiles**: Register contracted dental insurance TPAs, EDI payer IDs, and fee schedules.

---

## 4. Audit Logging & Regulatory Compliance

1. Navigate to **Security -> Audit Trail**.
2. All read, update, delete, and export operations on Protected Health Information (PHI) are logged with:
   - User ID & Role
   - Clinic ID & Patient ID
   - Client IP Address & User-Agent
   - Cryptographic timestamp (UTC)
3. Audit logs are tamper-evident and archived for 7 years to meet HIPAA Security Rule § 164.312(b).
