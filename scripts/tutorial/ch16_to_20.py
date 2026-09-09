# scripts/tutorial/ch16_to_20.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_16_to_20(styles):
    story = []

    # =========================================================================
    # CHAPTER 16: CLINICAL AI ASSISTANT
    # =========================================================================
    story.append(Paragraph("Chapter 16: Clinical AI Assistant & Automated SOAP", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro integrates a clinical AI copilot designed to reduce documentation burden, "
        "synthesize diagnostic narratives, and assist in treatment estimate calculations.",
        styles["TutorialBody"]
    ))

    ai_features = [
        ["Automated SOAP Note Synthesis", "Converts raw dentist shorthand or dictation into structured, medico-legally sound clinical notes."],
        ["Radiographic Finding Suggestions", "Assists clinicians by cross-referencing marked odontogram pathologies with typical restorative protocols."],
        ["Appointment No-Show Prediction", "Predictive ML models analyze patient historical attendance to flag high-risk no-shows for proactive confirmation."],
        ["Smart Treatment Cost Estimates", "Calculates complex insurance deductibles and copayment tier estimates based on payer history."],
    ]
    story.append(make_table(["AI Capability", "Operational Impact on Clinical Practice"], ai_features, col_widths=[150, 365], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Clinical Guardrails & Human-In-The-Loop",
        "The AI Assistant acts strictly as an assistive tool. It cannot sign off treatments, prescribe medications, or submit claims "
        "without explicit review and cryptographic authorization by a licensed dentist.",
        "warning",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 17: MULTI-CLINIC & DSO ADMINISTRATION
    # =========================================================================
    story.append(Paragraph("Chapter 17: Multi-Branch & DSO Administration", styles["ChapterHeading"]))
    story.append(Paragraph(
        "For Dental Support Organizations (DSOs) and multi-location practices, DentalCare Pro provides hierarchical "
        "management spanning corporate headquarters, regional networks, and individual clinic branches.",
        styles["TutorialBody"]
    ))

    dso_rows = [
        ["Corporate Hierarchy Modeling", "Organizes practice networks into Organization $\rightarrow$ Regional Hub $\rightarrow$ Branch Clinic."],
        ["Centralized Supply Procurement", "Master warehouse purchases supplies in bulk and dispatches inter-branch inventory transfers."],
        ["Inter-Branch Patient Record Transfer", "Securely transfers complete patient history, radiographs, and balances between clinics with audit logs."],
        ["Multi-Branch Financial Consolidation", "Consolidates P&L, collections, and dentist production across all branch locations on a single screen."],
    ]
    story.append(make_table(["DSO Management Layer", "Enterprise Multi-Branch Functionality"], dso_rows, col_widths=[160, 355], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 18: HR & AUTOMATED PAYROLL
    # =========================================================================
    story.append(Paragraph("Chapter 18: HR, Attendance & Automated Payroll", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The HR module manages staff shifts, biometric timeclock tracking, leave entitlements, "
        "and automated gross-to-net payroll processing with statutory deductions.",
        styles["TutorialBody"]
    ))

    hr_rows = [
        ["Shift & Schedule Management", "Defines clinic operating shifts (Morning, Evening, Weekend) with staff role allocations."],
        ["Biometric Time & Attendance", "Tracks clock-in/out timestamps via biometric hardware scanners with tardiness and overtime calculations."],
        ["Leave Request & Approval", "Staff submit annual, sick, and maternity leave requests through self-service portal with manager approval."],
        ["Automated Payroll Processing", "Calculates basic pay, overtime, bonuses, dentist procedure commissions, taxes, and pension deductions."],
        ["Digital Pay Slips", "Generates itemized PDF salary slips accessible securely through staff mobile self-service."],
    ]
    story.append(make_table(["HR / Payroll Feature", "Administrative Capabilities"], hr_rows, col_widths=[145, 370], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 19: MOBILE APPLICATIONS
    # =========================================================================
    story.append(Paragraph("Chapter 19: Mobile Applications (Dentist, Receptionist, Patient)", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro provides a unified Flutter cross-platform mobile suite available on Android and iOS, "
        "featuring tailored role-specific experiences and offline-first data synchronization.",
        styles["TutorialBody"]
    ))

    mob_rows = [
        ["Dentist Mobile App", "Chairside agenda, 32-tooth odontogram review, intraoral camera photo upload, and instant SOAP note dictation."],
        ["Receptionist Mobile App", "Rapid QR code patient check-in scanner, live waiting room queue triage, and contactless mobile billing."],
        ["Patient Mobile Portal", "Appointment self-booking, digital consent form signing, treatment progress review, and invoice payments."],
        ["Offline-First Architecture", "Local SQLite database caches records; mutations are queued locally and synchronized automatically upon reconnect."],
        ["Biometric Unlock & Push Alerts", "FaceID / TouchID biometric hardware unlock, APNs and FCM push notifications for chair calls."],
    ]
    story.append(make_table(["Mobile App Feature", "Technical Implementation & User Experience"], mob_rows, col_widths=[145, 370], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 20: SYSTEM ADMINISTRATION & MAINTENANCE
    # =========================================================================
    story.append(Paragraph("Chapter 20: System Administration & Health Monitoring", styles["ChapterHeading"]))
    story.append(Paragraph(
        "System administrators manage global configuration parameters, database connection pools, audit logs, "
        "and telemetry alerts.",
        styles["TutorialBody"]
    ))

    sys_rows = [
        ["System Settings & Branding", "Configure clinic logos, currency codes, date formats, tooth notation systems, and email/SMS templates."],
        ["Audit Log Inspection", "Searchable, tamper-evident log capturing timestamp, user ID, IP address, and exact action for every PHI access."],
        ["Service Health Checks", "Real-time automated status monitors for PostgreSQL, Redis, Celery workers, and S3 storage at /api/health."],
        ["Connection Pool Monitoring", "Monitors PgBouncer active and waiting connections to prevent database connection exhaustion."],
    ]
    story.append(make_table(["Admin Capability", "System Operational Scope"], sys_rows, col_widths=[145, 370], styles=styles))

    story.append(PageBreak())
    return story
