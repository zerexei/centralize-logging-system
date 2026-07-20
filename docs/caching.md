# Caching Strategy

## 1. Overview

The system uses **Redis (v8.6)** to cache expensive query results and dashboard metrics, reducing database load and delivering fast sub-10ms API responses.

## 2. Redis Client Configuration (`app/src/shared/cache.py`)

- **Host/Port**: Configured via `REDIS_HOST` (default `redis`) and `REDIS_PORT` (default `6379`).
- **Connection Timeouts**: `socket_connect_timeout=2`, `socket_timeout=2`.
- **String Decoding**: `decode_responses=True` to eliminate binary byte handling in application code.

---

## 3. Cache Keys & TTL Policy

| Cache Key Pattern | Cached Content | TTL (Seconds) | Invalidation Trigger |
| :--- | :--- | :--- | :--- |
| `logs:service:{svc}:level:{lvl}` | Filtered log lists | 10s | Log creation or log deletion |
| `log:{log_id}` | Single log response payload | 60s | Log deletion |
| `logs:stats` | Aggregated log statistics | 10s | Log creation or log deletion |
| `logs:trends` | Hourly trend counts (last 24h) | 10s | Log creation or log deletion |
| `logs:issues` | Issue breakdown list | 10s | Log creation or log deletion |
| `logs:alerts` | High error rate alerts | 10s | Log creation or log deletion |
| `logs:reports` | System reliability summaries | 10s | Log creation or log deletion |

---

## 4. Write-Through & Invalidation Pattern

When a log is inserted (`create_log`) or deleted (`delete_log`), stale cache entries are purged immediately via `Cache.forget(key)`:

```python
await Cache.forget("logs:service::level:")
await Cache.forget(f"logs:service:{log.get('service')}:level:{log.get('level')}")
await Cache.forget(f"log:{log.get('id')}")
await Cache.forget("logs:stats")
await Cache.forget("logs:trends")
await Cache.forget("logs:issues")
await Cache.forget("logs:alerts")
await Cache.forget("logs:reports")
```

---

## 5. Offline Resiliency

If Redis encounters connectivity issues:
- Calls to `Cache.get()` catch exceptions and return `None`.
- Application gracefully queries PostgreSQL directly.
- Calls to `Cache.set()` and `Cache.forget()` catch exceptions and log warnings (`logger.warning("Cache write error...")`).
