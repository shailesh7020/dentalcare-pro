# scripts/tutorial/styles.py
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer

# Palette
PRIMARY = colors.HexColor("#0f766e")       # Deep Medical Teal
PRIMARY_LIGHT = colors.HexColor("#f0fdfa") # Soft Teal Tint
SECONDARY = colors.HexColor("#0284c7")     # Clinical Blue
SECONDARY_LIGHT = colors.HexColor("#f0f9ff")
TEXT_DARK = colors.HexColor("#0f172a")     # Deep Slate for text
TEXT_MUTED = colors.HexColor("#64748b")    # Slate Muted
BORDER_COLOR = colors.HexColor("#cbd5e1")  # Light border
BG_LIGHT = colors.HexColor("#f8fafc")      # Alternate row tint
SUCCESS = colors.HexColor("#059669")       # Green
WARNING = colors.HexColor("#d97706")       # Amber
DANGER = colors.HexColor("#dc2626")        # Red
CARD_BG = colors.HexColor("#ffffff")

def get_tutorial_styles():
    styles = getSampleStyleSheet()

    # Base typography overrides
    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        alignment=0,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=SECONDARY,
        alignment=0,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=TEXT_MUTED,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "ChapterHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=TEXT_DARK,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "SubSectionHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "TutorialBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        "TutorialBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        "CodeText",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    ))

    styles.add(ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
    ))

    return styles


def make_callout(title: str, text: str, callout_type: str = "note", styles = None):
    if styles is None:
        styles = get_tutorial_styles()

    type_configs = {
        "tip": (SUCCESS, colors.HexColor("#ecfdf5"), "[TIP]"),
        "note": (SECONDARY, colors.HexColor("#f0f9ff"), "[NOTE]"),
        "warning": (WARNING, colors.HexColor("#fffbeb"), "[WARNING]"),
        "important": (DANGER, colors.HexColor("#fef2f2"), "[IMPORTANT]"),
    }
    border_color, bg_color, tag = type_configs.get(callout_type.lower(), type_configs["note"])

    header_html = f"<b><font color='{border_color.hexval()}'>{tag} {title}</font></b>"
    body_html = f"<br/>{text}"

    p = Paragraph(header_html + body_html, styles["CalloutText"])
    table = Table([[p]], colWidths=[515])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (0, 0), (0, -1), 4, border_color),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    return table


def make_table(headers: list[str], rows: list[list[str]], col_widths: list[float] = None, styles = None):
    if styles is None:
        styles = get_tutorial_styles()

    formatted_data = []
    header_row = [Paragraph(f"<b>{h}</b>", styles["TableHeader"]) for h in headers]
    formatted_data.append(header_row)

    for row in rows:
        formatted_row = []
        for cell in row:
            formatted_row.append(Paragraph(str(cell), styles["TableCell"]))
        formatted_data.append(formatted_row)

    table = Table(formatted_data, colWidths=col_widths)
    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]

    # Alternating row background
    for i in range(1, len(formatted_data)):
        if i % 2 == 0:
            t_style.append(("BACKGROUND", (0, i), (-1, i), BG_LIGHT))

    table.setStyle(TableStyle(t_style))
    return table


def make_mockup_box(title: str, lines: list[str], styles = None):
    if styles is None:
        styles = get_tutorial_styles()

    content_str = "<br/>".join([f"&gt; {l}" for l in lines])
    p = Paragraph(f"<b>{title}</b><br/>{content_str}", styles["CodeText"])
    table = Table([[p]], colWidths=[515])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#38bdf8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1e293b")),
    ]))
    return table
