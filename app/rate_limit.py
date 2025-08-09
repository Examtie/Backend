from fastapi import Depends, HTTPException, Request, status
from typing import Tuple

from .database import redis_client
from .dependencies import get_current_user


# Limits: 1/sec, 4/min, 15/hour, 30/day
WINDOW_LIMITS: Tuple[Tuple[int, int], ...] = (
    (1, 1),          # 1 request per 1 second
    (60, 4),         # 4 requests per 60 seconds (1 minute)
    (3600, 15),      # 15 requests per 3600 seconds (1 hour)
    (86400, 30),     # 30 requests per 86400 seconds (1 day)
)


async def _inc_and_check(user_id: str) -> None:
    """Increment per-window counters and raise 429 if any window exceeded."""
    for window_seconds, limit in WINDOW_LIMITS:
        key = f"rl:{user_id}:{window_seconds}"
        # INCR is atomic; set expiry only when first created
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        if count > limit:
            # Compute simple retry-after based on TTL
            ttl = await redis_client.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limited",
                    "message": f"Rate limit exceeded: {limit} per {window_seconds} seconds",
                    "retry_after": max(ttl, 1),
                },
                headers={"Retry-After": str(max(ttl, 1))} if ttl and ttl > 0 else None,
            )


async def rate_limit_dependency(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Rate limit dependency for AI generation endpoints.
    Skips rate limits if BYO key header "X-API-Key" is present and non-empty.
    """
    # Skip rate limiting when user supplies their own provider API key
    byo_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if byo_key:
        return

    user_id = str(current_user.get("_id") or current_user.get("id") or current_user.get("email") or "anon")
    await _inc_and_check(user_id)
