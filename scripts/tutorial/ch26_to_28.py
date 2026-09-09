# scripts/tutorial/ch26_to_28.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_26_to_28(styles):
    story = []

    # =========================================================================
    # CHAPTER 26: ROLE-BASED DAILY WORKFLOW GUIDE
    # =========================================================================
    story.append(Paragraph("Chapter 26: Role-Based Daily Workflow Guide", styles["ChapterHeading"]))
    story.append(Paragraph(
        "This chapter maps the exact step-by-step chronological daily routine for every team member in a dental practice.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("1. Receptionist Daily Flow", styles["SectionHeading"]))
    story.append(Paragraph(
        "• **08:00 AM**: Log in, review Today's Agenda, verify emergency buffer slots.<br/>"
        "• **Patient Arrival**: Scan patient QR code or search name $\rightarrow$ Confirm contact info $\rightarrow$ Move ticket to 'WAITING' queue.<br/>"
        "• **Operatory Calling**: When chair turns green, advance patient to 'IN_CHAIR'.<br/>"
        "• **Checkout**: Receive completed treatment ticket $\rightarrow$ Generate invoice $\rightarrow$ Collect co-pay $\rightarrow$ Book 6-month recall visit.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("2. Dentist Operatory Flow", styles["SectionHeading"]))
    story.append(Paragraph(
        "• **Chairside Review**: Open patient electronic chart $\rightarrow$ Review medical alert banner (e.g. Penicillin allergy).<br/>"
        "• **Clinical Examination**: Open 32-Tooth Odontogram $\rightarrow$ Chart new pathologies (e.g. #14 Caries) $\rightarrow$ Propose restorative treatment plan.<br/>"
        "• **Procedure Execution**: Perform restoration $\rightarrow$ Click tooth surface $\rightarrow$ Mark 'Completed' $\rightarrow$ Dictate SOAP note.<br/>"
        "• **Prescription & Sign-Off**: Issue electronic prescription if needed $\rightarrow$ Authorize procedure sign-off $\rightarrow$ Send to reception for billing.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("3. Clinic Administrator Flow", styles["SectionHeading"]))
    story.append(Paragraph(
        "• **Midday**: Review unbilled procedures, review claim pre-authorizations.<br/>"
        "• **End of Day (18:00 PM)**: Review Day Sheet, verify cash drawer against collected payments, execute daily financial close.",
        styles["TutorialBody"]
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 27: KEYBOARD SHORTCUTS & PRODUCTIVITY
    # =========================================================================
    story.append(Paragraph("Chapter 27: Keyboard Shortcuts & Rapid Actions", styles["ChapterHeading"]))
    story.append(Paragraph(
        "Power users can navigate DentalCare Pro without lifting their hands from the keyboard using global hotkeys:",
        styles["TutorialBody"]
    ))

    hotkeys = [
        ["Alt + N", "Global Shortcut", "Open New Patient Registration modal from any screen."],
        ["Alt + B", "Global Shortcut", "Open Quick Appointment Booking modal."],
        ["Alt + S", "Global Shortcut", "Focus global Patient Search autocomplete bar."],
        ["Alt + Q", "Global Shortcut", "Jump directly to the live Waiting Room Queue view."],
        ["Ctrl + Enter", "Forms / Modals", "Save, submit, and confirm the active modal dialog."],
        ["Esc", "Modals / Drawers", "Cancel active dialog and return focus to underlying screen."],
        ["1 to 8", "Odontogram", "Select tooth position inside current quadrant."],
        ["M, O, D, B, L", "Odontogram", "Toggle Mesial, Occlusal, Distal, Buccal, Lingual surface selection."],
    ]
    story.append(make_table(["Key Combination", "Scope", "Productivity Action Triggered"], hotkeys, col_widths=[125, 120, 270], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 28: SCHEDULED MAINTENANCE GUIDE
    # =========================================================================
    story.append(Paragraph("Chapter 28: Scheduled Maintenance Runbooks", styles["ChapterHeading"]))
    story.append(Paragraph(
        "To ensure high performance and zero data loss, IT administrators should adhere to this maintenance schedule:",
        styles["TutorialBody"]
    ))

    maint_rows = [
        ["Daily (01:00 UTC)", "Automated PostgreSQL full backup and S3 encrypted upload; review failed email/SMS logs."],
        ["Weekly (Sunday)", "PostgreSQL VACUUM ANALYZE on high-churn tables (appointments, queue_tickets); review disk capacity."],
        ["Monthly (1st)", "Rotate staff API tokens; review inactive accounts; export financial reconciliation reports."],
        ["Quarterly", "Perform full Point-In-Time Recovery (PITR) drill to an isolated staging environment; audit HIPAA access logs."],
        ["Yearly", "Archive closed patient records older than statutory retention limits; review SSL/TLS certificate renewals."],
    ]
    story.append(make_table(["Frequency", "Required Maintenance Action & Operational Protocols"], maint_rows, col_widths=[130, 385], styles=styles))

    story.append(PageBreak())
    return story
