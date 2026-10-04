import os
import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BACKEND_DIR = PROJECT_ROOT / "backend"

if __name__ == "__main__":
    # In production or runner mode, reload is False for rock-solid stability on Windows
    reload_flag = os.getenv("UVICORN_RELOAD", "false").lower() in ("true", "1")
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload_flag,
        reload_dirs=[str(BACKEND_DIR)] if reload_flag else None,
    )
