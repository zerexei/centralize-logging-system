# Observability Telemetry & Analytics

## 1. Overview

The Centralized Logging System provides endpoints for real-time observability dashboards, analytics trends, high error rate alerts, and reliability metrics.

## 2. Analytics Subsystem Endpoints

### 2.1 Statistics Summary (`GET /v1/logs/stats`)
Returns log volume breakdowns by level, service, environment, and overall error rate:

```json
{
  "total_count": 1250,
  "by_level": {
    "INFO": 800,
    "WARNING": 300,
    "ERROR": 140,
    "CRITICAL": 10
  },
  "by_service": {
    "chat-api": 600,
    "auth-service": 400,
    "payment-gateway": 250
  },
  "by_environment": {
    "production": 1000,
    "staging": 250
  },
  "error_rate": 12.0
}
```

### 2.2 Hourly Volume Trends (`GET /v1/logs/trends`)
Aggregates event volume into 24 one-hour time buckets spanning the last 24 hours:

```json
[
  {
    "timestamp": "2026-07-20 09:00",
    "info_count": 45,
    "warning_count": 12,
    "error_count": 3,
    "total_count": 60
  }
]
```

### 2.3 Automated Incident Alerts (`GET /v1/logs/alerts`)
Evaluates sliding 15-minute windows for services generating high error rates (>= 3 errors in 15 mins):

```json
[
  {
    "id": "alt_a1b2c3d4e5f6",
    "service": "payment-gateway",
    "title": "High Error Rate",
    "description": "Service 'payment-gateway' generated 6 errors in the last 15 minutes.",
    "severity": "CRITICAL",
    "timestamp": "2026-07-20T10:00:00+00:00",
    "status": "Active"
  }
]
```

### 2.4 Reliability Audit Summary (`GET /v1/logs/reports`)
Computes SLA uptime metrics and generates daily/weekly observability reports.
