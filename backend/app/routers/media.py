from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from typing import Optional

import jwt

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.security import get_current_user, decode_token
from backend.app.services.case_service import resolve_case_path

router = APIRouter(prefix="/media", tags=["Protected Media"])


def authenticate_media_request(
    token: Optional[str] = Query(None, description="Access token query param for <img> tags"),
    current_user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """
    Allow authentication either via standard Authorization Bearer header OR
    via ?token= query parameter (essential for direct <img src="..."> loads in browser).
    """
    if current_user:
        return current_user
    if token:
        payload = decode_token(token, expected_type="access")
        user_id = payload.get("sub")
        with get_db() as conn:
            user = conn.execute(
                "SELECT id, username, role, display_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if user:
                return dict(user)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required to view clinical media",
    )


@router.get("/{case_id}/{image_type}")
def get_case_media(
    case_id: str,
    image_type: str,
    auth_user: dict = Depends(authenticate_media_request),
):
    """
    Serve uploaded radiograph or Grad-CAM overlay with strict per-case authorization.
    Verifies user ownership (for patients) or clinician role (for doctors) on EVERY image request.
    """
    if image_type not in ("original", "gradcam"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image_type. Must be 'original' or 'gradcam'.",
        )

    with get_db() as conn:
        case = conn.execute(
            "SELECT id, patient_id, image_path, gradcam_path FROM cases WHERE id = ?",
            (case_id,),
        ).fetchone()

        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        # Per-case authorization check
        if auth_user["role"] == "patient" and case["patient_id"] != auth_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you do not have permission to view this medical scan.",
            )

        target_path_str = case["gradcam_path"] if image_type == "gradcam" else case["image_path"]
        resolved_file = resolve_case_path(target_path_str)

        if not resolved_file or not resolved_file.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requested {image_type} scan image is unavailable on disk.",
            )

        # Directory traversal prevention
        try:
            resolved_file.resolve().relative_to(settings.project_root)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Illegal path access outside application root.",
            )

        return FileResponse(
            path=str(resolved_file),
            media_type="image/png",
            headers={
                "Cache-Control": "private, max-age=3600",
                "X-Content-Type-Options": "nosniff",
            },
        )
