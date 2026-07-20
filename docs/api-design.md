# API Specification & Design Guidelines

## 1. Overview

The Centralized Logging API follows standard RESTful principles. All payloads use JSON encoding except for the PDF export endpoint (`POST /v1/audit/export/pdf`), which streams binary `application/pdf` output.

---

## 2. API Endpoints Reference

### 2.1 Ingestion & Log Management Router (`/v1/logs`)

#### `POST /v1/logs`
- **Description**: Submit a new log entry to the system.
- **Rate Limit**: 5 requests / minute
- **Request Body** (`LogCreate`):
  ```json
  {
    "service": "chat-api",
    "environment": "production",
    "level": "ERROR",
    "log_message": "Failed to connect to database host 10.0.0.1",
    "trace_id": "req_88192a01",
    "metadata": { "endpoint": "/v1/chat", "method": "POST" }
  }
  ```
- **Response** (`200 OK`, `LogResponse`):
  ```json
  {
    "id": "e4b2d184-7a31-4c12-9b21-123456789abc",
    "service": "chat-api",
    "environment": "production",
    "level": "ERROR",
    "log_message": "Failed to connect to database host 10.0.0.1",
    "trace_id": "req_88192a01",
    "metadata": { "endpoint": "/v1/chat", "method": "POST" },
    "created_at": "2026-07-20T10:00:00.000000+00:00"
  }
  ```

#### `GET /v1/logs`
- **Description**: Query filtered log entries (max 100).
- **Rate Limit**: 20 requests / minute
- **Query Parameters**:
  - `service` (optional string): Filter by service name.
  - `level` (optional string): Filter by log severity.
- **Response**: `200 OK`, List of `LogResponse` objects.

#### `GET /v1/logs/{log_id}`
- **Description**: Fetch log details by ID.
- **Rate Limit**: 20 requests / minute
- **Response**: `200 OK` (`LogResponse`) or `404 Not Found`.

#### `DELETE /v1/logs/{log_id}`
- **Description**: Delete a log entry by ID.
- **Rate Limit**: 2 requests / minute
- **Response**: `200 OK` `{"status": "deleted"}`.

---

### 2.2 System Analytics & Dashboard Endpoints

| Endpoint | Method | Rate Limit | Description |
| :--- | :--- | :--- | :--- |
| `/v1/logs/stats` | `GET` | 100 req/min | Overall counts, level distribution, error rates |
| `/v1/logs/trends` | `GET` | 100 req/min | 24-hour hourly trend distribution |
| `/v1/logs/issues` | `GET` | 100 req/min | Aggregated issue signature list |
| `/v1/logs/alerts` | `GET` | 100 req/min | Active high error rate alerts |
| `/v1/logs/reports` | `GET` | 100 req/min | Reliability and uptime reports |

---

### 2.3 Issue Tracking & PDF Export Router (`/v1`)

#### `GET /v1/issues`
- **Description**: Scan logs, run pattern detection rules, and return grouped issues.
- **Rate Limit**: 50 requests / minute
- **Query Parameters**: `id`, `severity` (`CRI`, `MED`, `LOW`), `category` (`DI`, `CON`, `FH`, `OBS`, `SEC`), `endpoint`.

#### `POST /v1/audit/export/pdf`
- **Description**: Compiles filtered issues into a downloadable PDF report.
- **Rate Limit**: 10 requests / minute
- **Request Body** (`PDFExportRequest`):
  ```json
  {
    "filters": { "severity": "CRI" },
    "date_range": { "start_date": "2026-07-01", "end_date": "2026-07-20" },
    "issue_ids": null
  }
  ```
- **Response**: `200 OK`, `application/pdf` streaming response with attachment content disposition.

---

### 2.4 System Operations Endpoints

| Endpoint | Method | Rate Limit | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Unlimited | System health check (`{"status": "ok", "redis": "connected"}`) |
| `/clear-redis` | `GET` | Unlimited | Administrative endpoint to clear all Redis keys |
