# services/pdf_export.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
from models import Permit, PermitTool, PermitRisk, PermitMeasure, Risk, Tool
from sqlmodel import Session, select
from db import engine

def export_permit_pdf(permit: Permit, filename: str):
    """Maak een PDF met kerngegevens van een vergunning."""
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph(f"Werkvergunning #{permit.id}", styles['Title']))
    elems.append(Spacer(1, 12))

    # Basisgegevens
    data = [
        ["Titel", permit.title or ""],
        ["Status", permit.status or ""],
        ["Werkwijze", permit.work_type or ""],
        ["Werkgebied", permit.work_area or ""],
        ["Risicoklasse", permit.risk_class or ""],
        ["Locatie", permit.location or ""],
        ["Afdeling", permit.department or ""],
        ["Reden", permit.reason or ""],
        ["Aanvrager naam", permit.applicant_name or ""],
        ["Team / Afdeling", permit.applicant_team or ""],
        ["Contractor", permit.applicant_org or ""],
        ["Periode", f"{permit.start_dt:%d-%m-%Y %H:%M} – {permit.end_dt:%d-%m-%Y %H:%M}"],
    ]
    table = Table(data, colWidths=[120, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elems.append(table)
    elems.append(Spacer(1, 20))

    with Session(engine) as s:
        # Tools
        tools = s.exec(
            select(Tool).join(PermitTool, PermitTool.tool_id == Tool.id).where(PermitTool.permit_id == permit.id)
        ).all()
        if tools:
            elems.append(Paragraph("Gereedschappen:", styles['Heading3']))
            for t in tools:
                elems.append(Paragraph(f"- {t.name}", styles['Normal']))
            elems.append(Spacer(1, 12))

        # Risks
        risks = s.exec(
            select(Risk).join(PermitRisk, PermitRisk.risk_id == Risk.id).where(PermitRisk.permit_id == permit.id)
        ).all()
        if risks:
            elems.append(Paragraph("Risico's:", styles['Heading3']))
            for r in risks:
                elems.append(Paragraph(f"- {r.name} ({r.category})", styles['Normal']))
            elems.append(Spacer(1, 12))

        # Measures
        measures = s.exec(
            select(PermitMeasure).where(PermitMeasure.permit_id == permit.id)
        ).all()
        if measures:
            elems.append(Paragraph("Maatregelen:", styles['Heading3']))
            for m in measures:
                mark = "✅" if m.required else "◻️"
                elems.append(Paragraph(f"{mark} {m.description}", styles['Normal']))

    doc.build(elems)
    return filename
