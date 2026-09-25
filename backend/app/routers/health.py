from datetime import datetime, timezone
from fastapi import APIRouter
import torch

from backend.app.database import get_db
from backend.app.ml.model import _model, load_model
from backend.app.models.schemas import HealthResponse

router = APIRouter(tags=["Health & Telemetry"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Verify model readiness, database connectivity, and CUDA acceleration."""
    model_loaded = False
    try:
        load_model()
        model_loaded = True
    except Exception as e:
        print(f"[ERROR] Health check model failure: {e}")

    db_connected = False
    try:
        with get_db() as conn:
            conn.execute("SELECT 1").fetchone()
            db_connected = True
    except Exception as e:
        print(f"[ERROR] Health check DB failure: {e}")

    status_str = "healthy" if (model_loaded and db_connected) else "degraded"
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"

    return HealthResponse(
        status=status_str,
        model_loaded=model_loaded,
        db_connected=db_connected,
        device=device_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
