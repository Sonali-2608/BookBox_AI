"""
EasyOCR text detection, lazily loaded (model init downloads weights and
takes real time) so it only happens on the first actual scan request —
not at server startup, and not for requests that don't need it.
"""

import numpy as np

_reader = None

MIN_OCR_CONFIDENCE = 0.3  # below this, a "detection" is likely noise, not a title
MIN_TEXT_LENGTH = 3


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr

        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def detect_text(image: np.ndarray) -> list[dict]:
    """Returns [{"text": str, "confidence": float}, ...] for text
    fragments EasyOCR found and is at least somewhat confident about.
    Short or very-low-confidence fragments are dropped here rather than
    left for callers to filter — they're consistently noise, not
    partial titles worth showing for manual correction."""
    reader = _get_reader()
    results = reader.readtext(image)

    detections = []
    for _bbox, text, confidence in results:
        cleaned = text.strip()
        if len(cleaned) >= MIN_TEXT_LENGTH and confidence >= MIN_OCR_CONFIDENCE:
            detections.append({"text": cleaned, "confidence": float(confidence)})
    return detections
