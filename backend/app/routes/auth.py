from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import GoogleAuthRequest
from app.schemas.user import TokenResponse, UserOut
from app.services.google_auth import InvalidGoogleTokenError, verify_google_token
from app.utils.jwt import create_access_token
from app.utils.security import get_current_user

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Full flow: verify the Google ID token -> find or create the local
    user -> issue our own JWT. The frontend uses the returned
    access_token on all subsequent authenticated requests.
    """
    try:
        google_user = verify_google_token(payload.id_token)
    except InvalidGoogleTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.query(User).filter(User.google_id == google_user["google_id"]).first()

    if user is None:
        # Fall back to matching by email, in case this Google account was
        # somehow already registered under a different google_id.
        user = db.query(User).filter(User.email == google_user["email"]).first()

    if user is None:
        user = User(
            google_id=google_user["google_id"],
            name=google_user["name"],
            email=google_user["email"],
            profile_image=google_user.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Keep profile info in sync with Google on every login.
        changed = False
        if user.google_id != google_user["google_id"]:
            user.google_id = google_user["google_id"]
            changed = True
        if user.name != google_user["name"]:
            user.name = google_user["name"]
            changed = True
        if google_user.get("picture") and user.profile_image != google_user["picture"]:
            user.profile_image = google_user["picture"]
            changed = True
        if changed:
            db.commit()
            db.refresh(user)

    access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    JWTs are stateless, so there's nothing to invalidate server-side —
    the frontend simply discards the token. This endpoint exists so the
    frontend has a single, auth-checked call to hit on sign-out (and
    it's the natural place to add a token blocklist later if needed).
    """
    return {"message": "Logged out successfully"}
