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

from app.models.inventory import PurchaseOrder
from app.schemas.inventory import PurchaseOrderDetail


class InventoryPDFService:
    @staticmethod
    def generate_purchase_order_pdf(
        po: PurchaseOrderDetail | PurchaseOrder,
        clinic_name: str = "DentalCare Pro Clinic",
        clinic_address: str = "Healthcare Plaza, Suite 400",
        clinic_phone: str = "+91 98765 43210",
        clinic_email: str = "procurement@dentalcarepro.in",
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

        primary_color = colors.HexColor("#0f766e")  # Teal
        slate_color = colors.HexColor("#1e293b")
        muted_color = colors.HexColor("#64748b")
        status_color = (
            colors.HexColor("#059669")
            if po.status in ("RECEIVED", "PARTIALLY_RECEIVED")
            else colors.HexColor("#d97706")
        )

        clinic_name_style = ParagraphStyle(
            "POClinicName",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=primary_color,
        )

        doc_title_style = ParagraphStyle(
            "PODocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=slate_color,
            alignment=2,
        )

        doc_meta_style = ParagraphStyle(
            "PODocMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
            alignment=2,
        )

        clinic_meta_style = ParagraphStyle(
            "POClinicMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=muted_color,
        )

        section_title = ParagraphStyle(
            "POSectionTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )

        cell_style = ParagraphStyle(
            "POTableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        cell_bold = ParagraphStyle(
            "POTableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=slate_color,
        )

        header_cell = ParagraphStyle(
            "POHeaderCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        )

        story = []

        # 1. Header Banner
        clinic_info = (
            f"Address: {clinic_address}<br/>"
            f"Phone: {clinic_phone} | Email: {clinic_email}"
        )

        doc_meta = (
            f"<b>PO #:</b> {po.po_number}<br/>"
            f"<b>Date:</b> {po.order_date.strftime('%d-%b-%Y')}<br/>"
            f"<b>Status:</b> <font color='{status_color.hexval()}'>{po.status}</font>"
        )
        if po.expected_delivery_date:
            doc_meta += f"<br/><b>Delivery By:</b> {po.expected_delivery_date.strftime('%d-%b-%Y')}"

        header_table = Table(
            [
                [
                    Paragraph(f"<b>{clinic_name}</b>", clinic_name_style),
                    Paragraph("PURCHASE ORDER", doc_title_style),
                ],
                [
                    Paragraph(clinic_info, clinic_meta_style),
                    Paragraph(doc_meta, doc_meta_style),
                ],
            ],
            colWidths=[320, 202],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=primary_color,
                spaceBefore=2,
                spaceAfter=10,
            )
        )

        # 2. Supplier / Vendor Details
        supplier_name = getattr(po, "supplier_name", None)
        supplier_contact = ""
        supplier_phone = ""
        supplier_email = ""
        supplier_gst = ""
        supplier_addr = ""

        if hasattr(po, "supplier") and po.supplier:
            s = po.supplier
            supplier_name = s.name
            supplier_contact = s.contact_person or ""
            supplier_phone = s.phone or ""
            supplier_email = s.email or ""
            supplier_gst = s.gst_number or ""
            supplier_addr = s.address or ""

        vendor_content = (
            f"<b>{supplier_name or 'VENDOR / SUPPLIER'}</b><br/>"
            + (f"Contact: {supplier_contact}<br/>" if supplier_contact else "")
            + (f"Phone: {supplier_phone} | Email: {supplier_email}<br/>" if supplier_phone or supplier_email else "")
            + (f"GSTIN: {supplier_gst}<br/>" if supplier_gst else "")
            + (f"Address: {supplier_addr}" if supplier_addr else "")
        )

        shipping_content = (
            f"<b>Deliver To:</b><br/>"
            f"{clinic_name}<br/>"
            f"{clinic_address}<br/>"
            f"Attn: Inventory & Pharmacy In-Charge"
        )

        vendor_table = Table(
            [
                [
                    Paragraph("<b>VENDOR / SUPPLIER DETAILS</b>", section_title),
                    Paragraph("<b>SHIPPING / DELIVERY DESTINATION</b>", section_title),
                ],
                [
                    Paragraph(vendor_content, cell_style),
                    Paragraph(shipping_content, cell_style),
                ],
            ],
            colWidths=[261, 261],
        )
        vendor_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ])
        )
        story.append(vendor_table)
        story.append(Spacer(1, 14))

        # 3. Line Items Table
        items_data = [
            [
                Paragraph("ITEM / DESCRIPTION", header_cell),
                Paragraph("QTY ORD", header_cell),
                Paragraph("QTY RCV", header_cell),
                Paragraph("UNIT PRICE", header_cell),
                Paragraph("TAX %", header_cell),
                Paragraph("TOTAL (INR)", header_cell),
            ]
        ]

        raw_items = getattr(po, "items", []) or []
        for it in raw_items:
            item_name = getattr(it, "item_name", "")
            item_sku = getattr(it, "item_sku", "")
            if not item_name and hasattr(it, "item") and it.item:
                item_name = it.item.name
                item_sku = it.item.sku
            name_text = f"<b>{item_name}</b>"
            if item_sku:
                name_text += f"<br/><font color='{muted_color.hexval()}'>SKU: {item_sku}</font>"

            items_data.append([
                Paragraph(name_text, cell_style),
                Paragraph(str(it.quantity_ordered), cell_style),
                Paragraph(str(it.quantity_received), cell_style),
                Paragraph(f"₹{float(it.unit_price):,.2f}", cell_style),
                Paragraph(f"{float(it.tax_rate):.1f}%", cell_style),
                Paragraph(f"₹{float(it.total):,.2f}", cell_bold),
            ])

        if len(items_data) == 1:
            items_data.append([
                Paragraph("<i>No items listed</i>", cell_style),
                "", "", "", "", "",
            ])

        line_table = Table(items_data, colWidths=[202, 60, 60, 70, 50, 80])
        line_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ])
        )
        story.append(line_table)
        story.append(Spacer(1, 10))

        # 4. Totals Summary Table
        subtotal = float(po.subtotal)
        tax = float(po.tax_amount)
        discount = float(po.discount_amount)
        grand_total = float(po.grand_total)

        totals_data = [
            [Paragraph("Subtotal:", cell_style), Paragraph(f"₹{subtotal:,.2f}", cell_style)],
            [Paragraph("Taxes (GST):", cell_style), Paragraph(f"₹{tax:,.2f}", cell_style)],
        ]
        if discount > 0:
            totals_data.append([
                Paragraph("Discount:", cell_style),
                Paragraph(f"-₹{discount:,.2f}", cell_style),
            ])
        totals_data.append([
            Paragraph("<b>GRAND TOTAL:</b>", cell_bold),
            Paragraph(f"<b>₹{grand_total:,.2f}</b>", cell_bold),
        ])

        totals_table = Table(totals_data, colWidths=[120, 90])
        totals_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ])
        )

        summary_wrap = Table(
            [
                [
                    Paragraph(
                        f"<b>Terms & Conditions:</b><br/>{po.terms or 'Payment within agreed terms upon verified goods receipt.'}",
                        clinic_meta_style,
                    ),
                    totals_table,
                ]
            ],
            colWidths=[312, 210],
        )
        summary_wrap.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(summary_wrap)
        story.append(Spacer(1, 20))

        # 5. Authorization Signatures
        sig_data = [
            [
                Paragraph("Prepared By:<br/><br/>_____________________<br/>Procurement Officer", cell_style),
                Paragraph("Approved By:<br/><br/>_____________________<br/>Clinic Administrator", cell_style),
                Paragraph("Vendor Acknowledgement:<br/><br/>_____________________<br/>Authorized Signature & Stamp", cell_style),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[174, 174, 174])
        sig_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(sig_table)

        doc.build(story)
        return buffer.getvalue()
