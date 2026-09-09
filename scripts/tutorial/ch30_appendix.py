# scripts/tutorial/ch30_appendix.py
from reportlab.platypus import Paragraph, Spacer, PageBreak
from .styles import make_callout, make_table, make_mockup_box

def build_chapter_30(styles):
    story = []

    # =========================================================================
    # CHAPTER 30: APPENDIX
    # =========================================================================
    story.append(Paragraph("Chapter 30: Appendix & Reference Materials", styles["ChapterHeading"]))
    story.append(Paragraph(
        "This appendix provides a clinical and technical glossary, abbreviation key, and architecture reference.",
        styles["TutorialBody"]
    ))

    story.append(Paragraph("Technical & Clinical Abbreviations", styles["SectionHeading"]))
    abbr_rows = [
        ["CDT", "Current Dental Terminology - Standardized procedure code set maintained by the American Dental Association (ADA)."],
        ["EDR / PMS", "Electronic Dental Record / Practice Management Software - Digital clinical record and practice administration system."],
        ["FDI", "Fédération Dentaire Internationale - International two-digit tooth numbering system."],
        ["HIPAA", "Health Insurance Portability and Accountability Act - US law establishing privacy and security safeguards for PHI."],
        ["MODBL", "Mesial, Occlusal, Distal, Buccal, Lingual - Five anatomical surfaces of human teeth."],
        ["OPG", "Orthopantomogram - Panoramic scanning dental X-ray of the upper and lower jaw."],
        ["PHI", "Protected Health Information - Individually identifiable health data protected under federal privacy rules."],
        ["PITR", "Point-In-Time Recovery - Database restoration method enabling rollback to an exact second in time via WAL logs."],
        ["RCT", "Root Canal Treatment - Endodontic therapy involving removal of dental pulp and canal obturation."],
        ["SOAP", "Subjective, Objective, Assessment, Plan - Medical and clinical documentation methodology."],
    ]
    story.append(make_table(["Abbreviation", "Full Definition & Contextual Meaning"], abbr_rows, col_widths=[120, 395], styles=styles))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Comprehensive Clinical Glossary", styles["SectionHeading"]))
    gloss_rows = [
        ["Caries", "Infectious microbiological disease of the teeth that results in localized dissolution and destruction of calcified tissues."],
        ["Composite", "Tooth-colored resin restorative material cured with a dental blue light for fillings."],
        ["Crown", "Artificial prosthodontic replacement that restores missing tooth structure by surrounding the remaining coronal tooth."],
        ["Implant", "Surgical fixture placed into the jawbone which fuses with the bone over time to act as an artificial root for a prosthetic tooth."],
        ["Periodontitis", "Chronic inflammatory disease affecting the periodontium tissues supporting the teeth, leading to bone loss."],
        ["Prophylaxis", "Scaling and polishing procedure performed to remove dental plaque, calculus, and stains from the coronal surfaces of teeth."],
    ]
    story.append(make_table(["Clinical Term", "Dental Practice Definition"], gloss_rows, col_widths=[120, 395], styles=styles))
    story.append(Spacer(1, 10))

    story.append(make_callout(
        "Documentation Sign-Off",
        "This tutorial serves as the official enterprise instructional manual for DentalCare Pro v1.0.0. "
        "For additional developer runbooks and operational guides, visit the /docs directory in the source repository.",
        "tip",
        styles
    ))

    return story
