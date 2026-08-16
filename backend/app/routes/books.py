from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.reading_history import ReadingHistory, ReadingStatus
from app.models.recommendation import Recommendation
from app.models.user import User
from app.models.wishlist import Wishlist
from app.recommendation.embedding_pipeline import ensure_book_embedded
from app.recommendation.faiss_index import reconstruct, search as faiss_search
from app.recommendation.scorer import get_recommendations
from app.schemas.book import (
    BookOut,
    BookSearchResponse,
    RecommendationsResponse,
    ScoredBookOut,
    SimilarBooksResponse,
)
from app.schemas.library import (
    ReadingHistoryItemOut,
    ReadingHistoryResponse,
    ReadingStatusUpdateRequest,
    WishlistAddRequest,
    WishlistItemOut,
    WishlistResponse,
)
from app.services.book_search import perform_book_search
from app.utils.security import get_current_user

router = APIRouter()

VALID_SEARCH_TYPES = {"title", "author", "isbn", "genre", "keyword"}
VALID_READING_STATUSES = {s.value for s in ReadingStatus}

# NOTE: static-path routes (/search, /similar/{id}, /recommendations,
# /wishlist, /reading-status) must be registered before the catch-all
# /{book_id} route below — otherwise FastAPI tries to parse e.g.
# "recommendations" as an int and 422s instead of matching this route.


@router.get("/search", response_model=BookSearchResponse)
def search_books(
    q: str = Query(..., min_length=1, max_length=300, description="Search text"),
    search_type: str = Query("keyword", description="title | author | isbn | genre | keyword"),
    limit: int = Query(20, ge=1, le=40),
    db: Session = Depends(get_db),
):
    if search_type not in VALID_SEARCH_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"search_type must be one of {sorted(VALID_SEARCH_TYPES)}",
        )

    books, source = perform_book_search(db, q, search_type, limit)
    return BookSearchResponse(
        query=q, search_type=search_type, source=source, count=len(books), results=books
    )


@router.get("/similar/{book_id}", response_model=SimilarBooksResponse)
def get_similar_books(
    book_id: int, limit: int = Query(10, ge=1, le=40), db: Session = Depends(get_db)
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    ensure_book_embedded(db, book)
    vector = reconstruct(book_id)
    if vector is None:
        return SimilarBooksResponse(book_id=book_id, count=0, results=[])

    matches = faiss_search(vector, k=limit, exclude_ids={book_id})
    score_by_id = dict(matches)
    if not score_by_id:
        return SimilarBooksResponse(book_id=book_id, count=0, results=[])

    candidates = db.query(Book).filter(Book.id.in_(score_by_id.keys())).all()
    scored = sorted(
        (
            ScoredBookOut(
                **BookOut.model_validate(b).model_dump(),
                score=score_by_id[b.id],
                reason="Semantically similar",
            )
            for b in candidates
        ),
        key=lambda item: item.score,
        reverse=True,
    )
    return SimilarBooksResponse(book_id=book_id, count=len(scored), results=scored)


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations_route(
    limit: int = Query(20, ge=1, le=40),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scored = get_recommendations(db, current_user, limit)

    # Recommendations are recomputed fresh each call; replace the user's
    # stored set rather than letting old rows accumulate unbounded.
    db.query(Recommendation).filter(Recommendation.user_id == current_user.id).delete()
    for book, score, reason in scored:
        db.add(Recommendation(user_id=current_user.id, book_id=book.id, score=score, reason=reason))
    db.commit()

    results = [
        ScoredBookOut(**BookOut.model_validate(book).model_dump(), score=score, reason=reason)
        for book, score, reason in scored
    ]
    return RecommendationsResponse(count=len(results), results=results)


@router.get("/wishlist", response_model=WishlistResponse)
def get_wishlist(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    items = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user.id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )
    return WishlistResponse(
        count=len(items),
        items=[
            WishlistItemOut(book=BookOut.model_validate(w.book), added_at=w.created_at)
            for w in items
        ],
    )


@router.post("/wishlist", response_model=WishlistItemOut, status_code=201)
def add_to_wishlist(
    payload: WishlistAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user.id, Wishlist.book_id == book.id)
        .first()
    )
    if existing:
        return WishlistItemOut(book=BookOut.model_validate(book), added_at=existing.created_at)

    entry = Wishlist(user_id=current_user.id, book_id=book.id)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return WishlistItemOut(book=BookOut.model_validate(book), added_at=entry.created_at)


@router.delete("/wishlist/{book_id}", status_code=204)
def remove_from_wishlist(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user.id, Wishlist.book_id == book_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Book is not in your wishlist")
    db.delete(entry)
    db.commit()
    return None


def _reading_history_out(book: Book, entry: ReadingHistory) -> ReadingHistoryItemOut:
    return ReadingHistoryItemOut(
        book=BookOut.model_validate(book),
        status=entry.status.value,
        started_at=entry.started_at,
        completed_at=entry.completed_at,
        updated_at=entry.updated_at,
    )


@router.get("/reading-status", response_model=ReadingHistoryResponse)
def get_reading_history(
    status: Optional[str] = Query(None, description="Filter: want_to_read | reading | completed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status is not None and status not in VALID_READING_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {sorted(VALID_READING_STATUSES)}"
        )

    query = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id)
    if status is not None:
        query = query.filter(ReadingHistory.status == ReadingStatus(status))
    items = query.order_by(ReadingHistory.updated_at.desc()).all()

    return ReadingHistoryResponse(
        count=len(items), items=[_reading_history_out(h.book, h) for h in items]
    )


@router.put("/reading-status", response_model=ReadingHistoryItemOut)
def set_reading_status(
    payload: ReadingStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in VALID_READING_STATUSES:
        raise HTTPException(
            status_code=400, detail=f"status must be one of {sorted(VALID_READING_STATUSES)}"
        )

    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    status_enum = ReadingStatus(payload.status)
    now = datetime.now(timezone.utc)

    entry = (
        db.query(ReadingHistory)
        .filter(ReadingHistory.user_id == current_user.id, ReadingHistory.book_id == book.id)
        .first()
    )
    if entry is None:
        entry = ReadingHistory(user_id=current_user.id, book_id=book.id, status=status_enum)
        db.add(entry)
    else:
        entry.status = status_enum

    if status_enum in (ReadingStatus.reading, ReadingStatus.completed) and entry.started_at is None:
        entry.started_at = now
    entry.completed_at = now if status_enum == ReadingStatus.completed else None

    # Keep wishlist and tracker mutually exclusive: once a book is
    # actively being read or finished, it's no longer just a "want to
    # read" wishlist item. This is also what makes "move wishlist book
    # to reading" work — it's just this same status update.
    if status_enum in (ReadingStatus.reading, ReadingStatus.completed):
        db.query(Wishlist).filter(
            Wishlist.user_id == current_user.id, Wishlist.book_id == book.id
        ).delete()

    db.commit()
    db.refresh(entry)
    return _reading_history_out(book, entry)


@router.delete("/reading-status/{book_id}", status_code=204)
def remove_reading_status(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = (
        db.query(ReadingHistory)
        .filter(ReadingHistory.user_id == current_user.id, ReadingHistory.book_id == book_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Book is not being tracked")
    db.delete(entry)
    db.commit()
    return None


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
