import pytest
from httpx import AsyncClient
import os
from redis import Redis


redis = Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
)


@pytest.mark.asyncio
async def test_rate_limiter():
    redis.flushdb()

    success = 0
    blocked = 0

    async with AsyncClient(base_url="http://localhost:8000") as client:
        for _ in range(7):
            response = await client.get("/v1/logs")
            if response.status_code == 200:
                success += 1
            elif response.status_code == 429:
                blocked += 1

    assert success == 5  # allowed
    assert blocked == 2  # blocked

    redis.close()
