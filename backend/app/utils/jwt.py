"""
JWT helpers. These are used by the Google OAuth flow (Phase 3) to issue
tokens after verifying a Google ID token, and by get_current_user to
validate tokens on protected routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encode `data` into a signed JWT. Caller should pass sub=<user id>."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Return the decoded payload, or None if the token is invalid/expired."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
