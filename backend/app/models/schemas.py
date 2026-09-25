from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


class UserRegisterRequest(BaseModel):
    username: str = Field(..., description="Unique alphanumeric username (3-30 chars)")
    password: str = Field(..., min_length=8, description="Account password (min 8 chars)")
    display_name: str = Field(..., min_length=2, max_length=60, description="Full name or clinical display name")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", clean):
            raise ValueError("Username must be 3-30 characters and contain only letters, numbers, hyphens, and underscores.")
        return clean

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 2 or len(clean) > 60:
            raise ValueError("Display name must be between 2 and 60 characters.")
        return clean


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserPublic(BaseModel):
    id: int
    username: str
    role: str
    display_name: str
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class CaseReviewRequest(BaseModel):
    doctor_verdict: str = Field(..., min_length=2, description="Physician final verdict (e.g. Malignant, Benign, Indeterminate)")
    doctor_explanation: str = Field(..., min_length=5, description="Clinical findings and radiologic interpretation")
    recommendation: str = Field(..., min_length=5, description="Next actionable clinical recommendation (e.g. Biopsy, CT, Follow-up)")


class CaseResponse(BaseModel):
    id: str
    patient_id: int
    patient_name: Optional[str] = None
    image_url: str
    gradcam_url: Optional[str] = None
    model_prediction: str
    cancer_probability: float
    risk_band: str
    status: str
    doctor_verdict: Optional[str] = None
    doctor_explanation: Optional[str] = None
    recommendation: Optional[str] = None
    created_at: str
    reviewed_at: Optional[str] = None


class PaginatedCasesResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class DashboardStats(BaseModel):
    pending_count: int
    reviewed_count: int
    high_risk_count: int
    total_patients: int
    model_version: str
    device: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    db_connected: bool
    device: str
    timestamp: str
