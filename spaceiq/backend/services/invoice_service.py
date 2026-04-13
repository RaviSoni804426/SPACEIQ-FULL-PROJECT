"""
PDF Invoice Generator using ReportLab
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import base64


def generate_invoice_pdf(booking: dict) -> str:
    """
    Generate a PDF invoice and return as base64 string.
    booking: dict with id, user_name, unit_name, location_name,
             start_time, end_time, amount, payment_id
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title", fontSize=22, fontName="Helvetica-Bold",
                                  textColor=colors.HexColor("#6c63ff"), spaceAfter=6)
    sub_style = ParagraphStyle("Sub", fontSize=10, textColor=colors.grey, spaceAfter=20)
    label_style = ParagraphStyle("Label", fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("Value", fontSize=11, fontName="Helvetica-Bold")

    story = []
    story.append(Paragraph("SpaceIQ", title_style))
    story.append(Paragraph("Booking Invoice", sub_style))
    story.append(Spacer(1, 0.5*cm))

    data = [
        ["Booking ID", booking.get("id", "—")],
        ["Customer", booking.get("user_name", "—")],
        ["Space", booking.get("unit_name", "—")],
        ["Location", booking.get("location_name", "—")],
        ["Start", booking.get("start_time", "—")],
        ["End", booking.get("end_time", "—")],
        ["Amount", f"₹{booking.get('amount', 0):.2f}"],
        ["Payment ID", booking.get("payment_id", "—")],
        ["Issued", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
    ]

    table = Table(data, colWidths=[5*cm, 11*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f3ff")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(table)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Thank you for booking with SpaceIQ!", sub_style))

    doc.build(story)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
