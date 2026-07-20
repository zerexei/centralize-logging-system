# 3. Asynchronous Database Access with SQLAlchemy 2.0

- **Status**: Accepted
- **Date**: 2026-07-20
- **Deciders**: Database & Backend Engineering Team

## Context & Problem Statement

Database operations must align with FastAPI's asynchronous architecture. Traditional synchronous database drivers (e.g. standard `psycopg2`) block worker threads during I/O queries, reducing concurrency under heavy log ingestion loads.

## Decision Drivers

- Asynchronous DB execution (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite).
- Modern SQLAlchemy 2.0 ORM patterns (`select()`, `AsyncSession`).
- Seamless support for in-memory SQLite fallbacks during automated unit testing.

## Decision Outcome

**Chosen Option**: **SQLAlchemy 2.0 Async Engine** (`create_async_engine`, `AsyncSession`).

- Uses `postgresql+asyncpg` driver in production.
- Uses `sqlite+aiosqlite` for lightweight test execution when `SUPABASE_URL=""`.
- Wrapped in `PostgresSupabaseAdapter` query builder to provide simple chainable query primitives across services.

## Consequences

- **Positive**: Prevents thread starvation during high database write traffic; dual PostgreSQL/SQLite backend support.
- **Negative**: Requires async session handling and standardizing `await session.commit()` across transactions.
