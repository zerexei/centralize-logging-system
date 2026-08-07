from functools import wraps
from fastapi import Request, HTTPException
from app.shared.cache import redis


async def _rate_limiter(request: Request, limit: int, window: int):
    ip = request.client.host if request.client else "unknown"
    route = request.scope.get("route")
    path = route.path if route else request.url.path

    key = f"rate:{ip}:{path}"

    count = await redis.incr(key)

    if count == 1:
        await redis.expire(key, window)

    if count > limit:
        raise HTTPException(status_code=429, detail="Too Many Requests")


def rate_limiter(limit: int = 100, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")

            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                raise RuntimeError("Request is required for rate limiting")

            await _rate_limiter(request, limit, window)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
