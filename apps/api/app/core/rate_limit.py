"""
Rate limiting using Redis sliding window counters.

Strategy: sliding window per (user_id OR ip) per endpoint family.
Limits are checked AFTER auth so user-scoped limits apply.
IP-based limits apply before auth for DOS protection.

Headers returned on every response:
  X-RateLimit-Limit: <limit>
  X-RateLimit-Remaining: <remaining>
  X-RateLimit-Reset: <unix timestamp>

On 429, response body is RFC 7807 problem detail.
"""
from __future__ import annotations

import time
from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─── Redis client (lazy singleton) ────────────────────────────────────────────

_redis_client: aioredis.Redis | None = None  # type: ignore[type-arg]


async def get_redis() -> aioredis.Redis:  # type: ignore[type-arg]
    """Return (or lazily create) the async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


# ─── Sliding window rate limiter ──────────────────────────────────────────────

async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
) -> tuple[int, int, int]:
    """
    Sliding window rate limit check using Redis INCR + EXPIRE.

    Returns (limit, remaining, reset_ts_unix).
    Raises HTTP 429 if the limit is exceeded.

    Note: this is a simple fixed-window counter (increment + TTL reset).
    For high-traffic production, replace with a true sliding window using
    Redis sorted sets (ZADD/ZREMRANGEBYSCORE/ZCARD pipeline).
    """
    redis = await get_redis()
    pipe = redis.pipeline(transaction=True)
    pipe.incr(key)
    pipe.ttl(key)
    count_raw, ttl_raw = await pipe.execute()
    count: int = int(count_raw)
    ttl: int = int(ttl_raw)

    if ttl < 0:
        # Key just created or expired — set TTL
        await redis.expire(key, window_seconds)
        ttl = window_seconds

    remaining = max(0, limit - count)
    reset_ts = int(time.time()) + ttl

    if count > limit:
        logger.warning("Rate limit exceeded", key=key, count=count, limit=limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "https://docpilot.dev/errors/rate-limit-exceeded",
                "title": "Too Many Requests",
                "status": 429,
                "detail": (
                    f"Rate limit of {limit} requests/minute exceeded. "
                    f"Retry after {ttl} seconds."
                ),
            },
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_ts),
            },
        )

    return limit, remaining, reset_ts


async def rate_limit_by_ip(request: Request) -> None:
    """
    Dependency: rate limit by client IP (applied before auth).
    Protects unauthenticated endpoints (health, login) from DOS.
    """
    client_ip = request.client.host if request.client else "unknown"
    key = f"rl:ip:{client_ip}:{request.url.path}"
    # Lenient IP limit: 120 req/min
    limit, remaining, reset_ts = await check_rate_limit(key, limit=120, window_seconds=60)
    # Headers will be added by the calling route or middleware


async def rate_limit_by_user(
    request: Request,
    user_id: str,
) -> None:
    """
    Dependency: rate limit by authenticated user ID.
    Stricter than IP limit; applied after auth.
    """
    key = f"rl:user:{user_id}"
    await check_rate_limit(
        key,
        limit=settings.rate_limit_requests_per_minute,
        window_seconds=60,
    )


# ─── FastAPI dependency helpers ───────────────────────────────────────────────

RateLimitByIP = Annotated[None, Depends(rate_limit_by_ip)]
