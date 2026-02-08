from typing import Optional
from redis import Redis

redis = Redis(host="redis", port=6379, db=0)


class Cache:
    @staticmethod
    def set(key: str, value: str, expire_seconds: int = 60):
        redis.setex(key, expire_seconds, value)

    @staticmethod
    def get(key: str) -> Optional[str]:
        value = redis.get(key)
        return value.decode("utf-8") if value else None

    @staticmethod
    def has(key: str) -> bool:
        return bool(redis.exists(key))

    @staticmethod
    def forget(key: str):
        redis.delete(key)
