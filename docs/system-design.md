# System Design Document

## 1. Subsystem Breakdown

The system is structured into key submodules located within `app/src/`:

```
app/src/
├── main.py              # Application lifecycle, CORS, route inclusions, & health check
├── config.py            # Environment configuration (Database, Redis, Supabase)
├── database.py          # SQLAlchemy ORM, engine setup, & query builder adapter
├── logs/
│   ├── router.py        # API routes for log ingestion & analytics endpoints
│   ├── schemas.py       # Pydantic schemas (LogCreate, LogResponse)
│   └── service.py       # Core business logic for logs, stats, trends, & alerts
├── issues/
│   ├── router.py        # API routes for issue tracking & PDF exports
│   ├── schemas.py       # Issue response schemas & PDF export requests
│   └── service.py       # Log pattern detection, risk scoring, & ReportLab PDF generator
└── shared/
    ├── cache.py         # Async Redis client wrapper with fallback error handling
    ├── rate_limiter.py  # Rate limiting decorator with IP/route-based bucket logic
    └── exceptions.py   # Domain specific exceptions
```

---

## 2. Component Design & Inter-Module Workflows

### 2.1 Ingestion & Processing Flow

```
[ HTTP POST /v1/logs ]
        │
        ▼
[ rate_limiter Decorator ] ──(Exceeds 5 req/min)──► [ HTTP 429 Too Many Requests ]
        │
        ▼ (Allowed)
[ LogService.create_log() ]
        │
        ├──► Insert record via PostgresSupabaseAdapter into PostgreSQL/SQLite
        │
        └──► Invalidate affected Redis cache keys (stats, trends, issues, lists)
```

1. **Validation & Rate Control**: Incoming request passes through `@rate_limiter(limit=5, window=60)`.
2. **Schema Parsing**: Pydantic validates input (`LogCreate`).
3. **Database Insertion**: Record is written to `LogModel` in PostgreSQL/SQLite.
4. **Cache Invalidation**: Redis keys (`logs:stats`, `logs:trends`, `logs:issues`, `logs:alerts`, `logs:reports`) are invalidated to maintain fresh dashboard views.

---

### 2.2 Issue Detection & Categorization Engine

The `IssueService.detect_issues()` method analyzes ingested log messages against a set of predefined diagnostic rules (`RULE_DEFINITIONS`):

1. **Rule Keyword Matching**: Log messages are scanned for category-specific keywords:
   - **DI (Data Integrity)**: Duplicate requests, key violations, invalid state transitions.
   - **CON (Concurrency)**: Transaction deadlocks, lock clashes, concurrent webhooks.
   - **FH (Failure Handling)**: External API outages, un-retried failed jobs, cascading timeouts.
   - **OBS (Observability)**: Missing correlation trace IDs, unstructured log formats.
   - **SEC (Security)**: Unauthorized endpoint hits, admin route probing.
2. **Signature Normalization**: Parameterized messages (removing digits and UUIDs) group duplicate logs into distinct issue buckets.
3. **Risk Score Computation**: Evaluated via:
   $$\text{Risk Score} = \min\left(10.0, (\text{Impact} \times \text{Likelihood}) + \min(3.0, \text{Frequency} \times 0.1)\right)$$
4. **Severity Categorization**:
   - `risk_score >= 8.0` $\rightarrow$ **CRI** (Critical)
   - `risk_score >= 5.0` $\rightarrow$ **MED** (Medium)
   - `risk_score < 5.0` $\rightarrow$ **LOW** (Low)

---

## 3. PDF Report Generation Subsystem

The system includes an automated PDF generation capability built on **ReportLab** within `IssueService.generate_pdf_report()`:

- Configures a custom document template (`SimpleDocTemplate`) with custom color palettes (Primary Navy, Accent Blue, Dark Slate text).
- Includes dynamic headers, footers with page numbering (`NumberedCanvas`), statistical summary grid, issue details table, and evidence breakdown (log IDs and correlation request IDs).
- Returns a non-blocking `StreamingResponse` with `application/pdf` headers.
