from pydantic import BaseModel

from app.schemas.book import BookOut


class DetectedTextItem(BaseModel):
    text: str
    confidence: float


class MatchedBookItem(BaseModel):
    ocr_text: str
    ocr_confidence: float
    match_confidence: float
    book: BookOut


class ScanResponse(BaseModel):
    detected_texts: list[DetectedTextItem]
    matched: list[MatchedBookItem]
    unmatched: list[str]
