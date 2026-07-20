# Deployment & Container Topology

## 1. Overview

The application is deployed using Docker Compose with multi-container service orchestration: Traefik (Edge Proxy), React Client (Frontend App), FastAPI API (Backend), Redis (Cache & Rate Limiting), and PostgreSQL (Relational Database).

## 2. Container Service Architecture (`docker-compose.yml`)

```yaml
services:
  traefik:
    image: traefik:v3.6.8
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"

  app:
    build:
      context: ./client
      dockerfile: Dockerfile
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.localhost`)"
      - "traefik.http.services.app.loadbalancer.server.port=3000"

  api:
    build:
      context: .
      dockerfile: app/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://sentry_user:sentry_password@postgres:5432/sentry_db
      - REDIS_HOST=redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.logging-api.rule=Host(`api.localhost`)"
      - "traefik.http.services.logging-api.loadbalancer.server.port=8000"

  redis:
    image: redis:8.6.0-alpine3.23
    ports:
      - "6379:6379"

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: sentry_user
      POSTGRES_PASSWORD: sentry_password
      POSTGRES_DB: sentry_db
    ports:
      - "5432:5432"
    volumes:
      - data-postgres:/var/lib/postgresql/data
```

---

## 3. Environment Variables Configuration

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://sentry_user:sentry_password@postgres:5432/sentry_db` | Asynchronous PostgreSQL connection string |
| `REDIS_HOST` | `redis` | Redis container host name |
| `REDIS_PORT` | `6379` | Redis port number |
| `SUPABASE_URL` | Optional | External Supabase URL override (empty string triggers SQLite fallback mode) |

---

## 4. Operational Commands

### Start All Services
```bash
docker compose up -d --build
```

### Check Service Status & Logs
```bash
docker compose ps
docker compose logs -f api
```

### Stop All Services
```bash
docker compose down -v
```
