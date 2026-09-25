from contextlib import asynccontextmanager
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import init_database
from backend.app.ml.model import load_model
from backend.app.routers import auth, cases, health, media


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    print("[INIT] Initializing CareLens database schema...")
    init_database()
    print("[INIT] Pre-loading ResNet-50 clinical model...")
    try:
        load_model()
        print("[INIT] Model successfully loaded and ready.")
    except Exception as e:
        print(f"[WARN] Deferred model loading error: {e}")

    yield

    # Teardown sequence
    print("[SHUTDOWN] CareLens API service stopped.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Clinical decision-support API for plain radiograph bone tumor detection and Grad-CAM interpretability.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration: Explicit origins, explicit methods/headers, credentials enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# Global Exception Handler for Clean Clinical Error Responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    print(f"[UNHANDLED ERROR] {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal clinical system error occurred. Please contact hospital technical support."},
    )


# Mount Routers under both root and /api for full compatibility with OpenAPI specification
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(media.router)
app.include_router(health.router)

app.include_router(auth.router, prefix="/api")
app.include_router(cases.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(health.router, prefix="/api")


@app.get("/me", response_model=auth.UserPublic, tags=["Authentication"])
@app.get("/api/me", response_model=auth.UserPublic, tags=["Authentication"])
def get_me_alias(current_user: dict = auth.Depends(auth.get_current_user)):
    return auth.UserPublic(**current_user)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "documentation": "/docs",
        "disclaimer": "AI decision-support prototype — not a certified diagnostic device.",
    }


def export_openapi_schema(target_path: Path):
    """Write current OpenAPI schema to disk for frontend type generation."""
    schema = app.openapi()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"[SUCCESS] Exported OpenAPI schema to {target_path}")
