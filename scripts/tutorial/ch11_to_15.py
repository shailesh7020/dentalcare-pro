# scripts/tutorial/ch11_to_15.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapters_11_to_15(styles):
    story = []

    # =========================================================================
    # CHAPTER 11: PRESCRIPTION MANAGEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 11: Electronic Prescription (e-Rx) Module", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Prescription module enables dentists to issue digital prescriptions with automated drug interaction checks, "
        "pre-configured clinic medication templates, and high-resolution PDF printing.",
        styles["TutorialBody"]
    ))

    rx_rows = [
        ["Formulary Database", "Searchable catalog of dental pharmaceuticals categorized by therapeutic class (Antibiotics, Analgesics, Antiseptics)."],
        ["Drug Allergy Warnings", "Cross-references prescribed drugs against patient recorded allergies (e.g., Penicillin, NSAIDs) with visual blocker alerts."],
        ["Dosage & Sig Calculation", "Standardized dispensing instructions: Strength (e.g. 500mg), Route (Oral), Frequency (TID / q8h), Duration (5 Days)."],
        ["Prescription Templates", "One-click regimens for common dental protocols (e.g., 'Post-Extraction Regimen', 'Acute Periapical Abscess')."],
        ["Official PDF Generation", "Generates branded prescription slips with clinic letterhead, doctor registration numbers, and QR verification codes."],
    ]
    story.append(make_table(["Prescription Capability", "Clinical Workflow & Safeguards"], rx_rows, col_widths=[145, 370], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Pharmacy Regulatory Compliance",
        "Prescriptions are cryptographically timestamped and locked upon issuance. Changes require issuing an amended prescription, "
        "maintaining strict medico-legal compliance.",
        "note",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 12: BILLING & PAYMENT MANAGEMENT
    # =========================================================================
    story.append(Paragraph("Chapter 12: Billing, Invoicing & Payments", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Billing module unifies clinical procedure fees, laboratory charges, tax computations, and multi-gateway payment collection.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Invoicing & Payment Lifecycle", styles["SectionHeading"]))
    bill_rows = [
        ["Automated Invoice Generation", "Completed clinical procedures automatically flow into draft invoices with pre-set ADA CDT procedure pricing."],
        ["Discounts & Dental Insurance", "Supports line-item percentage discounts, promotional vouchers, and insurance co-pay splits."],
        ["Multi-Gateway Collection", "Accepts Cash, Credit/Debit Cards (Stripe / Square integration), Bank Transfers, and Online Patient Portal payments."],
        ["Partial Payments & Balances", "Tracks outstanding balances, installment plans, and accounts receivable with automated SMS payment reminders."],
        ["Receipts & Credit Notes", "Official numbered receipts generated instantly on payment capture; credit notes for approved fee adjustments."],
    ]
    story.append(make_table(["Financial Workflow", "Capabilities & Accounting Controls"], bill_rows, col_widths=[150, 365], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Tax & Audit Compliance",
        "Invoices comply with regional tax requirements (GST / VAT / Sales Tax) with immutable sequential invoice numbering and tax breakdown tables.",
        "tip",
        styles
    ))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 13: INVENTORY & PROCUREMENT
    # =========================================================================
    story.append(Paragraph("Chapter 13: Dental Supply & Inventory Management", styles["ChapterHeading"]))
    story.append(Paragraph(
        "Dental clinics consume hundreds of consumable supplies daily. DentalCare Pro tracks stock levels, purchase orders, "
        "lot numbers, and expiration dates with automated depletion linked directly to treatment procedures.",
        styles["TutorialBody"]
    ))

    inv_rows = [
        ["Consumable Item Catalog", "SKU, generic name, brand, package size, unit cost, storage location (Cabinet 3, Autoclave Room)."],
        ["Automated Procedure Depletion", "Completing a 'Composite Restoration #14' automatically decrements 1 composite compule and 1 bonding applicator."],
        ["Reorder Threshold Alerts", "Flags supplies falling below minimum safety stock levels with automated purchase order suggestions."],
        ["Batch & Expiry Management", "Tracks manufacturer lot numbers and alerts staff 60/30 days prior to material expiration (First-In, First-Out)."],
        ["Purchase Order (PO) Workflow", "Draft PO $\rightarrow$ Vendor Dispatch $\rightarrow$ Receiving Audit $\rightarrow$ Inventory Reconciliation."],
    ]
    story.append(make_table(["Inventory Module", "Operational Control & Stock Protection"], inv_rows, col_widths=[150, 365], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 14: DENTAL INSURANCE CLEARINGHOUSE
    # =========================================================================
    story.append(Paragraph("Chapter 14: Dental Insurance Claims & EDI", styles["ChapterHeading"]))
    story.append(Paragraph(
        "The Insurance module streamlines the complex world of dental insurance claims, pre-authorizations, and clearinghouse integrations.",
        styles["TutorialBody"]
    ))

    ins_rows = [
        ["Policy Eligibility Verification", "Validates patient coverage, annual maximums, deductibles, and waiting periods prior to treatment."],
        ["Pre-Authorization Requests", "Submits proposed treatment plans and radiographic evidence to payers for formal coverage approval."],
        ["EDI 837D Claim Generation", "Automates standard dental electronic claim formatting with CDT codes, tooth surface modifiers, and provider NPIs."],
        ["Adjudication & EOB Tracking", "Records electronic Remittance Advices (835 ERA), calculates payer write-offs, and transfers remaining balance to patient."],
        ["Claim Denial Management", "Categorizes denied claims with reason codes and facilitates resubmission with additional clinical narratives."],
    ]
    story.append(make_table(["Insurance Feature", "Clearinghouse & Billing Automation"], ins_rows, col_widths=[145, 370], styles=styles))
    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 15: EXECUTIVE REPORTS & CLINICAL ANALYTICS
    # =========================================================================
    story.append(Paragraph("Chapter 15: Reports & Practice Analytics", styles["ChapterHeading"]))
    story.append(Paragraph(
        "DentalCare Pro provides an extensive suite of clinical, financial, and operational analytics "
        "designed for practice optimization and DSO executive reporting.",
        styles["TutorialBody"]
    ))

    report_rows = [
        ["Financial P&L & Aging", "Gross production, net collections, accounts receivable aging (30/60/90+ days), and tax summaries."],
        ["Clinician Productivity", "Procedure volume, production-per-hour, and treatment plan acceptance rates by individual dentist."],
        ["Chair & Operatory Utilization", "Chair occupancy percentages, idle gaps, and peak utilization hours across clinic operatories."],
        ["Patient Acquisition & Retention", "New patient acquisition channels, recall adherence rates, and appointment cancellation trends."],
        ["Supply Consumption & Waste", "Top consumed clinical items, inventory turnover ratios, and expired stock write-offs."],
    ]
    story.append(make_table(["Analytics Domain", "Key Performance Indicators (KPIs) Delivered"], report_rows, col_widths=[150, 365], styles=styles))

    story.append(PageBreak())
    return story
