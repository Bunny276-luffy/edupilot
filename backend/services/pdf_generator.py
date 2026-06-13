"""
PDF generation service using ReportLab.
Generates CO-PO Matrix and NAAC Report PDFs.
"""
import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
    PageBreak,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Brand colours ─────────────────────────────────────────────────────────────
DEEP_BLUE = colors.HexColor("#1a237e")
ACCENT_ORANGE = colors.HexColor("#f57c00")
LIGHT_GREY = colors.HexColor("#f5f5f5")
MED_GREY = colors.HexColor("#e0e0e0")


def _header_footer(canvas, doc):
    """Draw page header and footer on every page."""
    canvas.saveState()
    width, height = doc.pagesize

    # Header bar
    canvas.setFillColor(DEEP_BLUE)
    canvas.rect(0, height - 60, width, 60, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(width / 2, height - 35, "EduPilot — Academic Analytics Report")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 20, height - 50, f"Generated: {datetime.utcnow().strftime('%d %b %Y')}")

    # Footer
    canvas.setFillColor(DEEP_BLUE)
    canvas.rect(0, 0, width, 28, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(width / 2, 10, f"Page {doc.page}  |  Confidential — NAAC Accreditation Document")

    canvas.restoreState()


def generate_copo_pdf(matrix_data: dict[str, Any]) -> bytes:
    """
    Generate a CO-PO attainment matrix PDF.
    Returns raw PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    heading = ParagraphStyle("Heading", parent=styles["Heading1"], textColor=DEEP_BLUE, spaceAfter=6)
    sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, spaceAfter=4)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER)

    story = []

    # Title section
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"CO-PO Attainment Matrix", heading))
    story.append(Paragraph(f"Course: {matrix_data.get('course_name', '')} ({matrix_data.get('course_code', '')})", sub))
    story.append(Paragraph(f"Semester: {matrix_data.get('semester', '')}   |   Academic Year: {matrix_data.get('academic_year', '')}", sub))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT_ORANGE, spaceAfter=10))

    cos = matrix_data.get("cos", [])
    pos = matrix_data.get("pos", [])
    cells = matrix_data.get("cells", [])

    if cos and pos and cells:
        # Build lookup
        lookup: dict[tuple, float] = {}
        for cell in cells:
            lookup[(cell["co_id"], cell["po_id"])] = cell["attainment"]

        # Table header
        header_row = ["CO \\ PO"] + pos
        table_data = [header_row]
        co_attainment = matrix_data.get("co_attainment", {})

        for co in cos:
            row = [co]
            for po in pos:
                val = lookup.get((co, po), 0.0)
                row.append(f"{val:.1f}" if val > 0 else "-")
            table_data.append(row)

        # Averages row
        avg_row = ["Avg"]
        for po in pos:
            po_vals = [lookup.get((co, po), 0.0) for co in cos]
            non_zero = [v for v in po_vals if v > 0]
            avg = sum(non_zero) / len(non_zero) if non_zero else 0.0
            avg_row.append(f"{avg:.2f}" if avg > 0 else "-")
        table_data.append(avg_row)

        col_count = len(pos) + 1
        col_width = (landscape(A4)[0] - 3 * cm) / col_count

        tbl = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
        tbl.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DEEP_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 1), (0, -1), LIGHT_GREY),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), ACCENT_ORANGE),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, MED_GREY),
                ("ROWBACKGROUNDS", (1, 1), (-1, -2), [colors.white, LIGHT_GREY]),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(tbl)

    # Summary
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<b>Average CO Attainment:</b> {matrix_data.get('avg_attainment', 0):.2f} / 3.00  "
        f"&nbsp;&nbsp;&nbsp; <b>Total Questions Analysed:</b> {matrix_data.get('total_questions', 0)}",
        sub,
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Scale:</b> 3 = High (≥70%)  &nbsp; 2 = Moderate (60–70%)  &nbsp; 1 = Low (50–60%)  &nbsp; 0 = Not Addressed",
        ParagraphStyle("scale", parent=styles["Normal"], fontSize=8, textColor=colors.grey),
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


def generate_naac_pdf(
    course_data: dict[str, Any],
    blooms_dist: list[dict],
    co_attainment: dict[str, float],
    summary_text: str,
) -> bytes:
    """
    Generate a complete NAAC accreditation PDF report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=DEEP_BLUE, spaceAfter=8)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=DEEP_BLUE, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=6)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)

    story = []
    story.append(Spacer(1, 40))

    # Cover block
    story.append(Paragraph("NAAC Accreditation Report", h1))
    story.append(Paragraph(f"<b>Course:</b> {course_data.get('course_name', '')} ({course_data.get('course_code', '')})", body))
    story.append(Paragraph(f"<b>Faculty:</b> {course_data.get('faculty_id', 'N/A')}", body))
    story.append(Paragraph(f"<b>Semester:</b> {course_data.get('semester', '')}   &nbsp;&nbsp; <b>Academic Year:</b> {course_data.get('academic_year', '')}", body))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_ORANGE, spaceAfter=16))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h2))
    story.append(Paragraph(summary_text, body))

    # Bloom's Distribution Table
    story.append(Paragraph("2. Bloom's Taxonomy Distribution", h2))
    bloom_header = ["Level", "Count", "Percentage (%)", "Status"]
    bloom_rows = [bloom_header]
    for item in blooms_dist:
        level = item.get("level", "")
        count = item.get("count", 0)
        pct = item.get("percentage", 0.0)
        status = "✓ Higher Order" if level in ("Analyze", "Evaluate", "Create") else "Lower Order"
        bloom_rows.append([level, str(count), f"{pct:.1f}%", status])

    bloom_table = Table(bloom_rows, colWidths=[4 * cm, 2.5 * cm, 4 * cm, 5 * cm])
    bloom_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DEEP_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, MED_GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(bloom_table)

    # CO Attainment
    story.append(Spacer(1, 12))
    story.append(Paragraph("3. Course Outcome Attainment", h2))
    co_header = ["Course Outcome", "Attainment Level", "NBA Rating"]
    co_rows = [co_header]
    for co, att in co_attainment.items():
        rating = "High" if att >= 2.5 else "Moderate" if att >= 1.5 else "Low"
        co_rows.append([co, f"{att:.2f} / 3.00", rating])

    co_table = Table(co_rows, colWidths=[4 * cm, 5 * cm, 5 * cm])
    co_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DEEP_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, MED_GREY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(co_table)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "This report was generated automatically by <b>EduPilot</b> using AI-powered analysis. "
        "It conforms to NBA Criterion 2.3 and NAAC Criterion 1.2 reporting requirements.",
        small,
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
