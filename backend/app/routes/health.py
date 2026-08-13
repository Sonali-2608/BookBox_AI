from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "lexora-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """Confirms the API can actually reach the database, not just boot."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
