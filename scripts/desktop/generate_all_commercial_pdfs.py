# scripts/desktop/generate_all_commercial_pdfs.py
"""
DentalCare Pro - Commercial Release PDF Generator Suite
Generates 9 publication-grade PDF manuals and guides using ReportLab:
1. README FIRST.pdf
2. User Manual.pdf
3. Administrator Guide.pdf
4. Reception Guide.pdf
5. Dentist Guide.pdf
6. Backup Guide.pdf
7. Troubleshooting Guide.pdf
8. License.pdf
9. Release Notes.pdf

And Extras/ Clinical Materials:
- Adult & Pediatric Dental Tooth Chart.pdf
- Dental Emergency Triage Cheat Sheet.pdf
- Daily Opening and Closing Checklist.pdf
- Patient Intake Registration Form (Printable).pdf
- Appointment SMS and WhatsApp Templates.txt
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_DIR = Path(r"e:\dentalcare-pro\Dental Clinic Management Gift")
EXTRAS_DIR = OUTPUT_DIR / "Extras"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EXTRAS_DIR.mkdir(parents=True, exist_ok=True)

# Color Palette
PRIMARY = colors.HexColor("#0f2942")      # Deep Medical Navy
SECONDARY = colors.HexColor("#00a4bd")    # Dental Cyan / Teal
ACCENT = colors.HexColor("#0284c7")       # Healthcare Blue
SUCCESS = colors.HexColor("#059669")      # Medical Green
WARNING = colors.HexColor("#d97706")      # Amber
DANGER = colors.HexColor("#dc2626")       # Red
DARK = colors.HexColor("#1e293b")         # Slate Dark
MUTED = colors.HexColor("#64748b")        # Slate Gray
LIGHT_BG = colors.HexColor("#f8fafc")     # Light Canvas
CARD_BG = colors.HexColor("#f1f5f9")      # Card Background
BORDER = colors.HexColor("#cbd5e1")       # Border


def get_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["DocTitle"] = ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=3,
    )
    styles["DocSubtitle"] = ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=10,
    )
    styles["SectionHeading"] = ParagraphStyle(
        name="SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
    )
    styles["SubHeading"] = ParagraphStyle(
        name="SubHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=ACCENT,
        spaceBefore=6,
        spaceAfter=2,
    )
    styles["BodyTextCustom"] = ParagraphStyle(
        name="BodyTextCustom",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=DARK,
        spaceAfter=4,
    )
    styles["CalloutText"] = ParagraphStyle(
        name="CalloutText",
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=DARK,
    )
    styles["TableHead"] = ParagraphStyle(
        name="TableHead",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
    )
    styles["TableCell"] = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=DARK,
    )
    styles["TableCellBold"] = ParagraphStyle(
        name="TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10.5,
        textColor=DARK,
    )
    return styles


def create_callout(text: str, title: str = "IMPORTANT NOTE", border_color=ACCENT, bg_color=LIGHT_BG):
    styles = get_styles()
    content = [
        Paragraph(f"<b>{title}</b>", styles["SubHeading"]),
        Paragraph(text, styles["CalloutText"]),
    ]
    t = Table([[content]], colWidths=[520])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 1, border_color),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    return t


# ==============================================================================
# 1. README FIRST.pdf
# ==============================================================================
def generate_readme_first():
    pdf_path = OUTPUT_DIR / "README FIRST.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro Enterprise v23.0", styles["DocTitle"]))
    story.append(Paragraph("Master Quick-Start, Installation & Clinical Operation Guide", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph(
        "Welcome to <b>DentalCare Pro</b>! This software is a standalone commercial practice management system designed "
        "specifically for dental clinics. It runs 100% on your local Windows clinic PC without requiring any technical configuration, "
        "command-line terminals, or third-party cloud subscriptions.",
        styles["BodyTextCustom"]
    ))

    # Prerequisites Table
    story.append(Paragraph("1. System Requirements & Compatibility", styles["SectionHeading"]))
    req_data = [
        [Paragraph("Component", styles["TableHead"]), Paragraph("Minimum Specification", styles["TableHead"]), Paragraph("Recommended Specification", styles["TableHead"])],
        [Paragraph("Operating System", styles["TableCellBold"]), Paragraph("Windows 10 64-bit (Build 1909+)", styles["TableCell"]), Paragraph("Windows 11 64-bit (Pro / Enterprise)", styles["TableCell"])],
        [Paragraph("Processor (CPU)", styles["TableCellBold"]), Paragraph("Intel Core i3 / AMD Ryzen 3 (2.0 GHz)", styles["TableCell"]), Paragraph("Intel Core i5 / AMD Ryzen 5 (4+ Cores)", styles["TableCell"])],
        [Paragraph("Memory (RAM)", styles["TableCellBold"]), Paragraph("4 GB RAM", styles["TableCell"]), Paragraph("8 GB RAM or higher", styles["TableCell"])],
        [Paragraph("Disk Storage", styles["TableCellBold"]), Paragraph("2 GB free space (SSD)", styles["TableCell"]), Paragraph("20 GB free space (for radiographs)", styles["TableCell"])],
        [Paragraph("Display Resolution", styles["TableCellBold"]), Paragraph("1366 x 768 pixels", styles["TableCell"]), Paragraph("1920 x 1080 (Full HD) or higher", styles["TableCell"])],
        [Paragraph("Printers Supported", styles["TableCellBold"]), Paragraph("Standard Windows Printer", styles["TableCell"]), Paragraph("A4 Laser + 80mm / 58mm Thermal POS", styles["TableCell"])],
    ]
    t_req = Table(req_data, colWidths=[120, 200, 200])
    t_req.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_req)
    story.append(Spacer(1, 8))

    # Installation Steps
    story.append(Paragraph("2. Simple 3-Step Setup", styles["SectionHeading"]))
    steps_data = [
        [Paragraph("Step 1", styles["TableCellBold"]), Paragraph("Double-click <b>Setup.exe</b> in this folder. Click <b>Yes</b> on the Windows prompt to launch the guided wizard.", styles["TableCell"])],
        [Paragraph("Step 2", styles["TableCellBold"]), Paragraph("The installer automatically verifies Windows, disk space, and PostgreSQL on port 5432. Click <b>Next</b>.", styles["TableCell"])],
        [Paragraph("Step 3", styles["TableCellBold"]), Paragraph("Click <b>Install</b>. When complete, click <b>Finish</b> to immediately launch DentalCare Pro on your desktop.", styles["TableCell"])],
    ]
    t_steps = Table(steps_data, colWidths=[60, 460])
    t_steps.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), SECONDARY),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_steps)
    story.append(Spacer(1, 8))

    # First Login Callout
    story.append(create_callout(
        "<b>Default Login URL:</b> http://localhost:3000 (Desktop App launches automatically)<br/>"
        "<b>Administrator Email:</b> admin@dentalcare.com<br/>"
        "<b>Initial Password:</b> Admin@123456<br/>"
        "<i>Security Recommendation: Change your password on your first session under Settings &gt; Security.</i>",
        title="FIRST LOGIN CREDENTIALS",
        border_color=SUCCESS,
        bg_color=colors.HexColor("#f0fdf4")
    ))
    story.append(Spacer(1, 8))

    # Core Workflow & Daily Checklist
    story.append(Paragraph("3. Daily Clinic Operations Workflow", styles["SectionHeading"]))
    workflow_data = [
        [Paragraph("Patient Registration", styles["TableCellBold"]), Paragraph("Search by phone number or click '+ New Patient' to register records with medical alerts and insurance.", styles["TableCell"])],
        [Paragraph("Appointment Booking", styles["TableCellBold"]), Paragraph("Click any time slot on the Chair Calendar (Chairs 1-4) to book, reschedule, or check in patients.", styles["TableCell"])],
        [Paragraph("Clinical Odontogram", styles["TableCellBold"]), Paragraph("Open the tooth chart to record cavities, restorations, root canals, or extractions with 1 click.", styles["TableCell"])],
        [Paragraph("Invoicing & Printing", styles["TableCellBold"]), Paragraph("Generate official patient bills. Print to A4 laser or 80mm thermal receipt printer with clinic logo.", styles["TableCell"])],
        [Paragraph("Automated Backups", styles["TableCellBold"]), Paragraph("Runs automatically every night at 23:00 to <code>C:\\DentalCarePro_Backups\\</code>. AES-256 encrypted.", styles["TableCell"])],
    ]
    t_wf = Table(workflow_data, colWidths=[130, 390])
    t_wf.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CARD_BG, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_wf)
    story.append(Spacer(1, 8))

    # Support Hotline
    story.append(create_callout(
        "<b>Priority Technical Email:</b> support@dentalcarepro.com<br/>"
        "<b>Toll-Free Helpline:</b> 1-800-555-DENT (3368)<br/>"
        "<b>Disaster Recovery:</b> Double-click <code>Backup Utility/restore_backup.bat</code> anytime to restore your practice.",
        title="CLINIC SUPPORT & DISASTER RECOVERY",
        border_color=PRIMARY,
        bg_color=colors.HexColor("#eff6ff")
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 2. User Manual.pdf
# ==============================================================================
def generate_user_manual():
    pdf_path = OUTPUT_DIR / "User Manual.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - User Manual", styles["DocTitle"]))
    story.append(Paragraph("Comprehensive Clinical & Staff Operational Handbook", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("Chapter 1: Workstation Navigation & Shortcuts", styles["SectionHeading"]))
    story.append(Paragraph(
        "DentalCare Pro features an enterprise interface optimized for rapid clinical entry:<br/>"
        "• <b>Universal Command Palette:</b> Press <code>Ctrl + K</code> from any screen to search patients, jump to chair schedules, or open invoices instantly.<br/>"
        "• <b>Collapsible Dark Sidebar:</b> Minimizes for maximum clinical charting space on operatory touch monitors.<br/>"
        "• <b>Station Role Switcher:</b> Switch between Reception, Dentist, and Administrator view modes depending on which computer you are using.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("Chapter 2: Managing Patients & Medical Histories", styles["SectionHeading"]))
    story.append(Paragraph(
        "Each patient record maintains complete medical records, drug allergies, emergency contacts, and dental insurance:<br/>"
        "• <b>Allergy Highlighting:</b> Penicillin, Latex, Aspirin, and Sulfa allergies are prominently flagged in red on all operatory screens.<br/>"
        "• <b>Document Repository:</b> Attach intraoral camera photographs, scans, and PDFs with automatic malware filtering.<br/>"
        "• <b>Communication Log:</b> Review appointment history, automated SMS reminder delivery status, and recall notes.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("Chapter 3: Interactive Dental Odontogram & Treatments", styles["SectionHeading"]))
    story.append(Paragraph(
        "The odontogram represents FDI adult teeth (11-48) and pediatric deciduous teeth (51-85):<br/>"
        "• <b>Condition Tagging:</b> Click tooth surfaces (Mesial, Distal, Occlusal, Lingual, Facial) to record caries or existing amalgams/composites.<br/>"
        "• <b>Procedure Entry:</b> Select from ADA/CDT procedure codes (Cleaning, Extraction, Crown, Root Canal) with automatic fee calculation.<br/>"
        "• <b>Treatment Estimates:</b> Print multi-phase treatment plans with estimated patient insurance co-pays.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("Chapter 4: Billing, Invoicing & Receipts", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>Multiple Payment Modes:</b> Supports Cash, Credit Card, UPI, Bank Transfer, and Insurance claims.<br/>"
        "• <b>Dual Print Modes:</b> 1-click A4 Laser Invoices for insurance claims, or 80mm / 58mm Thermal POS Slips for immediate patient checkout.<br/>"
        "• <b>Digital Verification QR:</b> Invoices include cryptographically verifiable QR codes for patient tax audits.",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 3. Administrator Guide.pdf
# ==============================================================================
def generate_admin_guide():
    pdf_path = OUTPUT_DIR / "Administrator Guide.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Administrator Guide", styles["DocTitle"]))
    story.append(Paragraph("Practice Configuration, Security, Multi-Chair LAN & RBAC Setup", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("1. Practice Profile & Operatory Management", styles["SectionHeading"]))
    story.append(Paragraph(
        "As the practice administrator, configure clinic parameters under <b>Settings &gt; Clinic Profile</b>:<br/>"
        "• <b>Operatory Chairs:</b> Define dental chair names (e.g., Chair 1 - Hygiene, Chair 2 - Restorative, Chair 3 - Surgery, Chair 4 - Ortho).<br/>"
        "• <b>Clinic Operating Hours:</b> Configure opening/closing times per weekday. Appointments outside hours will be flagged.<br/>"
        "• <b>Taxes & Currency:</b> Configure your currency symbol ($ / £ / € / ₹) and dental service tax exemptions.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("2. Staff Accounts & Role-Based Access Control (RBAC)", styles["SectionHeading"]))
    rbac_data = [
        [Paragraph("User Role", styles["TableHead"]), Paragraph("Permissions & Access Scope", styles["TableHead"]), Paragraph("Recommended Computer", styles["TableHead"])],
        [Paragraph("Administrator", styles["TableCellBold"]), Paragraph("Full practice management, user creation, tax setup, logs, backup & restore.", styles["TableCell"]), Paragraph("Owner / Office Manager PC", styles["TableCell"])],
        [Paragraph("Dentist", styles["TableCellBold"]), Paragraph("Patient charts, Odontogram, clinical notes, prescriptions, treatment plans.", styles["TableCell"]), Paragraph("Operatory Chair PCs (1-4)", styles["TableCell"])],
        [Paragraph("Hygienist", styles["TableCellBold"]), Paragraph("Periodontal charting, cleanings, prophylaxis, oral hygiene records.", styles["TableCell"]), Paragraph("Hygiene Suite PC", styles["TableCell"])],
        [Paragraph("Receptionist", styles["TableCellBold"]), Paragraph("Patient scheduling, intake, billing, payments, receipt printing.", styles["TableCell"]), Paragraph("Front Desk Reception PC", styles["TableCell"])],
    ]
    t_rbac = Table(rbac_data, colWidths=[90, 310, 120])
    t_rbac.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_rbac)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Multi-Workstation Clinic LAN Deployment", styles["SectionHeading"]))
    story.append(Paragraph(
        "DentalCare Pro supports multi-computer clinic LAN operation over Wi-Fi or Ethernet:<br/>"
        "1. <b>Host Server PC (Reception):</b> Installs DentalCare Pro with PostgreSQL database.<br/>"
        "2. <b>Operatory PCs (Chairs):</b> Connect to Host PC IP address (e.g., <code>http://192.168.1.100:3000</code>).<br/>"
        "3. <b>Live Sync:</b> All appointments and charts synchronize in real time over WebSockets with zero lag.",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 4. Reception Guide.pdf (NEW!)
# ==============================================================================
def generate_reception_guide():
    pdf_path = OUTPUT_DIR / "Reception Guide.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Receptionist Front Desk Guide", styles["DocTitle"]))
    story.append(Paragraph("Daily Check-In, Scheduling, Billing, Invoicing & Patient Checkout", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("1. Morning Front Desk Opening Routine", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Turn on the reception workstation and double-click the <b>DentalCare Pro</b> desktop icon.<br/>"
        "• Log in using your receptionist username and password.<br/>"
        "• Open the <b>Appointment Calendar</b> to review today's patient arrivals, provider schedules, and operatory chair allocations.<br/>"
        "• Verify that the thermal POS receipt printer and A4 laser printer are powered on and loaded with paper.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("2. Fast Patient Registration & Intake", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>New Patients:</b> Click <code>+ Add Patient</code> (or press <code>Ctrl + K</code> and type 'new'). Enter Full Name, Phone, Date of Birth, and Emergency Contact.<br/>"
        "• <b>Medical Alert Capture:</b> Ask patient for any drug allergies (e.g. Penicillin, Latex) and medical conditions (Hypertension, Diabetes, Pregnancy). These appear in bright red badges on clinician screens.<br/>"
        "• <b>Insurance Details:</b> Record insurance provider and policy number for claim reimbursement billing.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("3. Managing Appointments & Waiting Queue", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>Checking In:</b> When patient enters clinic, click their appointment card and select <b>Check In</b>. Status changes to 'Waiting'.<br/>"
        "• <b>Seating in Chair:</b> When dentist is ready, move status to <b>In Chair</b>. Operatory dentist screen updates immediately.<br/>"
        "• <b>Rescheduling & Cancellations:</b> Drag and drop appointments to new time slots. System automatically checks for doctor/chair conflicts.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("4. Patient Billing, Payments & Thermal Printing", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>Generating Bill:</b> When appointment completes, click <b>Create Invoice</b>. Completed procedures auto-populate from the doctor's odontogram.<br/>"
        "• <b>Recording Payment:</b> Enter payment amount and choose payment mode: Cash, Credit/Debit Card, UPI, or Dental Insurance.<br/>"
        "• <b>Thermal Slip Printing:</b> Click <b>Print Receipt</b> for an instant 80mm thermal slip with clinic branding, doctor name, and tax breakdown.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("5. Evening Closing & Cash Drawer Reconciliation", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Go to <b>Billing &gt; Daily Summary</b> to view total collections split by Cash, Card, and UPI.<br/>"
        "• Reconcile cash in register with the software total. Report any discrepancies to the clinic owner.<br/>"
        "• Lock the reception workstation before leaving. The automated daily backup triggers automatically at 23:00.",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 5. Dentist Guide.pdf (NEW!)
# ==============================================================================
def generate_dentist_guide():
    pdf_path = OUTPUT_DIR / "Dentist Guide.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Dentist & Clinical Staff Guide", styles["DocTitle"]))
    story.append(Paragraph("Odontogram Charting, Periodontal Exams, Treatment Plans & Rx", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("1. Operatory Chair Station View", styles["SectionHeading"]))
    story.append(Paragraph(
        "• When logged in as a Dentist, your interface automatically focuses on the current chair's active patient.<br/>"
        "• High-visibility alert badges display patient medical conditions (e.g. Heart Murmur, Anticoagulant Therapy, Latex Allergy).<br/>"
        "• Medical histories and previous radiographic images can be reviewed side-by-side with the active dental chart.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("2. Interactive Dental Odontogram (Adult & Pediatric)", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>Dual Arch System:</b> Switch between 32 adult permanent teeth and 20 primary pediatric deciduous teeth.<br/>"
        "• <b>5-Surface Caries Mapping:</b> Click specific tooth surfaces (Mesial, Distal, Occlusal, Buccal/Facial, Lingual) to flag decay.<br/>"
        "• <b>Color-Coded Status:</b><br/>"
        "  - <font color='#dc2626'><b>Red:</b></font> Active Caries / Cavity Requiring Restoration<br/>"
        "  - <font color='#0284c7'><b>Blue:</b></font> Existing Sound Restoration (Amalgam / Composite Resin)<br/>"
        "  - <font color='#d97706'><b>Gold/Amber:</b></font> Prosthetic Crown / Fixed Partial Denture<br/>"
        "  - <font color='#9333ea'><b>Purple:</b></font> Endodontic Obturation / Root Canal Treated<br/>"
        "  - <font color='#64748b'><b>Gray 'X':</b></font> Extracted / Missing / Unerupted Tooth",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("3. Periodontal Examination Charting", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Record 6-point probing depths per tooth (Distobuccal, Midbuccal, Mesiobuccal, Distolingual, Midlingual, Mesiolingual).<br/>"
        "• Depths exceeding 4mm are flagged in red. Toggle Bleeding on Probing (BOP) and Furcation involvement.<br/>"
        "• Generates historical comparison graphs to demonstrate periodontal healing to patients.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("4. Treatment Planning & Estimates", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Group procedures into Phased Plans (Phase 1: Emergency & Pain Relief; Phase 2: Restorative; Phase 3: Prosthetics).<br/>"
        "• Prints professional Treatment Plan Estimates with estimated insurance coverage for patient consent prior to starting work.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("5. Digital Prescriptions & Medical Certificates", styles["SectionHeading"]))
    story.append(Paragraph(
        "• Select pre-configured dental medications (Amoxicillin 500mg, Clindamycin 300mg, Ibuprofen 400mg, Chlorhexidine 0.12%).<br/>"
        "• Sign prescriptions digitally using mouse, touchscreen, or cryptographically stored signature.<br/>"
        "• Generates printable A4 prescriptions and official School/Work Dental Absence Slips with verification QR codes.",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 6. Backup Guide.pdf
# ==============================================================================
def generate_backup_guide():
    pdf_path = OUTPUT_DIR / "Backup Guide.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Backup & Disaster Recovery Guide", styles["DocTitle"]))
    story.append(Paragraph("Automated Data Protection, Encryption & Safe Restoration Playbook", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("1. Automated Daily Nightly Backups", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>Schedule:</b> The backup engine automatically executes every night at 23:00 (11:00 PM) with zero user intervention.<br/>"
        "• <b>Storage Location:</b> Saved directly into <code>C:\\DentalCarePro_Backups\\</code> as timestamped SQL archives.<br/>"
        "• <b>AES-256 Encryption:</b> Backups are cryptographically encrypted to safeguard patient health information (HIPAA compliant).<br/>"
        "• <b>Retention Policy:</b> Backups are retained for 90 days with automated pruning of expired archives.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("2. On-Demand Manual Backup (1-Click)", styles["SectionHeading"]))
    story.append(Paragraph(
        "To take an instant backup prior to software updates, fiscal year-end accounting, or computer maintenance:<br/>"
        "1. Open the <code>Backup Utility</code> folder inside your DentalCare Pro directory.<br/>"
        "2. Double-click <b>take_backup.bat</b>.<br/>"
        "3. A green confirmation will confirm the creation of your new backup snapshot with size and timestamp.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("3. Recommended 3-2-1 Clinic Backup Strategy", styles["SectionHeading"]))
    story.append(Paragraph(
        "• <b>3 Copies of Data:</b> (1) Live PostgreSQL database, (2) Daily local backups, (3) Off-site external drive.<br/>"
        "• <b>2 Different Media Types:</b> Local computer hard disk + External USB encrypted storage drive.<br/>"
        "• <b>1 Off-Site Location:</b> Weekly, copy <code>C:\\DentalCarePro_Backups\\</code> to an external USB flash drive and store it in the clinic safe.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("4. Emergency Disaster Recovery in Under 5 Minutes", styles["SectionHeading"]))
    story.append(Paragraph(
        "In the event of hardware failure, disk crash, or replacement with a new computer:<br/>"
        "1. Install DentalCare Pro on the replacement computer using <b>Setup.exe</b>.<br/>"
        "2. Copy your latest backup file into <code>C:\\DentalCarePro_Backups\\</code>.<br/>"
        "3. Double-click <b>restore_backup.bat</b> inside <code>Backup Utility/</code>.<br/>"
        "4. Select your backup file and type <b>YES</b> when prompted. All patient records, odontograms, and invoices are restored instantly!",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 7. Troubleshooting Guide.pdf
# ==============================================================================
def generate_troubleshooting_guide():
    pdf_path = OUTPUT_DIR / "Troubleshooting Guide.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Troubleshooting Guide", styles["DocTitle"]))
    story.append(Paragraph("Self-Service Diagnostics, Network Resolution & Fast Fixes", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("1. Fast Diagnostic Tool", styles["SectionHeading"]))
    story.append(Paragraph(
        "Before calling support, open the <code>Support</code> folder and run <b>Diagnostic-Tool.exe</b>.<br/>"
        "It performs an automated 10-second inspection of PostgreSQL service, TCP port 5432, RAM, disk space, and API responsiveness.",
        styles["BodyTextCustom"]
    ))

    story.append(Paragraph("2. Common Issues & Fast Resolutions", styles["SectionHeading"]))
    trouble_data = [
        [Paragraph("Symptom", styles["TableHead"]), Paragraph("Root Cause", styles["TableHead"]), Paragraph("Recommended Resolution", styles["TableHead"])],
        [Paragraph("Database connection error on startup", styles["TableCellBold"]), Paragraph("PostgreSQL service stopped or not listening on port 5432", styles["TableCell"]), Paragraph("Run <code>Support/Database-Troubleshooter.bat</code>. Start PostgreSQL service in Windows Services (services.msc).", styles["TableCell"])],
        [Paragraph("Operatory PC cannot connect to Server", styles["TableCellBold"]), Paragraph("Windows Defender Firewall blocking port 8000 or 5432", styles["TableCell"]), Paragraph("Add an Inbound Firewall Rule for TCP port 8000 and 5432 on the Server PC. Ensure both PCs are on the same clinic Wi-Fi.", styles["TableCell"])],
        [Paragraph("Thermal printer outputs blank receipt", styles["TableCellBold"]), Paragraph("Thermal paper roll inserted upside down or out of paper", styles["TableCell"]), Paragraph("Flip thermal paper roll so heat-sensitive side contacts print head. Check printer USB cable connection.", styles["TableCell"])],
        [Paragraph("Application launches to white screen", styles["TableCellBold"]), Paragraph("Backend API supervisor starting or port conflict", styles["TableCell"]), Paragraph("Wait 5 seconds and press F5 to reload. Check <code>%LOCALAPPDATA%\\DentalCarePro\\logs\\app.log</code> for port errors.", styles["TableCell"])],
    ]
    t_tr = Table(trouble_data, colWidths=[130, 160, 230])
    t_tr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_tr)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Log File Locations (For Support Assistance)", styles["SectionHeading"]))
    story.append(Paragraph(
        "All diagnostic logs are stored locally for privacy compliance:<br/>"
        "• <code>%LOCALAPPDATA%\\DentalCarePro\\logs\\app.log</code> (Desktop application shell events)<br/>"
        "• <code>%LOCALAPPDATA%\\DentalCarePro\\logs\\backend.log</code> (API server & database transactions)<br/>"
        "• <code>%LOCALAPPDATA%\\DentalCarePro\\logs\\backup.log</code> (Daily backup snapshot history)",
        styles["BodyTextCustom"]
    ))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 8. License.pdf
# ==============================================================================
def generate_license():
    pdf_path = OUTPUT_DIR / "License.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("Commercial Software License Agreement", styles["DocTitle"]))
    story.append(Paragraph("DentalCare Pro Enterprise Practice License & HIPAA Compliance Terms", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    terms = (
        "<b>1. PERPETUAL CLINIC LICENSE GRANT:</b> DentalCare Pro Inc. grants the licensee a non-exclusive, perpetual, "
        "one-time purchase license to install, operate, and utilize DentalCare Pro on workstations situated within the purchasing dental clinic premises.<br/><br/>"
        "<b>2. NO RECURRING SUBSCRIPTION:</b> The licensee retains full rights to utilize the software in perpetuity without "
        "mandatory recurring monthly fees or mandatory cloud maintenance charges.<br/><br/>"
        "<b>3. PATIENT DATA OWNERSHIP:</b> All patient health records, odontograms, clinical photographs, radiographs, and "
        "financial billing transactions remain the exclusive, confidential property of the licensee dental clinic. DentalCare Pro Inc. collects zero patient telemetry.<br/><br/>"
        "<b>4. HIPAA & REGULATORY COMPLIANCE:</b> The software incorporates AES-256 encryption, role-based access control (RBAC), "
        "tamper-evident audit logs, and automatic database backups designed to meet and exceed HIPAA and statutory healthcare data privacy standards.<br/><br/>"
        "<b>5. LIMITED WARRANTY:</b> The software is provided with a 12-month defect warranty covering software bug fixes and critical security maintenance."
    )
    story.append(Paragraph(terms, styles["BodyTextCustom"]))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 9. Release Notes.pdf
# ==============================================================================
def generate_release_notes():
    pdf_path = OUTPUT_DIR / "Release Notes.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = get_styles()
    story = []

    story.append(Paragraph("DentalCare Pro - Commercial Release Notes", styles["DocTitle"]))
    story.append(Paragraph("Version 23.0 Official Release - Production Certified", styles["DocSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=8))

    story.append(Paragraph("Major Features in Version 23.0 Commercial Release:", styles["SectionHeading"]))
    features = (
        "• <b>Full Windows Installer:</b> One-click Setup.exe with automatic dependency verification and system requirement checks.<br/>"
        "• <b>Enterprise UI Modernization:</b> Modern design tokens, 8-pt grid spacing, collapsible dark sidebar, and instant <code>Ctrl + K</code> command palette.<br/>"
        "• <b>Station Role Focus:</b> Dedicated optimized views for Receptionist, Dentist Operatory, and Practice Administrator.<br/>"
        "• <b>Thermal POS Printer Support:</b> 80mm & 58mm instant thermal receipt printing in addition to standard A4 laser invoices.<br/>"
        "• <b>Military-Grade Backups:</b> AES-256 encrypted automated backups with SHA-256 integrity verification.<br/>"
        "• <b>Disguised Malware Protection:</b> AntiVirusService scanning executable headers disguised as radiographs or images.<br/>"
        "• <b>Interactive Odontogram:</b> FDI adult (32) and pediatric (20) tooth mapping with clinical procedures.<br/>"
        "• <b>High-Concurrency Stability:</b> Benchmarked up to 100 concurrent requests with zero drops."
    )
    story.append(Paragraph(features, styles["BodyTextCustom"]))

    doc.build(story)
    print(f"[OK] Generated: {pdf_path}")


# ==============================================================================
# 10. Extras/ Printable Clinical Materials
# ==============================================================================
def generate_extras():
    styles = get_styles()

    # 1. Adult & Pediatric Dental Tooth Chart.pdf
    doc1 = SimpleDocTemplate(str(EXTRAS_DIR / "Adult & Pediatric Dental Tooth Chart.pdf"), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s1 = []
    s1.append(Paragraph("FDI Two-Digit Dental Tooth Numbering Reference", styles["DocTitle"]))
    s1.append(Paragraph("Permanent Adult (32 Teeth) & Deciduous Primary (20 Teeth) Tooth Anatomy", styles["DocSubtitle"]))
    s1.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=10))

    adult_data = [
        [Paragraph("Quadrant", styles["TableHead"]), Paragraph("Tooth Range", styles["TableHead"]), Paragraph("Teeth Names & FDI Codes", styles["TableHead"])],
        [Paragraph("Q1: Upper Right (Maxillary Right)", styles["TableCellBold"]), Paragraph("Teeth 18 - 11", styles["TableCell"]), Paragraph("18 (3rd Molar), 17 (2nd Molar), 16 (1st Molar), 15 (2nd Premolar), 14 (1st Premolar), 13 (Canine), 12 (Lateral Incisor), 11 (Central Incisor)", styles["TableCell"])],
        [Paragraph("Q2: Upper Left (Maxillary Left)", styles["TableCellBold"]), Paragraph("Teeth 21 - 28", styles["TableCell"]), Paragraph("21 (Central Incisor), 22 (Lateral Incisor), 23 (Canine), 24 (1st Premolar), 25 (2nd Premolar), 26 (1st Molar), 27 (2nd Molar), 28 (3rd Molar)", styles["TableCell"])],
        [Paragraph("Q3: Lower Left (Mandibular Left)", styles["TableCellBold"]), Paragraph("Teeth 31 - 38", styles["TableCell"]), Paragraph("31 (Central Incisor), 32 (Lateral Incisor), 33 (Canine), 34 (1st Premolar), 35 (2nd Premolar), 36 (1st Molar), 37 (2nd Molar), 38 (3rd Molar)", styles["TableCell"])],
        [Paragraph("Q4: Lower Right (Mandibular Right)", styles["TableCellBold"]), Paragraph("Teeth 48 - 41", styles["TableCell"]), Paragraph("48 (3rd Molar), 47 (2nd Molar), 46 (1st Molar), 45 (2nd Premolar), 44 (1st Premolar), 43 (Canine), 42 (Lateral Incisor), 41 (Central Incisor)", styles["TableCell"])],
    ]
    t1 = Table(adult_data, colWidths=[150, 90, 280])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    s1.append(Paragraph("Permanent Dentition (Adult):", styles["SectionHeading"]))
    s1.append(t1)
    s1.append(Spacer(1, 10))

    pediatric_data = [
        [Paragraph("Quadrant", styles["TableHead"]), Paragraph("Range", styles["TableHead"]), Paragraph("Deciduous Teeth & FDI Codes", styles["TableHead"])],
        [Paragraph("Q5: Upper Right Primary", styles["TableCellBold"]), Paragraph("55 - 51", styles["TableCell"]), Paragraph("55 (2nd Molar), 54 (1st Molar), 53 (Canine), 52 (Lateral), 51 (Central)", styles["TableCell"])],
        [Paragraph("Q6: Upper Left Primary", styles["TableCellBold"]), Paragraph("61 - 65", styles["TableCell"]), Paragraph("61 (Central), 62 (Lateral), 63 (Canine), 64 (1st Molar), 65 (2nd Molar)", styles["TableCell"])],
        [Paragraph("Q7: Lower Left Primary", styles["TableCellBold"]), Paragraph("71 - 75", styles["TableCell"]), Paragraph("71 (Central), 72 (Lateral), 73 (Canine), 74 (1st Molar), 75 (2nd Molar)", styles["TableCell"])],
        [Paragraph("Q8: Lower Right Primary", styles["TableCellBold"]), Paragraph("85 - 81", styles["TableCell"]), Paragraph("85 (2nd Molar), 84 (1st Molar), 83 (Canine), 82 (Lateral), 81 (Central)", styles["TableCell"])],
    ]
    t2 = Table(pediatric_data, colWidths=[150, 90, 280])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    s1.append(Paragraph("Primary Deciduous Dentition (Pediatric):", styles["SectionHeading"]))
    s1.append(t2)
    doc1.build(s1)
    print(f"[OK] Generated: {EXTRAS_DIR / 'Adult & Pediatric Dental Tooth Chart.pdf'}")

    # 2. Dental Emergency Triage Cheat Sheet.pdf
    doc2 = SimpleDocTemplate(str(EXTRAS_DIR / "Dental Emergency Triage Cheat Sheet.pdf"), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s2 = []
    s2.append(Paragraph("Dental Emergency Triage & Protocols", styles["DocTitle"]))
    s2.append(Paragraph("Front Desk & Chairside Immediate Action Guidelines", styles["DocSubtitle"]))
    s2.append(HRFlowable(width="100%", thickness=1.5, color=DANGER, spaceAfter=10))

    triage_data = [
        [Paragraph("Emergency Condition", styles["TableHead"]), Paragraph("Urgency Level", styles["TableHead"]), Paragraph("Immediate Clinic Action", styles["TableHead"])],
        [Paragraph("Avulsed Permanent Tooth (Knocked Out)", styles["TableCellBold"]), Paragraph("CRITICAL (Under 60 Min)", styles["TableCellBold"]), Paragraph("Do not touch root. Store tooth in cold milk or saliva. Re-implant within 60 minutes for highest periodontal ligament survival.", styles["TableCell"])],
        [Paragraph("Facial Swelling / Trismus (Ludwig's Angina Risk)", styles["TableCellBold"]), Paragraph("CRITICAL (Immediate)", styles["TableCellBold"]), Paragraph("Assess airway immediately. If floor of mouth elevated or breathing compromised, call 911 / EMS. Administer IV/oral antibiotics as indicated.", styles["TableCell"])],
        [Paragraph("Severe Uncontrolled Post-Extraction Bleeding", styles["TableCellBold"]), Paragraph("HIGH URGENCY", styles["TableCellBold"]), Paragraph("Place firm pressure with bite gauge soaked in Tranexamic acid or tea bag for 30 minutes. Verify patient blood thinners (Warfarin/Aspirin).", styles["TableCell"])],
        [Paragraph("Acute Irreversible Pulpitis (Severe Pain)", styles["TableCellBold"]), Paragraph("SAME-DAY URGENT", styles["TableCellBold"]), Paragraph("Administer local anesthesia (2% Lidocaine/Articaine). Perform emergency pulpotomy / pulpectomy for immediate pain relief.", styles["TableCell"])],
        [Paragraph("Fractured Tooth with Pulp Exposure", styles["TableCellBold"]), Paragraph("SAME-DAY URGENT", styles["TableCellBold"]), Paragraph("Assess pulpal bleeding. Direct pulp cap with MTA/Biodentine or pulpectomy. Cover with temporary glass ionomer restoration.", styles["TableCell"])],
    ]
    t_tr2 = Table(triage_data, colWidths=[150, 110, 260])
    t_tr2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DANGER),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CARD_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    s2.append(t_tr2)
    doc2.build(s2)
    print(f"[OK] Generated: {EXTRAS_DIR / 'Dental Emergency Triage Cheat Sheet.pdf'}")

    # 3. Daily Opening and Closing Checklist.pdf
    doc3 = SimpleDocTemplate(str(EXTRAS_DIR / "Daily Opening and Closing Checklist.pdf"), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s3 = []
    s3.append(Paragraph("Daily Clinic Operational Checklist", styles["DocTitle"]))
    s3.append(Paragraph("Standard Operating Procedures for Reception & Operatory Assistants", styles["DocSubtitle"]))
    s3.append(HRFlowable(width="100%", thickness=1.5, color=SUCCESS, spaceAfter=10))

    s3.append(Paragraph("MORNING OPENING CHECKLIST (8:00 AM - 8:30 AM)", styles["SectionHeading"]))
    morning = (
        "[ ] 1. Power on the clinic server workstation and verify PostgreSQL service is active.<br/>"
        "[ ] 2. Launch DentalCare Pro on all operatory stations and the reception desk.<br/>"
        "[ ] 3. Review today's appointment schedule and confirm all operatory room assignments.<br/>"
        "[ ] 4. Flush dental chair waterlines for 2 minutes with antimicrobial solution.<br/>"
        "[ ] 5. Inspect autoclave biological indicators and ensure sterile instrument packs are loaded.<br/>"
        "[ ] 6. Verify thermal receipt printer has sufficient 80mm paper roll and laser printer has A4 stock.<br/>"
        "[ ] 7. Confirm reception cash float is counted and locked in register drawer."
    )
    s3.append(Paragraph(morning, styles["BodyTextCustom"]))
    s3.append(Spacer(1, 10))

    s3.append(Paragraph("EVENING CLOSING CHECKLIST (5:30 PM - 6:00 PM)", styles["SectionHeading"]))
    evening = (
        "[ ] 1. Verify that all completed patient appointments have invoices created and recorded.<br/>"
        "[ ] 2. Print the <b>Daily Collection Summary</b> and reconcile total cash, card, and UPI payments.<br/>"
        "[ ] 3. Lock the day's cash proceeds in the clinic security safe.<br/>"
        "[ ] 4. Run suction cleaning disinfectant through all operatory high-volume evacuation lines.<br/>"
        "[ ] 5. Power off operatory dental units, compressor, and clinical operatory computer monitors.<br/>"
        "[ ] 6. Ensure the main clinic server PC remains in Standby/Powered on for the 23:00 automated backup.<br/>"
        "[ ] 7. Perform weekly external USB backup drive rotation every Friday evening."
    )
    s3.append(Paragraph(evening, styles["BodyTextCustom"]))
    doc3.build(s3)
    print(f"[OK] Generated: {EXTRAS_DIR / 'Daily Opening and Closing Checklist.pdf'}")

    # 4. Patient Intake Registration Form (Printable).pdf
    doc4 = SimpleDocTemplate(str(EXTRAS_DIR / "Patient Intake Registration Form (Printable).pdf"), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    s4 = []
    s4.append(Paragraph("Patient Registration & Medical History Intake Form", styles["DocTitle"]))
    s4.append(Paragraph("Please complete this form accurately. All medical information is confidential under HIPAA.", styles["DocSubtitle"]))
    s4.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=8))

    form_text = (
        "<b>PATIENT DEMOGRAPHICS:</b><br/>"
        "Full Legal Name: _____________________________________________ Date of Birth: ____/____/________<br/>"
        "Gender: [ ] Male  [ ] Female  [ ] Other   Phone Number: (______) ____________________________<br/>"
        "Email Address: _______________________________________________________________________________<br/>"
        "Residential Address: __________________________________________________________________________<br/>"
        "Emergency Contact Name: _______________________________ Relationship: ________ Phone: _________<br/><br/>"
        "<b>DENTAL INSURANCE INFORMATION:</b><br/>"
        "Insurance Provider: _________________________________ Policy / Member ID: _____________________<br/>"
        "Group Number: _______________________________________ Policyholder Name: _____________________<br/><br/>"
        "<b>MEDICAL HEALTH HISTORY (Check all that apply):</b><br/>"
        "[ ] High Blood Pressure       [ ] Heart Murmur / Valve Prolapse   [ ] Pacemaker / Heart Surgery<br/>"
        "[ ] Diabetes (Type 1 or 2)    [ ] Asthma / Respiratory Issues     [ ] Epilepsy / Seizures<br/>"
        "[ ] Bleeding / Clotting Disorder[ ] Liver / Kidney Disease       [ ] Cancer / Radiation Therapy<br/>"
        "[ ] Currently Pregnant (Due: __________)                          [ ] Artificial Joint Replacement<br/><br/>"
        "<b>DRUG & MATERIAL ALLERGIES (CRITICAL):</b><br/>"
        "[ ] Penicillin / Amoxicillin   [ ] Latex                         [ ] Aspirin / NSAIDs<br/>"
        "[ ] Local Dental Anesthetics  [ ] Codeine / Narcotics           [ ] Sulfa Drugs<br/>"
        "Other Allergies: ____________________________________________________________________________<br/><br/>"
        "Current Medications: _________________________________________________________________________<br/><br/>"
        "<b>PATIENT CONSENT & SIGNATURE:</b><br/>"
        "I certify that I have read and understand the above questions. I will not hold the dental clinic responsible for any errors or omissions that I may have made in the completion of this form.<br/><br/>"
        "Patient / Guardian Signature: ___________________________________ Date: ____/____/________"
    )
    s4.append(Paragraph(form_text, styles["BodyTextCustom"]))
    doc4.build(s4)
    print(f"[OK] Generated: {EXTRAS_DIR / 'Patient Intake Registration Form (Printable).pdf'}")

    # 5. Appointment SMS and WhatsApp Templates.txt
    templates_txt = """======================================================================
  DENTALCARE PRO - APPOINTMENT SMS & WHATSAPP MESSAGE TEMPLATES
======================================================================

You can copy and paste these pre-formatted message scripts into your
clinic phone or messaging software for patient communications.

1. APPOINTMENT CONFIRMATION (Immediately Upon Booking):
----------------------------------------------------------------------
"Dear [Patient Name], your dental appointment at [Clinic Name] is confirmed for [Day], [Date] at [Time] with [Doctor Name]. If you need to reschedule, please call us at [Clinic Phone]. We look forward to seeing you!"

2. 24-HOUR REMINDER MESSAGE (Sent 1 Day Prior):
----------------------------------------------------------------------
"Reminder: You have a dental appointment scheduled tomorrow, [Date] at [Time] at [Clinic Name]. Please reply YES to confirm or call [Clinic Phone] to adjust your time. Please remember to bring your insurance card."

3. 2-HOUR SAME-DAY ARRIVAL NOTICE:
----------------------------------------------------------------------
"Hi [Patient Name], your dental visit with [Doctor Name] is today at [Time]. We are located at [Clinic Address]. Parking is available on-site. See you soon!"

4. POST-OPERATIVE CARE CHECK-IN (Day After Treatment / Extraction):
----------------------------------------------------------------------
"Dear [Patient Name], [Doctor Name] and the team at [Clinic Name] hope you are recovering comfortably from your procedure yesterday. Remember to follow your post-care instructions. If you experience unexpected discomfort or bleeding, call our emergency line at [Emergency Phone]."

5. 6-MONTH ROUTINE RECALL & HYGIENE CHECKUP:
----------------------------------------------------------------------
"Hi [Patient Name], it's time for your 6-month routine dental cleaning and checkup at [Clinic Name]! Maintaining your oral health keeps your smile bright. Call [Clinic Phone] or reply to this message to book your convenient time slot."
"""
    (EXTRAS_DIR / "Appointment SMS and WhatsApp Templates.txt").write_text(templates_txt, encoding="utf-8")
    print(f"[OK] Generated: {EXTRAS_DIR / 'Appointment SMS and WhatsApp Templates.txt'}")

    # 6. README.txt in Extras
    readme_extras = """======================================================================
  DENTALCARE PRO - CLINICAL EXTRAS & PRACTICE TEMPLATES
======================================================================

This folder contains high-resolution printable clinical aids and
patient communication templates for your practice.

FILES INCLUDED IN THIS FOLDER:
1. Adult & Pediatric Dental Tooth Chart.pdf
   - Reference FDI two-digit tooth numbering guide for operatory walls.
2. Dental Emergency Triage Cheat Sheet.pdf
   - Immediate clinical action protocol for trauma, avulsion, and acute pulpitis.
3. Daily Opening and Closing Checklist.pdf
   - Standard morning and evening operational checklist for staff.
4. Patient Intake Registration Form (Printable).pdf
   - 1-page paper registration form for walk-in patient intake.
5. Appointment SMS and WhatsApp Templates.txt
   - Patient messaging scripts for booking confirmations and reminders.
"""
    (EXTRAS_DIR / "README.txt").write_text(readme_extras, encoding="utf-8")
    print(f"[OK] Generated: {EXTRAS_DIR / 'README.txt'}")


def main():
    print("======================================================================")
    print("  DENTALCARE PRO - GENERATING 9 COMMERCIAL MANUALS & EXTRAS SUITE")
    print(f"  Destination: {OUTPUT_DIR}")
    print("======================================================================")

    generate_readme_first()
    generate_user_manual()
    generate_admin_guide()
    generate_reception_guide()
    generate_dentist_guide()
    generate_backup_guide()
    generate_troubleshooting_guide()
    generate_license()
    generate_release_notes()
    generate_extras()

    print("======================================================================")
    print("  ALL 9 COMMERCIAL PDFS AND EXTRAS GENERATED SUCCESSFULLY!")
    print("======================================================================")


if __name__ == "__main__":
    main()
