# Rate Limiting

## 1. Design Overview

To prevent abuse, protect downstream databases, and ensure fair resource sharing, the API implements a custom sliding-window rate limiter powered by Redis (`app/src/shared/rate_limiter.py`).

## 2. Rate Limiting Mechanism

Rate limiting is enforced at the controller layer via Python decorator syntax `@rate_limiter(limit, window)`:

```python
def rate_limiter(limit: int = 100, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            ...
            await _rate_limiter(request, limit, window)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Redis Key Structure & Algorithm

1. **Key Pattern**: `rate:{client_ip}:{route_path}` (e.g. `rate:192.168.1.50:/v1/logs`).
2. **Increment & TTL**:
   - `redis.incr(key)` increments request count for the specific key atomically.
   - If `count == 1`, `redis.expire(key, window)` sets key expiration time (TTL) to `window` seconds.
3. **Threshold Enforcement**:
   - If `count > limit`, throws `HTTPException(status_code=429, detail="Too Many Requests")`.

---

## 3. Endpoints Rate Limit Policy Matrix

| Endpoint | Method | Limit | Window | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `/v1/logs` | `POST` | **5 req** | 60 sec | High protection against log spamming and database ingestion overload. |
| `/v1/logs` | `GET` | **20 req** | 60 sec | Throttles bulk query execution while supporting active dashboard polling. |
| `/v1/logs/{log_id}` | `GET` | **20 req** | 60 sec | Controls single-log lookup requests. |
| `/v1/logs/{log_id}` | `DELETE` | **2 req** | 60 sec | Strict limits on destructive deletion operations. |
| `/v1/issues` | `GET` | **50 req** | 60 sec | Supports issue scanner polling on dashboard. |
| `/v1/audit/export/pdf` | `POST` | **10 req** | 60 sec | Limits CPU/RAM heavy PDF report compilation requests. |
| `/v1/logs/stats` | `GET` | **100 req** | 60 sec | Analytics summary endpoints. |
| `/v1/logs/trends` | `GET` | **100 req** | 60 sec | Analytics trends endpoints. |
| `/health` | `GET` | **Unlimited** | N/A | Excluded from rate limits to allow reliable docker health checks. |

---

## 4. Administrative Rate Limit Reset (`GET /clear-redis`)

For administrative testing and automated test execution, the API provides `GET /clear-redis`:
- Calls `redis.flushdb()` to clear all rate limit buckets and cache keys immediately.
- Used in pytest fixtures (`test_rate_limit.py`) to reset state between test assertions.
