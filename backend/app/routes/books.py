from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.recommendation import Recommendation
from app.models.user import User
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
from app.services.book_search import perform_book_search
from app.utils.security import get_current_user

router = APIRouter()

VALID_SEARCH_TYPES = {"title", "author", "isbn", "genre", "keyword"}

# NOTE: static-path routes (/search, /similar/{id}, /recommendations) must
# be registered before the catch-all /{book_id} route below — otherwise
# FastAPI tries to parse "recommendations" as an int and 422s instead of
# matching this route.


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


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
