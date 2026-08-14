"""
Book-level AI insights:
  - A summary/key-takeaways/target-audience, shared across all users and
    cached on the Book row after first generation (a book's summary
    doesn't depend on who's asking, so there's no reason to regenerate
    it on every page view).
  - A "why Lexora recommends this" explanation, generated fresh per user
    since it depends on that specific reader's stated taste — but only
    when there's real signal to ground it in; a cold-start user gets no
    Gemini call and no fabricated explanation.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.ai.gemini_client import GeminiError, generate_json
from app.models.book import Book
from app.models.preference import UserPreference
from app.models.reading_history import ReadingHistory
from app.models.user import User
from app.models.wishlist import Wishlist

SUMMARY_SYSTEM_INSTRUCTION = """You are a precise book-cataloguing assistant. You're given \
metadata for one real book. Using ONLY the provided metadata — never invent plot details, \
facts, or reviews you weren't given — produce a concise, useful summary for someone \
deciding whether to read it.

Respond with ONLY a JSON object of this exact form:
{"summary": "<2-4 sentence summary>", "key_takeaways": ["<short takeaway>", "..."], "target_audience": "<one sentence: who this book is for>"}
key_takeaways should have at most 4 items."""

WHY_SYSTEM_INSTRUCTION = """You are Lexora, briefly explaining why a specific book might \
appeal to a specific reader. Use ONLY the reader's stated interests and the book's \
metadata provided below — never invent facts about the book or the reader, and never \
assume interests they didn't state. Keep it to one short, warm sentence.

Respond with ONLY a JSON object of this exact form:
{"explanation": "<one sentence>"}"""


def _book_metadata_text(book: Book) -> str:
    bits = [f"Title: {book.title}"]
    if book.authors:
        bits.append("Authors: " + ", ".join(book.authors))
    if book.categories:
        bits.append("Categories: " + ", ".join(book.categories))
    if book.page_count:
        bits.append(f"Pages: {book.page_count}")
    if book.rating:
        bits.append(f"Average rating: {book.rating}/5")
    if book.description:
        bits.append("Description: " + book.description[:1500])
    return "\n".join(bits)


def get_or_generate_summary(db: Session, book: Book) -> dict:
    """Returns {"summary", "key_takeaways", "target_audience"} (any of
    which may be None/[] if generation hasn't happened or failed)."""
    if book.ai_summary:
        return {
            "summary": book.ai_summary,
            "key_takeaways": book.ai_key_takeaways or [],
            "target_audience": book.ai_target_audience,
        }

    if not book.description:
        # Nothing to ground a summary in — don't ask Gemini to invent one.
        return {"summary": None, "key_takeaways": [], "target_audience": None}

    try:
        parsed = generate_json(
            _book_metadata_text(book), system_instruction=SUMMARY_SYSTEM_INSTRUCTION
        )
    except GeminiError:
        return {"summary": None, "key_takeaways": [], "target_audience": None}

    summary = parsed.get("summary")
    key_takeaways = parsed.get("key_takeaways") or []
    target_audience = parsed.get("target_audience")

    book.ai_summary = summary
    book.ai_key_takeaways = key_takeaways
    book.ai_target_audience = target_audience
    db.commit()

    return {"summary": summary, "key_takeaways": key_takeaways, "target_audience": target_audience}


def get_personalized_explanation(db: Session, user: User, book: Book) -> Optional[str]:
    """Returns a short personalized explanation, or None if the user has
    no stated signal to ground one in, or if generation fails."""
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    favorite_genres = (preferences.favorite_genres or []) if preferences else []
    favorite_authors = (preferences.favorite_authors or []) if preferences else []

    wishlist_titles = [
        w.book.title for w in db.query(Wishlist).filter(Wishlist.user_id == user.id) if w.book
    ][:5]
    history_titles = [
        h.book.title
        for h in db.query(ReadingHistory).filter(ReadingHistory.user_id == user.id)
        if h.book
    ][:5]

    if not (favorite_genres or favorite_authors or wishlist_titles or history_titles):
        return None

    signal_lines = []
    if favorite_genres:
        signal_lines.append("Favorite genres: " + ", ".join(favorite_genres))
    if favorite_authors:
        signal_lines.append("Favorite authors: " + ", ".join(favorite_authors))
    if wishlist_titles:
        signal_lines.append("On their wishlist: " + ", ".join(wishlist_titles))
    if history_titles:
        signal_lines.append("Books they've read: " + ", ".join(history_titles))

    prompt = (
        "Reader's stated interests:\n"
        + "\n".join(signal_lines)
        + "\n\nBook:\n"
        + _book_metadata_text(book)
    )

    try:
        parsed = generate_json(prompt, system_instruction=WHY_SYSTEM_INSTRUCTION)
        return parsed.get("explanation")
    except GeminiError:
        return None
