from __future__ import annotations

from io import BytesIO

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

from app.schemas.billing import InvoiceDetail, PaymentDetail


class BillingPDFService:
    @staticmethod
    def generate_invoice_pdf(invoice: InvoiceDetail) -> bytes:
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

        primary_color = colors.HexColor("#0f766e")  # Dental Teal
        slate_color = colors.HexColor("#1e293b")
        muted_color = colors.HexColor("#64748b")
        paid_green = colors.HexColor("#059669")
        unpaid_amber = colors.HexColor("#d97706")

        clinic_name_style = ParagraphStyle(
            "ClinicName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_color,
        )

        doc_title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=slate_color,
            alignment=2,
        )

        meta_style = ParagraphStyle(
            "DocMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
            alignment=2,
        )

        clinic_meta_style = ParagraphStyle(
            "ClinicMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
        )

        section_title = ParagraphStyle(
            "SectionTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            textTransform="uppercase",
        )

        cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        header_cell = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        )

        story = []

        # 1. Header Banner
        clinic_name = invoice.clinic_name or "DENTALCARE PRO CLINIC"
        clinic_info = (
            f"Address: {invoice.clinic_address or 'City Centre, Opp. General Hospital'}<br/>"
            f"Phone: {invoice.clinic_phone or '+91 98765 43210'} | Email: {invoice.clinic_email or 'contact@dentalcarepro.in'}"
        )

        doc_meta = (
            f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
            f"<b>Date:</b> {invoice.date.strftime('%d-%b-%Y')}<br/>"
            f"<b>Status:</b> {invoice.status}"
        )
        if invoice.due_date:
            doc_meta += f"<br/><b>Due Date:</b> {invoice.due_date.strftime('%d-%b-%Y')}"

        header_table = Table(
            [
                [
                    Paragraph(f"<b>{clinic_name}</b>", clinic_name_style),
                    Paragraph("TAX INVOICE", doc_title_style),
                ],
                [
                    Paragraph(clinic_info, clinic_meta_style),
                    Paragraph(doc_meta, meta_style),
                ],
            ],
            colWidths=[320, 203],
        )
        header_table.setStyle(
            TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])
        )
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=12))

        # 2. Patient & Clinician Block
        patient_text = (
            f"<b>Patient:</b> {invoice.patient_name or 'N/A'}<br/>"
            f"<b>Patient ID:</b> {invoice.patient_number or 'N/A'}<br/>"
            f"<b>Phone:</b> {invoice.patient_phone or 'N/A'}"
        )
        clinician_text = (
            f"<b>Doctor:</b> {invoice.dentist_name or 'Dental Surgeon'}<br/>"
            f"<b>Treatment #:</b> {invoice.treatment_number or 'N/A'}<br/>"
            f"<b>Appointment #:</b> {invoice.appointment_number or 'N/A'}"
        )

        info_table = Table(
            [
                [
                    Paragraph("<b>BILLED TO (PATIENT)</b>", section_title),
                    Paragraph("<b>ATTENDING CLINICIAN & TREATMENT</b>", section_title),
                ],
                [
                    Paragraph(patient_text, cell_style),
                    Paragraph(clinician_text, cell_style),
                ],
            ],
            colWidths=[260, 263],
        )
        info_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(info_table)
        story.append(Spacer(1, 14))

        # 3. Line Items Table
        items_data = [
            [
                Paragraph("#", header_cell),
                Paragraph("Description", header_cell),
                Paragraph("Type", header_cell),
                Paragraph("Qty", header_cell),
                Paragraph("Unit Price", header_cell),
                Paragraph("Disc", header_cell),
                Paragraph("Tax", header_cell),
                Paragraph("Total (INR)", header_cell),
            ]
        ]

        for idx, it in enumerate(invoice.items, start=1):
            items_data.append(
                [
                    Paragraph(str(idx), cell_style),
                    Paragraph(f"<b>{it.description}</b>", cell_style),
                    Paragraph(it.item_type, cell_style),
                    Paragraph(str(it.quantity), cell_style),
                    Paragraph(f"₹{it.unit_price:,.2f}", cell_style),
                    Paragraph(f"₹{it.discount_amount:,.2f}" if it.discount_amount > 0 else "-", cell_style),
                    Paragraph(f"₹{it.tax_amount:,.2f}" if it.tax_amount > 0 else "-", cell_style),
                    Paragraph(f"₹{it.total:,.2f}", cell_bold),
                ]
            )

        items_table = Table(items_data, colWidths=[22, 185, 76, 30, 60, 45, 45, 60])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 12))

        # 4. Financial Totals Table (right-aligned)
        status_color = paid_green if invoice.balance_due <= 0.0 else unpaid_amber
        totals_data = [
            [Paragraph("Subtotal:", cell_bold), Paragraph(f"₹{invoice.subtotal:,.2f}", cell_style)],
            [Paragraph("Discount:", cell_style), Paragraph(f"- ₹{invoice.discount_amount:,.2f}", cell_style)],
            [Paragraph(f"Tax / GST ({invoice.tax_rate}%):", cell_style), Paragraph(f"+ ₹{invoice.tax_amount:,.2f}", cell_style)],
            [Paragraph("<b>Grand Total:</b>", cell_bold), Paragraph(f"<b>₹{invoice.grand_total:,.2f}</b>", cell_bold)],
            [Paragraph("Amount Paid:", cell_style), Paragraph(f"₹{invoice.amount_paid:,.2f}", cell_style)],
            [
                Paragraph("<b>Balance Due:</b>", ParagraphStyle("BalLabel", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=status_color)),
                Paragraph(f"<b>₹{invoice.balance_due:,.2f}</b>", ParagraphStyle("BalVal", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=status_color)),
            ],
        ]
        totals_table = Table(totals_data, colWidths=[120, 90], hAlign="RIGHT")
        totals_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 3), (-1, 3), 1, colors.HexColor("#94a3b8")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(totals_table)
        story.append(Spacer(1, 14))

        # 5. Notes and Terms
        notes_text = []
        if invoice.notes:
            notes_text.append(f"<b>Notes:</b> {invoice.notes}")
        if invoice.terms:
            notes_text.append(f"<b>Terms & Conditions:</b> {invoice.terms}")
        else:
            notes_text.append("<b>Terms:</b> Payment is due upon receipt. Cheques payable to DentalCare Pro Clinic.")

        story.append(Paragraph("<br/>".join(notes_text), cell_style))
        story.append(Spacer(1, 20))

        # 6. Signature Block
        sig_data = [
            [
                Paragraph("Thank you for choosing DentalCare Pro for your dental health.", cell_style),
                Paragraph("<b>Authorized Signatory</b><br/><br/>_______________________", ParagraphStyle("Sig", parent=styles["Normal"], alignment=2, fontName="Helvetica", fontSize=8.5)),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[320, 203])
        sig_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story.append(sig_table)

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def generate_receipt_pdf(payment: PaymentDetail) -> bytes:
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

        primary_color = colors.HexColor("#0f766e")
        slate_color = colors.HexColor("#1e293b")
        muted_color = colors.HexColor("#64748b")
        emerald_color = colors.HexColor("#059669")

        clinic_name_style = ParagraphStyle(
            "ClinicName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_color,
        )

        doc_title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=slate_color,
            alignment=2,
        )

        meta_style = ParagraphStyle(
            "DocMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
            alignment=2,
        )

        clinic_meta_style = ParagraphStyle(
            "ClinicMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
        )

        cell_style = ParagraphStyle(
            "Cell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=slate_color,
        )

        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=slate_color,
        )

        amount_callout = ParagraphStyle(
            "AmountCallout",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=emerald_color,
            alignment=1,
        )

        story = []

        # 1. Header
        clinic_name = payment.clinic_name or "DENTALCARE PRO CLINIC"
        clinic_info = (
            f"Phone: {payment.clinic_phone or '+91 98765 43210'} | Email: {payment.clinic_email or 'contact@dentalcarepro.in'}"
        )
        receipt_meta = (
            f"<b>Receipt #:</b> {payment.receipt_number}<br/>"
            f"<b>Date:</b> {payment.payment_date.strftime('%d-%b-%Y')}<br/>"
            f"<b>Status:</b> {payment.status}"
        )

        header_table = Table(
            [
                [
                    Paragraph(f"<b>{clinic_name}</b>", clinic_name_style),
                    Paragraph("OFFICIAL PAYMENT RECEIPT", doc_title_style),
                ],
                [
                    Paragraph(clinic_info, clinic_meta_style),
                    Paragraph(receipt_meta, meta_style),
                ],
            ],
            colWidths=[300, 223],
        )
        header_table.setStyle(
            TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])
        )
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=14))

        # 2. Large Amount Received Callout Box
        callout_data = [
            [Paragraph("AMOUNT RECEIVED", ParagraphStyle("Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, textColor=muted_color, alignment=1))],
            [Paragraph(f"₹{payment.amount:,.2f}", amount_callout)],
            [Paragraph(f"Payment Method: <b>{payment.method}</b>" + (f" | Ref: <b>{payment.transaction_reference}</b>" if payment.transaction_reference else ""), ParagraphStyle("Sub", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, textColor=slate_color, alignment=1))],
        ]
        callout_table = Table(callout_data, colWidths=[523])
        callout_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#a7f3d0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(callout_table)
        story.append(Spacer(1, 16))

        # 3. Transaction Details
        details_data = [
            [Paragraph("Received From:", cell_bold), Paragraph(f"{payment.patient_name or 'Patient'} (ID: {payment.patient_number or 'N/A'})", cell_style)],
            [Paragraph("Invoice Number:", cell_bold), Paragraph(payment.invoice_number or "N/A", cell_style)],
            [Paragraph("Payment Date:", cell_bold), Paragraph(payment.payment_date.strftime("%d-%b-%Y"), cell_style)],
            [Paragraph("Payment Method:", cell_bold), Paragraph(str(payment.method), cell_style)],
            [Paragraph("Transaction Reference:", cell_bold), Paragraph(payment.transaction_reference or "N/A", cell_style)],
            [Paragraph("Received By:", cell_bold), Paragraph(payment.receiver_name or "Front Desk Cashier", cell_style)],
            [Paragraph("Remaining Balance Due:", cell_bold), Paragraph(f"<b>₹{payment.remaining_balance:,.2f}</b>", cell_bold)],
        ]
        if payment.notes:
            details_data.append([Paragraph("Notes:", cell_bold), Paragraph(payment.notes, cell_style)])

        details_table = Table(details_data, colWidths=[160, 363])
        details_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(details_table)
        story.append(Spacer(1, 24))

        # 4. Sign-off block
        sig_data = [
            [
                Paragraph("This is a computer-generated receipt issued by DentalCare Pro.", cell_style),
                Paragraph("<b>Cashier / Clinic Seal</b><br/><br/>_______________________", ParagraphStyle("Sig", parent=styles["Normal"], alignment=2, fontName="Helvetica", fontSize=8.5)),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[320, 203])
        sig_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        story.append(sig_table)

        doc.build(story)
        return buffer.getvalue()
