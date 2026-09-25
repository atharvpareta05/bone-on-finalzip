import os
from pathlib import Path
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    # App Information
    app_name: str = "CareLens API"
    app_version: str = "2.0.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Paths
    project_root: Path = PROJECT_ROOT
    model_path: Path = PROJECT_ROOT / "outputs" / "resnet50_augmented" / "best_resnet50.pt"
    db_path: Path = PROJECT_ROOT / "app_data.sqlite3"
    upload_dir: Path = PROJECT_ROOT / "app_uploads"
    demo_users_path: Path = PROJECT_ROOT / ".demo_users.json"

    # Security & JWT
    jwt_secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "carelens-clinical-prototype-jwt-secret-do-not-use-in-production-change-in-env"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cookie_secure: bool = Field(default_factory=lambda: os.getenv("COOKIE_SECURE", "false").lower() == "true")
    cookie_samesite: str = Field(default_factory=lambda: os.getenv("COOKIE_SAMESITE", "lax"))

    # Lockout Controls
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    # Upload Bounds
    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    min_image_dimension: int = 64
    max_image_dimension: int = 4096
    allowed_formats: tuple = ("PNG", "JPEG", "MPO")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
            if origin.strip()
        ]
    )


settings = Settings()
