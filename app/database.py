import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import Column, String, Text, DateTime, JSON, select, insert, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

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

# PostgreSQL or SQLite Connection Setup
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://sentry_user:sentry_password@localhost:5432/sentry_db"
)

# Force SQLite in-memory database for testing/fallback if credentials are empty
if os.environ.get("SUPABASE_URL") == "" or "sqlite" in DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

logger.info(f"Database URL configured: {DATABASE_URL}")
async_engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# MockResponse containing data matching Supabase responses
class MockResponse:
    def __init__(self, data):
        self.data = data

# Async Query Builder replicating Supabase query methods using SQLAlchemy
class PostgresQueryBuilder:
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.filters = []
        self.sort_col = None
        self.sort_desc = False
        self.limit_val = None
        self.is_single = False
        self.is_delete = False
        self.insert_data = None

    def insert(self, data):
        self.insert_data = data
        return self

    def select(self, projection="*"):
        return self

    def delete(self):
        self.is_delete = True
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.sort_col = column
        self.sort_desc = desc
        return self

    def limit(self, value):
        self.limit_val = value
        return self

    def single(self):
        self.is_single = True
        return self

    async def execute(self):
        async with async_session() as session:
            # 1. Handle Insert
            if self.insert_data is not None:
                records = self.insert_data if isinstance(self.insert_data, list) else [self.insert_data]
                inserted_records = []
                for r in records:
                    new_record = dict(r)
                    if "id" not in new_record:
                        new_record["id"] = str(uuid.uuid4())
                    if "created_at" not in new_record:
                        new_record["created_at"] = datetime.now(timezone.utc)
                    elif isinstance(new_record["created_at"], str):
                        try:
                            # Convert ISO timestamp string to datetime
                            new_record["created_at"] = datetime.fromisoformat(new_record["created_at"].replace("Z", "+00:00"))
                        except Exception:
                            new_record["created_at"] = datetime.now(timezone.utc)
                    
                    db_log = LogModel(
                        id=new_record.get("id"),
                        service=new_record.get("service"),
                        environment=new_record.get("environment"),
                        level=new_record.get("level"),
                        log_message=new_record.get("log_message"),
                        trace_id=new_record.get("trace_id"),
                        log_metadata=new_record.get("metadata"),
                        created_at=new_record.get("created_at")
                    )
                    session.add(db_log)
                    
                    # Convert datetimes back to strings for API matching format
                    new_record["created_at"] = new_record["created_at"].isoformat()
                    inserted_records.append(new_record)
                
                await session.commit()
                return MockResponse(inserted_records)

            # 2. Handle Delete
            if self.is_delete:
                stmt = delete(LogModel)
                for col, val in self.filters:
                    stmt = stmt.where(getattr(LogModel, col) == val)
                
                # Fetch matching records first to return them as deleted items
                select_stmt = select(LogModel)
                for col, val in self.filters:
                    select_stmt = select_stmt.where(getattr(LogModel, col) == val)
                result = await session.execute(select_stmt)
                deleted_rows = result.scalars().all()
                
                deleted_dicts = []
                for row in deleted_rows:
                    deleted_dicts.append({
                        "id": row.id,
                        "service": row.service,
                        "environment": row.environment,
                        "level": row.level,
                        "log_message": row.log_message,
                        "trace_id": row.trace_id,
                        "metadata": row.log_metadata,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })
                
                await session.execute(stmt)
                await session.commit()
                return MockResponse(deleted_dicts)

            # 3. Handle Select
            stmt = select(LogModel)
            for col, val in self.filters:
                stmt = stmt.where(getattr(LogModel, col) == val)
            
            if self.sort_col:
                col_attr = getattr(LogModel, self.sort_col)
                stmt = stmt.order_by(col_attr.desc() if self.sort_desc else col_attr.asc())
            
            if self.limit_val:
                stmt = stmt.limit(self.limit_val)
            
            result = await session.execute(stmt)
            rows = result.scalars().all()
            
            results_dicts = []
            for row in rows:
                results_dicts.append({
                    "id": row.id,
                    "service": row.service,
                    "environment": row.environment,
                    "level": row.level,
                    "log_message": row.log_message,
                    "trace_id": row.trace_id,
                    "metadata": row.log_metadata,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                })

            if self.is_single:
                if not results_dicts:
                    class PostgrestError(Exception):
                        def __init__(self):
                            self.code = "PGRST116"
                            self.message = "JSON object requested, multiple rows or no rows returned"
                    raise PostgrestError()
                return MockResponse(results_dicts[0])

            return MockResponse(results_dicts)

class PostgresSupabaseAdapter:
    def table(self, table_name: str):
        return PostgresQueryBuilder(table_name)

# Global database client instance (fully PostgreSQL / SQLite backed)
supabase = PostgresSupabaseAdapter()
