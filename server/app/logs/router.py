from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from app.logs.schemas import LogCreate, LogResponse
from app.logs.service import LogService
from app.shared.rate_limiter import rate_limiter
from app.shared.exceptions import LogInsertionException

router = APIRouter(prefix="/v1/logs", tags=["logs"])


@router.post(
    "",
    response_model=LogResponse,
)
@rate_limiter(limit=5, window=60)
async def create_log(request: Request, log: LogCreate):
    try:
        return await LogService.create_log(log)
    except LogInsertionException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "",
    response_model=List[LogResponse],
)
@rate_limiter(limit=20, window=60)
async def list_logs(
    request: Request, service: Optional[str] = None, level: Optional[str] = None
):
    return await LogService.list_logs(service, level)


@router.get(
    "/stats",
)
@rate_limiter(limit=100, window=60)
async def get_stats(request: Request):
    return await LogService.get_stats()


@router.get(
    "/trends",
)
@rate_limiter(limit=100, window=60)
async def get_trends(request: Request):
    return await LogService.get_trends()


@router.get(
    "/issues",
)
@rate_limiter(limit=100, window=60)
async def get_issues(request: Request):
    return await LogService.get_issues()


@router.get(
    "/alerts",
)
@rate_limiter(limit=100, window=60)
async def get_alerts(request: Request):
    return await LogService.get_alerts()


@router.get(
    "/reports",
)
@rate_limiter(limit=100, window=60)
async def get_reports(request: Request):
    return await LogService.get_reports()


@router.get(
    "/{log_id}",
    response_model=LogResponse,
)
@rate_limiter(limit=20, window=60)
async def get_log(request: Request, log_id: str):
    try:
        return await LogService.get_log(log_id)
    except Exception as e:
        # TODO: improve error handling
        if hasattr(e, "code") and e.code == "PGRST116":
            raise HTTPException(status_code=404, detail="Log not found")
        raise


@router.delete("/{log_id}")
@rate_limiter(limit=2, window=60)
async def delete_log(request: Request, log_id: str):
    await LogService.delete_log(log_id)
    return {"status": "deleted"}

