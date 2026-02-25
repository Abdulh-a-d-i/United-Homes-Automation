"""
API key authentication for Retell-facing endpoints.
These endpoints cannot use JWT because they are called by Retell's agent.
Instead they use a shared secret sent as X-API-Key header.
"""
import os
import logging
from fastapi import HTTPException, Request

RETELL_TOOL_API_KEY = os.getenv("RETELL_TOOL_API_KEY", "")


def verify_retell_api_key(request: Request):
    """Validate X-API-Key header on Retell tool endpoints."""
    if not RETELL_TOOL_API_KEY:
        logging.warning("[AUTH] RETELL_TOOL_API_KEY not set -- Retell endpoints are UNPROTECTED")
        return

    api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if not api_key or api_key != RETELL_TOOL_API_KEY:
        logging.warning(f"[AUTH] Invalid or missing API key on {request.url.path}")
        raise HTTPException(status_code=401, detail="Invalid API key")
