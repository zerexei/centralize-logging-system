from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.logs.router import router as logs_router
from app.issues.router import router as issues_router
from app.shared.cache import redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await redis.aclose()


app = FastAPI(title="Centralized Logging Service", lifespan=lifespan)

# Add CORS Middleware to support frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs_router)
app.include_router(issues_router)


# --------------------
# Health Check & Redis Utilities
# --------------------
@app.get("/health")
@app.get("/healthz")
async def health():
    try:
        redis_status = "connected" if await redis.ping() else "disconnected"
    except Exception:
        redis_status = "offline"
    return {"status": "ok", "redis": redis_status}


@app.get("/clear-redis")
async def clear_redis():
    try:
        await redis.flushdb()
        return {"status": "cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}