# Storage Architecture & Database Abstraction

## 1. Overview

The persistence layer (`app/src/database.py`) uses **SQLAlchemy 2.0 Async** engine with **asyncpg** driver for PostgreSQL. It includes a fallback mechanism to in-memory **aiosqlite** for testing or local offline setups.

## 2. Relational ORM Model Schema

Logs are stored in the `logs` table mapped by `LogModel`:

```python
class LogModel(Base):
    __tablename__ = "logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    service = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    level = Column(String, nullable=False)
    log_message = Column(Text, nullable=False)
    trace_id = Column(String, nullable=True)
    log_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### Table Schema Summary

| Column Name | Data Type | Nullable | Primary Key | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `VARCHAR` (UUID) | No | **Yes** | Unique log identifier |
| `service` | `VARCHAR` | No | No | Originating microservice name |
| `environment` | `VARCHAR` | No | No | Environment tag (e.g. `production`, `staging`) |
| `level` | `VARCHAR` | No | No | Severity level (`INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `log_message` | `TEXT` | No | No | Raw log body content |
| `trace_id` | `VARCHAR` | Yes | No | Distributed correlation identifier |
| `metadata` | `JSON` | Yes | No | Structured key-value payload |
| `created_at` | `TIMESTAMPTZ` | No | No | Ingestion timestamp in UTC |

---

## 3. Query Builder Adapter (`PostgresSupabaseAdapter`)

To maintain clean compatibility across query execution patterns, `database.py` includes `PostgresQueryBuilder`:

```python
class PostgresQueryBuilder:
    def insert(self, data): ...
    def select(self, projection="*"): ...
    def delete(self): ...
    def eq(self, column, value): ...
    def order(self, column, desc=False): ...
    def limit(self, value): ...
    def single(self): ...
    async def execute(self): ...
```

- Converts ISO timestamp strings automatically to UTC datetime objects.
- Handles string formatting for json serialization matching API expected schema.
- Global singleton exported as `supabase = PostgresSupabaseAdapter()`.

---

## 4. Connection Management & Fallback

```python
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://sentry_user:sentry_password@localhost:5432/sentry_db"
)

if os.environ.get("SUPABASE_URL") == "" or "sqlite" in DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
```

- In production (Docker Compose), connects to PostgreSQL 16 on port 5432.
- During pytest execution (when `SUPABASE_URL` is set to `""`), switches to in-memory SQLite (`sqlite+aiosqlite:///:memory:`).
