# Ingestion Pipeline

## 1. Overview

The log ingestion pipeline processes incoming telemetry data submitted via `POST /v1/logs`. The pipeline ensures payload validation, rate limit enforcement, asynchronous database persistence, and cache consistency.

## 2. Ingestion Stages

```
[ Client Request ]
       │
       ▼
[ Stage 1: Rate Limiting ] ──► (Key: rate:{ip}:/v1/logs, Limit: 5/min)
       │
       ▼
[ Stage 2: Schema Validation ] ──► (Pydantic LogCreate Model)
       │
       ▼
[ Stage 3: Database Persistence ] ──► (SQLAlchemy AsyncSession / LogModel)
       │
       ▼
[ Stage 4: Cache Invalidation ] ──► (Redis forget on stale cache keys)
       │
       ▼
[ Stage 5: Response Serialization ] ──► (LogResponse payload returned)
```

### Stage 1: Rate Limiting
- Handled by `@rate_limiter(limit=5, window=60)` decorator on the `create_log` router.
- Evaluates incoming IP (`request.client.host`) and route path (`/v1/logs`).
- If request count exceeds 5 per 60-second window, throws `HTTPException(429, detail="Too Many Requests")`.

### Stage 2: Schema Validation
- Pydantic schema `LogCreate` verifies input format:
  ```python
  class LogCreate(BaseModel):
      service: str            # e.g., "chat-api"
      environment: str        # e.g., "production"
      level: str              # e.g., "ERROR", "INFO", "WARNING"
      log_message: str        # Raw message content
      trace_id: Optional[str] # Distributed correlation ID
      metadata: Optional[Dict[str, Any]] # Structured metadata JSON
  ```

### Stage 3: Database Persistence
- `LogService.create_log()` delegates persistence to `supabase.table("logs").insert(...)`.
- `PostgresQueryBuilder` creates a unique UUID `id` if omitted and sets `created_at` timestamp in UTC ISO 8601.
- Data is written via SQLAlchemy `AsyncSession` to PostgreSQL database (`LogModel` table).

### Stage 4: Cache Invalidation
Upon successful log insertion, the service invalidates related Redis keys to prevent stale dashboard metrics:
```python
await Cache.forget("logs:service::level:")
await Cache.forget(f"logs:service:{log.get('service')}:level:{log.get('level')}")
await Cache.forget("logs:stats")
await Cache.forget("logs:trends")
await Cache.forget("logs:issues")
await Cache.forget("logs:alerts")
await Cache.forget("logs:reports")
```

### Stage 5: Response Serialization
Returns a complete `LogResponse` containing `id` and ISO `created_at` timestamp alongside original log fields.

---

## 3. High-Concurrency & Performance Considerations

- **Non-blocking Execution**: The pipeline is completely asynchronous. Heavy database operations do not block Python's event loop.
- **Fast Response Time**: Typical log insertion execution takes < 15ms under standard conditions.
- **Index Support**: Log tables are indexed on `created_at`, `service`, `level`, and `environment` for quick retrieval during issue detection scans.
