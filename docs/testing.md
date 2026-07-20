# Testing Strategy & Verification

## 1. Overview

The test suite is built using **Pytest** and **pytest-asyncio**, testing API endpoints, database interactions, rate limiting, issue detection algorithms, risk scoring, and PDF report generation.

## 2. Test Suite Structure

```
app/tests/
├── test_issues.py       # Unit & integration tests for issue detection, risk scoring, filtering, & PDF generation
└── test_rate_limit.py   # Rate limiting integration tests across endpoints
```

## 3. Test Environment Setup

To run tests in isolation without external dependencies:

```python
# Forced test environment overrides in test_issues.py
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_KEY"] = ""
os.environ["REDIS_HOST"] = "127.0.0.1"
```

Setting `SUPABASE_URL=""` forces the database connection string to use an in-memory SQLite database (`sqlite+aiosqlite:///:memory:`).

---

## 4. Key Test Scenarios Covered

### 4.1 Risk Score & Severity Calculation (`test_issues.py`)
- Verifies mathematical accuracy of formula:
  $$\text{Score} = (\text{Impact} \times \text{Likelihood}) + \min(3.0, \text{Frequency} \times 0.1)$$
- Tests threshold evaluation for `CRI` (>=8.0), `MED` (>=5.0), and `LOW` (<5.0).

### 4.2 Fallback Seeding & Completeness (`test_issues.py`)
- Verifies that `detect_issues()` succeeds and returns a complete list of `IssueResponse` items even when the database contains no logs.

### 4.3 Endpoint Filtering (`test_issues.py`)
- Tests filtering issue lists by `severity`, `category`, and `endpoint`.

### 4.4 Rate Limiting Boundaries (`test_rate_limit.py`)
- Uses `AsyncClient` against local server instance.
- Clears Redis state before each test run via `GET /clear-redis`.
- Verifies:
  - `POST /v1/logs`: 5 requests pass, 6th returns `HTTP 429`.
  - `GET /v1/logs`: 20 requests pass, 21st returns `HTTP 429`.
  - `DELETE /v1/logs/{id}`: 2 requests pass, 3rd returns `HTTP 429`.
  - `GET /health`: 50+ requests pass without rate limiting.

### 4.5 PDF Audit Generation (`test_issues.py`)
- Verifies `generate_pdf_report()` compiles without errors and returns `application/pdf` `StreamingResponse`.

---

## 5. Execution Commands

Run tests using `uv` or `pytest`:

```bash
# Execute full test suite
uv run pytest

# Execute with verbose output
uv run pytest -v -s
```
