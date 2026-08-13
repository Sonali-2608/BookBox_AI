"""
Orchestrates the AI reading assistant: retrieves grounding candidates
from the local catalog via semantic search, prompts Gemini to answer
using ONLY those books, and persists the exchange to ChatHistory.

Retrieval is scoped to books already in our local catalog (the same
ones search/recommendations use) rather than live-querying Google
Books/Open Library mid-chat — keeps the assistant fast and avoids
sending Gemini a large uncurated dataset (project guidance: filter with
vector retrieval first, then send only the relevant book info).
"""

from sqlalchemy.orm import Session

from app.ai.embeddings import embed_text
from app.ai.gemini_client import GeminiError, generate_json
from app.models.book import Book
from app.models.chat_history import ChatHistory, ChatRole
from app.models.user import User
from app.recommendation import faiss_index

RETRIEVAL_K = 8
MIN_SIMILARITY = 0.15  # below this, a "match" isn't worth grounding a reply in

SYSTEM_INSTRUCTION = """You are Lexora, a friendly, precise reading assistant embedded in a \
book discovery app. You are given a shortlist of real books retrieved from the app's \
catalog, each with an id. Answer the reader's question using ONLY the books in the \
shortlist below. Never invent a book, author, or detail that isn't in the shortlist. If \
none of the shortlisted books genuinely fit the request, say so plainly rather than \
forcing a recommendation.

Respond with ONLY a JSON object of this exact form:
{"reply": "<1-3 sentence conversational reply>", "book_ids": [<ids of books you're referencing, best first>]}
book_ids must only contain ids that appear in the shortlist. Use an empty list if none fit."""


def _format_book_for_prompt(book: Book) -> str:
    bits = [f'id={book.id}', f'title="{book.title}"']
    if book.authors:
        bits.append("authors=" + ", ".join(book.authors))
    if book.categories:
        bits.append("categories=" + ", ".join(book.categories))
    if book.page_count:
        bits.append(f"pages={book.page_count}")
    if book.rating:
        bits.append(f"rating={book.rating}")
    if book.description:
        bits.append("description=" + book.description[:300])
    return " | ".join(bits)


def _retrieve_candidates(db: Session, message: str) -> list[Book]:
    vector = embed_text(message)
    matches = faiss_index.search(vector, k=RETRIEVAL_K)
    matches = [(book_id, score) for book_id, score in matches if score >= MIN_SIMILARITY]
    if not matches:
        return []

    ids = [book_id for book_id, _ in matches]
    books = db.query(Book).filter(Book.id.in_(ids)).all()
    order = {book_id: i for i, book_id in enumerate(ids)}
    books.sort(key=lambda b: order.get(b.id, len(ids)))
    return books


def send_chat_message(db: Session, user: User, message: str) -> tuple[str, list[Book]]:
    """Returns (reply_text, referenced_books). Persists both the user's
    message and the assistant's reply to ChatHistory."""
    db.add(ChatHistory(user_id=user.id, role=ChatRole.user, message=message))
    db.commit()

    candidates = _retrieve_candidates(db, message)

    if not candidates:
        reply = (
            "I don't have enough books in the catalog yet to answer that well — try "
            "searching for a few books first, and I'll have more to work with."
        )
        db.add(ChatHistory(user_id=user.id, role=ChatRole.assistant, message=reply))
        db.commit()
        return reply, []

    catalog_text = "\n".join(_format_book_for_prompt(b) for b in candidates)
    prompt = f"Reader's shortlist:\n{catalog_text}\n\nReader's question: {message}"

    try:
        parsed = generate_json(prompt, system_instruction=SYSTEM_INSTRUCTION)
        reply = parsed.get("reply") or "Here's what I found in the catalog."
        book_ids = [bid for bid in parsed.get("book_ids", []) if isinstance(bid, int)]
    except GeminiError:
        # Gemini failed or returned something unusable — fall back to a
        # deterministic response grounded in the retrieved books rather
        # than a 500 or a guessed answer.
        reply = "Here's what I found that might match what you're looking for:"
        book_ids = [b.id for b in candidates]

    by_id = {b.id: b for b in candidates}
    referenced = [by_id[bid] for bid in book_ids if bid in by_id]

    db.add(ChatHistory(user_id=user.id, role=ChatRole.assistant, message=reply))
    db.commit()

    return reply, referenced


def get_chat_history(db: Session, user: User, limit: int = 50) -> list[ChatHistory]:
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user.id)
        .order_by(ChatHistory.created_at.asc())
        .limit(limit)
        .all()
    )
