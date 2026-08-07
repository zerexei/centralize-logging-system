from fastapi import APIRouter, Request, Query, HTTPException
from typing import List, Optional
from app.issues.schemas import IssueResponse, PDFExportRequest
from app.issues.service import IssueService
from app.shared.rate_limiter import rate_limiter

router = APIRouter(prefix="/v1", tags=["issues"])

@router.get(
    "/issues",
    response_model=List[IssueResponse],
)
@rate_limiter(limit=50, window=60)
async def list_issues(
    request: Request,
    id: Optional[str] = Query(None, description="Filter by issue ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRI, MED, LOW)"),
    category: Optional[str] = Query(None, description="Filter by category (DI, CON, FH, OBS, SEC)"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint path")
):
    try:
        return await IssueService.list_issues(
            issue_id=id,
            severity=severity,
            category=category,
            endpoint=endpoint
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list issues: {str(e)}")

@router.post(
    "/audit/export/pdf",
)
@rate_limiter(limit=10, window=60)
async def export_pdf(
    request: Request,
    payload: PDFExportRequest
):
    try:
        return await IssueService.generate_pdf_report(
            filters=payload.filters,
            date_range=payload.date_range,
            issue_ids=payload.issue_ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")
