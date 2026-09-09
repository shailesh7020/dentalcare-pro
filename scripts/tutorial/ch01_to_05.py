# scripts/tutorial/ch01_to_05.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_01_to_05(styles):
    story = []

    # =========================================================================
    # CHAPTER 1: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("Chapter 1: Introduction to DentalCare Pro", styles["ChapterHeading"]))
    story.append(Paragraph(
        "<b>DentalCare Pro</b> is an enterprise-grade, cloud-native, AI-assisted Dental Practice Management System (PMS) "
        "and Electronic Dental Record (EDR) platform designed for multi-branch clinic networks, Dental Support Organizations (DSOs), "
        "and solo practitioners. It unifies clinical odontograms, operatory scheduling, patient intake, multi-tier billing, "
        "insurance EDI claim adjudication, supply inventory, human resources, and cross-platform mobile portals.",
        styles["TutorialBody"]
    ))

    story.append(make_callout(
        "Clinical Excellence",
        "DentalCare Pro complies with HIPAA Title II Security Safeguards (45 CFR § 164.312) and GDPR Article 32, "
        "providing tamper-evident PHI audit trails and zero-trust multi-clinic tenancy isolation.",
        "tip",
        styles
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Target Users & Stakeholders", styles["SectionHeading"]))
    story.append(Paragraph("The platform provides role-tailored user interfaces designed for distinct operatory workflows:", styles["TutorialBody"]))

    user_rows = [
        ["Dentist / Specialist", "Chairside 32-tooth odontogram, treatment staging, SOAP notes, e-prescriptions, intraoral imaging."],
        ["Dental Hygienist / Assistant", "Periodontal probing depth recording, operatory chair prep, patient medical intake history."],
        ["Receptionist / Front Desk", "Rapid QR check-in, real-time waiting queue, calendar booking, co-pay collection, recalls."],
        ["Billing & Insurance Clerk", "Itemized dental invoicing, ADA CDT code billing, EDI 837D insurance claims, reconciliation."],
        ["Inventory / Supply Manager", "Central warehouse procurement, minimum threshold alerts, batch expiry tracking, inter-branch transfers."],
        ["Clinic Administrator", "Branch staff onboarding, fee schedules, operatory chair configuration, financial P&L reporting."],
        ["Patient (Mobile & Web)", "Self-service booking, digital consent signatures, treatment history, invoice online payments."],
    ]
    story.append(make_table(["Role", "Primary Responsibilities & Key Workflows"], user_rows, col_widths=[140, 375], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("System Architecture Overview", styles["SectionHeading"]))
    story.append(Paragraph(
        "DentalCare Pro employs a modern 4-tier microservices-ready topology designed for high availability, zero downtime, "
        "and multi-tenant cloud operations:",
        styles["TutorialBody"]
    ))

    arch_rows = [
        ["Web Application Tier", "Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS, TanStack Query v5."],
        ["Core API Services Tier", "FastAPI (Python 3.13), Pydantic v2, Async SQLAlchemy 2.0, Uvicorn, Celery/Worker."],
        ["Database & Cache Tier", "PostgreSQL 16 HA (Patroni / PgBouncer Connection Pooler), Redis 7 (Cache & Queues)."],
        ["Cross-Platform Mobile Tier", "Flutter 3.24, Dart, SQLite Offline Sync Cache, Biometric Auth, APNs & FCM Push."],
        ["Infrastructure & DevOps", "Docker Multi-stage, Kubernetes Helm 3, Terraform IaC, Prometheus, Grafana, Loki."],
    ]
    story.append(make_table(["Architecture Layer", "Underlying Technology & Capabilities"], arch_rows, col_widths=[140, 375], styles=styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Minimum System Requirements", styles["SectionHeading"]))
    req_rows = [
        ["Single Clinic Pilot Server", "4 vCPUs, 16 GB RAM, 100 GB NVMe SSD, Ubuntu 22.04 LTS or Docker 24+"],
        ["Enterprise DSO Cluster (50+ Clinics)", "16 vCPUs, 64 GB RAM, 500 GB Managed PostgreSQL, Kubernetes Cluster with 3 Nodes"],
        ["Clinician Desktop Workstation", "Modern Browser (Chrome 120+, Edge 120+, Firefox 120+, Safari 17+), 1920x1080 display"],
        ["Mobile Tablet / Smartphone", "Android 7.0+ (API 24+) or iOS 15.0+, Biometric Scanner, Camera for intraoral records"],
    ]
    story.append(make_table(["Deployment Environment", "Hardware & Operating System Specifications"], req_rows, col_widths=[150, 365], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 2: INSTALLATION GUIDE
    # =========================================================================
    story.append(Paragraph("Chapter 2: Installation Guide", styles["ChapterHeading"]))
    story.append(Paragraph(
        "This chapter covers step-by-step installation instructions for local development, on-premise clinic servers, "
        "and containerized cloud environments.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Step 1: Prerequisites Verification", styles["SectionHeading"]))
    story.append(Paragraph("Ensure your host environment has Git, Docker Compose, Node.js 20+, and Python 3.12+ installed:", styles["TutorialBody"]))
    story.append(make_mockup_box("Terminal - Prerequisites Check", [
        "docker --version        # Requires Docker 24.0+",
        "docker compose version # Requires Docker Compose v2.20+",
        "node --version          # Requires Node.js v20+ or v22+",
        "python --version        # Requires Python 3.12 or 3.13"
    ], styles=styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Step 2: Automated Docker Compose Deployment (Recommended)", styles["SectionHeading"]))
    story.append(Paragraph(
        "The fastest method to launch DentalCare Pro is using the pre-configured production Docker Compose stack:",
        styles["TutorialBody"]
    ))
    story.append(make_mockup_box("Terminal - Docker Compose Launch", [
        "git clone https://github.com/shailesh7020/dentalcare-pro.git",
        "cd dentalcare-pro",
        "cp backend/.env.example backend/.env",
        "cp apps/web/.env.example apps/web/.env.local",
        "docker compose up -d",
        "# Wait ~30 seconds for database migrations to apply automatically"
    ], styles=styles))
    story.append(Spacer(1, 8))

    story.append(make_callout(
        "Port Bindings",
        "By default, the Web Portal is accessible at http://localhost:3000, the REST API documentation at http://localhost:8000/docs, "
        "and the Grafana Telemetry Dashboard at http://localhost:3001 (admin / admin).",
        "note",
        styles
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Step 3: Manual Bare-Metal Installation (Windows & Linux)", styles["SectionHeading"]))
    story.append(Paragraph("For on-premise clinic servers running bare-metal installations:", styles["TutorialBody"]))
    story.append(make_mockup_box("Terminal - Backend Setup", [
        "cd backend",
        "python -m venv .venv",
        "source .venv/bin/activate  # Windows: .venv/Scripts/activate",
        "pip install -e .",
        "alembic upgrade head",
        "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"
    ], styles=styles))
    story.append(Spacer(1, 6))
    story.append(make_mockup_box("Terminal - Frontend Web Setup", [
        "cd apps/web",
        "pnpm install --frozen-lockfile",
        "pnpm build",
        "pnpm start  # Launches Next.js standalone production server on port 3000"
    ], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 3: PROJECT REPOSITORY STRUCTURE
    # =========================================================================
    story.append(Paragraph("Chapter 3: Project Repository Structure", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro is structured as an enterprise monorepo housing the backend API, Next.js web application, "
        "Flutter cross-platform mobile suite, infrastructure-as-code (IaC), and compliance documentation.",
        styles["TutorialBody"]
    ))

    dir_rows = [
        ["/backend", "FastAPI application: API routers, SQLAlchemy models, Pydantic schemas, Celery tasks, and Pytest suite."],
        ["/apps/web", "Next.js 16 Web Portal: React 19 pages, Tailwind v4 styles, TanStack Query hooks, and Vitest suite."],
        ["/apps/mobile", "Flutter 3.24 mobile application: Dentist, Receptionist, and Patient experiences with SQLite sync."],
        ["/database", "SQL migration scripts, composite indexes, and autovacuum optimization configurations."],
        ["/docker", "Hardened Dockerfiles, Nginx WAF reverse proxy configurations, and health check scripts."],
        ["/helm", "Production Kubernetes Helm 3 charts: Deployments, Services, HPAs, Ingress, and Network Policies."],
        ["/terraform", "Infrastructure as Code: AWS/GCP VPCs, EKS/GKE clusters, RDS PostgreSQL HA, and S3 backup buckets."],
        ["/monitoring", "Telemetry stack: Prometheus scrape configs, Grafana SLO dashboards, Loki, and Alertmanager."],
        ["/docs", "6 comprehensive operation manuals, 8 audit reports, HIPAA runbooks, and REST API specifications."],
    ]
    story.append(make_table(["Directory Path", "Core Components & Architectural Purpose"], dir_rows, col_widths=[110, 405], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Monorepo Principle",
        "Every layer shares consistent domain terminology (CDT dental codes, FDI tooth numbering 11-48, ISO 8601 timestamps), "
        "ensuring seamless interoperability across web, mobile, and backend services.",
        "tip",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 4: DATABASE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("Chapter 4: Database Architecture & Data Modeling", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The relational database schema is built on PostgreSQL 16, enforcing foreign keys, multi-tenant isolation, "
        "and zero-orphan cascading rules.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Core Relational Entities", styles["SectionHeading"]))
    db_rows = [
        ["clinics", "Tenant boundary. Holds practice identity, licensing, tax identifiers, and configuration settings."],
        ["users", "Staff and practitioners. Linked to clinic_id with encrypted passwords (Bcrypt) and assigned roles."],
        ["patients", "Demographic records, emergency contacts, blood group, medical insurance policy IDs."],
        ["appointments", "Operatory bookings, chair allocation, start/end times, status state machine, cancellation reason."],
        ["teeth & surfaces", "32 anatomical adult teeth and 20 primary teeth. Tracks Mesial, Distal, Occlusal, Buccal, Lingual states."],
        ["treatments", "Staged clinical plans, procedure CDT codes, tooth numbers, estimated costs, and dentist sign-offs."],
        ["prescriptions", "e-Rx records: drug names, dosage strength, frequency, duration, dispensing instructions."],
        ["invoices & payments", "Itemized financial ledger: subtotal, dental discounts, taxes, payments captured, balances due."],
        ["inventory_items", "Clinical supplies, SKU, manufacturer, batch numbers, expiration dates, unit stock quantities."],
        ["insurance_claims", "EDI 837D electronic claims, clearinghouse tracking numbers, pre-auth approvals, copays."],
    ]
    story.append(make_table(["Database Table", "Relational Mapping & Clinical Functionality"], db_rows, col_widths=[125, 390], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("High-Impact Production Composite Indexes", styles["SectionHeading"]))
    story.append(Paragraph(
        "DentalCare Pro utilizes composite and partial B-Tree indexes to ensure sub-millisecond query execution even under heavy DSO load:",
        styles["TutorialBody"]
    ))
    idx_rows = [
        ["idx_patients_clinic_name_search", "(clinic_id, last_name, first_name)", "Instant patient directory autocomplete and phone triage."],
        ["idx_appointments_clinic_date_status", "(clinic_id, appointment_date, status)", "Accelerates daily calendar and chair scheduling grids."],
        ["idx_teeth_patient_quadrant", "(patient_id, tooth_number)", "Sub-millisecond retrieval of complete 32-tooth odontogram charts."],
        ["idx_invoices_outstanding_balance", "(clinic_id, balance_due) WHERE balance_due > 0", "Partial index for immediate retrieval of accounts receivable."],
    ]
    story.append(make_table(["Index Identifier", "Columns / Predicate", "Performance Impact"], idx_rows, col_widths=[140, 165, 210], styles=styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Backup & Point-In-Time Recovery (PITR)", styles["SectionHeading"]))
    story.append(Paragraph(
        "PostgreSQL continuous Write-Ahead Log (WAL) archiving guarantees a Recovery Point Objective (RPO) of ≤ 15 minutes. "
        "Ad-hoc snapshots can be executed via:",
        styles["TutorialBody"]
    ))
    story.append(make_mockup_box("Terminal - Database Backup & Restore", [
        "# Trigger automated encrypted backup",
        "bash scripts/backup_postgres.sh",
        "# Restore database to specific UTC point-in-time",
        "bash scripts/restore_pitr.sh '2026-09-09 14:15:00 UTC'"
    ], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: AUTHENTICATION & SECURITY
    # =========================================================================
    story.append(Paragraph("Chapter 5: Authentication & Access Control", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro enforces a zero-trust, role-based access control (RBAC) security framework. "
        "Authentication is stateless using JSON Web Tokens (JWT) with strict cryptographic signature verification.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Role-Based Permission Matrix", styles["SectionHeading"]))
    rbac_rows = [
        ["Super Admin", "Full platform access: Organization management, branch provisioning, global system settings."],
        ["Clinic Admin", "Branch-scoped administrator: Staff onboarding, chair setup, financial reports, fee schedules."],
        ["Dentist", "Clinical authority: Full odontogram charting, treatment planning, prescription sign-off, SOAP notes."],
        ["Hygienist / Assistant", "Clinical support: Periodontal charting, medical intake history, chair prep, dental triage."],
        ["Receptionist", "Front-office: Patient registration, appointment scheduling, waiting queue triage, payment capture."],
        ["Accountant", "Finance only: Invoices, payment reconciliation, insurance claims, financial tax exports."],
        ["Patient", "Portal self-service: View own treatment plans, book appointments, view invoices, make co-payments."],
    ]
    story.append(make_table(["User Role", "Privileges & Clinical Access Boundaries"], rbac_rows, col_widths=[130, 385], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Authentication & Token Rotation Lifecycle", styles["SectionHeading"]))
    story.append(Paragraph(
        "1. **Login**: Client submits email, password, and optional clinic slug to `/api/v1/auth/login`.<br/>"
        "2. **Validation**: Bcrypt verifies password salt against database hash (minimum 12 rounds).<br/>"
        "3. **Token Issuance**: Server returns a short-lived Access Token (15-minute expiry) and a long-lived Refresh Token (7-day expiry).<br/>"
        "4. **API Requests**: Client includes Access Token in HTTP header: `Authorization: Bearer <token>`.<br/>"
        "5. **Token Rotation**: When expired, client submits Refresh Token to `/api/v1/auth/refresh`. The server issues a new key pair and invalidates the prior refresh token.",
        styles["TutorialBody"]
    ))

    story.append(make_callout(
        "Multi-Tenancy Isolation Rule",
        "Every JWT payload contains an immutable clinic_id claim. Even if a user knows the UUID of a patient in another clinic, "
        "all database queries enforce WHERE clinic_id = :token_clinic_id, strictly returning HTTP 403 Forbidden on cross-tenant requests.",
        "important",
        styles
    ))

    story.append(PageBreak())
    return story
