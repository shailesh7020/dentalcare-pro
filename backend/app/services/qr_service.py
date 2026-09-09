from __future__ import annotations

import base64
import io
from typing import Any
import qrcode
from reportlab.graphics.barcode import createBarcodeDrawing, qr
from reportlab.graphics.shapes import Drawing, Group
from reportlab.graphics import renderSVG
from reportlab.platypus import Image as PlatypusImage


class QRCodeService:
    @staticmethod
    def generate_patient_payload(patient_id: str, clinic_id: str | None = None) -> str:
        cid = clinic_id or "MAIN"
        return f"DENTALCARE:PATIENT:{patient_id}:{cid}"

    @staticmethod
    def generate_appointment_payload(appointment_id: str, patient_id: str) -> str:
        return f"DENTALCARE:APPT:{appointment_id}:{patient_id}"

    @staticmethod
    def generate_invoice_payload(invoice_id: str, amount: float | str, signature_hash: str) -> str:
        return f"DENTALCARE:INV:{invoice_id}:{amount}:{signature_hash}"

    @staticmethod
    def generate_prescription_payload(prescription_id: str, signature_hash: str) -> str:
        return f"DENTALCARE:RX:{prescription_id}:{signature_hash}"

    @staticmethod
    def generate_qr_png_base64(data: str, box_size: int = 4, border: int = 2) -> str:
        """Generates a PNG data URI for web and API usage."""
        qr_obj = qrcode.QRCode(box_size=box_size, border=border)
        qr_obj.add_data(data)
        qr_obj.make(fit=True)
        img = qr_obj.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    @staticmethod
    def generate_qr_bytes(data: str, box_size: int = 4, border: int = 1) -> bytes:
        """Generates raw PNG bytes."""
        qr_obj = qrcode.QRCode(box_size=box_size, border=border)
        qr_obj.add_data(data)
        qr_obj.make(fit=True)
        img = qr_obj.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def generate_qr_flowable(data: str, size: float = 60.0) -> PlatypusImage:
        """Generates a ReportLab Platypus Image flowable for embedding in tables/stories."""
        raw_bytes = QRCodeService.generate_qr_bytes(data)
        return PlatypusImage(io.BytesIO(raw_bytes), width=size, height=size)

    @staticmethod
    def generate_qr_drawing(data: str, size: float = 60.0) -> Drawing:
        """Generates a native ReportLab Drawing vector flowable for PDF inclusion."""
        d = Drawing(size, size)
        w = qr.QrCodeWidget(data)
        bounds = w.getBounds()
        qr_w = bounds[2] - bounds[0]
        qr_h = bounds[3] - bounds[1]
        if qr_w > 0 and qr_h > 0:
            g = Group()
            g.scale(size / qr_w, size / qr_h)
            g.add(w)
            d.add(g)
        else:
            d.add(w)
        return d

    @staticmethod
    def generate_barcode_drawing(value: str, bar_width: float = 1.0, bar_height: float = 28.0) -> Drawing:
        """Generates a native ReportLab Code128 Drawing flowable for PDF inclusion."""
        return createBarcodeDrawing(
            "Code128",
            value=value,
            barWidth=bar_width,
            barHeight=bar_height,
            humanReadable=True,
        )

    @staticmethod
    def generate_barcode_svg_base64(value: str, bar_width: float = 1.0, bar_height: float = 28.0) -> str:
        """Generates an SVG data URI of a Code128 barcode."""
        drawing = createBarcodeDrawing(
            "Code128",
            value=value,
            barWidth=bar_width,
            barHeight=bar_height,
            humanReadable=True,
        )
        svg_content = renderSVG.drawToString(drawing)
        b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"
