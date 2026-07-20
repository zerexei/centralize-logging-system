# Reliability & Operational Telemetry

## 1. Reliability Objectives & Service Level Agreements (SLAs)

The system targets high availability and minimal mean time to recovery (MTTR):

- **API Gateway Availability Target**: **99.9% Uptime**
- **Log Ingestion P99 Latency Target**: **< 50ms**
- **Dashboard Metrics Freshness**: **< 10s TTL** (redis cache expire duration)

---

## 2. Automated Reliability Metrics Calculation

The system dynamically computes uptime and reliability indicators via `LogService.get_reports()`:

$$\text{Error Rate (\%)} = \left(\frac{\text{ERROR Count} + \text{CRITICAL Count}}{\text{Total Logs}}\right) \times 100$$

$$\text{API Gateway Uptime (\%)} = \max\left(95.0, \text{round}(100.0 - (\text{Error Rate} \times 0.5), 2)\right)$$

### Reliability Reports Structure (`GET /v1/logs/reports`)

```json
[
  {
    "id": "rep_today",
    "title": "Daily Reliability Report",
    "period": "2026-07-20",
    "total_events": 1420,
    "incidents_count": 0,
    "avg_mttr": "0m",
    "service_uptime": {
      "api-gateway": "99.85%",
      "database": "99.99%",
      "auth-service": "100%"
    },
    "summary": "System operations normal. Service error rate is at 0.3%. Uptime remains within SLA guidelines."
  }
]
```

---

## 3. High Error Rate Alerting Engine (`GET /v1/logs/alerts`)

The `LogService.get_alerts()` algorithm continuously scans log telemetry across 15-minute sliding windows:

1. Filters logs with level `ERROR` or `CRITICAL` created within the last 15 minutes (`diff.total_seconds() <= 15 * 60`).
2. Groups error counts by service (`by_service`).
3. Triggers automated alerts when service error thresholds are passed:
   - **Threshold >= 3 errors in 15 mins**: Generates alert with `WARNING` severity.
   - **Threshold >= 5 errors in 15 mins**: Escalates alert to `CRITICAL` severity.

---

## 4. Health Check Mechanics (`GET /health`)

The API exposes an unthrottled health check route used by Traefik and Docker health checks:

- Executes an HTTP ping against the `/health` endpoint.
- Verifies system status and Redis connectivity.
- Returns `{"status": "ok", "redis": "connected"}` with `200 OK`.
