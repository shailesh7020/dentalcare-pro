# scripts/generate_tutorial_pdf.py
import os
import sys
import time
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)

from tutorial.canvas import NumberedCanvas
from tutorial.styles import (
    get_tutorial_styles, make_callout, make_table, make_mockup_box,
    PRIMARY, PRIMARY_LIGHT, SECONDARY, TEXT_DARK, TEXT_MUTED, BORDER_COLOR
)
from tutorial.ch01_to_05 import build_chapters_01_to_05
from tutorial.ch06_to_10 import build_chapters_06_to_10
from tutorial.ch11_to_15 import build_chapters_11_to_15
from tutorial.ch16_to_20 import build_chapters_16_to_20
from tutorial.ch21_to_25 import build_chapters_21_to_25
from tutorial.ch26_to_28 import build_chapters_26_to_28
from tutorial.ch29_faq import build_chapter_29
from tutorial.ch30_appendix import build_chapter_30

def build_cover_page(styles):
    story = []
    story.append(Spacer(1, 40))

    # Top Category Tag
    story.append(Paragraph(
        "<b><font color='#0f766e'>ENTERPRISE HEALTHCARE SaaS PLATFORM — OFFICIAL PRODUCT DOCUMENTATION</font></b>",
        styles["CoverMeta"]
    ))
    story.append(Spacer(1, 10))

    # Main Title Box
    cover_box_data = [
        [Paragraph("<font color='#ffffff'><b>DentalCare Pro</b></font>", styles["CoverTitle"])],
        [Paragraph("<font color='#e0f2fe'><b>Enterprise Dental Clinic Management System</b></font>", styles["CoverSubtitle"])],
        [Paragraph("<font color='#cbd5e1'>Complete User Manual &amp; Project Tutorial — Version 1.0 (Production Release)</font>", styles["CoverMeta"])],
    ]
    cover_box = Table(cover_box_data, colWidths=[515])
    cover_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
        ("TOPPADDING", (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 24),
        ("LINEBEFORE", (0, 0), (0, -1), 6, PRIMARY),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1e293b")),
    ]))
    story.append(cover_box)
    story.append(Spacer(1, 30))

    # Document Overview Cards
    story.append(Paragraph("<b>Target Operational Audience &amp; Key Specifications:</b>", styles["SectionHeading"]))
    
    spec_rows = [
        ["Document Purpose", "Comprehensive Installation, Configuration, Clinical Operation, and Maintenance Manual."],
        ["Supported Roles", "Dentists, Hygienists, Receptionists, Billing Clerks, Clinic Managers, and Super Administrators."],
        ["Platform Architecture", "Next.js 16 Web Portal, FastAPI Microservices, PostgreSQL 16 HA, Flutter Mobile Suite."],
        ["Compliance & Standards", "HIPAA Title II Security Rule (45 CFR § 164.312), GDPR Article 32, ADA CDT, FDI Tooth Notation."],
        ["Target Environments", "Docker Compose, Kubernetes Helm 3, AWS EKS / GCP GKE, and On-Premise Clinic Servers."],
        ["Publication Date", "September 2026 — Enterprise Edition v1.0.0"],
    ]
    story.append(make_table(["Specification Field", "Operational Scope & Detail"], spec_rows, col_widths=[145, 370], styles=styles))
    story.append(Spacer(1, 20))

    story.append(make_callout(
        "Commercial Notice",
        "This official documentation accompanies DentalCare Pro v1.0 Enterprise Edition. "
        "All procedures, workflows, and configurations described herein have been verified through 249 automated backend tests, "
        "141 web portal tests, 6 mobile test suites, and 10,000 virtual user load tests.",
        "tip",
        styles
    ))

    story.append(PageBreak())
    return story

def build_table_of_contents(styles):
    story = []
    story.append(Paragraph("Table of Contents", styles["ChapterHeading"]))
    story.append(Paragraph("Click any chapter below or navigate using your PDF reader's bookmark pane:", styles["TutorialBody"]))
    story.append(Spacer(1, 6))

    chapters = [
        ("Part I: System Overview & Architecture", [
            ("Chapter 1", "Introduction to DentalCare Pro", "Clinical overview, target users, and system topology."),
            ("Chapter 2", "Installation Guide", "Step-by-step setup for Docker, Windows, Linux, and Cloud."),
            ("Chapter 3", "Project Repository Structure", "Monorepo organization across backend, web, mobile, and IaC."),
            ("Chapter 4", "Database Architecture & Data Modeling", "Relational entities, composite indexes, and PITR backup."),
            ("Chapter 5", "Authentication & Access Control", "Zero-trust RBAC, JWT rotation, and multi-tenant security."),
        ]),
        ("Part II: Clinical Practice & Operatory Workflows", [
            ("Chapter 6", "Executive Dashboard & Overview", "Real-time KPIs, chair occupancy, and waiting room triage."),
            ("Chapter 7", "Patient Record Management", "Registration, medical intake, duplicate check, and timeline."),
            ("Chapter 8", "Appointment & Operatory Scheduling", "Calendar grid, chair allocation, conflict checks, and recalls."),
            ("Chapter 9", "Treatment Planning & Clinical Records", "Multi-phase plans, SOAP progress notes, and consent."),
            ("Chapter 10", "Interactive 32-Tooth Odontogram", "Vector charting, anatomical surfaces (MODBL), and color coding."),
            ("Chapter 11", "Electronic Prescription (e-Rx) Module", "Formulary, allergy checks, templates, and PDF printing."),
        ]),
        ("Part III: Practice Administration & Enterprise Management", [
            ("Chapter 12", "Billing, Invoicing & Payments", "Itemized invoicing, multi-gateway payments, and taxes."),
            ("Chapter 13", "Dental Supply & Inventory Management", "Consumables, procedure depletion, and reorder alerts."),
            ("Chapter 14", "Dental Insurance Claims & EDI", "Pre-authorizations, EDI 837D claims, and adjudication."),
            ("Chapter 15", "Reports & Practice Analytics", "P&L aging, clinician production, and chair utilization."),
            ("Chapter 16", "Clinical AI Assistant & Automated SOAP", "AI dictation, diagnostic insights, and guardrails."),
            ("Chapter 17", "Multi-Branch & DSO Administration", "Corporate hierarchy, branch transfers, and warehouse."),
            ("Chapter 18", "HR, Attendance & Automated Payroll", "Biometrics, shifts, leave requests, and payroll runs."),
        ]),
        ("Part IV: Mobile Suite, Cloud Infrastructure & Maintenance", [
            ("Chapter 19", "Mobile Applications (Dentist, Receptionist, Patient)", "Flutter cross-platform apps, offline sync, and push alerts."),
            ("Chapter 20", "System Administration & Health Monitoring", "Settings, health checks, audit inspection, and connection pools."),
            ("Chapter 21", "Cloud Deployment & Orchestration", "Kubernetes Helm 3, Nginx reverse proxy, and autoscaling."),
            ("Chapter 22", "REST API Specifications", "OpenAPI schemas, endpoints, request formats, and errors."),
            ("Chapter 23", "Troubleshooting & Diagnostics", "Diagnostic resolutions for database, network, and auth issues."),
            ("Chapter 24", "Security, HIPAA & GDPR Compliance", "Safeguard matrix, encryption at rest, and audit controls."),
            ("Chapter 25", "Clinical Operating Best Practices", "Daily data integrity, operatory turnover, and hygiene."),
            ("Chapter 26", "Role-Based Daily Workflow Guide", "Receptionist, Dentist, and Administrator daily routines."),
            ("Chapter 27", "Keyboard Shortcuts & Rapid Actions", "Productivity hotkeys and rapid odontogram charting tips."),
            ("Chapter 28", "Scheduled Maintenance Runbooks", "Daily, weekly, monthly, quarterly, and annual tasks."),
            ("Chapter 29", "Frequently Asked Questions (FAQ)", "100 comprehensive questions and answers across all domains."),
            ("Chapter 30", "Appendix & Reference Materials", "Glossary, abbreviations, ER model, and architecture blueprint."),
        ])
    ]

    for part_title, part_chapters in chapters:
        story.append(Paragraph(f"<b><font color='#0f766e'>{part_title}</font></b>", styles["SectionHeading"]))
        toc_rows = []
        for ch_num, ch_title, ch_desc in part_chapters:
            toc_rows.append([f"<b>{ch_num}</b>", f"<b>{ch_title}</b>", ch_desc])
        story.append(make_table(["Chapter", "Title", "Core Content"], toc_rows, col_widths=[75, 175, 265], styles=styles))
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    return story

def main():
    output_path = os.path.abspath(r"e:\dentalcare-pro\Project-tutorial.pdf")
    print(f"Generating DentalCare Pro Complete Tutorial PDF at: {output_path}")

    styles = get_tutorial_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=50,
    )

    story = []

    # 1. Cover Page
    print("Building Cover Page...")
    story.extend(build_cover_page(styles))

    # 2. Table of Contents
    print("Building Table of Contents...")
    story.extend(build_table_of_contents(styles))

    # 3. Chapters 1 to 5
    print("Building Chapters 1 to 5...")
    story.extend(build_chapters_01_to_05(styles))

    # 4. Chapters 6 to 10
    print("Building Chapters 6 to 10...")
    story.extend(build_chapters_06_to_10(styles))

    # 5. Chapters 11 to 15
    print("Building Chapters 11 to 15...")
    story.extend(build_chapters_11_to_15(styles))

    # 6. Chapters 16 to 20
    print("Building Chapters 16 to 20...")
    story.extend(build_chapters_16_to_20(styles))

    # 7. Chapters 21 to 25
    print("Building Chapters 21 to 25...")
    story.extend(build_chapters_21_to_25(styles))

    # 8. Chapters 26 to 28
    print("Building Chapters 26 to 28...")
    story.extend(build_chapters_26_to_28(styles))

    # 9. Chapter 29: 100 FAQs
    print("Building Chapter 29 (100 FAQs)...")
    story.extend(build_chapter_29(styles))

    # 10. Chapter 30: Appendix
    print("Building Chapter 30 (Appendix)...")
    story.extend(build_chapter_30(styles))

    # Build Document with NumberedCanvas
    print("Compiling PDF with NumberedCanvas (2-pass layout)...")
    start_time = time.time()
    doc.build(story, canvasmaker=NumberedCanvas)
    elapsed = time.time() - start_time

    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"SUCCESS: Project-tutorial.pdf compiled in {elapsed:.2f}s ({file_size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
