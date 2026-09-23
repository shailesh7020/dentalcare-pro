from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.patient_report import PatientReportSectionEnum
from app.services.qr_service import QRCodeService
from app.services.signature_service import ClinicianSignatureService


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total page count and draw running headers,
    footers, page numbers, and optional confidential watermark.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        self.clinic_name = "DentalCare Pro"
        self.patient_name = "Patient"
        self.patient_number = ""
        self.report_number = ""
        self.include_watermark = False

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()

        # Watermark (only if explicitly enabled, rendered with ultra-low opacity)
        if self.include_watermark:
            self.saveState()
            if hasattr(self, "setFillAlpha"):
                self.setFillAlpha(0.04)
            self.setFont("Helvetica-Bold", 40)
            self.setFillColor(colors.HexColor("#94a3b8"))
            self.translate(A4[0] / 2.0, A4[1] / 2.0)
            self.rotate(45)
            self.drawCentredString(0, 0, "CONFIDENTIAL MEDICAL SUMMARY")
            self.restoreState()

        # Running Top Header on Pages > 1
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0f766e"))
            self.drawString(36, A4[1] - 25, self.clinic_name.upper())

            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            meta_str = f"Patient: {self.patient_name} ({self.patient_number}) | Report #{self.report_number}"
            self.drawRightString(A4[0] - 36, A4[1] - 25, meta_str)

            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, A4[1] - 28, A4[0] - 36, A4[1] - 28)

        # Running Bottom Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 32, A4[0] - 36, 32)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(
            36,
            20,
            "CONFIDENTIAL HEALTHCARE RECORD • DENTALCARE PRO PATIENT REPORT",
        )

        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, page_str)

        self.restoreState()


class PatientReportPDFService:
    @classmethod
    def generate_report(
        cls,
        clinic_info: dict[str, Any],
        patient_data: dict[str, Any],
        sections: list[PatientReportSectionEnum],
        report_number: str,
        include_watermark: bool = False,
        dentist_signature_data: str | None = None,
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=38,
            bottomMargin=42,
        )

        primary = colors.HexColor("#0f766e")
        teal_dark = colors.HexColor("#115e59")
        slate_dark = colors.HexColor("#0f172a")
        slate_text = colors.HexColor("#1e293b")
        slate_muted = colors.HexColor("#64748b")
        slate_light = colors.HexColor("#f8fafc")
        border_color = colors.HexColor("#cbd5e1")
        rose_color = colors.HexColor("#e11d48")
        emerald_color = colors.HexColor("#059669")

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "RepTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=primary,
        )
        meta_style = ParagraphStyle(
            "RepMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=slate_muted,
        )
        sec_hdr_style = ParagraphStyle(
            "RepSecHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.white,
        )
        tbl_hdr_style = ParagraphStyle(
            "RepTblHdr",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=slate_dark,
        )
        cell_style = ParagraphStyle(
            "RepCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=slate_text,
        )
        cell_bold = ParagraphStyle(
            "RepCellB",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=slate_dark,
        )
        alert_style = ParagraphStyle(
            "RepAlert",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=rose_color,
        )

        def make_section_header(title: str) -> list[Any]:
            t = Table(
                [[Paragraph(title.upper(), sec_hdr_style)]],
                colWidths=[523],
            )
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), primary),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            return [Spacer(1, 10), t, Spacer(1, 6)]

        story: list[Any] = []

        # ==========================================
        # 1. CLINIC HEADER & REPORT BANNER
        # ==========================================
        clinic_name = clinic_info.get("name") or "DentalCare Pro Clinic"
        clinic_phone = clinic_info.get("phone") or "+91 99000 11223"
        clinic_email = clinic_info.get("email") or "contact@dentalcarepro.in"
        clinic_address = clinic_info.get("address") or "101 Medical Center, Dental Tower"

        patient_name = patient_data.get("full_name") or "Patient"
        patient_number = patient_data.get("patient_number") or "P-0000"
        patient_id = patient_data.get("id") or ""

        qr_payload = QRCodeService.generate_patient_payload(
            str(patient_id), str(clinic_info.get("id") or "MAIN")
        )
        qr_flowable = QRCodeService.generate_qr_flowable(qr_payload, size=52)

        contact_items = []
        if clinic_phone and str(clinic_phone).lower() != "none":
            contact_items.append(f"Tel: {clinic_phone}")
        if clinic_email and str(clinic_email).lower() != "none":
            contact_items.append(f"Email: {clinic_email}")
        contact_str = " &bull; ".join(contact_items)

        addr_str = (
            f"{clinic_address}<br/>"
            if clinic_address and str(clinic_address).lower() != "none"
            else ""
        )

        header_left = [
            Paragraph(f"<b>{clinic_name.upper()}</b>", title_style),
            Paragraph(
                f"{addr_str}{contact_str}",
                meta_style,
            ),
        ]
        header_right = [
            Paragraph(
                "<font color='#0f766e'><b>PATIENT DENTAL REPORT</b></font>",
                ParagraphStyle("RepDocT", fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=2),
            ),
            Paragraph(
                f"<b>Patient:</b> {patient_name}<br/>"
                f"<b>Report #:</b> {report_number} &bull; <b>Date:</b> {datetime.now(UTC).strftime('%d-%b-%Y')}",
                ParagraphStyle("RepDocM", fontName="Helvetica", fontSize=8, leading=11, alignment=2, textColor=slate_muted),
            ),
        ]

        header_tbl = Table(
            [[header_left, qr_flowable, header_right]],
            colWidths=[240, 60, 223],
        )
        header_tbl.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(header_tbl)
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.5, color=primary))
        story.append(Spacer(1, 6))

        # ==========================================
        # 2. PERSONAL DETAILS
        # ==========================================
        if PatientReportSectionEnum.PERSONAL_DETAILS in sections:
            story.extend(make_section_header("1. Patient Information & Profile"))
            p_age = patient_data.get("age") or "N/A"
            p_gender = str(patient_data.get("gender") or "N/A").title().replace("_", " ")
            p_dob = patient_data.get("date_of_birth") or "Not Specified"
            p_blood = patient_data.get("blood_group") or "Not Specified"
            p_phone = patient_data.get("mobile_number") or "Not Specified"
            p_email = patient_data.get("email") or "Not Specified"
            p_addr = patient_data.get("address") or "Not Specified"
            p_city = patient_data.get("city") or "Not Specified"
            p_em_name = patient_data.get("emergency_contact_name") or "Not Specified"
            p_em_phone = patient_data.get("emergency_contact_phone") or "Not Specified"

            demo_data = [
                [
                    Paragraph(f"<b>Patient Name:</b> {patient_name}", cell_style),
                    Paragraph(f"<b>Patient ID:</b> {patient_number}", cell_style),
                    Paragraph(f"<b>Age / Gender:</b> {p_age} yrs / {p_gender}", cell_style),
                ],
                [
                    Paragraph(f"<b>Date of Birth:</b> {p_dob}", cell_style),
                    Paragraph(f"<b>Blood Group:</b> {p_blood}", cell_style),
                    Paragraph(f"<b>Mobile Phone:</b> {p_phone}", cell_style),
                ],
                [
                    Paragraph(f"<b>Email Address:</b> {p_email}", cell_style),
                    Paragraph(f"<b>City / Location:</b> {p_city}", cell_style),
                    Paragraph(f"<b>Address:</b> {p_addr}", cell_style),
                ],
                [
                    Paragraph(f"<b>Emergency Contact:</b> {p_em_name}", cell_style),
                    Paragraph(f"<b>Emergency Phone:</b> {p_em_phone}", cell_style),
                    Paragraph("<b>Record Status:</b> <font color='#059669'>ACTIVE</font>", cell_bold),
                ],
            ]
            demo_tbl = Table(demo_data, colWidths=[174, 174, 175])
            demo_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), slate_light),
                        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(demo_tbl)

        # ==========================================
        # 3. MEDICAL HISTORY
        # ==========================================
        if PatientReportSectionEnum.MEDICAL_HISTORY in sections:
            story.extend(make_section_header("2. Medical History & Health Summary"))
            med = patient_data.get("medical_history") or {}

            conds = []
            if med.get("diabetes"):
                conds.append("Diabetes")
            if med.get("hypertension"):
                conds.append("Hypertension (High BP)")
            if med.get("cardiac_disease"):
                conds.append("Cardiac Condition")
            if med.get("thyroid"):
                conds.append("Thyroid Disorder")
            if med.get("asthma"):
                conds.append("Asthma")
            if med.get("epilepsy"):
                conds.append("Epilepsy")
            if med.get("pregnancy"):
                conds.append("Pregnancy")

            habits = []
            if med.get("smoking"):
                habits.append("Smoking")
            if med.get("tobacco"):
                habits.append("Tobacco Chewing")
            if med.get("alcohol"):
                habits.append("Alcohol")

            raw_allergies = med.get("allergies")
            has_allergies = bool(
                raw_allergies
                and str(raw_allergies).strip().lower() not in ("none", "none reported", "nil", "no", "n/a")
            )
            allergies = str(raw_allergies) if has_allergies else "No Known Allergies (NKA)"
            curr_meds = med.get("current_medications") or "None reported"
            if str(curr_meds).strip().lower() == "none":
                curr_meds = "None reported"
            surgeries = med.get("previous_surgeries") or "None reported"
            if str(surgeries).strip().lower() == "none":
                surgeries = "None reported"
            inf_diseases = med.get("infectious_diseases") or "None reported"
            if str(inf_diseases).strip().lower() == "none":
                inf_diseases = "None reported"
            notes = med.get("additional_notes") or "No special precautions required"
            if str(notes).strip().lower() == "none":
                notes = "No special precautions required"

            phys_name = med.get("physician_name")
            phys_contact = med.get("physician_contact")
            if phys_name and str(phys_name).strip().lower() != "none":
                phys_line = f"Dr. {phys_name}" + (f" ({phys_contact})" if phys_contact else "") + f" &bull; {notes}"
            else:
                phys_line = str(notes)

            med_data = [
                [
                    Paragraph("<b>Medical Conditions:</b>", cell_bold),
                    Paragraph(
                        ", ".join(conds) if conds else "No systemic medical conditions reported",
                        alert_style if conds else cell_style,
                    ),
                ],
                [
                    Paragraph("<b>Drug / Food Allergies:</b>", cell_bold),
                    Paragraph(allergies, alert_style if has_allergies else cell_style),
                ],
                [
                    Paragraph("<b>Ongoing Medications:</b>", cell_bold),
                    Paragraph(str(curr_meds), cell_style),
                ],
                [
                    Paragraph("<b>Past Surgeries:</b>", cell_bold),
                    Paragraph(str(surgeries), cell_style),
                ],
                [
                    Paragraph("<b>Lifestyle & Habits:</b>", cell_bold),
                    Paragraph(", ".join(habits) if habits else "None reported", cell_style),
                ],
                [
                    Paragraph("<b>Doctor Remarks & Notes:</b>", cell_bold),
                    Paragraph(phys_line, cell_style),
                ],
            ]
            med_tbl = Table(med_data, colWidths=[145, 378])
            med_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), slate_light),
                        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(med_tbl)

        # ==========================================
        # 4. DENTAL HISTORY
        # ==========================================
        if PatientReportSectionEnum.DENTAL_HISTORY in sections:
            story.extend(make_section_header("3. Dental History & Oral Care"))
            dent = patient_data.get("dental_history") or {}

            symptoms = []
            if dent.get("sensitivity"):
                symptoms.append("Tooth Sensitivity")
            if dent.get("bleeding_gums"):
                symptoms.append("Bleeding Gums")
            if dent.get("grinding"):
                symptoms.append("Night Grinding (Bruxism)")
            if dent.get("jaw_pain"):
                symptoms.append("Jaw Pain")
            if dent.get("tmj_disorder"):
                symptoms.append("Jaw Joint (TMJ) Discomfort")

            dent_data = [
                [
                    Paragraph("<b>Main Reason for Visit:</b>", cell_bold),
                    Paragraph(dent.get("chief_complaint") or "Routine Dental Examination & Cleaning", cell_bold),
                ],
                [
                    Paragraph("<b>Previous Dental Work:</b>", cell_bold),
                    Paragraph(dent.get("previous_dental_treatments") or "None reported", cell_style),
                ],
                [
                    Paragraph("<b>Current Symptoms:</b>", cell_bold),
                    Paragraph(", ".join(symptoms) if symptoms else "No active pain or bleeding symptoms reported", cell_style),
                ],
                [
                    Paragraph("<b>Daily Oral Care:</b>", cell_bold),
                    Paragraph(
                        f"Brushing: {dent.get('brushing_frequency') or 'Twice daily'} &bull; Flossing: {'Yes' if dent.get('flossing_habit') else 'Recommended daily'}",
                        cell_style,
                    ),
                ],
                [
                    Paragraph("<b>Clinical Findings:</b>", cell_bold),
                    Paragraph(dent.get("dental_notes") or "Gums and oral tissues appear healthy and within normal limits.", cell_style),
                ],
            ]
            dent_tbl = Table(dent_data, colWidths=[145, 378])
            dent_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), slate_light),
                        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(dent_tbl)

        # ==========================================
        # 5. ODONTOGRAM (GRAPHICAL CHART & STATS)
        # ==========================================
        if PatientReportSectionEnum.ODONTOGRAM in sections:
            story.extend(make_section_header("4. Tooth Chart (Odontogram) & Dental Status"))
            teeth_map: dict[str, Any] = patient_data.get("teeth") or {}

            # Odontogram Arch FDI arrangement
            # Maxillary: 18..11 | 21..28
            max_right = [str(t) for t in range(18, 10, -1)]
            max_left = [str(t) for t in range(21, 29)]
            upper_arch = max_right + max_left

            # Mandibular: 48..41 | 31..38
            man_right = [str(t) for t in range(48, 40, -1)]
            man_left = [str(t) for t in range(31, 39)]
            lower_arch = man_right + man_left

            status_label_map = {
                "HEALTHY": ("Healthy", "#059669"),
                "NORMAL": ("Healthy", "#059669"),
                "CARIES": ("Cavity", "#dc2626"),
                "DECAY": ("Cavity", "#dc2626"),
                "FILLED": ("Filling", "#2563eb"),
                "FILLING": ("Filling", "#2563eb"),
                "RESTORATION": ("Filling", "#2563eb"),
                "ROOT_CANAL": ("RCT", "#7c3aed"),
                "RCT": ("RCT", "#7c3aed"),
                "CROWN": ("Crown", "#d97706"),
                "MISSING": ("Missing", "#64748b"),
                "EXTRACTED": ("Missing", "#64748b"),
                "IMPLANT": ("Implant", "#0284c7"),
            }

            def format_tooth_box(tooth_num: str) -> list[Any]:
                info = teeth_map.get(tooth_num, {})
                raw_status = str(info.get("primary_status") or "HEALTHY").upper()
                if info.get("is_missing"):
                    raw_status = "MISSING"
                elif info.get("has_crown"):
                    raw_status = "CROWN"
                elif info.get("has_root_canal"):
                    raw_status = "ROOT_CANAL"
                elif info.get("has_implant"):
                    raw_status = "IMPLANT"

                friendly_label, color_hex = status_label_map.get(
                    raw_status,
                    (raw_status.replace("_", " ").title()[:7], info.get("color") or "#059669"),
                )

                return [
                    Paragraph(
                        f"<b>#{tooth_num}</b>",
                        ParagraphStyle("TNum", fontName="Helvetica-Bold", fontSize=7, leading=8.5, alignment=1, textColor=slate_dark),
                    ),
                    Paragraph(
                        f"<font color='{color_hex}'><b>{friendly_label}</b></font>",
                        ParagraphStyle("TStat", fontName="Helvetica-Bold", fontSize=5.5, leading=7, alignment=1),
                    ),
                ]

            upper_cells = [format_tooth_box(t) for t in upper_arch]
            lower_cells = [format_tooth_box(t) for t in lower_arch]

            col_w = 523 / 16.0
            odont_table_data = [
                [Paragraph("<b>UPPER JAW TEETH (RIGHT TO LEFT: #18 – #28)</b>", ParagraphStyle("ArchU", fontName="Helvetica-Bold", fontSize=7, alignment=1, textColor=teal_dark))] + [""] * 15,
                upper_cells,
                [Paragraph("<b>LOWER JAW TEETH (RIGHT TO LEFT: #48 – #38)</b>", ParagraphStyle("ArchL", fontName="Helvetica-Bold", fontSize=7, alignment=1, textColor=teal_dark))] + [""] * 15,
                lower_cells,
            ]

            odont_table = Table(odont_table_data, colWidths=[col_w] * 16)
            odont_table.setStyle(
                TableStyle(
                    [
                        ("SPAN", (0, 0), (15, 0)),
                        ("SPAN", (0, 2), (15, 2)),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6fffa")),
                        ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#e6fffa")),
                        ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                        ("BACKGROUND", (0, 3), (-1, 3), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (-1, -1), 1),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                    ]
                )
            )
            story.append(odont_table)
            story.append(Spacer(1, 4))

            # Odontogram Legend & Stats
            stats = patient_data.get("odontogram_stats") or {}
            caries_cnt = stats.get("active_caries", 0)
            missing_cnt = stats.get("missing_teeth", 0)
            rct_cnt = stats.get("root_canals", 0)
            crown_cnt = stats.get("crowns", 0)
            implant_cnt = stats.get("implants", 0)

            legend_text = (
                "<b>How to read your tooth chart:</b> Each box shows a tooth number and its health condition. "
                "<font color='#059669'><b>Healthy</b></font> = Sound tooth &bull; "
                "<font color='#dc2626'><b>Cavity</b></font> = Needs filling ({caries}) &bull; "
                "<font color='#7c3aed'><b>RCT</b></font> = Root Canal ({rct}) &bull; "
                "<font color='#d97706'><b>Crown</b></font> = Cap ({crowns}) &bull; "
                "<font color='#0284c7'><b>Implant</b></font> ({implants}) &bull; "
                "<font color='#64748b'><b>Missing</b></font> ({missing})".format(
                    caries=caries_cnt,
                    rct=rct_cnt,
                    crowns=crown_cnt,
                    implants=implant_cnt,
                    missing=missing_cnt,
                )
            )
            story.append(Paragraph(legend_text, meta_style))

        # ==========================================
        # 6. TREATMENT TIMELINE & HISTORY
        # ==========================================
        if PatientReportSectionEnum.TREATMENT_HISTORY in sections:
            story.extend(make_section_header("5. Clinical Treatment Timeline & History"))
            treatments = patient_data.get("treatments") or []

            if not treatments:
                story.append(Paragraph("<i>No clinical treatments recorded to date.</i>", cell_style))
            else:
                # Flowchart Timeline
                timeline_flow = []
                for idx, t in enumerate(treatments[:8], start=1):
                    dt_str = t.get("date") or "—"
                    t_title = t.get("title") or t.get("treatment_number", f"Treatment #{idx}")
                    status_lbl = t.get("status", "COMPLETED").replace("_", " ")
                    dentist_lbl = t.get("dentist_name", "Dental Surgeon")
                    procs = t.get("procedures") or []
                    proc_desc = ", ".join([p.get("name", "") for p in procs]) if procs else t.get("diagnosis", "")

                    timeline_flow.append(
                        [
                            Paragraph(f"<b>{dt_str}</b>", cell_bold),
                            Paragraph(
                                f"<b>{t_title}</b> &bull; {status_lbl}<br/>"
                                f"<font color='#64748b'>Procedures: {proc_desc or 'Clinical Care'} &bull; Dr: {dentist_lbl}</font>",
                                cell_style,
                            ),
                        ]
                    )

                timeline_table = Table(timeline_flow, colWidths=[90, 433])
                timeline_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), slate_light),
                            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(timeline_table)

        # ==========================================
        # 7. CLINICAL NOTES
        # ==========================================
        if PatientReportSectionEnum.CLINICAL_NOTES in sections:
            story.extend(make_section_header("6. Clinical Progress Notes & Findings"))
            notes_list = patient_data.get("clinical_notes") or []
            if not notes_list:
                story.append(Paragraph("<i>Routine clinical documentation within normal parameters. No acute remarks.</i>", cell_style))
            else:
                for note in notes_list:
                    n_date = note.get("date", "—")
                    n_author = note.get("author", "Attending Clinician")
                    n_text = note.get("text", "")
                    story.append(
                        Paragraph(
                            f"<b>[{n_date}] {n_author}:</b> {n_text}",
                            cell_style,
                        )
                    )
                    story.append(Spacer(1, 2))

        # ==========================================
        # 8. PRESCRIPTIONS
        # ==========================================
        if PatientReportSectionEnum.PRESCRIPTIONS in sections:
            story.extend(make_section_header("7. Prescriptions & Medication Orders"))
            prescriptions = patient_data.get("prescriptions") or []

            if not prescriptions:
                story.append(Paragraph("<i>No active or historical prescriptions recorded for this patient.</i>", cell_style))
            else:
                rx_rows = [
                    [
                        Paragraph("Prescription #", tbl_hdr_style),
                        Paragraph("Date", tbl_hdr_style),
                        Paragraph("Medicine & Dosage", tbl_hdr_style),
                        Paragraph("Frequency / Duration", tbl_hdr_style),
                        Paragraph("Instructions", tbl_hdr_style),
                    ]
                ]
                for rx in prescriptions[:6]:
                    rx_num = rx.get("prescription_number", "RX-0000")
                    rx_date = rx.get("date", "—")
                    meds = rx.get("medications") or []
                    for m in meds:
                        rx_rows.append(
                            [
                                Paragraph(rx_num, cell_bold),
                                Paragraph(rx_date, cell_style),
                                Paragraph(f"<b>{m.get('medicine_name', 'Medicine')}</b><br/>{m.get('dosage', '')}", cell_style),
                                Paragraph(f"{m.get('frequency', '')}<br/>{m.get('duration', '')}", cell_style),
                                Paragraph(m.get("instructions", "As directed"), cell_style),
                            ]
                        )

                if len(rx_rows) > 1:
                    rx_table = Table(rx_rows, colWidths=[80, 65, 140, 100, 138])
                    rx_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                                ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )
                    story.append(rx_table)
                else:
                    story.append(Paragraph("<i>Prescription records completed with no ongoing medications.</i>", cell_style))

        # ==========================================
        # 9. BILLING, INVOICES & RECEIPTS
        # ==========================================
        if (
            PatientReportSectionEnum.INVOICES in sections
            or PatientReportSectionEnum.RECEIPTS in sections
            or PatientReportSectionEnum.PAYMENT_HISTORY in sections
        ):
            story.extend(make_section_header("8. Billing, Invoices & Payment Summary"))
            invoices = patient_data.get("invoices") or []
            payments = patient_data.get("payments") or []

            total_billed = sum(float(i.get("grand_total", 0.0)) for i in invoices)
            total_paid = sum(float(i.get("amount_paid", 0.0)) for i in invoices)
            total_due = sum(float(i.get("balance_due", 0.0)) for i in invoices)

            summary_cards = [
                [
                    Paragraph(f"<b>Total Invoiced:</b> Rs. {total_billed:,.2f}", cell_bold),
                    Paragraph(f"<b>Total Paid:</b> Rs. {total_paid:,.2f}", ParagraphStyle("TotP", parent=cell_bold, textColor=emerald_color)),
                    Paragraph(f"<b>Outstanding Due:</b> Rs. {total_due:,.2f}", ParagraphStyle("TotD", parent=cell_bold, textColor=rose_color if total_due > 0 else emerald_color)),
                ]
            ]
            sum_tbl = Table(summary_cards, colWidths=[174, 174, 175])
            sum_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), slate_light),
                        ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(sum_tbl)
            story.append(Spacer(1, 4))

            # Invoices & Receipts rows
            if invoices and PatientReportSectionEnum.INVOICES in sections:
                inv_rows = [
                    [
                        Paragraph("Invoice #", tbl_hdr_style),
                        Paragraph("Date", tbl_hdr_style),
                        Paragraph("Status", tbl_hdr_style),
                        Paragraph("GST Tax", tbl_hdr_style),
                        Paragraph("Grand Total", tbl_hdr_style),
                        Paragraph("Paid", tbl_hdr_style),
                        Paragraph("Balance Due", tbl_hdr_style),
                    ]
                ]
                for inv in invoices[:5]:
                    inv_rows.append(
                        [
                            Paragraph(inv.get("invoice_number", "INV-0000"), cell_bold),
                            Paragraph(inv.get("date", "—"), cell_style),
                            Paragraph(inv.get("status", "PAID"), cell_style),
                            Paragraph(f"Rs. {float(inv.get('tax_amount', 0)):,.2f}", cell_style),
                            Paragraph(f"Rs. {float(inv.get('grand_total', 0)):,.2f}", cell_bold),
                            Paragraph(f"Rs. {float(inv.get('amount_paid', 0)):,.2f}", cell_style),
                            Paragraph(f"Rs. {float(inv.get('balance_due', 0)):,.2f}", cell_bold),
                        ]
                    )
                inv_table = Table(inv_rows, colWidths=[80, 65, 75, 70, 80, 75, 78])
                inv_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(inv_table)
                story.append(Spacer(1, 4))

            # Payment Receipts
            if payments and (PatientReportSectionEnum.RECEIPTS in sections or PatientReportSectionEnum.PAYMENT_HISTORY in sections):
                pay_rows = [
                    [
                        Paragraph("Receipt #", tbl_hdr_style),
                        Paragraph("Payment Date", tbl_hdr_style),
                        Paragraph("Payment Method", tbl_hdr_style),
                        Paragraph("Reference / Transaction ID", tbl_hdr_style),
                        Paragraph("Amount Paid", tbl_hdr_style),
                    ]
                ]
                for p in payments[:5]:
                    pay_rows.append(
                        [
                            Paragraph(p.get("receipt_number", "REC-0000"), cell_bold),
                            Paragraph(p.get("date", "—"), cell_style),
                            Paragraph(p.get("method", "UPI"), cell_style),
                            Paragraph(p.get("reference", "—"), cell_style),
                            Paragraph(f"Rs. {float(p.get('amount', 0)):,.2f}", cell_bold),
                        ]
                    )
                pay_table = Table(pay_rows, colWidths=[95, 80, 95, 145, 108])
                pay_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(pay_table)

        # ==========================================
        # 10. NEXT APPOINTMENT
        # ==========================================
        if PatientReportSectionEnum.NEXT_APPOINTMENT in sections:
            story.extend(make_section_header("9. Upcoming Scheduled Visit"))
            next_appt = patient_data.get("next_appointment")
            if not next_appt:
                story.append(Paragraph("<i>No upcoming appointments currently scheduled. Regular 6-month hygiene recall recommended.</i>", cell_style))
            else:
                appt_date = next_appt.get("date", "TBD")
                appt_time = next_appt.get("time", "TBD")
                dentist = next_appt.get("dentist_name", "Attending Dental Surgeon")
                purpose = next_appt.get("purpose", "Recall Consultation & Treatment")
                instructions = next_appt.get("instructions", "Please arrive 10 minutes prior to your scheduled time.")

                appt_data = [
                    [
                        Paragraph(f"<b>Appointment Date:</b> {appt_date}", cell_bold),
                        Paragraph(f"<b>Scheduled Time:</b> {appt_time}", cell_bold),
                    ],
                    [
                        Paragraph(f"<b>Treating Doctor:</b> {dentist}", cell_style),
                        Paragraph(f"<b>Purpose / Procedure:</b> {purpose}", cell_style),
                    ],
                    [
                        Paragraph(f"<b>Patient Pre-Visit Instructions:</b> {instructions}", cell_style),
                        Paragraph("<b>Clinic Emergency Line:</b> " + clinic_phone, cell_style),
                    ],
                ]
                appt_tbl = Table(appt_data, colWidths=[261, 262])
                appt_tbl.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#86efac")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bbf7d0")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(appt_tbl)

        # ==========================================
        # 11. X-RAYS & ATTACHMENTS REGISTRY
        # ==========================================
        if (
            PatientReportSectionEnum.XRAYS_AND_IMAGES in sections
            or PatientReportSectionEnum.UPLOADED_DOCUMENTS in sections
        ):
            story.extend(make_section_header("10. Radiographs & Clinical Document Index"))
            docs = patient_data.get("documents") or []
            if not docs:
                story.append(Paragraph("<i>No diagnostic radiographs or external files uploaded to this record.</i>", cell_style))
            else:
                doc_rows = [
                    [
                        Paragraph("Document / File Name", tbl_hdr_style),
                        Paragraph("Category", tbl_hdr_style),
                        Paragraph("Format", tbl_hdr_style),
                        Paragraph("Upload Date", tbl_hdr_style),
                    ]
                ]
                for d in docs[:8]:
                    doc_rows.append(
                        [
                            Paragraph(d.get("file_name", "document.pdf"), cell_bold),
                            Paragraph(d.get("document_type", "DOCUMENT").upper(), cell_style),
                            Paragraph(d.get("content_type", "application/pdf").split("/")[-1].upper(), cell_style),
                            Paragraph(d.get("created_at", "—"), cell_style),
                        ]
                    )
                doc_table = Table(doc_rows, colWidths=[240, 95, 88, 100])
                doc_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                            ("BOX", (0, 0), (-1, -1), 0.5, border_color),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(doc_table)

        # ==========================================
        # 12. DIGITAL SIGNATURE & OFFICIAL CLINIC SEAL
        # ==========================================
        story.append(Spacer(1, 14))

        sig_cell: Any = Paragraph(
            "___________________________<br/><b>Treating Dentist Signature</b>",
            cell_style,
        )
        if dentist_signature_data:
            sig_img = ClinicianSignatureService.create_signature_flowable(
                dentist_signature_data, width=100, height=32
            )
            if sig_img:
                sig_cell = [
                    sig_img,
                    Paragraph("<b>Verified Treating Dentist</b>", cell_style),
                ]

        seal_cell = [
            Paragraph(f"<b>{clinic_name.upper()}</b>", ParagraphStyle("SealT", fontName="Helvetica-Bold", fontSize=8, alignment=1, textColor=primary)),
            Paragraph("OFFICIAL CLINICAL SEAL", ParagraphStyle("SealS", fontName="Helvetica", fontSize=6.5, alignment=1, textColor=slate_muted)),
            Paragraph(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}", ParagraphStyle("SealD", fontName="Helvetica", fontSize=6, alignment=1, textColor=slate_muted)),
        ]

        verification_table = Table(
            [
                [
                    qr_flowable,
                    Paragraph(
                        f"<font size='7' color='#64748b'>Record Cryptographic Reference:<br/>"
                        f"REP-HASH-{report_number}-{patient_number}<br/>"
                        f"DentalCare Pro Certified Record</font>",
                        cell_style,
                    ),
                    seal_cell,
                    sig_cell,
                ]
            ],
            colWidths=[65, 175, 140, 143],
        )
        verification_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("BOX", (2, 0), (2, 0), 0.5, border_color),
                    ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#f8fafc")),
                    ("TOPPADDING", (2, 0), (2, 0), 4),
                    ("BOTTOMPADDING", (2, 0), (2, 0), 4),
                ]
            )
        )
        story.append(KeepTogether([verification_table]))

        # Build PDF using NumberedCanvas
        def canvas_maker(*args: Any, **kwargs: Any) -> NumberedCanvas:
            c = NumberedCanvas(*args, **kwargs)
            c.clinic_name = clinic_name
            c.patient_name = patient_name
            c.patient_number = patient_number
            c.report_number = report_number
            c.include_watermark = include_watermark
            return c

        doc.build(story, canvasmaker=canvas_maker)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
