# 2. Redis Sliding Window Rate Limiting Strategy

- **Status**: Accepted
- **Date**: 2026-07-20
- **Deciders**: Security & Infrastructure Team

## Context & Problem Statement

To protect the centralized logging API against malicious log flooding, denial-of-service attempts, and database connection pool exhaustion, the API must enforce granular per-endpoint rate limits.

## Decision Drivers

- Sub-millisecond latency overhead per API request.
- Centralized counter state accessible across horizontal API container replicas.
- Dynamic key expiration without manual background cleanup threads.
- Graceful degradation if the rate limiter storage experiences temporary outages.

## Considered Options

1. **Redis Key Increment with TTL Expiration**
2. **In-Memory Python Memory Cache (`dict` / `TTLCache`)**
3. **PostgreSQL Database Row Counter**

## Decision Outcome

**Chosen Option**: **Redis Key Increment with TTL Expiration** via custom Python decorator `@rate_limiter(limit, window)`.

- Key pattern: `rate:{client_ip}:{route_path}`.
- Uses `redis.incr()` and `redis.expire()` for atomic bucket tracking.
- If Redis connection drops, the helper logs a warning and permits requests to continue processing, prioritizing system availability.

## Consequences

- **Positive**: Sub-millisecond execution, distributed across containers, zero database overhead.
- **Negative**: Adds dependency on external Redis container.
