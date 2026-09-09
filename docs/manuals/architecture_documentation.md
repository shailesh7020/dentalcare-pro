# DentalCare Pro - Enterprise System Architecture & Engineering Blueprint

## 1. Architectural Philosophy
DentalCare Pro is engineered according to the following foundational tenets:
1. **Cloud-Native & Modular**: Deployable to any major cloud provider (AWS, GCP, Azure) or bare-metal Kubernetes.
2. **Zero-Trust Multi-Tenancy**: Complete logical separation between dental practices, organizations, and clinics.
3. **Offline-First Resilience**: Full chairside operational capability during cloud or internet outages.
4. **Strict Regulatory Compliance**: Built-in HIPAA Security Rule technical safeguards, GDPR data protection, and immutable audit streaming.

---

## 2. High-Level Architecture Diagram

```mermaid
graph TD
    UserWeb[Clinician Next.js 16 Web App] -->|HTTPS / WSS| Ingress[Ingress Controller - TLS 1.3 & Rate Limiting]
    UserMobile[Patient & Dentist Flutter App] -->|HTTPS / REST| Ingress

    subgraph EKS_Cluster["Kubernetes Cluster (EKS / GKE)"]
        Ingress --> WebSvc[Next.js Web Service Pods]
        Ingress --> ApiSvc[FastAPI Backend Microservice Cluster]
        
        ApiSvc --> WorkerSvc[Background Task Queue Workers]
        ApiSvc --> Telemetry[Prometheus Metrics Exporter :8000/metrics]
    end

    subgraph Persistence_Tier["High Availability Persistence Tier"]
        ApiSvc --> PgBouncer[PgBouncer Connection Pooler :6432]
        WorkerSvc --> PgBouncer
        PgBouncer --> PG_Primary[(PostgreSQL 17 Primary Multi-AZ)]
        PG_Primary -.->|Streaming Replication| PG_Standby[(PostgreSQL 17 Read Standby)]
        PG_Primary -->|Continuous WAL Stream| S3_WAL[Encrypted Object Storage - AES-256]
        
        ApiSvc --> RedisCluster[(Redis 7 In-Memory Cache & Distributed Lock)]
        WorkerSvc --> RedisCluster
    end
```

---

## 3. Data Architecture & Entity Relationship Summary

The schema consists of over 50 normalized relational entities structured across domains:
- **Identity & Organization**: `organizations`, `regions`, `clinics`, `users`, `departments`, `user_branch_assignments`.
- **Patient Health Records**: `patients`, `medical_histories`, `dental_histories`, `patient_timeline_events`, `consent_records`.
- **Clinical Dentistry**: `appointments`, `chairs`, `treatments`, `treatment_procedures`, `treatment_follow_ups`, `teeth`, `tooth_surfaces`.
- **Pharmacy & Billing**: `prescriptions`, `prescription_items`, `invoices`, `invoice_items`, `payments`.
- **Insurance & Claims**: `insurance_providers`, `insurance_plans`, `patient_insurance_policies`, `insurance_claims`.
- **Workforce & HR**: `employees`, `work_shifts`, `attendance_records`, `leave_requests`, `payroll_runs`, `payslips`.
- **Audit & Telemetry**: `audit_events`, `ai_audit_logs`.
