"""
Clinician PDF report generator for Digital Twin simulation results.
Uses reportlab for a clean, printable one-page + detail layout.
"""

from io import BytesIO
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.schemas.report import SimulationReport
from app.core.constants import DISCLAIMER, PRODUCT_POSITIONING, APP_MODEL_VERSION


# Brand colours (match frontend)
NAVY = colors.HexColor("#173a74")
PINK = colors.HexColor("#f7c6d9")
OK = colors.HexColor("#1a7f4e")
WARN = colors.HexColor("#b36b00")
BAD = colors.HexColor("#b00020")
MUTED = colors.HexColor("#555555")
LIGHT_BG = colors.HexColor("#f4f7fb")
LINE = colors.HexColor("#d0d8e8")


def _risk_color(level: str):
    l = (level or "").lower()
    if "high" in l:
        return BAD
    if "caution" in l:
        return WARN
    return OK


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "DTTitle",
            parent=base["Heading1"],
            fontSize=18,
            textColor=NAVY,
            spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "DTSub",
            parent=base["Normal"],
            fontSize=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "DTH2",
            parent=base["Heading2"],
            fontSize=11,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "DTBody",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.black,
        ),
        "small": ParagraphStyle(
            "DTSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=MUTED,
        ),
        "disclaimer": ParagraphStyle(
            "DTDisc",
            parent=base["Normal"],
            fontSize=7.5,
            leading=9,
            textColor=BAD,
            alignment=TA_LEFT,
            spaceBefore=6,
        ),
        "risk": ParagraphStyle(
            "DTRisk",
            parent=base["Normal"],
            fontSize=16,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "label": ParagraphStyle(
            "DTLabel",
            parent=base["Normal"],
            fontSize=8,
            textColor=MUTED,
        ),
    }
    return styles


def _kv_table(rows, col_widths=None):
    data = [[Paragraph(str(k), _styles()["label"]), Paragraph(str(v), _styles()["body"])] for k, v in rows]
    t = Table(data, colWidths=col_widths or [55 * mm, 120 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
            ]
        )
    )
    return t


def build_simulation_pdf(report: SimulationReport, simulation_id: Optional[int] = None) -> bytes:
    """Build a clinician-ready PDF from a SimulationReport. Returns PDF bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = _styles()
    story = []

    # Header
    story.append(Paragraph("Digital Twin — Individualized PK Risk Report", styles["title"]))
    story.append(
        Paragraph(
            f"{PRODUCT_POSITIONING} · Model {APP_MODEL_VERSION} · "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            + (f" · Simulation #{simulation_id}" if simulation_id else ""),
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=6))

    # Risk banner
    risk = report.risk_level or "—"
    conf = report.overall_confidence or "—"
    risk_para = Paragraph(
        f'<font color="{_risk_color(risk).hexval()}">{risk}</font>',
        styles["risk"],
    )
    banner_data = [
        [
            Paragraph("<b>Risk level</b>", styles["label"]),
            risk_para,
            Paragraph("<b>Confidence</b>", styles["label"]),
            Paragraph(conf, styles["body"]),
        ]
    ]
    banner = Table(banner_data, colWidths=[30 * mm, 50 * mm, 30 * mm, 50 * mm])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(banner)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(report.summary_text or "", styles["body"]))
    story.append(Spacer(1, 3 * mm))

    # Patient snapshot
    pp = report.patient_profile
    story.append(Paragraph("1. Patient profile", styles["h2"]))
    patient_rows = [
        ("Age / Sex", f"{pp.age} y · {pp.sex}"),
        ("Weight / BMI", f"{pp.weight_kg} kg · BMI {pp.bmi or '–'}"),
        ("eGFR", f"{pp.egfr or '–'} mL/min/1.73m² ({pp.egfr_category or ''})"),
        ("Liver capacity", f"{round((pp.liver_capacity_score or 1) * 100)}% of normal"),
        ("Clearance factor", f"{pp.clearance_adjustment_factor}"),
        ("Conditions", ", ".join(pp.conditions) or "None"),
        ("Allergies", ", ".join(pp.allergies) or "None"),
        (
            "Current medicines",
            ", ".join(f"{m.name} {m.dose_mg}mg" for m in (pp.current_medicines or [])) or "None",
        ),
    ]
    story.append(_kv_table(patient_rows))

    # Drug
    dp = report.drug_profile
    story.append(Paragraph("2. Drug & regimen", styles["h2"]))
    mol = dp.molecular_properties
    drug_rows = [
        ("Drug", dp.name or dp.identifier_used),
        ("Identifier used", dp.identifier_used),
        ("MW / logP", f"{mol.molecular_weight or '–'} / {mol.logp or '–'}"),
        ("CYP enzymes", ", ".join(dp.cyp_enzymes) or "–"),
        ("Metabolism", ", ".join(dp.metabolism_pathways[:4]) or "–"),
        ("Therapeutic window", dp.therapeutic_window_note or "Not defined in knowledge base"),
    ]
    story.append(_kv_table(drug_rows))

    # PK metrics
    pk = report.pharmacokinetic_results
    mp = pk.metrics_patient
    story.append(Paragraph("3. Pharmacokinetic metrics (patient-adjusted)", styles["h2"]))
    pk_rows = [
        ("Cmax", f"{mp.cmax} (units as modelled)"),
        ("Tmax", f"{mp.tmax_h} h"),
        ("Half-life", f"{mp.half_life_h} h"),
        ("AUC", f"{mp.auc}"),
        ("Accumulation factor", f"{mp.accumulation_factor}×"),
        ("Clearance (adjusted)", f"{mp.clearance_adjusted}"),
        ("Vd (adjusted)", f"{mp.vd_adjusted}"),
        ("Accumulation risk", pk.accumulation_risk),
        (
            "Therapeutic window",
            f"{pk.therapeutic_window_low or '–'} – {pk.therapeutic_window_high or '–'}",
        ),
        ("Toxic threshold", str(pk.toxic_threshold or "–")),
    ]
    story.append(_kv_table(pk_rows))

    # Dose assessment
    da = report.dose_assessment
    story.append(Paragraph("4. Dose assessment", styles["h2"]))
    story.append(
        Paragraph(
            f"<b>Assessment:</b> {da.standard_dose_assessment.replace('_', ' ').title()}<br/>"
            f"<b>Suggestion:</b> {da.suggested_adjustment_range}<br/>"
            f"<b>Rationale:</b> {da.rationale}",
            styles["body"],
        )
    )

    # Organ flags
    story.append(Paragraph("5. Organ flags", styles["h2"]))
    if report.organ_flags:
        of_data = [["Organ", "Risk", "Reason"]] + [
            [f.organ, f.risk_level, f.reason] for f in report.organ_flags
        ]
        of_t = Table(of_data, colWidths=[30 * mm, 25 * mm, 120 * mm])
        of_t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(of_t)
    else:
        story.append(Paragraph("No organ-specific flags raised.", styles["body"]))

    # Contraindications
    story.append(Paragraph("6. Contraindications & allergy matches", styles["h2"]))
    if report.contraindications:
        for c in report.contraindications:
            story.append(
                Paragraph(
                    f"• <b>[{c.severity}]</b> {c.type}: {c.matched_item} — {c.message}",
                    styles["body"],
                )
            )
    else:
        story.append(Paragraph("No allergy or condition contraindications detected.", styles["body"]))

    # DDI
    story.append(Paragraph("7. Drug–drug interactions", styles["h2"]))
    if report.drug_drug_interactions:
        ddi_data = [["Interacting drug", "Type", "Severity", "Mechanism / advice"]] + [
            [
                i.interacting_drug,
                i.interaction_type,
                i.severity,
                f"{i.mechanism} → {i.recommendation}",
            ]
            for i in report.drug_drug_interactions
        ]
        ddi_t = Table(ddi_data, colWidths=[35 * mm, 35 * mm, 22 * mm, 83 * mm])
        ddi_t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(ddi_t)
    else:
        story.append(
            Paragraph(
                "No interactions matched against the current rules base for listed co-medications.",
                styles["body"],
            )
        )

    # Adverse effects
    story.append(Paragraph("8. Predicted adverse-effect priors (top)", styles["h2"]))
    if report.adverse_effects:
        ae_data = [["Effect", "Organ", "Relative probability"]] + [
            [a.effect, a.organ or "–", f"{round(a.probability * 100)}%"]
            for a in report.adverse_effects[:5]
        ]
        ae_t = Table(ae_data, colWidths=[90 * mm, 35 * mm, 40 * mm])
        ae_t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(ae_t)
    else:
        story.append(Paragraph("No prior list available for this compound.", styles["body"]))

    # Explainability
    story.append(Paragraph("9. What drove the result", styles["h2"]))
    story.append(Paragraph(report.explainability.key_drivers_summary or "–", styles["body"]))
    if report.explainability.top_patient_parameters:
        for p in report.explainability.top_patient_parameters[:5]:
            story.append(
                Paragraph(
                    f"• {p.get('param', '?')}: impact weight ~{p.get('impact', 0)}",
                    styles["small"],
                )
            )

    # Confidence / data quality
    cq = report.confidence_and_quality
    story.append(Paragraph("10. Confidence & data quality", styles["h2"]))
    story.append(
        Paragraph(
            f"Overall: <b>{cq.overall_confidence}</b> · Novel compound: {cq.novel_compound_flag}",
            styles["body"],
        )
    )
    for w in (cq.data_quality_warnings or [])[:8]:
        story.append(Paragraph(f"• {w}", styles["small"]))

    # Disclaimer
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BAD, spaceAfter=4))
    story.append(Paragraph(DISCLAIMER, styles["disclaimer"]))
    story.append(
        Paragraph(
            "This report is for research/educational use by clinicians as decision support only. "
            "It does not replace clinical judgement, local guidelines, or therapeutic drug monitoring.",
            styles["disclaimer"],
        )
    )

    doc.build(story)
    return buf.getvalue()
