import io
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, HRFlowable
from PIL import Image

from backend.app.config import settings


def generate_case_pdf(
    case_data: dict,
    patient_name: str,
    original_img_path: Optional[Path],
    gradcam_img_path: Optional[Path],
) -> io.BytesIO:
    """Generate a publication-grade clinical review PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography
    header_style = ParagraphStyle(
        "ReportHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f766e"),  # Teal
    )
    subheader_style = ParagraphStyle(
        "ReportSubHeader",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),  # Slate
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )
    body_text = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#94a3b8"),
        alignment=1,  # Center
    )

    story = []

    # Title Banner
    story.append(Paragraph("CareLens Clinical Oncology & Radiology Portal", header_style))
    story.append(Paragraph("Diagnostic Plain Radiograph Evaluation & AI Interpretability Report", subheader_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f766e"), spaceAfter=12))

    # Case Metadata Table
    case_id = case_data.get("id", "N/A")
    created_at = case_data.get("created_at", "N/A")
    reviewed_at = case_data.get("reviewed_at", "Pending")
    status_str = case_data.get("status", "N/A")

    meta_table_data = [
        [
            Paragraph("<b>Case Reference:</b>", body_bold),
            Paragraph(f"<code>{case_id}</code>", body_text),
            Paragraph("<b>Patient Name:</b>", body_bold),
            Paragraph(patient_name, body_text),
        ],
        [
            Paragraph("<b>Submission Date:</b>", body_bold),
            Paragraph(created_at, body_text),
            Paragraph("<b>Review Status:</b>", body_bold),
            Paragraph(status_str, body_text),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[95, 175, 95, 175])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # AI Decision Support Assessment
    prob = float(case_data.get("cancer_probability", 0.0))
    risk_band = (
        "High Risk" if prob >= 0.70 else ("Borderline / Indeterminate" if prob >= 0.35 else "Low Risk")
    )
    prediction = case_data.get("model_prediction", "N/A")
    band_color = "#dc2626" if prob >= 0.70 else ("#d97706" if prob >= 0.35 else "#059669")

    ai_data = [
        [
            Paragraph("<b>Model Prediction:</b>", body_bold),
            Paragraph(prediction, body_text),
            Paragraph("<b>Calibrated Cancer Risk:</b>", body_bold),
            Paragraph(f"<b><font color='{band_color}'>{prob:.1%} ({risk_band})</font></b>", body_text),
        ]
    ]
    ai_table = Table(ai_data, colWidths=[105, 165, 120, 150])
    ai_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0fdf4" if prob < 0.35 else ("#fefce8" if prob < 0.70 else "#fef2f2"))),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(band_color)),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Paragraph("AI Decision-Support Saliency Analysis", section_title))
    story.append(ai_table)
    story.append(Spacer(1, 12))

    # Visual Evidence: Original Scan vs Grad-CAM
    img_cells = []
    if original_img_path and original_img_path.exists():
        img_cells.append(RLImage(str(original_img_path), width=230, height=230))
    else:
        img_cells.append(Paragraph("Original Scan Unavailable", body_text))

    if gradcam_img_path and gradcam_img_path.exists():
        img_cells.append(RLImage(str(gradcam_img_path), width=230, height=230))
    else:
        img_cells.append(Paragraph("Grad-CAM Overlay Unavailable", body_text))

    img_table_data = [
        [Paragraph("<b>Submitted Plain Radiograph</b>", body_bold), Paragraph("<b>Grad-CAM Saliency Overlay (Layer4)</b>", body_bold)],
        img_cells,
        [
            Paragraph("<font size='7.5' color='#64748b'>Native bone radiograph input (224x224 crop)</font>", body_text),
            Paragraph("<font size='7.5' color='#64748b'>Warm colors (red/yellow) indicate focal morphological regions driving classification</font>", body_text),
        ],
    ]
    img_table = Table(img_table_data, colWidths=[270, 270])
    img_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(img_table)
    story.append(Spacer(1, 14))

    # Physician Review Section
    verdict = case_data.get("doctor_verdict") or "Pending clinical review"
    explanation = case_data.get("doctor_explanation") or "The attending physician has not submitted review notes for this case yet."
    recommendation = case_data.get("recommendation") or "Pending physician confirmation."

    review_data = [
        [Paragraph("<b>Attending Physician Verdict:</b>", body_bold), Paragraph(f"<b>{verdict}</b>", body_text)],
        [Paragraph("<b>Clinical Findings & Notes:</b>", body_bold), Paragraph(explanation, body_text)],
        [Paragraph("<b>Recommended Next Actions:</b>", body_bold), Paragraph(recommendation, body_text)],
    ]
    review_table = Table(review_data, colWidths=[140, 400])
    review_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Paragraph("Attending Physician Formal Review", section_title))
    story.append(review_table)
    story.append(Spacer(1, 16))

    # Regulatory Disclaimer Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    disclaimer_text = (
        "CONFIDENTIAL MEDICAL REPORT — FOR PROFESSIONAL CLINICAL USE ONLY.<br/>"
        "CareLens AI decision-support algorithms are intended solely to assist licensed medical professionals. "
        "AI probabilities and Grad-CAM saliency heatmaps do not constitute a standalone medical diagnosis. "
        "Pathological diagnoses require correlation with clinical history, specialized imaging (CT/MRI), and histological biopsy."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
