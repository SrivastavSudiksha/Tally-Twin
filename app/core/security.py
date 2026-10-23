"""API key authentication. Empty keys only allowed outside production."""

from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """
    Require a valid X-API-Key when API_KEYS is configured.
    In production, API_KEYS is mandatory (enforced at startup in get_settings).
    """
    settings = get_settings()
    keys = settings.api_keys_list

    if not keys:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API keys not configured",
            )
        # Development only: open when no keys set
        return None

    if not x_api_key or x_api_key not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return x_api_key


def optional_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
):
    """Validate key if present; used for soft checks. Prefer require_api_key for PHI."""
    settings = get_settings()
    keys = settings.api_keys_list
    if not keys:
        return None
    if x_api_key and x_api_key in keys:
        return x_api_key
    return None
