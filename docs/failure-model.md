# Failure Model & Resiliency

## 1. Overview

This document outlines system failure domains, fault isolation boundaries, error recovery mechanisms, and fallback behavior implemented across the Centralized Logging System.

## 2. Component Failure Matrix

| Component | Failure Mode | System Impact | Mitigation / Fallback Strategy |
| :--- | :--- | :--- | :--- |
| **Redis Cache** | Process crash, network partition, connection timeout | Cache hits unavailable; rate limiter keys lost | **Resilient Fallback**: `Cache.get` and `Cache.set` catch all exceptions, log warnings, and fall back to querying PostgreSQL directly without raising HTTP 500 errors. |
| **PostgreSQL DB** | Host disconnect, container crash | Persistence writes fail; query reads fail | **In-Memory Fallback**: If connection string points to SQLite or missing credentials, auto-falls back to `sqlite+aiosqlite:///:memory:` mode. Raises `LogInsertionException` mapped to HTTP 500. |
| **Rate Limiter** | Redis unreachable | Key increment fails | Rate limiting logic is bypassed safely if Redis connection drops, allowing API requests to process rather than total service shutdown. |
| **Traefik Gateway** | Container crash | External HTTP access drops | Docker health checks (`urllib.request` against `/health`) restart dead containers automatically (`restart: unless-stopped`). |

---

## 3. Detailed Failure Scenarios & Fallbacks

### 3.1 Redis Outage Handling

The Redis helper (`app/src/shared/cache.py`) is designed with defensive exception handling:

```python
class Cache:
    @staticmethod
    async def get(key: str) -> Optional[str]:
        try:
            value = await redis.get(key)
            return value or None
        except Exception as e:
            logger.warning(f"Cache read error (Redis offline): {e}")
            return None
```

If Redis goes down:
1. All `Cache.get()` calls return `None`, causing services to fetch live data from PostgreSQL.
2. All `Cache.set()` and `Cache.forget()` operations swallow connection errors gracefully.
3. System availability remains unaffected; response latency slightly increases due to direct DB queries.

---

### 3.2 Database Connection & Transaction Recovery

- Database sessions use SQLAlchemy `AsyncSession` with explicit rollback management on errors.
- Schema auto-creation (`init_db`) runs on container boot, creating tables automatically if missing.
- In-memory SQLite fallback allows running test suites and offline local development without external postgres services.

---

### 3.3 Endpoint Error Boundary Mapping

Standard domain exceptions are mapped cleanly to HTTP status codes at the API boundary (`app/src/logs/router.py` & `app/src/issues/router.py`):

| Exception Type | Trigger Condition | HTTP Status Code | Response Payload |
| :--- | :--- | :--- | :--- |
| `HTTPException(429)` | Rate limit exceeded | `429 Too Many Requests` | `{"detail": "Too Many Requests"}` |
| `LogInsertionException` | Database insert failed | `500 Internal Server Error` | `{"detail": "Failed to insert log"}` |
| `PostgrestError (PGRST116)` | Single record lookup empty | `404 Not Found` | `{"detail": "Log not found"}` |
