import io
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, status
from PIL import Image

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.ml.model import get_risk_band, run_inference_and_gradcam


def resolve_case_path(rel_or_abs: Optional[str]) -> Optional[Path]:
    if not rel_or_abs:
        return None
    p = Path(rel_or_abs)
    if p.is_absolute() and p.exists():
        return p
    if (settings.project_root / p).exists():
        return settings.project_root / p
    if (settings.upload_dir / p.name).exists():
        return settings.upload_dir / p.name
    return settings.project_root / p


def validate_uploaded_image(file_bytes: bytes) -> Image.Image:
    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds maximum permitted size of {settings.max_upload_size_bytes // (1024 * 1024)}MB.",
        )

    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or unreadable image file: {e}",
        )

    if image.format not in settings.allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{image.format}'. Only PNG and JPEG scans are permitted.",
        )

    w, h = image.size
    if (
        w < settings.min_image_dimension
        or h < settings.min_image_dimension
        or w > settings.max_image_dimension
        or h > settings.max_image_dimension
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Image dimensions ({w}x{h}) are outside allowed boundaries "
                f"({settings.min_image_dimension}x{settings.min_image_dimension} to "
                f"{settings.max_image_dimension}x{settings.max_image_dimension})."
            ),
        )

    return image.convert("RGB")


def create_case(patient_id: int, file_bytes: bytes) -> dict:
    image = validate_uploaded_image(file_bytes)
    pred_label, cancer_prob, risk_band, overlay_img = run_inference_and_gradcam(image)

    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    img_filename = f"{case_id}.png"
    cam_filename = f"{case_id}_gradcam.png"

    image.save(settings.upload_dir / img_filename, format="PNG")
    overlay_img.save(settings.upload_dir / cam_filename, format="PNG")

    rel_image_path = f"app_uploads/{img_filename}"
    rel_cam_path = f"app_uploads/{cam_filename}"
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO cases
            (id, patient_id, image_path, gradcam_path, model_prediction, cancer_probability, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'AI-analyzed', ?)
            """,
            (case_id, patient_id, rel_image_path, rel_cam_path, pred_label, cancer_prob, now_iso),
        )
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, case_id, details) VALUES (?, 'case_created', ?, ?)",
            (patient_id, case_id, f"Risk: {risk_band}, Prob: {cancer_prob:.4f}"),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.id = ?
            """,
            (case_id,),
        ).fetchone()
        return format_case_row(row)


def format_case_row(row) -> dict:
    d = dict(row)
    prob = float(d.get("cancer_probability", 0.0))
    d["risk_band"] = get_risk_band(prob)
    d["image_url"] = f"/api/media/{d['id']}/original"
    d["gradcam_url"] = f"/api/media/{d['id']}/gradcam" if d.get("gradcam_path") else None
    return d


def get_case(case_id: str, current_user: dict) -> dict:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.id = ?
            """,
            (case_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        # Per-case authorization guard
        if current_user["role"] == "patient" and row["patient_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this patient case")

        return format_case_row(row)


def list_cases_for_patient(patient_id: int, page: int = 1, limit: int = 20) -> dict:
    offset = (page - 1) * limit
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM cases WHERE patient_id = ?",
            (patient_id,),
        ).fetchone()[0]

        rows = conn.execute(
            """
            SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.patient_id = ?
            ORDER BY cases.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (patient_id, limit, offset),
        ).fetchall()

        items = [format_case_row(r) for r in rows]
        total_pages = max(1, math.ceil(total / limit))
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }


def list_cases_for_doctor(
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    offset = (page - 1) * limit
    with get_db() as conn:
        query_base = "FROM cases JOIN users ON users.id = cases.patient_id"
        where_clause = ""
        params = []

        if status_filter:
            if status_filter.lower() == "pending":
                where_clause = "WHERE cases.status IN ('AI-analyzed', 'Pending doctor review', 'In review')"
            elif status_filter.lower() == "reviewed":
                where_clause = "WHERE cases.status = 'Reviewed'"
            else:
                where_clause = "WHERE cases.status = ?"
                params.append(status_filter)

        total_sql = f"SELECT COUNT(*) {query_base} {where_clause}"
        total = conn.execute(total_sql, params).fetchone()[0]

        select_sql = f"""
            SELECT cases.*, users.display_name AS patient_name
            {query_base} {where_clause}
            ORDER BY
                CASE WHEN cases.status = 'Reviewed' THEN 1 ELSE 0 END,
                cases.created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(select_sql, params + [limit, offset]).fetchall()

        items = [format_case_row(r) for r in rows]
        total_pages = max(1, math.ceil(total / limit))
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }


def review_case(
    case_id: str,
    doctor_id: int,
    verdict: str,
    explanation: str,
    recommendation: str,
) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with get_db() as conn:
        row = conn.execute("SELECT id, status FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        conn.execute(
            """
            UPDATE cases
            SET status = 'Reviewed',
                doctor_verdict = ?,
                doctor_explanation = ?,
                recommendation = ?,
                reviewed_at = ?
            WHERE id = ?
            """,
            (verdict.strip(), explanation.strip(), recommendation.strip(), now_iso, case_id),
        )
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, case_id, details) VALUES (?, 'case_reviewed', ?, ?)",
            (doctor_id, case_id, f"Verdict: {verdict}"),
        )
        conn.commit()

        updated = conn.execute(
            """
            SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.id = ?
            """,
            (case_id,),
        ).fetchone()
        return format_case_row(updated)


def get_dashboard_stats() -> dict:
    with get_db() as conn:
        pending = conn.execute(
            "SELECT COUNT(*) FROM cases WHERE status IN ('AI-analyzed', 'Pending doctor review', 'In review')"
        ).fetchone()[0]
        reviewed = conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'Reviewed'").fetchone()[0]
        high_risk = conn.execute("SELECT COUNT(*) FROM cases WHERE cancer_probability >= 0.70").fetchone()[0]
        patients = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'patient'").fetchone()[0]

        import torch
        device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"

        return {
            "pending_count": pending,
            "reviewed_count": reviewed,
            "high_risk_count": high_risk,
            "total_patients": patients,
            "model_version": "ResNet-50 Augmented Champion (Epoch 12, 97.19% Test Acc)",
            "device": device_name,
        }
