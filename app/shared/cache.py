import logging
from typing import Optional
from app.config import REDIS_HOST, REDIS_PORT
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

try:
    import fakeredis.aioredis
    fake_redis_instance = fakeredis.aioredis.FakeRedis(decode_responses=True)
except ImportError:
    fake_redis_instance = None

real_redis = Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1
)


class RedisWrapper:
    def __init__(self, real_client):
        self.real_client = real_client
        self._use_fake = False

    async def _get_client(self):
        if self._use_fake and fake_redis_instance is not None:
            return fake_redis_instance
        try:
            await self.real_client.ping()
            return self.real_client
        except Exception:
            if fake_redis_instance is not None:
                self._use_fake = True
                return fake_redis_instance
            return self.real_client

    async def ping(self):
        client = await self._get_client()
        return await client.ping()

    async def incr(self, name: str, amount: int = 1):
        client = await self._get_client()
        return await client.incr(name, amount)

    async def expire(self, name: str, time: int):
        client = await self._get_client()
        return await client.expire(name, time)

    async def set(self, name: str, value: str, ex: Optional[int] = None):
        client = await self._get_client()
        return await client.set(name, value, ex=ex)

    async def get(self, name: str):
        client = await self._get_client()
        return await client.get(name)

    async def exists(self, *names: str):
        client = await self._get_client()
        return await client.exists(*names)

    async def delete(self, *names: str):
        client = await self._get_client()
        return await client.delete(*names)

    async def flushdb(self):
        client = await self._get_client()
        return await client.flushdb()

    async def aclose(self):
        if fake_redis_instance is not None:
            await fake_redis_instance.aclose()
        await self.real_client.aclose()


redis = RedisWrapper(real_redis)


class Cache:
    @staticmethod
    async def set(key: str, value: str, expire_seconds: int = 60):
        try:
            await redis.set(key, value, ex=expire_seconds)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    @staticmethod
    async def get(key: str) -> Optional[str]:
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


