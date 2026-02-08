import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field

from supabase import create_client, Client

from cache import Cache

from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
from fastapi_limiter.decorators import skip_limiter

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
)

# LOG_QUEUE_KEY = "log_queue"


# async def process_log_queue_background():
#     while True:
#         try:
#             # BLPOP waits until an item is available in the queue
#             # Timeout is 1 second, so it doesn't block indefinitely
#             # and allows for graceful shutdown if needed.
#             item = redis.blpop(LOG_QUEUE_KEY, timeout=1)
#             if item:
#                 _queue_name, log_json = item
#                 try:
#                     log_data = json.loads(log_json)
#                     log = LogCreate(**log_data)
#                     result = supabase.table("logs").insert(log.model_dump()).execute()
#                     if not result.data:
#                         print(
#                             f"Error: Failed to insert log into Supabase: {log.model_dump()}"
#                         )
#                     else:
#                         print(f"Log processed and inserted: {result.data[0].get('id')}")
#                 except Exception as e:
#                     print(f"Error processing log from queue: {log_json} - {e}")
#                     # In a real system, you might push this to a dead-letter queue
#             else:
#                 print("Log queue is empty, waiting...")
#                 pass  # Queue was empty for 1 second, continue looping
#         except Exception as e:
#             print(f"Unhandled error in background log processor: {e}")

#         await asyncio.sleep(0.1)


# # Define the lifespan context manager to manage background tasks
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Start the background task when the app starts
#     task = asyncio.create_task(process_log_queue_background())
#     yield  # Keeps the app alive and running
#     # Cancel the background task when the app shuts down
#     task.cancel()
#     try:
#         await task  # Wait for the task to finish (handle cancellation)
#     except asyncio.CancelledError:
#         pass  # Ignore the cancellation exception


# app = FastAPI(title="Centralized Logging Service", lifespan=lifespan)

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
    # # Push log to Redis queue
    # redis.rpush(LOG_QUEUE_KEY, log.model_dump_json())

    result = supabase.table("logs").insert(log.model_dump()).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to insert log")

    log = result.data[0]
    Cache.forget("logs:service::level:")
    cache_key = f"logs:service:{log.get('service')}:level:{log.get('level')}"
    Cache.forget(cache_key)

    return log

    # return {
    #     "id": "log-123",
    #     "created_at": "2022-01-01T00:00:00Z",
    #     "service": "payment-api",
    #     "environment": "prod",
    #     "level": "ERROR",
    #     "log_message": "Payment gateway timeout",
    #     "trace_id": "req-123",
    #     "metadata": {"order_id": 9981, "latency_ms": 2500},
    # }


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
    # limit: int = Query(100, le=500),
):
    cache_key = f"logs:service:{service}:level:{level}"

    if Cache.has(cache_key):
        return json.loads(Cache.get(cache_key))

    limit = 100  # Fixed limit for simplicity
    query = (
        supabase.table("logs").select("*").order("created_at", desc=True).limit(limit)
    )

    if service:
        query = query.eq("service", service)

    if level:
        query = query.eq("level", level)

    result = query.execute()

    Cache.set(cache_key, json.dumps(result.data), expire_seconds=60)

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
    if Cache.has(f"log:{log_id}"):
        return json.loads(Cache.get(f"log:{log_id}"))

    try:
        response = (
            supabase.table("logs").select("*").eq("id", log_id).single().execute()
        )
    except Exception as e:
        if e.code == "PGRST116":
            raise HTTPException(status_code=404, detail="Log not found")
        raise

    Cache.set(f"log:{log_id}", json.dumps(response.data), expire_seconds=60)

    return response.data


# --------------------
# Delete Log (Retention / Cleanup)
# --------------------
@app.delete(
    "/v1/logs/{log_id}",
    # dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(2, Duration.MINUTE))))],
)
def delete_log(log_id: str):
    try:
        response = (
            supabase.table("logs").select("*").eq("id", log_id).single().execute()
        )
    except Exception as e:
        if e.code == "PGRST116":
            raise HTTPException(status_code=404, detail="Log not found")
        raise

    log = response.data

    supabase.table("logs").delete().eq("id", log.get("id")).execute()

    Cache.forget("logs:service::level:")
    cache_key = f"logs:service:{log.get('service')}:level:{log.get('level')}"
    Cache.forget(cache_key)
    Cache.forget(f"log:{log.get('id')}")

    return {"status": "deleted"}


# --------------------
# Health Check
# --------------------
@app.get("/health")
@skip_limiter
async def health():
    # return {"status": "ok", "redis": "connected"}
    return {"status": "ok"}


# @app.get("/clear-redis", dependencies=[])
# def clear_redis():
#     try:
#         if not redis.ping():
#             raise HTTPException(status_code=503, detail="Redis not reachable")
#     except Exception:
#         raise HTTPException(status_code=503, detail="Redis not reachable")

#     redis.flushdb()

#     return {"status": "redis cleared", "redis": "connected"}


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
