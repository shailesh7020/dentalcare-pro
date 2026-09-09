from __future__ import annotations

from datetime import date, datetime
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

from app.services.qr_service import QRCodeService
from app.services.signature_service import ClinicianSignatureService


class ClinicalDocumentPDFService:
    @classmethod
    def _build_header(
        cls,
        clinic_name: str,
        clinic_phone: str,
        clinic_email: str,
        doc_title: str,
        doc_subtitle: str = "",
    ) -> list[Any]:
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")
        muted_color = colors.HexColor("#64748b")

        clinic_name_style = ParagraphStyle(
            "DocClinicName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=primary_color,
        )
        clinic_meta_style = ParagraphStyle(
            "DocClinicMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=muted_color,
        )
        title_style = ParagraphStyle(
            "DocTitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=slate_color,
            alignment=2,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=muted_color,
            alignment=2,
        )

        header_data = [
            [
                Paragraph(f"<b>{clinic_name.upper()}</b>", clinic_name_style),
                Paragraph(doc_title, title_style),
            ],
            [
                Paragraph(f"Tel: {clinic_phone} &bull; Email: {clinic_email}", clinic_meta_style),
                Paragraph(doc_subtitle, subtitle_style),
            ],
        ]
        header_table = Table(header_data, colWidths=[280, 243])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        return [header_table, Spacer(1, 6), HRFlowable(width="100%", thickness=1.5, color=primary_color), Spacer(1, 10)]

    @classmethod
    def generate_treatment_plan_pdf(
        cls,
        clinic_info: dict[str, str],
        patient_info: dict[str, str],
        doctor_info: dict[str, str],
        plan_title: str,
        procedures: list[dict[str, Any]],
        total_estimated: float,
        notes: str = "",
        signature_data: str | None = None,
        verification_hash: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")

        cell_style = ParagraphStyle("TCell", fontName="Helvetica", fontSize=8.5, leading=11, textColor=slate_color)
        cell_bold = ParagraphStyle("TCellB", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=slate_color)
        hdr_style = ParagraphStyle("THdr", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)

        story: list[Any] = []
        story.extend(
            cls._build_header(
                clinic_name=clinic_info.get("name", "DentalCare Pro Clinic"),
                clinic_phone=clinic_info.get("phone", "+91 98765 43210"),
                clinic_email=clinic_info.get("email", "info@dentalcarepro.in"),
                doc_title="TREATMENT PLAN ESTIMATE",
                doc_subtitle=f"Date: {date.today().strftime('%d-%b-%Y')}",
            )
        )

        # Patient & Doctor Info
        pat_data = [
            [
                Paragraph(f"<b>Patient Name:</b> {patient_info.get('name', 'N/A')}", cell_style),
                Paragraph(f"<b>Treating Doctor:</b> {doctor_info.get('name', 'Dental Surgeon')}", cell_style),
            ],
            [
                Paragraph(f"<b>Patient ID:</b> {patient_info.get('id', 'N/A')} &bull; Age/Sex: {patient_info.get('age_gender', 'N/A')}", cell_style),
                Paragraph(f"<b>Specialty / Reg:</b> {doctor_info.get('reg_number', 'N/A')}", cell_style),
            ],
            [
                Paragraph(f"<b>Plan Title:</b> <b>{plan_title}</b>", cell_style),
                Paragraph(f"<b>Status:</b> Proposed Estimate", cell_style),
            ],
        ]
        info_table = Table(pat_data, colWidths=[261, 262])
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(info_table)
        story.append(Spacer(1, 12))

        # Procedures Table
        table_rows = [
            [
                Paragraph("#", hdr_style),
                Paragraph("Tooth", hdr_style),
                Paragraph("Procedure / Description", hdr_style),
                Paragraph("Visits", hdr_style),
                Paragraph("Est. Fee (INR)", hdr_style),
            ]
        ]
        for idx, p in enumerate(procedures, start=1):
            fee = float(p.get("fee", 0.0))
            table_rows.append(
                [
                    Paragraph(str(idx), cell_style),
                    Paragraph(str(p.get("tooth", "-")), cell_bold),
                    Paragraph(f"<b>{p.get('name', '')}</b><br/>{p.get('description', '')}", cell_style),
                    Paragraph(str(p.get("visits", 1)), cell_style),
                    Paragraph(f"₹{fee:,.2f}", cell_bold),
                ]
            )

        # Totals row
        table_rows.append(
            [
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph("<b>Total Estimated Treatment Cost</b>", cell_bold),
                Paragraph("", cell_style),
                Paragraph(f"<b>₹{total_estimated:,.2f}</b>", ParagraphStyle("TotVal", fontName="Helvetica-Bold", fontSize=9, textColor=primary_color)),
            ]
        )

        proc_table = Table(table_rows, colWidths=[25, 55, 275, 55, 113])
        proc_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (4, 1), (4, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#cbd5e1")),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, primary_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(proc_table)
        story.append(Spacer(1, 10))

        if notes:
            story.append(Paragraph(f"<b>Clinical Notes & Phasing:</b><br/>{notes}", cell_style))
            story.append(Spacer(1, 10))

        # Terms
        disclaimer = (
            "<font size='7' color='#64748b'>Terms & Conditions: This treatment plan is an estimate based on current clinical findings. "
            "Unforeseen clinical complications may alter procedure requirements or costs. Estimate valid for 30 days.</font>"
        )
        story.append(Paragraph(disclaimer, cell_style))
        story.append(Spacer(1, 16))

        # Signatures & QR
        v_hash = verification_hash or f"TXPLAN-{patient_info.get('id', 'PAT')}-{int(total_estimated)}"
        qr_flow = QRCodeService.generate_qr_flowable(f"DENTALCARE:PLAN:{v_hash}", size=55)

        sig_cell: Any = Paragraph("___________________________<br/><b>Treating Dentist</b>", cell_style)
        if signature_data:
            sig_img = ClinicianSignatureService.create_signature_flowable(signature_data, width=100, height=35)
            if sig_img:
                sig_cell = [sig_img, Paragraph(f"<b>{doctor_info.get('name', '')}</b>", cell_style)]

        footer_table = Table(
            [
                [
                    qr_flow,
                    Paragraph("<font size='7' color='#94a3b8'>Cryptographic Plan Hash:<br/>" f"{v_hash[:32]}...</font>", cell_style),
                    Paragraph("___________________________<br/><b>Patient Acceptance Signature</b>", cell_style),
                    sig_cell,
                ]
            ],
            colWidths=[65, 140, 160, 158],
        )
        footer_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story.append(footer_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_medical_certificate_pdf(
        cls,
        clinic_info: dict[str, str],
        patient_info: dict[str, str],
        doctor_info: dict[str, str],
        diagnosis: str,
        leave_start_date: date,
        leave_end_date: date,
        resume_date: date,
        recommendations: str = "Advised strict rest and avoidance of strenuous physical activity.",
        signature_data: str | None = None,
        verification_hash: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")

        body_style = ParagraphStyle("CertBody", fontName="Helvetica", fontSize=10, leading=16, textColor=slate_color)
        cert_no = f"MC-{patient_info.get('id', 'PAT')[:6]}-{leave_start_date.strftime('%Y%m%d')}"

        story: list[Any] = []
        story.extend(
            cls._build_header(
                clinic_name=clinic_info.get("name", "DentalCare Pro Clinic"),
                clinic_phone=clinic_info.get("phone", "+91 98765 43210"),
                clinic_email=clinic_info.get("email", "info@dentalcarepro.in"),
                doc_title="MEDICAL CERTIFICATE",
                doc_subtitle=f"Cert #: {cert_no}<br/>Date: {date.today().strftime('%d-%b-%Y')}",
            )
        )
        story.append(Spacer(1, 15))

        cert_text = (
            f"This is to certify that <b>{patient_info.get('name', 'the patient')}</b>, "
            f"aged <b>{patient_info.get('age', 'N/A')} years</b>, Patient ID: <b>{patient_info.get('id', 'N/A')}</b>, "
            f"was examined and treated at this dental clinic on <b>{leave_start_date.strftime('%d %B %Y')}</b>.<br/><br/>"
            f"<b>Clinical Diagnosis & Procedure:</b><br/>{diagnosis}<br/><br/>"
            f"In my professional clinical opinion, the patient was medically unfit to attend work / school / duties from "
            f"<b>{leave_start_date.strftime('%d %B %Y')}</b> to <b>{leave_end_date.strftime('%d %B %Y')}</b> inclusive.<br/><br/>"
            f"The patient is considered fit to resume normal duties on <b>{resume_date.strftime('%d %B %Y')}</b>.<br/><br/>"
            f"<b>Clinical Recommendations & Restrictions:</b><br/>{recommendations}"
        )
        story.append(Paragraph(cert_text, body_style))
        story.append(Spacer(1, 35))

        # Signatures
        v_hash = verification_hash or f"MEDCERT-{cert_no}"
        qr_flow = QRCodeService.generate_qr_flowable(f"DENTALCARE:CERT:{v_hash}", size=60)

        sig_cell: Any = Paragraph("___________________________<br/><b>Treating Dental Surgeon</b>", body_style)
        if signature_data:
            sig_img = ClinicianSignatureService.create_signature_flowable(signature_data, width=120, height=45)
            if sig_img:
                sig_cell = [
                    sig_img,
                    Paragraph(
                        f"<b>{doctor_info.get('name', 'Doctor')}</b><br/>"
                        f"<font size='8' color='#64748b'>Reg: {doctor_info.get('reg_number', 'N/A')}</font>",
                        body_style,
                    ),
                ]

        footer_table = Table(
            [
                [
                    qr_flow,
                    Paragraph(
                        f"<font size='7' color='#94a3b8'>Official Verification Hash:<br/>{v_hash}<br/>"
                        "Verify authenticity at clinic or via DentalCare Pro portal.</font>",
                        body_style,
                    ),
                    sig_cell,
                ]
            ],
            colWidths=[70, 250, 195],
        )
        footer_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story.append(footer_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_appointment_slip_pdf(
        cls,
        clinic_info: dict[str, str],
        patient_info: dict[str, str],
        appointment_info: dict[str, Any],
        instructions: str = "Please arrive 10 minutes prior to your scheduled time. Bring past dental records if any.",
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")

        cell_style = ParagraphStyle("ACell", fontName="Helvetica", fontSize=9, leading=12, textColor=slate_color)
        cell_bold = ParagraphStyle("ACellB", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=slate_color)
        callout_time = ParagraphStyle("ATime", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=primary_color)

        story: list[Any] = []
        story.extend(
            cls._build_header(
                clinic_name=clinic_info.get("name", "DentalCare Pro Clinic"),
                clinic_phone=clinic_info.get("phone", "+91 98765 43210"),
                clinic_email=clinic_info.get("email", "info@dentalcarepro.in"),
                doc_title="APPOINTMENT SLIP",
                doc_subtitle=f"Slip #: APPT-{appointment_info.get('id', 'N/A')[:8].upper()}",
            )
        )
        story.append(Spacer(1, 10))

        # QR payload for fast kiosk / reception scan
        appt_id = str(appointment_info.get("id", ""))
        patient_id = str(patient_info.get("id", ""))
        qr_payload = QRCodeService.generate_appointment_payload(appt_id, patient_id)
        qr_flow = QRCodeService.generate_qr_flowable(qr_payload, size=90)

        slip_data = [
            [
                Paragraph("<b>PATIENT DETAILS</b>", cell_bold),
                Paragraph("<b>APPOINTMENT SCHEDULE</b>", cell_bold),
                Paragraph("<b>KIOSK CHECK-IN</b>", cell_bold),
            ],
            [
                Paragraph(
                    f"Name: <b>{patient_info.get('name', 'N/A')}</b><br/>"
                    f"File #: {patient_info.get('id', 'N/A')}<br/>"
                    f"Phone: {patient_info.get('phone', 'N/A')}",
                    cell_style,
                ),
                Paragraph(
                    f"Date: <b>{appointment_info.get('date', 'N/A')}</b><br/>"
                    f"<font color='#0f766e'><b>Time: {appointment_info.get('time', 'N/A')}</b></font><br/>"
                    f"Dentist: {appointment_info.get('dentist_name', 'Dental Surgeon')}<br/>"
                    f"Chair: {appointment_info.get('chair_number', '1')} &bull; Type: {appointment_info.get('type', 'Consultation')}",
                    cell_style,
                ),
                qr_flow,
            ],
        ]
        slip_table = Table(slip_data, colWidths=[180, 220, 115])
        slip_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(slip_table)
        story.append(Spacer(1, 14))

        # Instructions
        story.append(Paragraph(f"<b>Instructions for Visit:</b><br/>{instructions}", cell_style))
        story.append(Spacer(1, 10))

        # Cancellation Policy
        policy = (
            "<font size='7.5' color='#64748b'><b>Cancellation / Rescheduling Policy:</b> "
            "If you need to change your appointment, please contact us at least 24 hours in advance. "
            "Present this slip or QR code at reception upon arrival for expedited check-in.</font>"
        )
        story.append(Paragraph(policy, cell_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_consent_form_pdf(
        cls,
        clinic_info: dict[str, str],
        patient_info: dict[str, str],
        procedure_name: str,
        risks_and_benefits: str,
        doctor_info: dict[str, str],
        signature_data: str | None = None,
        patient_signature_data: str | None = None,
        verification_hash: str | None = None,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")

        body_style = ParagraphStyle("CBody", fontName="Helvetica", fontSize=8.5, leading=12, textColor=slate_color)
        title_style = ParagraphStyle("CTitle", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=primary_color)

        story: list[Any] = []
        story.extend(
            cls._build_header(
                clinic_name=clinic_info.get("name", "DentalCare Pro Clinic"),
                clinic_phone=clinic_info.get("phone", "+91 98765 43210"),
                clinic_email=clinic_info.get("email", "info@dentalcarepro.in"),
                doc_title="INFORMED CONSENT FORM",
                doc_subtitle=f"Date: {date.today().strftime('%d-%b-%Y')}",
            )
        )
        story.append(Spacer(1, 8))

        story.append(Paragraph(f"<b>PROCEDURE:</b> {procedure_name.upper()}", title_style))
        story.append(Spacer(1, 6))

        consent_clauses = (
            f"I, <b>{patient_info.get('name', 'Patient')}</b>, hereby authorize "
            f"<b>{doctor_info.get('name', 'the treating doctor')}</b> and designated dental assistants to perform "
            f"the recommended procedure(s): <b>{procedure_name}</b>.<br/><br/>"
            f"<b>1. Clinical Explanation & Risks:</b><br/>"
            f"{risks_and_benefits}<br/><br/>"
            f"<b>2. Anesthesia Disclosure:</b> I understand that local anesthetics may be administered and carry rare risks "
            f"including temporary numbness, swelling, allergic reactions, or hematoma.<br/><br/>"
            f"<b>3. Alternative Treatments:</b> The alternatives to this procedure, including non-treatment, have been explained to me.<br/><br/>"
            f"<b>4. Patient Declaration:</b> I have had the opportunity to ask questions and all my questions have been answered to my satisfaction. "
            f"I voluntarily consent to this dental procedure."
        )
        story.append(Paragraph(consent_clauses, body_style))
        story.append(Spacer(1, 20))

        # Signatures
        v_hash = verification_hash or f"CONSENT-{patient_info.get('id', 'PAT')[:6]}-{datetime.now().strftime('%Y%m%d%H%M')}"
        qr_flow = QRCodeService.generate_qr_flowable(f"DENTALCARE:CONSENT:{v_hash}", size=55)

        pat_sig_cell: Any = Paragraph("___________________________<br/><b>Patient / Guardian Signature</b>", body_style)
        if patient_signature_data:
            p_img = ClinicianSignatureService.create_signature_flowable(patient_signature_data, width=100, height=35)
            if p_img:
                pat_sig_cell = [p_img, Paragraph(f"<b>{patient_info.get('name', '')}</b>", body_style)]

        doc_sig_cell: Any = Paragraph("___________________________<br/><b>Treating Clinician Counter-Signature</b>", body_style)
        if signature_data:
            d_img = ClinicianSignatureService.create_signature_flowable(signature_data, width=100, height=35)
            if d_img:
                doc_sig_cell = [d_img, Paragraph(f"<b>{doctor_info.get('name', '')}</b>", body_style)]

        sig_table = Table(
            [
                [
                    qr_flow,
                    Paragraph(f"<font size='7' color='#94a3b8'>Audit Hash:<br/>{v_hash}<br/>Digitally stamped</font>", body_style),
                    pat_sig_cell,
                    doc_sig_cell,
                ]
            ],
            colWidths=[65, 130, 164, 164],
        )
        sig_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story.append(sig_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_patient_card_pdf(
        cls,
        patient_info: dict[str, Any],
        clinic_info: dict[str, Any],
    ) -> bytes:
        """Generates a compact dental patient identification and appointment recall card."""
        buffer = BytesIO()
        # Standard ID card size (3.375 x 2.125 in) expanded to printable slip (300 x 200 pt)
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(300, 200),
            leftMargin=10,
            rightMargin=10,
            topMargin=10,
            bottomMargin=10,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("CardTitle", fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=colors.HexColor("#0f766e"))
        sub_style = ParagraphStyle("CardSub", fontName="Helvetica", fontSize=7, leading=9, textColor=colors.HexColor("#64748b"))
        label_style = ParagraphStyle("CardLabel", fontName="Helvetica-Bold", fontSize=7.5, leading=10, textColor=colors.HexColor("#1e293b"))
        val_style = ParagraphStyle("CardVal", fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#334155"))

        story = []
        story.append(Paragraph(f"<b>{clinic_info.get('name', 'DENTALCARE PRO CLINIC')}</b>", title_style))
        story.append(Paragraph(f"Tel: {clinic_info.get('phone', '+1 555-DENT')} | {clinic_info.get('email', 'clinic@dentalcarepro.local')}", sub_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0f766e"), spaceAfter=6))

        card_data = [
            [Paragraph("Patient Name:", label_style), Paragraph(f"<b>{patient_info.get('name', 'N/A')}</b>", label_style)],
            [Paragraph("Patient ID / Record #:", label_style), Paragraph(patient_info.get("patient_id", "P-10001"), val_style)],
            [Paragraph("Date of Birth / Age:", label_style), Paragraph(f"{patient_info.get('dob', 'N/A')} ({patient_info.get('gender', '')})", val_style)],
            [Paragraph("Primary Phone:", label_style), Paragraph(patient_info.get("phone", "N/A"), val_style)],
            [Paragraph("Medical Alerts:", label_style), Paragraph(f"<font color='#dc2626'><b>{patient_info.get('allergies', 'None documented')}</b></font>", val_style)],
        ]
        t = Table(card_data, colWidths=[95, 185])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.append(t)
        story.append(Spacer(1, 6))

        # QR and footer
        qr = QRCodeService.generate_qr_flowable(f"DENTAL-PATIENT:{patient_info.get('patient_id', '')}", size=30)
        footer_table = Table([[qr, Paragraph("Bring this identification card to every clinic appointment.<br/>Next Recall Due: <b>6 Months</b>", sub_style)]], colWidths=[35, 245])
        footer_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(footer_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @classmethod
    def generate_appointment_list_pdf(
        cls,
        appointments: list[dict[str, Any]],
        schedule_date: str,
        clinic_info: dict[str, Any],
    ) -> bytes:
        """Generates an A4 appointment schedule sheet for clinic operatories."""
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
        header = cls._build_header(
            clinic_info.get("name", "DENTALCARE PRO CLINIC"),
            clinic_info.get("phone", ""),
            clinic_info.get("email", ""),
            f"APPOINTMENT SCHEDULE - {schedule_date}",
            "Daily Operatory Patient Arrival List"
        )
        story = list(header)

        table_head = ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white)
        cell_style = ParagraphStyle("TC", fontName="Helvetica", fontSize=8, leading=11)
        cell_bold = ParagraphStyle("TCB", fontName="Helvetica-Bold", fontSize=8, leading=11)

        data = [
            [
                Paragraph("Time", table_head),
                Paragraph("Patient Name", table_head),
                Paragraph("Phone", table_head),
                Paragraph("Chair / Room", table_head),
                Paragraph("Dentist / Provider", table_head),
                Paragraph("Procedure / Reason", table_head),
                Paragraph("Status", table_head),
            ]
        ]

        for appt in appointments:
            data.append([
                Paragraph(appt.get("time", ""), cell_bold),
                Paragraph(f"<b>{appt.get('patient_name', '')}</b>", cell_style),
                Paragraph(appt.get("phone", ""), cell_style),
                Paragraph(appt.get("chair", ""), cell_style),
                Paragraph(appt.get("doctor", ""), cell_style),
                Paragraph(appt.get("procedure", ""), cell_style),
                Paragraph(appt.get("status", "Scheduled"), cell_style),
            ])

        t = Table(data, colWidths=[45, 110, 75, 75, 85, 80, 53])
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(t)
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
