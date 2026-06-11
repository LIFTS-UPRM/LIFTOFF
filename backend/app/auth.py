from __future__ import annotations

import logging

from fastapi import Header, HTTPException, status

from app.supabase_client import get_supabase

logger = logging.getLogger(__name__)


async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Missing or invalid Authorization header."},
        )
    token = authorization.split(" ", 1)[1]
    try:
        response = get_supabase().auth.get_user(token)
        return str(response.user.id)
    except Exception:
        logger.warning("JWT validation failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token."},
        )
