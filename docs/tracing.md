# Distributed Tracing & Correlation

## 1. Overview

Distributed correlation enables tracking requests across distributed microservices by tagging log statements with a unique correlation identifier (`trace_id`).

## 2. Trace Context Schema

The log schema (`LogCreate`) includes an optional `trace_id` field:

```python
class LogCreate(BaseModel):
    service: str
    environment: str
    level: str
    log_message: str
    trace_id: Optional[str] = None # Correlation header
    metadata: Optional[Dict[str, Any]] = None
```

In database storage (`LogModel`), `trace_id` is indexed and surfaced across issue diagnostic views and PDF audit reports as evidence items (`request_ids`).

---

## 3. Observability Rule Enforcement

The system monitors telemetry compliance to ensure microservices propagate trace contexts:

```python
# Check for missing trace ID in Observability diagnostic scan
has_trace = bool(trace_id and trace_id.strip())
if rule["category"] == "OBS" and "trace" in rule["keywords"] and not has_trace:
    matched = True
```

If logs are ingested without a valid `trace_id`, the issue detection engine flags an **OBS (Observability)** issue (`"Missing Distributed Correlation / Trace ID"`).

---

## 4. Evidence Linkage in Issue Reports

When issues are detected, matching `trace_id` identifiers are automatically linked as evidence in the `IssueResponse` object:

```json
{
  "id": "CRI-FH-001",
  "title": "Stripe Gateway Connection Timeout",
  "evidence": {
    "log_ids": ["log_stripe_001", "log_stripe_002"],
    "request_ids": ["req_checkout_991", "req_checkout_992"]
  }
}
```

This evidence mapping allows engineers to navigate directly from aggregated issue reports back to exact log entries and HTTP request spans.
