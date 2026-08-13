"""
Verifies Google ID tokens (issued by Google Sign-In on the frontend)
against Google's public keys, using this app's GOOGLE_CLIENT_ID as the
expected audience.

This is the only place that talks to Google for auth purposes — routes
call `verify_google_token` and never touch the google-auth library
directly, which keeps the auth route easy to test (just mock this
function) and easy to swap out later if needed.
"""

from typing import Optional, TypedDict

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings


class GoogleUserInfo(TypedDict):
    google_id: str
    email: str
    name: str
    picture: Optional[str]


class InvalidGoogleTokenError(Exception):
    """Raised when a Google ID token is missing, malformed, expired, or
    was not issued for this app."""


def verify_google_token(token: str) -> GoogleUserInfo:
    """
    Verify a Google ID token and return the signed-in user's profile.

    Raises InvalidGoogleTokenError if the token is invalid/expired, was
    not issued for this app's GOOGLE_CLIENT_ID, or the email on the
    Google account isn't verified.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise InvalidGoogleTokenError("GOOGLE_CLIENT_ID is not configured on the server")

    try:
        idinfo = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as exc:
        raise InvalidGoogleTokenError(f"Invalid Google ID token: {exc}") from exc

    issuer = idinfo.get("iss")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise InvalidGoogleTokenError("Invalid token issuer")

    if not idinfo.get("email_verified", False):
        raise InvalidGoogleTokenError("Google account email is not verified")

    if "sub" not in idinfo or "email" not in idinfo:
        raise InvalidGoogleTokenError("Google token is missing required claims")

    return GoogleUserInfo(
        google_id=idinfo["sub"],
        email=idinfo["email"],
        name=idinfo.get("name") or idinfo["email"].split("@")[0],
        picture=idinfo.get("picture"),
    )
