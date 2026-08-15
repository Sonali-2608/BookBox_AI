from typing import Optional

from pydantic import BaseModel


class PreferencesIn(BaseModel):
    favorite_genres: list[str] = []
    favorite_authors: list[str] = []
    reading_frequency: Optional[str] = None  # daily | several_times_a_week | weekly | occasionally
    preferred_length: Optional[str] = None  # short | medium | long


class PreferencesOut(PreferencesIn):
    onboarding_completed: bool


class GenreCount(BaseModel):
    name: str
    count: int


class AuthorCount(BaseModel):
    name: str
    count: int


class MonthlyActivity(BaseModel):
    month: str  # "YYYY-MM"
    completed: int


class AnalyticsResponse(BaseModel):
    books_completed: int
    currently_reading: int
    want_to_read: int
    favorite_genres: list[GenreCount]
    favorite_authors: list[AuthorCount]
    monthly_activity: list[MonthlyActivity]
    reading_streak_days: int
