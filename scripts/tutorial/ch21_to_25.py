# scripts/tutorial/ch21_to_25.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_21_to_25(styles):
    story = []

    # =========================================================================
    # CHAPTER 21: CLOUD DEPLOYMENT & DEVOPS
    # =========================================================================
    story.append(Paragraph("Chapter 21: Cloud Deployment & Orchestration", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro is cloud-agnostic and fully containerized, ready for deployment on AWS (EKS/RDS), "
        "Google Cloud (GKE/Cloud SQL), Azure (AKS), or on-premise private Kubernetes clusters.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Production Kubernetes (Helm 3) Architecture", styles["SectionHeading"]))
    k8s_rows = [
        ["dentalcare-backend", "FastAPI app deployment (3-20 pods, HPA scaling at 70% CPU/Memory), dumb-init PID 1 supervisor."],
        ["dentalcare-web", "Next.js 16 standalone deployment (2-10 pods, HPA), optimized for static page delivery and server-side rendering."],
        ["dentalcare-worker", "Asynchronous Celery/Redis workers handling email/SMS notifications, AI requests, and report generation."],
        ["ingress-nginx", "Ingress controller terminating TLS 1.3 with automated Let's Encrypt certificates managed via Cert-Manager."],
        ["monitoring-stack", "Prometheus metrics engine, Grafana visual dashboards, Loki log store, and Promtail log collector."],
    ]
    story.append(make_table(["Kubernetes Workload", "Deployment & Autoscaling Characteristics"], k8s_rows, col_widths=[145, 370], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Helm 3 Deployment Commands", styles["SectionHeading"]))
    story.append(make_mockup_box("Terminal - Kubernetes Helm Deployment", [
        "# Install or upgrade DentalCare Pro via Helm",
        "helm upgrade --install dentalcare ./helm/dentalcare \\\\",
        "  --namespace dentalcare --create-namespace \\\\",
        "  -f ./helm/dentalcare/values.prod.yaml",
        "# Verify rollout status",
        "kubectl rollout status deployment/dentalcare-backend -n dentalcare"
    ], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 22: REST API DOCUMENTATION
    # =========================================================================
    story.append(Paragraph("Chapter 22: REST API Specifications", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The DentalCare Pro REST API is fully documented via interactive OpenAPI (Swagger) and Redoc specifications "
        "accessible at `/api/v1/docs` and `/api/v1/redoc`.",
        styles["TutorialBody"]
    ))

    api_endpoints = [
        ["POST /api/v1/auth/login", "Staff & patient authentication. Returns JWT access and refresh token pair."],
        ["GET /api/v1/patients", "Clinic-scoped patient search with filtering (name, phone, status, gender)."],
        ["POST /api/v1/patients", "Patient registration with automated duplicate warning checks."],
        ["GET /api/v1/appointments", "Calendar query retrieving appointments filtered by date range and chair."],
        ["POST /api/v1/appointments", "Books an appointment with atomic double-booking conflict detection."],
        ["GET /api/v1/patients/{id}/odontogram", "Retrieves complete 32-tooth odontogram with condition history."],
        ["POST /api/v1/teeth/{id}/procedures", "Logs clinical restoration, extraction, or endodontic procedure."],
        ["POST /api/v1/billing/invoices", "Generates itemized invoice with procedure CDT codes and taxes."],
        ["POST /api/v1/invoices/{id}/payments", "Records cash/card payment and generates official receipt."],
    ]
    story.append(make_table(["API Endpoint", "Description & Response Specification"], api_endpoints, col_widths=[175, 340], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 23: TROUBLESHOOTING & DIAGNOSTICS
    # =========================================================================
    story.append(Paragraph("Chapter 23: Troubleshooting & Diagnostics", styles["ChapterHeading"]))
    story.append(Paragraph(
        "This chapter provides diagnostic resolutions for common administrative, networking, and database issues.",
        styles["TutorialBody"]
    ))

    trouble_rows = [
        ["HTTP 401 Unauthorized", "JWT access token expired. Client should call /api/v1/auth/refresh or re-authenticate."],
        ["HTTP 403 Forbidden", "Cross-tenant boundary violation or user role lacks required clinical permissions."],
        ["Database Connection Pool Exhaustion", "Verify PgBouncer is running in transaction pooling mode and pool_size is configured."],
        ["ReportLab PDF Generation Hang", "Ensure PDF services are invoked via asyncio.to_thread to avoid event-loop blocking."],
        ["Mobile Push Notifications Failing", "Verify APNs certificate validity in Apple Developer Portal or FCM server key in admin settings."],
    ]
    story.append(make_table(["Symptom / Error", "Root Cause & Remediation Protocol"], trouble_rows, col_widths=[160, 355], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 24: SECURITY & REGULATORY COMPLIANCE
    # =========================================================================
    story.append(Paragraph("Chapter 24: Security, HIPAA & GDPR Compliance", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro enforces comprehensive administrative, physical, and technical safeguards complying with "
        "HIPAA Title II (45 CFR § 164.312) and GDPR Article 32.",
        styles["TutorialBody"]
    ))

    sec_rows = [
        ["Access Control (§ 164.312(a)(1))", "Unique user identification, automatic session logoff after 15 minutes of inactivity."],
        ["Transmission Security (§ 164.312(e)(1))", "TLS 1.3 encryption for all HTTP and WebSocket traffic; HSTS preloaded."],
        ["Encryption at Rest (§ 164.312(a)(2)(iv))", "AES-256 encryption on PostgreSQL tablespaces, backups, and S3 radiograph storage."],
        ["Audit Controls (§ 164.312(b))", "Immutable, tamper-evident audit log recording user, timestamp, IP, and action on all PHI."],
        ["Right to Erasure (GDPR Art. 17)", "Patient anonymization routines for non-clinical identifiable contact data."],
    ]
    story.append(make_table(["Security Safeguard", "Technical Implementation in DentalCare Pro"], sec_rows, col_widths=[165, 350], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 25: CLINICAL PRACTICE BEST PRACTICES
    # =========================================================================
    story.append(Paragraph("Chapter 25: Clinical Operating Best Practices", styles["ChapterHeading"]))
    story.append(Paragraph(
        "To maximize clinical efficiency and maintain legal compliance, practices should adopt the following operational best practices:",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("1. Daily Data Integrity & Backup Hygiene", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Verify automated nightly backup completion every morning via the System Admin dashboard.<br/>"
        "• Perform a quarterly Point-In-Time Recovery (PITR) drill to a staging database.<br/>"
        "• Ensure digital consent signatures are captured before administering local anesthesia or initiating restorative work.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("2. Operatory Chair & Sterilization Turnover", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Receptionists should advance queue status to 'IN_CHAIR' only when the assistant confirms operatory sterilization is complete.<br/>"
        "• Dentists should record tooth condition charts and sign off treatments chairside immediately upon procedure completion.",
        styles["TutorialBody"]
    ))

    story.append(PageBreak())
    return story
