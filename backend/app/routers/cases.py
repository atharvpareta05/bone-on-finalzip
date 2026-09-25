from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from backend.app.models.schemas import (
    CaseResponse,
    CaseReviewRequest,
    DashboardStats,
    PaginatedCasesResponse,
)
from backend.app.security import get_current_user, require_role
from backend.app.services.case_service import (
    create_case,
    get_case,
    get_dashboard_stats,
    list_cases_for_doctor,
    list_cases_for_patient,
    resolve_case_path,
    review_case,
)
from backend.app.services.pdf_service import generate_case_pdf

router = APIRouter(prefix="/cases", tags=["Clinical Cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_case(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Submit plain radiograph image, execute ResNet-50 inference + Grad-CAM,
    and persist new clinical case record.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded.",
        )

    case_data = create_case(current_user["id"], file_bytes)
    return CaseResponse(**case_data)


@router.get("/stats", response_model=DashboardStats)
def get_stats(current_user: dict = Depends(get_current_user)):
    """Fetch aggregated clinical dashboard counters."""
    return DashboardStats(**get_dashboard_stats())


@router.get("", response_model=PaginatedCasesResponse)
def list_cases(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter: 'pending', 'reviewed', or specific status"),
    current_user: dict = Depends(get_current_user),
):
    """
    List cases:
    - Patients: view their own submitted scans
    - Doctors: view triage queue and reviewed cases with optional status filter
    """
    if current_user["role"] == "patient":
        result = list_cases_for_patient(current_user["id"], page=page, limit=limit)
    else:
        result = list_cases_for_doctor(status_filter=status, page=page, limit=limit)

    return PaginatedCasesResponse(
        items=[CaseResponse(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        total_pages=result["total_pages"],
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case_detail(
    case_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Fetch complete case details (enforces per-case ownership / doctor role)."""
    case_data = get_case(case_id, current_user)
    return CaseResponse(**case_data)


@router.post("/{case_id}/review", response_model=CaseResponse)
def submit_doctor_review(
    case_id: str,
    payload: CaseReviewRequest,
    current_user: dict = Depends(require_role(["doctor"])),
):
    """Submit formal clinical review (Doctor role required)."""
    updated_case = review_case(
        case_id=case_id,
        doctor_id=current_user["id"],
        verdict=payload.doctor_verdict,
        explanation=payload.doctor_explanation,
        recommendation=payload.recommendation,
    )
    return CaseResponse(**updated_case)


@router.get("/{case_id}/report.pdf")
def download_case_report(
    case_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Download comprehensive clinical PDF report for a case."""
    case_data = get_case(case_id, current_user)
    patient_name = case_data.get("patient_name") or "Patient"

    orig_path = resolve_case_path(case_data.get("image_path"))
    cam_path = resolve_case_path(case_data.get("gradcam_path"))

    pdf_buffer = generate_case_pdf(
        case_data=case_data,
        patient_name=patient_name,
        original_img_path=orig_path,
        gradcam_img_path=cam_path,
    )

    filename = f"CareLens_Report_{case_id}.pdf"
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
