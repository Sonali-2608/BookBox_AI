from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.preference import PreferredLength, ReadingFrequency, UserPreference
from app.models.user import User
from app.schemas.preferences import AnalyticsResponse, PreferencesIn, PreferencesOut
from app.services.analytics import compute_analytics
from app.utils.security import get_current_user

router = APIRouter()


def _preferences_out(pref: UserPreference) -> PreferencesOut:
    return PreferencesOut(
        favorite_genres=pref.favorite_genres or [],
        favorite_authors=pref.favorite_authors or [],
        reading_frequency=pref.reading_frequency.value if pref.reading_frequency else None,
        preferred_length=pref.preferred_length.value if pref.preferred_length else None,
        onboarding_completed=pref.onboarding_completed,
    )


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if pref is None:
        return PreferencesOut(
            favorite_genres=[],
            favorite_authors=[],
            reading_frequency=None,
            preferred_length=None,
            onboarding_completed=False,
        )
    return _preferences_out(pref)


@router.put("/preferences", response_model=PreferencesOut)
def update_preferences(
    payload: PreferencesIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        reading_frequency = (
            ReadingFrequency(payload.reading_frequency) if payload.reading_frequency else None
        )
        preferred_length = (
            PreferredLength(payload.preferred_length) if payload.preferred_length else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    if pref is None:
        pref = UserPreference(
            user_id=current_user.id,
            favorite_genres=payload.favorite_genres,
            favorite_authors=payload.favorite_authors,
            reading_frequency=reading_frequency,
            preferred_length=preferred_length,
            onboarding_completed=True,
        )
        db.add(pref)
    else:
        pref.favorite_genres = payload.favorite_genres
        pref.favorite_authors = payload.favorite_authors
        pref.reading_frequency = reading_frequency
        pref.preferred_length = preferred_length
        pref.onboarding_completed = True

    db.commit()
    db.refresh(pref)
    return _preferences_out(pref)


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    data = compute_analytics(db, current_user.id)
    return AnalyticsResponse(**data)
