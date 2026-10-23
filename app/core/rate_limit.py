"""Simple in-memory rate limiter (per-process). For multi-worker use Redis."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_hits = defaultdict(list)


def rate_limit(request: Request, max_per_minute: int | None = None):
    """
    Sliding 60s window per client IP.
    max_per_minute: override; else settings.RATE_LIMIT_PER_MINUTE; 0 = disabled.
    """
    settings_max = 60
    try:
        from app.core.config import get_settings

        s = get_settings()
        settings_max = int(getattr(s, "RATE_LIMIT_PER_MINUTE", 60) or 60)
    except Exception:
        pass

    limit = settings_max if max_per_minute is None else max_per_minute
    if limit <= 0:
        return

    ip = "unknown"
    if request.client:
        ip = request.client.host or "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip() or ip

    now = time.time()
    window = _hits[ip]
    _hits[ip] = [t for t in window if now - t < 60]
    if len(_hits[ip]) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _hits[ip].append(now)
