#!/usr/bin/env python3
"""
Resume PDF builder template using reportlab.
Modify the story content, styles, and model section below for each resume.

Usage: python3 reportlab_template.py
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

OUTPUT = "resume_output.pdf"
PAGE_W = letter[0] - 1.2 * inch  # usable width

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    topMargin=0.5 * inch,
    bottomMargin=0.5 * inch,
    leftMargin=0.6 * inch,
    rightMargin=0.6 * inch,
)

# ── Style helpers ────────────────────────────────────────────────────
styles = getSampleStyleSheet()
S = {}

S["name"] = ParagraphStyle(
    "Name", parent=styles["Normal"], fontSize=22, leading=26,
    spaceAfter=2, fontName="Helvetica-Bold", textColor=HexColor("#1a1a2e"),
)
S["contact"] = ParagraphStyle(
    "Contact", parent=styles["Normal"], fontSize=9, leading=13,
    spaceAfter=4, textColor=HexColor("#444444"), fontName="Helvetica",
)
S["section_head"] = ParagraphStyle(
    "SectionHead", parent=styles["Normal"], fontSize=12, leading=16,
    spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold",
    textColor=HexColor("#16213e"),
)
S["body"] = ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=10, leading=14,
    spaceAfter=6, fontName="Helvetica", textColor=HexColor("#222222"),
)
S["bullet"] = ParagraphStyle(
    "Bullet", parent=styles["Normal"], fontSize=10, leading=14,
    spaceAfter=3, leftIndent=14, bulletIndent=4,
    fontName="Helvetica", textColor=HexColor("#222222"),
)
S["role_title"] = ParagraphStyle(
    "RoleTitle", parent=styles["Normal"], fontSize=10, leading=14,
    spaceBefore=6, spaceAfter=2, fontName="Helvetica-Bold",
    textColor=HexColor("#1a1a2e"),
)
S["role_detail"] = ParagraphStyle(
    "RoleDetail", parent=styles["Normal"], fontSize=9, leading=13,
    spaceAfter=2, fontName="Helvetica-Oblique", textColor=HexColor("#555555"),
)

# ── Helper functions ─────────────────────────────────────────────────

def section(title):
    """Section header with horizontal rule."""
    return [
        HRFlowable(width="100%", thickness=1.2, color=HexColor("#16213e"), spaceAfter=3),
        Paragraph(title.upper(), S["section_head"]),
    ]


def role(title, detail):
    """Job title + company/date line."""
    return [Paragraph(title, S["role_title"]), Paragraph(detail, S["role_detail"])]


def b(text):
    """Single bullet point."""
    return Paragraph(f"\u2022 {text}", S["bullet"])


def skills_table(rows):
    """Two-column skills table: (category, details)."""
    t = Table(rows, colWidths=[doc.width * 0.30, doc.width * 0.70])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#222222")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, HexColor("#cccccc")),
    ]))
    return t


# ── Content ──────────────────────────────────────────────────────────
story = []

# Header
story.append(Paragraph("YOUR NAME", S["name"]))
story.append(Paragraph(
    "City, ST  |  (xxx) xxx-xxxx  |  you@email.com",
    S["contact"],
))
story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=2, color=HexColor("#16213e"), spaceAfter=6))

# Professional Summary
story += section("Professional Summary")
story.append(Paragraph(
    "Your summary here. Two to four sentences. Lead with experience level and "
    "core competency, mention leadership, and state the role you're targeting.",
    S["body"],
))

# Experience
story += section("Experience")
story += role(
    "Company Name — Job Title",
    "Location  |  Year – Year",
)
story.append(bullet("Bullet point describing a responsibility or achievement."))
story.append(bullet(
    "Use strong action verbs: Led, Coordinated, Managed, Developed, Implemented."
))

# Skills
story += section("Skills")
story.append(skills_table([
    ("Category", "Detail 1, Detail 2, Detail 3"),
    ("Another Category", "Detail A, Detail B"),
]))

# Certifications
story += section("Certifications")
story.append(bullet("Certification Name"))

# Education
story += section("Education")
story.append(Paragraph("School — Degree/Credential  |  Year", S["body"]))

# Build
doc.build(story)
print(f"PDF built: {OUTPUT}")
