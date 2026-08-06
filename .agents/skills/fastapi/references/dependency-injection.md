## 📌 Core Philosophy & Constraints
- **`typing.Annotated` Dependency Injection**: Use `typing.Annotated` with `Depends()` for clear, reusable, type-safe route handler parameters.
- **AsyncSession Generator Pattern**: Yield SQLAlchemy `AsyncSession` instances inside generator dependencies ensuring automatic cleanup/commit/rollback.
- **Service Layer Injection**: Inject domain service classes into router endpoints via dependencies.

## ⚡ Production Boilerplate / Standard Pattern

```python
from collections.abc import AsyncGenerator
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.users.service import UserService

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost:5432/dbname", pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Type-safe annotated dependency aliases
DbSession = Annotated[AsyncSession, Depends(get_db)]

def get_user_service(db: DbSession) -> UserService:
    return UserService(db=db)

UserServiceDep = Annotated[UserService, Depends(get_user_service)]
```

## 🚫 Forbidden Anti-Patterns
- ❌ **Unannotated Raw `Depends()`**: Declaring `db: AsyncSession = Depends(get_db)` repeatedly instead of reusable `Annotated` type aliases.
- ❌ **Global Unmanaged Sessions**: Instantiating a single global database session object shared across concurrent async requests.
- ❌ **Manual Try/Finally in Routers**: Opening and closing DB connections manually inside route handler functions.

## 🔍 Verification & Testing
- **Dependency Override Test**: Use `app.dependency_overrides[get_db] = override_get_db` in Pytest integration test suites.
