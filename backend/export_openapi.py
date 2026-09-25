import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app, export_openapi_schema

if __name__ == "__main__":
    out_file = PROJECT_ROOT / "backend" / "openapi.json"
    export_openapi_schema(out_file)
