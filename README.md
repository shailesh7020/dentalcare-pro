# DentalCare Pro – Enterprise Dental Practice Management SaaS (v1.0.0)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/shailesh7020/dentalcare-pro)
[![Tests](https://img.shields.io/badge/tests-249%20passed-success.svg)](https://github.com/shailesh7020/dentalcare-pro)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/shailesh7020/dentalcare-pro)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-compliant-blue.svg)](https://github.com/shailesh7020/dentalcare-pro)
[![License](https://img.shields.io/badge/license-Enterprise%20Commercial-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/Flutter-3.24-02569B.svg)](https://flutter.dev/)

**DentalCare Pro** is a modern, AI-powered, cloud-native, multi-branch Electronic Dental Record (EDR) and Dental Practice Management Software (PMS) SaaS platform built for multi-clinic dental networks, enterprise DSOs (Dental Support Organizations), and solo practices.

---

## 🌟 Key Highlights & Capabilities

- **Interactive 32-Tooth & Pediatric Odontogram**: Real-time vector-based tooth chart rendering surfaces (Mesial, Distal, Occlusal, Buccal, Lingual), restorations, crowns, implants, endodontics, and periodontal pocket depth probing.
- **Clinical EHR & Treatment Planning**: Automated diagnosis coding (ICD-10-CM / CDT), staged multi-visit treatment estimates, electronic prescriptions (e-Rx) with drug-interaction checks, and digital patient informed consents with cryptographic signatures.
- **Multi-Branch & DSO Enterprise Administration**: Hierarchical tenant modeling (Organization $\rightarrow$ Region $\rightarrow$ Branch Clinic), inter-branch patient record transfers, centralized supply warehouse management, and branch-level P&L analytics.
- **Automated Billing & Insurance Clearinghouse**: Itemized dental invoices, automated co-pay calculation, real-time insurance eligibility checks, and EDI 837D claim submission and adjudication workflows.
- **Human Resources (HR) & Automated Payroll**: Staff shift scheduling, biometric time tracking, automated gross-to-net payroll runs with tax withholdings, and employee performance reviews.
- **Cross-Platform Mobile Suite (Flutter)**: Unified mobile codebase with tailored role experiences for Dentists (chairside scheduling & charting), Receptionists (rapid QR check-in & queue triage), and Patients (portal booking, treatment review, billing payments).
- **Enterprise Cloud Infrastructure**: Turnkey Kubernetes Helm charts, Terraform IaC, multi-stage Docker containers, PostgreSQL with PgBouncer connection pooling, Prometheus & Grafana observability, and automated disaster recovery drills (RPO $\le$ 15m, RTO $\le$ 1h).

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend Web** | Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS, TanStack Query, Lucide Icons |
| **Backend API** | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Uvicorn, Celery/Worker |
| **Database & Cache** | PostgreSQL 16 (HA with Patroni/PgBouncer), Redis 7 (Caching, Queue, Session Store) |
| **Mobile Apps** | Flutter 3.24, Dart, Provider/Riverpod, Offline SQLite Cache, Biometric Auth, APNs/FCM |
| **Infrastructure** | Docker, Docker Compose, Kubernetes (Helm 3), Terraform (VPC, EKS/GKE, RDS), Nginx |
| **Observability** | Prometheus, Grafana, Loki, Promtail, Alertmanager, OpenTelemetry |
| **Compliance** | HIPAA Security Rule (45 CFR § 164.312), GDPR Article 32, OWASP Top 10 Hardened |

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose v2+
- Node.js 20+ & pnpm
- Python 3.12+
- Git

### 1. Clone & Environment Setup
```bash
git clone https://github.com/shailesh7020/dentalcare-pro.git
cd dentalcare-pro
cp backend/.env.example backend/.env
cp apps/web/.env.example apps/web/.env.local
```

### 2. Launch Full-Stack with Docker Compose
```bash
docker compose up -d
```
The services will be accessible at:
- **Web Application Portal**: http://localhost:3000
- **FastAPI REST API & Docs**: http://localhost:8000/docs
- **Grafana Observability Dashboards**: http://localhost:3001 (admin / admin)
- **Prometheus Metrics Engine**: http://localhost:9090

### 3. Running Test Suites
```bash
# Backend Pytest Suite (249 tests)
cd backend && pytest tests/ -q

# Web Vitest Suite (141 tests)
cd apps/web && npx vitest run

# Next.js 16 Production Build
cd apps/web && npm run build

# Mobile Test Runner (6 suites)
python apps/mobile/test/test_runner.py

# Final SLA Stress Benchmark (10,000 VUs)
python tests/load/final_sla_benchmark.py
```

---

## 📚 Documentation Index

All enterprise operational runbooks and audit reports are located in the [`docs/`](docs/) directory:

- [User Manual](docs/manuals/user_manual.md)
- [Administrator Guide](docs/manuals/admin_guide.md)
- [Developer Guide](docs/manuals/developer_guide.md)
- [REST API Reference](docs/manuals/api_reference.md)
- [System Architecture Documentation](docs/manuals/architecture_documentation.md)
- [Troubleshooting & Diagnostics Playbook](docs/manuals/troubleshooting_guide.md)
- [Security & OWASP Audit Report](docs/reports/security_audit_report.md)
- [Performance & SLA Benchmark Report](docs/reports/performance_benchmark_report.md)
- [HIPAA & GDPR Compliance Gap Analysis](docs/reports/compliance_gap_analysis.md)
- [Deployment Runbook](docs/ops/deployment_guide.md)
- [Disaster Recovery & PITR Runbook](docs/ops/backup_and_recovery_runbook.md)

---

## 🛡️ Security & Compliance

DentalCare Pro strictly enforces healthcare privacy and security safeguards:
- **Zero-Trust Multi-Tenancy**: Tenant database boundaries enforced at both query and middleware layers.
- **Encryption at Rest & in Transit**: TLS 1.3 for all endpoints, AES-256 for PostgreSQL tablespaces and backups.
- **Audit Logging**: Immutable, tamper-evident audit trails for every PHI (Protected Health Information) access event.
- **Role-Based Access Control (RBAC)**: Fine-grained permissions across Super Admin, Clinic Owner, Dentist, Hygienist, Receptionist, Accountant, and Patient roles.

---

## 📄 License & Commercial Support

DentalCare Pro is licensed under the [Enterprise Commercial License](LICENSE).  
For enterprise licensing, dedicated cloud hosting, or HIPAA Business Associate Agreements (BAA), contact [licensing@dentalcarepro.com](mailto:licensing@dentalcarepro.com).
