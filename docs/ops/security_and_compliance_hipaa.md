# DentalCare Pro - HIPAA, GDPR & Cloud Security Compliance Architecture

DentalCare Pro implements technical, administrative, and physical safeguards complying with HIPAA Security Rule (45 CFR Part 160 and Part 164) and GDPR Article 32.

---

## 1. Technical Safeguards (HIPAA § 164.312)

### 1.1 Access Control (§ 164.312(a))
- **Unique User Identification**: Every clinician, staff member, and admin authenticates with unique credentials. Shared accounts are strictly prohibited.
- **Role-Based Access Control (RBAC)**: Strict permission boundaries (Doctor, Receptionist, Hygienist, Billing Admin, Branch Manager, Superadmin).
- **Automatic Logoff**: Client applications automatically terminate idle sessions after 15 minutes of inactivity.
- **Emergency Access ('Break-Glass')**: Authorized clinical staff can override record locks during medical emergencies with mandatory reason logging and real-time alerts.

### 1.2 Audit Controls (§ 164.312(b))
- **Immutable Audit Trail**: Every read, write, update, and export of Protected Health Information (PHI) is logged in the `audit_logs` table with `user_id`, `clinic_id`, `patient_id`, `client_ip`, `action`, and cryptographic timestamp.
- **Log Centralization**: Logs are forwarded via Promtail to Loki with write-once retention and tamper-evident storage.

### 1.3 Transmission Security (§ 164.312(e))
- **Encryption in Transit**: All external and internal communications require TLS 1.3 with strong cipher suites (`ECDHE-RSA-AES256-GCM-SHA384`).
- **Internal Service Mesh**: Kubernetes inter-pod communication is secured via mutual TLS (mTLS) or encrypted overlay networks.

### 1.4 Data at Rest Encryption (§ 164.312(a)(2)(iv))
- **Database Storage**: PostgreSQL volumes are encrypted with AWS KMS customer-managed keys (CMK) using AES-256.
- **Diagnostic Media (X-Rays, Scans)**: S3 media buckets enforce server-side encryption with KMS (`aws:kms`) and strict bucket policies denying non-HTTPS requests.
- **Field-Level Encryption**: Sensitive patient identifiers (SSN, national ID, payment card tokens) utilize AES-256-GCM application-level encryption.

---

## 2. Multi-Tenant Isolation Controls

To ensure absolute separation between different dental practices:
1. **Row-Level Tenant Isolation**: Every SQL query dynamically enforces `WHERE clinic_id = :current_tenant_id` at the database repository layer.
2. **Zero Cross-Tenant Leakage**: Unit and integration tests validate that clinic A users cannot read or modify clinic B patient data.
3. **Database Network Boundaries**: Next.js web pods cannot communicate directly with database ports; all queries pass through authenticated backend API services.

---

## 3. Business Associate Agreement (BAA) Readiness

When deploying on public cloud infrastructure (AWS, GCP, Azure), ensure:
- An active BAA is signed with the cloud provider covering RDS, EKS, S3, KMS, CloudWatch, and ElastiCache.
- Backup encryption keys are rotated annually via KMS key rotation policies.
- Third-party vulnerability scans (Trivy, Bandit, pip-audit) run on every commit in the CI/CD pipeline.
