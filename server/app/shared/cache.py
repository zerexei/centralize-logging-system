import structlog
from redis.asyncio import Redis

from app.config import settings

logger = structlog.get_logger()

redis = Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    decode_responses=True,
)


class Cache:
    @staticmethod
    async def set(key: str, value: str, expire_seconds: int = 60):
        try:
            await redis.set(key, value, ex=expire_seconds)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    @staticmethod
    async def get(key: str) -> str | None:
        try:
            value = await redis.get(key)
            return value or None
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    @staticmethod
    async def has(key: str) -> bool:
        try:
            return bool(await redis.exists(key))
        except Exception as e:
            logger.warning(f"Cache check error: {e}")
            return False

    @staticmethod
    async def forget(key: str):
        try:
            await redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
