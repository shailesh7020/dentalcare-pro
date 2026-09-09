from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.prescription import PrescriptionDetail
from app.services.qr_service import QRCodeService
from app.services.signature_service import ClinicianSignatureService


class PrescriptionPDFService:
    @staticmethod
    def generate_pdf(
        rx: PrescriptionDetail,
        signature_data: str | None = None,
        verification_hash: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        primary_color = colors.HexColor("#0f766e")  # Dental Teal
        slate_color = colors.HexColor("#1e293b")
        muted_color = colors.HexColor("#64748b")
        alert_bg = colors.HexColor("#fef2f2")
        alert_text = colors.HexColor("#991b1b")

        clinic_name_style = ParagraphStyle(
            "ClinicName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_color,
        )

        doctor_title_style = ParagraphStyle(
            "DoctorTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=slate_color,
            alignment=2,  # Right aligned
        )

        doctor_meta_style = ParagraphStyle(
            "DoctorMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=muted_color,
            alignment=2,
        )

        rx_symbol_style = ParagraphStyle(
            "RxSymbol",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=24,
            textColor=primary_color,
        )

        label_style = ParagraphStyle(
            "LabelStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        value_style = ParagraphStyle(
            "ValueStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=0,
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=slate_color,
        )

        table_cell_bold_style = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=slate_color,
        )

        story: list[Any] = []

        # 1. Header: Clinic Info & Prescribing Doctor
        clinic_name = rx.clinic_name or "DentalCare Pro Clinic"
        clinic_phone = rx.clinic_phone or "+91 98765 43210"
        clinic_email = rx.clinic_email or "care@dentalcarepro.com"

        clinic_html = f"<b>{clinic_name}</b><br/>"
        clinic_meta_html = (
            f"Multi-Speciality Dental & Implant Center<br/>"
            f"Phone: {clinic_phone} &bull; Email: {clinic_email}<br/>"
            f"Registration No: DCI-CLI-2026-0881"
        )

        dentist_name = rx.dentist_name or "Dr. Treating Dentist"
        dentist_reg = rx.dentist_registration or "DCI-REG-DENTIST"
        dentist_html = f"<b>{dentist_name}</b><br/>"
        dentist_meta_html = (
            f"BDS, MDS (Oral & Maxillofacial Surgery)<br/>"
            f"Dental Council Reg: {dentist_reg}<br/>"
            f"Consultant Dental Surgeon"
        )

        header_table = Table(
            [
                [
                    Paragraph(clinic_html + clinic_meta_html, clinic_name_style),
                    Paragraph(dentist_html + dentist_meta_html, doctor_title_style),
                ]
            ],
            colWidths=[310, 210],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 8))

        # Divider
        story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=4, spaceAfter=8))

        # 2. Patient Demographics & Prescription Metadata
        patient_name = rx.patient_name or "Patient"
        patient_num = rx.patient_number or "PAT-000000"
        age_gender = f"{rx.patient_age or 'N/A'} yrs / {rx.patient_gender or 'N/A'}"
        rx_date = rx.date.strftime("%d %B %Y") if rx.date else "N/A"
        treatment_num = rx.treatment_number or "N/A"

        patient_info_data = [
            [
                Paragraph("<b>Patient Name:</b>", label_style),
                Paragraph(patient_name, value_style),
                Paragraph("<b>Date:</b>", label_style),
                Paragraph(rx_date, value_style),
            ],
            [
                Paragraph("<b>Patient ID:</b>", label_style),
                Paragraph(patient_num, value_style),
                Paragraph("<b>Prescription No:</b>", label_style),
                Paragraph(f"<b>{rx.prescription_number}</b>", value_style),
            ],
            [
                Paragraph("<b>Age / Gender:</b>", label_style),
                Paragraph(age_gender, value_style),
                Paragraph("<b>Treatment Ref:</b>", label_style),
                Paragraph(treatment_num, value_style),
            ],
        ]

        patient_table = Table(patient_info_data, colWidths=[80, 180, 95, 165])
        patient_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(patient_table)
        story.append(Spacer(1, 6))

        # 3. Medical Alerts / Allergy Banner
        if rx.patient_alerts:
            alerts_text = "  &bull;  ".join(rx.patient_alerts)
            alert_p = Paragraph(
                f"<b>MEDICAL ALERTS & ALLERGIES:</b> {alerts_text}",
                ParagraphStyle("AlertText", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, textColor=alert_text),
            )
            alert_table = Table([[alert_p]], colWidths=[520])
            alert_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), alert_bg),
                        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#fca5a5")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(alert_table)
            story.append(Spacer(1, 6))

        # 4. Clinical Diagnosis
        diagnosis_p = Paragraph(f"<b>Clinical Diagnosis:</b> {rx.diagnosis}", value_style)
        story.append(diagnosis_p)
        if rx.notes:
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<b>Clinical Notes:</b> {rx.notes}", value_style))

        story.append(Spacer(1, 10))

        # 5. Rx Symbol
        story.append(Paragraph("&#8478;", rx_symbol_style))
        story.append(Spacer(1, 4))

        # 6. Medicines Table
        med_headers = [
            Paragraph("#", table_header_style),
            Paragraph("Medicine & Strength", table_header_style),
            Paragraph("Form / Route", table_header_style),
            Paragraph("Dosage", table_header_style),
            Paragraph("Frequency / Timing", table_header_style),
            Paragraph("Duration", table_header_style),
            Paragraph("Food / Instructions", table_header_style),
        ]

        med_data = [med_headers]
        for idx, item in enumerate(rx.items, start=1):
            med_name_content = f"<b>{item.medicine_name}</b> {item.strength}"
            if item.generic_name:
                med_name_content += f"<br/><font color='#64748b' size='7'>({item.generic_name})</font>"

            form_route = f"{item.form.capitalize()} / {item.route}"
            freq_timing = f"<b>{item.frequency}</b>"
            if item.timing:
                freq_timing += f"<br/><font size='7'>{item.timing}</font>"

            food_notes = item.food_instructions or "As directed"
            if item.notes:
                food_notes += f"<br/><font color='#047857' size='7'>{item.notes}</font>"

            row = [
                Paragraph(str(idx), table_cell_style),
                Paragraph(med_name_content, table_cell_style),
                Paragraph(form_route, table_cell_style),
                Paragraph(item.dosage, table_cell_bold_style),
                Paragraph(freq_timing, table_cell_style),
                Paragraph(f"{item.duration} ({item.quantity} units)", table_cell_style),
                Paragraph(food_notes, table_cell_style),
            ]
            med_data.append(row)

        med_table = Table(med_data, colWidths=[20, 135, 65, 55, 85, 65, 95])
        med_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(med_table)
        story.append(Spacer(1, 10))

        # 7. Instructions & Follow-up Box
        if rx.instructions:
            inst_p = Paragraph(f"<b>Instructions & Clinical Advice:</b><br/>{rx.instructions}", value_style)
            story.append(inst_p)
            story.append(Spacer(1, 6))

        if rx.follow_up_date:
            follow_p = Paragraph(
                f"<b>Next Clinical Review / Follow-up:</b> {rx.follow_up_date.strftime('%d %B %Y')}",
                ParagraphStyle("FollowStyle", parent=value_style, fontName="Helvetica-Bold", textColor=primary_color),
            )
            story.append(follow_p)
            story.append(Spacer(1, 14))

        # 8. Signature & Stamp Footer
        story.append(Spacer(1, 15))
        actual_hash = verification_hash or f"DCP-RX-{str(rx.id)[:12].upper()}"
        qr_flow = QRCodeService.generate_qr_flowable(
            QRCodeService.generate_prescription_payload(str(rx.id), actual_hash),
            size=55,
        )

        dentist_sig_cell: list[Any] = []
        if signature_data:
            sig_img = ClinicianSignatureService.create_signature_flowable(signature_data, width=110, height=35)
            if sig_img:
                dentist_sig_cell.append(sig_img)
        dentist_sig_cell.append(
            Paragraph(
                f"______________________________________<br/>"
                f"<b>{dentist_name}</b><br/>"
                f"<font size='7' color='#64748b'>Authorized Dental Surgeon &bull; Reg: {dentist_reg}</font>",
                doctor_meta_style,
            )
        )

        sig_data = [
            [
                qr_flow,
                Paragraph(
                    "<font size='7' color='#94a3b8'>Status: "
                    f"<b>{rx.status}</b> &bull; Issued at: {rx.issued_at or rx.created_at}</font><br/>"
                    "<font size='6.5' color='#94a3b8'>Digital Verification Hash:<br/>"
                    f"{actual_hash}</font>",
                    table_cell_style,
                ),
                dentist_sig_cell,
            ]
        ]
        sig_table = Table(sig_data, colWidths=[65, 205, 250])
        sig_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(sig_table)
        story.append(Spacer(1, 10))

        # Fine print disclaimer
        disclaimer = Paragraph(
            "<font size='6.5' color='#94a3b8'>Notice: This is a verified electronic medical record prescription issued under DentalCare Pro EHR standards. Valid only with clinician credentials.</font>",
            ParagraphStyle("Disclaimer", parent=styles["Normal"], alignment=1),
        )
        story.append(disclaimer)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
