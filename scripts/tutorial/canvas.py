# scripts/tutorial/canvas.py
from reportlab.pdfgen import canvas
from reportlab.lib import colors

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that adds running headers, decorative accents,
    and accurate 'Page X of Y' footers across the entire document.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"Total Document Pages Generated: {num_pages}")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Skip running headers and footers on the cover page
            return

        page_width, page_height = self._pagesize

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Top decorative rule & Running Header
        self.setStrokeColor(colors.HexColor("#0f766e"))
        self.setLineWidth(1.5)
        self.line(40, page_height - 35, page_width - 40, page_height - 35)

        self.drawString(40, page_height - 30, "DentalCare Pro v1.0 — Enterprise User Manual & Tutorial")
        self.drawRightString(page_width - 40, page_height - 30, "Confidential & Proprietary")

        # Bottom decorative rule & Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.75)
        self.line(40, 45, page_width - 40, 45)

        self.drawString(40, 32, "© 2026 DentalCare Pro Inc. All Rights Reserved. HIPAA & GDPR Compliant.")
        self.drawRightString(page_width - 40, 32, f"Page {self._pageNumber} of {page_count}")

        self.restoreState()
