"""Génération du CV en PDF (ReportLab), charte bleu/blanc."""
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BLUE, ACCENT, TEXT = colors.HexColor("#1E3A8A"), colors.HexColor("#3B82F6"), colors.HexColor("#1E293B")


def _style(name, **kw):
    return ParagraphStyle(name, fontName=kw.pop("font", "Helvetica"), textColor=kw.pop("color", TEXT), **kw)


def build_pdf(cv: dict) -> bytes:
    s = {
        "name": _style("name", font="Helvetica-Bold", fontSize=22, leading=26, color=colors.white),
        "role": _style("role", fontSize=12, leading=16, color=colors.HexColor("#BFDBFE")),
        "contact": _style("contact", fontSize=9, leading=12, color=colors.white),
        "h": _style("h", font="Helvetica-Bold", fontSize=11, leading=14, color=BLUE, spaceBefore=10, spaceAfter=2),
        "body": _style("body", fontSize=10, leading=14),
        "bold": _style("bold", font="Helvetica-Bold", fontSize=10, leading=13),
        "meta": _style("meta", fontSize=9, leading=12, color=colors.HexColor("#64748B")),
        "bullet": _style("bullet", fontSize=10, leading=13, leftIndent=12, bulletIndent=2),
    }
    p = lambda text, st: Paragraph(escape(str(text or "")), s[st])  # noqa: E731
    contact = " · ".join(x for x in (cv.get("email"), cv.get("phone"), cv.get("city")) if x)

    head = Table([[[p(cv.get("full_name", ""), "name"), p(cv.get("title", ""), "role"), Spacer(1, 4), p(contact, "contact")]]],
                 colWidths=[17 * cm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE), ("LEFTPADDING", (0, 0), (-1, -1), 16),
                              ("TOPPADDING", (0, 0), (-1, -1), 16), ("BOTTOMPADDING", (0, 0), (-1, -1), 14)]))
    story = [head]

    def section(title):
        story.extend([p(title.upper(), "h"), HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=4)])

    if cv.get("summary"):
        section("Profil")
        story.append(p(cv["summary"], "body"))
    if cv.get("skills"):
        section("Compétences")
        story.append(p("  •  ".join(cv["skills"]), "body"))
    if cv.get("experiences"):
        section("Expériences professionnelles")
        for e in cv["experiences"]:
            story.append(p(f"{e.get('role', '')} — {e.get('company', '')}", "bold"))
            story.append(p(e.get("period", ""), "meta"))
            for line in filter(None, (l.strip(" -•\t") for l in (e.get("description") or "").splitlines())):
                story.append(Paragraph(escape(line), s["bullet"], bulletText="•"))
            story.append(Spacer(1, 6))
    if cv.get("education"):
        section("Formation")
        for e in cv["education"]:
            story.append(p(f"{e.get('degree', '')} — {e.get('school', '')}", "bold"))
            story.append(p(e.get("period", ""), "meta"))
    if cv.get("languages"):
        section("Langues")
        story.append(p("  •  ".join(cv["languages"]), "body"))

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.5 * cm,
                      bottomMargin=1.5 * cm, title=f"CV {cv.get('full_name', '')}").build(story)
    return buf.getvalue()
