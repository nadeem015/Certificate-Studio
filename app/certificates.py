import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

OUTPUT_DIR = Path(os.getenv("CERTIFICATE_OUTPUT_DIR", "certificates"))

def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_")
    return cleaned[:80] or "recipient"

def generate_certificate(recipient_name: str, event_name: str, certificate_id: int) -> str:
    """Create one PDF certificate and return its path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"certificate_{certificate_id}_{safe_filename(recipient_name)}.pdf"
    page = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=page)
    width, height = page

    # Simple, predefined certificate design.
    pdf.setFillColor(colors.HexColor("#F8F5ED"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#234E52"))
    pdf.setLineWidth(4)
    pdf.rect(24, 24, width - 48, height - 48, fill=0, stroke=1)

    pdf.setFillColor(colors.HexColor("#234E52"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 105, "CERTIFICATE OF PARTICIPATION")
    pdf.setFillColor(colors.HexColor("#333333"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 165, "This certificate is proudly presented to")
    pdf.setFillColor(colors.HexColor("#9A6A24"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 220, recipient_name[:100])
    pdf.setFillColor(colors.HexColor("#333333"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 270, f"for participating in {event_name[:120]}")
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, 65, f"Certificate ID: {certificate_id}")
    pdf.save()
    return str(output_path)
