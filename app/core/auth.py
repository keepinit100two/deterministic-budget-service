import os

from fastapi import Header, HTTPException


def require_ops_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key")
) -> None:
    """
    Ops authentication guard.

    Behavior:
    - 503 → OPS_API_KEY not configured (server not ready)
    - 401 → Missing API key header
    - 403 → Invalid API key
    """

    expected = os.getenv("OPS_API_KEY")

    # Config not set → service not ready
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="OPS_API_KEY not configured",
        )

    # Header missing → client not authenticated
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    # Header present but incorrect → forbidden
    if x_api_key != expected:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )