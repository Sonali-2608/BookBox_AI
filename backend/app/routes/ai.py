from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.book_insights import get_or_generate_summary, get_personalized_explanation
from app.ai.chat_assistant import get_chat_history, send_chat_message
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from app.schemas.ai import (
    BookSummaryResponse,
    ChatHistoryResponse,
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    WhyResponse,
)
from app.schemas.book import BookOut
from app.utils.security import get_current_user

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty")

    reply, books = send_chat_message(db, current_user, message)
    return ChatResponse(reply=reply, books=[BookOut.model_validate(b) for b in books])


@router.get("/chat/history", response_model=ChatHistoryResponse)
def chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = get_chat_history(db, current_user)
    return ChatHistoryResponse(
        messages=[ChatMessageOut(role=m.role.value, message=m.message) for m in messages]
    )


@router.get("/summary/{book_id}", response_model=BookSummaryResponse)
def summary(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    result = get_or_generate_summary(db, book)
    return BookSummaryResponse(book_id=book_id, **result)


@router.get("/why/{book_id}", response_model=WhyResponse)
def why(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    explanation = get_personalized_explanation(db, current_user, book)
    return WhyResponse(book_id=book_id, explanation=explanation)
