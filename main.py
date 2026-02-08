import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from redis import Redis
from supabase import create_client, Client

from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter.decorators import skip_limiter

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
)

redis = Redis(host="redis", port=6379, db=0)

app = FastAPI(title="Centralized Logging Service")


# --------------------
# Models
# --------------------
class LogCreate(BaseModel):
    service: str = Field(..., example="chat-api")
    environment: str = Field(..., example="production")
    level: str = Field(..., example="ERROR")
    log_message: str
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LogResponse(LogCreate):
    id: str
    created_at: str


# --------------------
# Create Log
# --------------------
@app.post(
    "/v1/logs",
    response_model=LogResponse,
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(5, Duration.MINUTE))))],
)
def create_log(log: LogCreate):
    result = supabase.table("logs").insert(log.model_dump()).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to insert log")

    return result.data[0]


# --------------------
# Read Logs (Query)
# --------------------
@app.get(
    "/v1/logs",
    response_model=List[LogResponse],
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(20, Duration.MINUTE))))],
)
def list_logs(
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = Query(100, le=500),
):
    query = (
        supabase.table("logs").select("*").order("created_at", desc=True).limit(limit)
    )

    if service:
        query = query.eq("service", service)

    if level:
        query = query.eq("level", level)

    result = query.execute()
    return result.data


# --------------------
# Get Log by ID
# --------------------
@app.get(
    "/v1/logs/{log_id}",
    response_model=LogResponse,
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(20, Duration.MINUTE))))],
)
def get_log(log_id: str):
    try:
        result = supabase.table("logs").select("*").eq("id", log_id).single().execute()
    except Exception as e:
        if e.code == "PGRST116":
            raise HTTPException(status_code=404, detail="Log not found")
        raise

    return result.data


# --------------------
# Delete Log (Retention / Cleanup)
# --------------------
@app.delete(
    "/v1/logs/{log_id}",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.MINUTE))))],
)
def delete_log(log_id: str):
    supabase.table("logs").delete().eq("id", log_id).execute()
    return {"status": "deleted"}


# --------------------
# Health Check
# --------------------
@app.get("/health")
@skip_limiter
async def health():
    # Check Redis connection
    try:
        if not redis.ping():
            raise HTTPException(status_code=503, detail="Redis not reachable")
    except Exception:
        raise HTTPException(status_code=503, detail="Redis not reachable")

    return {"status": "ok", "redis": "connected"}


@app.get("/clear-redis", dependencies=[])
def clear_redis():
    try:
        if not redis.ping():
            raise HTTPException(status_code=503, detail="Redis not reachable")
    except Exception:
        raise HTTPException(status_code=503, detail="Redis not reachable")

    redis.flushdb()

    return {"status": "redis cleared", "redis": "connected"}


"""
Example CURL Requests:

POST /v1/logs
Content-Type: application/json

{
  "service": "payment-api",
  "environment": "prod",
  "level": "ERROR",
  "log_message": "Payment gateway timeout",
  "trace_id": "req-123",
  "metadata": {
    "order_id": 9981,
    "latency_ms": 2500
  }
}

"""
