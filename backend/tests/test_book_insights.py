from app.ai import book_insights
from app.ai.gemini_client import GeminiError
from app.models.book import Book
from app.models.preference import UserPreference
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.user import User
from app.models.wishlist import Wishlist


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_book(db, **overrides):
    defaults = dict(
        title="Atomic Habits",
        authors=["James Clear"],
        categories=["Self-Help"],
        description="A guide to building good habits and breaking bad ones.",
    )
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


# --- get_or_generate_summary ---


def test_summary_generates_and_caches_on_book(db_session, monkeypatch):
    book = make_book(db_session)
    monkeypatch.setattr(
        book_insights,
        "generate_json",
        lambda *a, **k: {
            "summary": "A book about habits.",
            "key_takeaways": ["Start small", "Be consistent"],
            "target_audience": "Anyone wanting to build better habits.",
        },
    )

    result = book_insights.get_or_generate_summary(db_session, book)

    assert result["summary"] == "A book about habits."
    assert result["key_takeaways"] == ["Start small", "Be consistent"]

    db_session.refresh(book)
    assert book.ai_summary == "A book about habits."
    assert book.ai_key_takeaways == ["Start small", "Be consistent"]


def test_summary_uses_cache_without_calling_gemini_again(db_session, monkeypatch):
    book = make_book(
        db_session,
        ai_summary="Cached summary.",
        ai_key_takeaways=["Cached takeaway"],
        ai_target_audience="Cached audience.",
    )
    calls = {"n": 0}
    monkeypatch.setattr(
        book_insights, "generate_json", lambda *a, **k: calls.update(n=calls["n"] + 1)
    )

    result = book_insights.get_or_generate_summary(db_session, book)

    assert calls["n"] == 0
    assert result["summary"] == "Cached summary."


def test_summary_skips_gemini_when_no_description(db_session, monkeypatch):
    book = make_book(db_session, description=None)
    calls = {"n": 0}
    monkeypatch.setattr(
        book_insights, "generate_json", lambda *a, **k: calls.update(n=calls["n"] + 1)
    )

    result = book_insights.get_or_generate_summary(db_session, book)

    assert calls["n"] == 0
    assert result["summary"] is None


def test_summary_returns_none_fields_on_gemini_failure(db_session, monkeypatch):
    book = make_book(db_session)

    def raise_error(*a, **k):
        raise GeminiError("down")

    monkeypatch.setattr(book_insights, "generate_json", raise_error)

    result = book_insights.get_or_generate_summary(db_session, book)
    assert result == {"summary": None, "key_takeaways": [], "target_audience": None}
    db_session.refresh(book)
    assert book.ai_summary is None  # nothing cached on failure


# --- get_personalized_explanation ---


def test_why_returns_none_for_cold_start_user(db_session):
    user = make_user(db_session)
    book = make_book(db_session)

    result = book_insights.get_personalized_explanation(db_session, user, book)
    assert result is None


def test_why_returns_none_and_calls_no_gemini_when_no_signal(db_session, monkeypatch):
    user = make_user(db_session)
    book = make_book(db_session)
    calls = {"n": 0}
    monkeypatch.setattr(
        book_insights, "generate_json", lambda *a, **k: calls.update(n=calls["n"] + 1)
    )

    book_insights.get_personalized_explanation(db_session, user, book)
    assert calls["n"] == 0


def test_why_generates_explanation_from_stated_genre_preference(db_session, monkeypatch):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=["Self-Help"], favorite_authors=[])
    )
    db_session.commit()
    book = make_book(db_session)

    captured = {}

    def fake_generate_json(prompt, system_instruction=None):
        captured["prompt"] = prompt
        return {"explanation": "Because you love self-help books!"}

    monkeypatch.setattr(book_insights, "generate_json", fake_generate_json)

    result = book_insights.get_personalized_explanation(db_session, user, book)

    assert result == "Because you love self-help books!"
    assert "Self-Help" in captured["prompt"]


def test_why_incorporates_wishlist_and_reading_history_titles(db_session, monkeypatch):
    user = make_user(db_session)
    wishlisted = make_book(db_session, google_books_id="gb-w", title="Deep Work")
    read = make_book(db_session, google_books_id="gb-r", title="The Power of Habit")
    target = make_book(db_session, google_books_id="gb-t", title="Atomic Habits")

    db_session.add(Wishlist(user_id=user.id, book_id=wishlisted.id))
    db_session.add(
        ReadingHistory(user_id=user.id, book_id=read.id, status=ReadingStatus.completed)
    )
    db_session.commit()

    captured = {}

    def fake_generate_json(prompt, system_instruction=None):
        captured["prompt"] = prompt
        return {"explanation": "Fits your reading history."}

    monkeypatch.setattr(book_insights, "generate_json", fake_generate_json)

    book_insights.get_personalized_explanation(db_session, user, target)

    assert "Deep Work" in captured["prompt"]
    assert "The Power of Habit" in captured["prompt"]


def test_why_returns_none_on_gemini_failure(db_session, monkeypatch):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=["Self-Help"], favorite_authors=[])
    )
    db_session.commit()
    book = make_book(db_session)

    def raise_error(*a, **k):
        raise GeminiError("down")

    monkeypatch.setattr(book_insights, "generate_json", raise_error)

    result = book_insights.get_personalized_explanation(db_session, user, book)
    assert result is None
