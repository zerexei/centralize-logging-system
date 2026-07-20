# System Architecture

## 1. Executive Summary

The **Centralized Logging & Observability System** provides high-throughput log ingestion, automated risk-scoring issue detection, sliding-window rate limiting, and real-time observability dashboards. Designed for microservices environments, the architecture emphasizes low latency, non-blocking asynchronous I/O, resilience against component failures, and actionable security & data integrity audit generation.

## 2. High-Level Architecture Overview

```
                      +-----------------------------+
                      |   Client Web Application    |
                      |  (Vite + React + TS App)   |
                      +--------------+--------------+
                                     |
                                     v [HTTP / Port 80]
                      +-----------------------------+
                      |      Traefik v3 Proxy       |
                      | (Host: api.localhost/app)   |
                      +------+---------------+------+
                             |               |
             Host: app.localhost             Host: api.localhost
                             |               |
                             v               v
                +-----------------+  +-----------------------+
                |  React Frontend |  |  FastAPI Backend API  |
                |   (Port 3000)   |  |      (Port 8000)      |
                +-----------------+  +-----------+-----------+
                                                 |
                                 +---------------+---------------+
                                 |                               |
                                 v                               v
                       +------------------+           +--------------------+
                       | Redis (v8.6)     |           | PostgreSQL (v16)   |
                       | Cache & Limiter  |           | Persistent Store   |
                       +------------------+           +--------------------+
```

The system is composed of five core architectural layers:
1. **Edge Routing Layer (Traefik v3.6.8)**: Handles HTTP request ingress, routing domain hosts (`api.localhost` for backend, `app.localhost` for frontend) to downstream service containers.
2. **Presentation Layer (React Dashboard)**: Built with React, TypeScript, Tailwind CSS, providing visual interfaces for system logs, telemetry metrics, issue tracking, and PDF report downloads.
3. **Application Tier (FastAPI)**: Python 3.12+ ASGI application using `uvicorn`. Structured with domain-driven design (`logs`, `issues`, `shared`).
4. **Caching & Rate Limiting Tier (Redis v8.6)**: In-memory key-value cache implementing sliding-window rate limiting (`@rate_limiter`) and TTL-based query response caching (`Cache`).
5. **Persistence Tier (PostgreSQL 16 / SQLAlchemy 2.0)**: Relational storage accessed asynchronously via `asyncpg`. Automatically falls back to an in-memory SQLite database (`aiosqlite`) during test runs or offline database environments.

---

## 3. Core Component Responsibilities

### 3.1 Ingress & Gateway (Traefik)
- Serves as the central HTTP entrypoint listening on port `:80` and admin dashboard on `:8080`.
- Proxies requests dynamically based on Host headers (`Host('api.localhost')` -> FastAPI, `Host('app.localhost')` -> React).

### 3.2 Backend Service (FastAPI)
- **Log Ingestion Router (`app/src/logs/router.py`)**: Endpoints for log creation (`POST /v1/logs`), filtered list retrieval (`GET /v1/logs`), log details (`GET /v1/logs/{id}`), deletion (`DELETE /v1/logs/{id}`), and system metrics (`/stats`, `/trends`, `/alerts`, `/reports`).
- **Issue Detection Router (`app/src/issues/router.py`)**: Endpoints for listing detected issue clusters (`GET /v1/issues`) and exporting PDF audit reports (`POST /v1/audit/export/pdf`).
- **Shared Utilities (`app/src/shared/`)**: Custom `@rate_limiter` decorator, async Redis wrapper (`Cache`), and domain exceptions (`LogInsertionException`, `LogNotFoundException`).

### 3.3 Persistence & Database Layer (`app/src/database.py`)
- Standardized `LogModel` schema storing `id`, `service`, `environment`, `level`, `log_message`, `trace_id`, `metadata` (JSON), and `created_at`.
- Abstracted `PostgresSupabaseAdapter` query builder maintaining compatibility for flexible chainable database operations.

---

## 4. Architectural Principles & Quality Attributes

| Principle | Implementation Details |
| :--- | :--- |
| **Domain-Driven Design** | Code organized by business domain (`logs/`, `issues/`, `shared/`) rather than technical layers. |
| **Async First** | All I/O operations (database queries, Redis calls, HTTP requests) use Python `async`/`await` primitives. |
| **Graceful Degradation** | Redis connection outages degrade gracefully to direct database queries without causing client HTTP 500 errors. |
| **Stateless Application Tier** | API containers hold no local state, allowing horizontal scaling behind Traefik load balancers. |
