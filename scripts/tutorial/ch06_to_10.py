# scripts/tutorial/ch06_to_10.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_06_to_10(styles):
    story = []

    # =========================================================================
    # CHAPTER 6: DASHBOARD & CLINIC OVERVIEW
    # =========================================================================
    story.append(Paragraph("Chapter 6: Executive Dashboard & Overview", styles["ChapterHeading"]))
    story.append(Paragraph(
        "Upon logging in, users are greeted by the role-aware Executive Dashboard. "
        "The dashboard consolidates real-time operatory analytics, waiting queue statuses, financial summaries, "
        "and active clinical alerts.",
        styles["TutorialBody"]
    ))

    dash_widgets = [
        ["Today's Appointments", "Total scheduled visits, completed count, no-shows, and active patients in operatory chairs."],
        ["Operatory Chair Status", "Visual grid of clinic chairs (Chair 1, Chair 2, Surgery Suite) with live occupancy badges."],
        ["Waiting Queue Triage", "Real-time queue tracking patient arrival timestamp, wait duration, and called status."],
        ["Revenue & Payments", "Today's collections, unbilled completed treatments, pending insurance claims, and monthly targets."],
        ["Inventory Stock Alerts", "Low-stock warnings (anesthetics, composite resins, gloves) breaching reorder levels."],
        ["Quick Action Bar", "One-click shortcuts: New Patient (Alt+N), Book Visit (Alt+B), Emergency Queue (Alt+Q)."],
    ]
    story.append(make_table(["Dashboard Widget", "Clinical & Business Intelligence Data Displayed"], dash_widgets, col_widths=[140, 375], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Auto-Refresh & WebSockets",
        "The Dashboard and Queue views update automatically via WebSockets and polling, ensuring reception and clinical staff "
        "maintain synchronized awareness of patient movements without manual page refreshes.",
        "tip",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 7: PATIENT MANAGEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 7: Patient Record Management", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Patient Management module serves as the centralized Electronic Health Record (EHR) repository. "
        "It maintains complete demographic, medical, dental, and radiographic records.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Step-by-Step Patient Intake Workflow", styles["SectionHeading"]))
    story.append(Paragraph(
        "1. **Registration**: Click 'New Patient' or press Alt+N. Enter mandatory demographics: First Name, Last Name, Gender, Date of Birth, and Mobile Number.<br/>"
        "2. **Duplicate Prevention Engine**: As phone numbers or emails are typed, the system executes real-time deduplication to prevent accidental dual chart creation.<br/>"
        "3. **Medical History Questionnaire**: Record systemic conditions: Diabetes, Hypertension, Cardiac Disease, Asthma, Allergies (Penicillin, Latex), and Current Medications.<br/>"
        "4. **Dental History**: Document chief complaint, bleeding gums, bruxism, TMJ pain, and prior restorative interventions.<br/>"
        "5. **Document Upload**: Attach panoramic OPG X-rays, intraoral camera captures, and signed HIPAA consent forms.<br/>"
        "6. **Chronological Timeline**: Every clinical interaction, appointment, invoice, and note is automatically appended to an immutable audit timeline.",
        styles["TutorialBody"]
    ))
    story.append(Spacer(1, 8))

    story.append(make_callout(
        "Soft Delete & Data Preservation",
        "DentalCare Pro enforces regulatory non-destructive data retention. Archiving a patient sets deleted_at but preserves all historical "
        "treatments, prescriptions, and financial invoices for legal compliance (HIPAA 7-year retention rule).",
        "note",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 8: APPOINTMENT & CHAIR SCHEDULING
    # =========================================================================
    story.append(Paragraph("Chapter 8: Appointment & Operatory Scheduling", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Appointment module provides multi-operatory chair management, doctor schedule calendars, "
        "automated conflict detection, and queue progression.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Appointment Lifecycle State Machine", styles["SectionHeading"]))
    apt_states = [
        ["SCHEDULED", "Appointment booked in calendar; confirmation SMS/email sent to patient."],
        ["CONFIRMED", "Patient acknowledged 24-hour reminder via SMS or patient portal."],
        ["CHECKED_IN", "Patient arrived at clinic; ticket generated in waiting room queue."],
        ["IN_CHAIR", "Patient seated in dental chair; dentist began clinical consultation/procedure."],
        ["COMPLETED", "Procedure completed; treatment plan updated; routed to checkout desk for payment."],
        ["CANCELLED", "Patient or clinic cancelled visit; mandatory reason code recorded."],
        ["NO_SHOW", "Patient failed to arrive; automated recall engine triggers rescheduling outreach."],
    ]
    story.append(make_table(["Lifecycle State", "Operational Trigger & System Action"], apt_states, col_widths=[120, 395], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Conflict Detection Rules", styles["SectionHeading"]))
    story.append(Paragraph(
        "The scheduling engine automatically prevents scheduling errors by enforcing three concurrent validation checks:<br/>"
        "• **Chair Overlap**: A dental operatory chair cannot hold two overlapping appointments.<br/>"
        "• **Dentist Availability**: A practitioner cannot be scheduled across two chairs simultaneously.<br/>"
        "• **Working Hours & Blocked Time**: Appointments cannot be booked outside active doctor shift hours or during scheduled leaves.",
        styles["TutorialBody"]
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 9: TREATMENT MANAGEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 9: Treatment Planning & Clinical Records", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Treatment module enables clinicians to stage complex, multi-visit clinical interventions, "
        "record SOAP (Subjective, Objective, Assessment, Plan) progress notes, and obtain digital patient informed consent.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Staged Treatment Planning", styles["SectionHeading"]))
    story.append(Paragraph(
        "Dentists can organize proposed procedures into chronological phases (e.g., Phase 1: Urgent Endodontics & Extractions; "
        "Phase 2: Periodontal Scaling; Phase 3: Prosthodontic Crowns & Implants). Each stage generates transparent fee estimates "
        "with itemized patient copays and estimated insurance contributions.",
        styles["TutorialBody"]
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("SOAP Clinical Notes Architecture", styles["SectionHeading"]))
    soap_rows = [
        ["S - Subjective", "Patient's reported chief complaint, pain severity on 1-10 visual scale, trigger factors (hot/cold/chewing)."],
        ["O - Objective", "Clinical findings: percussion sensitivity, mobility score, periodontal pocket depths, radiographic pathology."],
        ["A - Assessment", "Diagnostic classification using ICD-10-CM / ADA CDT terminology (e.g. K02.62 Caries of dentin)."],
        ["P - Plan / Procedure", "Intervention performed: local anesthesia administered, restorative materials used, post-op instructions."],
    ]
    story.append(make_table(["SOAP Component", "Required Clinical Documentation Standards"], soap_rows, col_widths=[130, 385], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 10: INTERACTIVE ODONTOGRAM
    # =========================================================================
    story.append(Paragraph("Chapter 10: Interactive 32-Tooth Odontogram", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Interactive Odontogram is the visual core of DentalCare Pro. Built on interactive vector graphics, "
        "it supports the international FDI 2-digit numbering system (Teeth 11–48) as well as primary pediatric dentition (Teeth 51–85 / A–T).",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Anatomical Surface Mapping", styles["SectionHeading"]))
    surf_rows = [
        ["Mesial (M)", "Surface facing toward the anterior midline of the dental arch."],
        ["Distal (D)", "Surface facing away from the anterior midline."],
        ["Occlusal / Incisal (O/I)", "Biting or chewing surface of posterior/anterior teeth."],
        ["Buccal / Facial (B/F)", "Surface facing outward toward the cheeks or lips."],
        ["Lingual / Palatal (L/P)", "Surface facing inward toward the tongue or hard palate."],
    ]
    story.append(make_table(["Tooth Surface", "Anatomical Definition & Charting Representation"], surf_rows, col_widths=[140, 375], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Standardized Color Coding Standards", styles["SectionHeading"]))
    color_rows = [
        ["Active Caries / Decay", "Red (#dc2626)", "Pathology requiring restorative intervention."],
        ["Existing Composite Filling", "Blue (#2563eb)", "Satisfactory tooth-colored restoration present."],
        ["Existing Amalgam Filling", "Dark Gray (#475569)", "Existing metal alloy restoration."],
        ["Crown / Full Coverage", "Amber / Gold (#d97706)", "Porcelain-fused-to-metal (PFM) or zirconia crown."],
        ["Root Canal Treatment (RCT)", "Purple (#9333ea)", "Endodontic obturation with gutta-percha."],
        ["Extracted / Missing Tooth", "Strikethrough Cross (#94a3b8)", "Anatomically absent tooth."],
        ["Dental Implant", "Teal (#0d9488)", "Endosteal titanium implant fixture with abutment."],
    ]
    story.append(make_table(["Condition / Procedure", "Color Code", "Clinical Significance"], color_rows, col_widths=[160, 130, 225], styles=styles))

    story.append(Spacer(1, 8))
    story.append(make_callout(
        "Rapid Multi-Surface Charting",
        "Clinicians can click individual tooth facets (e.g. #14 MOD) or select multiple teeth simultaneously to apply bulk procedures "
        "(e.g., Full Mouth Scaling & Prophylaxis across all four quadrants).",
        "tip",
        styles
    ))

    story.append(PageBreak())
    return story
