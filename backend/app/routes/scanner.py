from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.ocr.scanner import ScanError, scan_bookshelf
from app.schemas.book import BookOut
from app.schemas.scanner import MatchedBookItem, ScanResponse

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8MB


@router.post("/upload", response_model=ScanResponse)
async def upload_scan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a JPEG, PNG, or WEBP image.",
        )

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image is too large. Max size is 8MB.")

    try:
        result = scan_bookshelf(db, contents)
    except ScanError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScanResponse(
        detected_texts=result["detected_texts"],
        matched=[
            MatchedBookItem(
                ocr_text=m["ocr_text"],
                ocr_confidence=m["ocr_confidence"],
                match_confidence=m["match_confidence"],
                book=BookOut.model_validate(m["book"]),
            )
            for m in result["matched"]
        ],
        unmatched=result["unmatched"],
    )
