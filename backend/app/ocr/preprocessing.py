"""
OpenCV preprocessing for bookshelf photos before OCR. Aims to improve
text legibility on real photos (uneven lighting, glare, low contrast)
without anything book-specific like per-spine rotation correction —
EasyOCR's detector already handles a range of text angles on its own.
"""

import cv2
import numpy as np

MAX_DIMENSION = 1600  # bounds OCR processing time on very large photos


class InvalidImageError(Exception):
    """Raised when the uploaded bytes can't be decoded as an image."""


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    try:
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise InvalidImageError("Could not decode image — the file may not be a valid image.") from exc

    if image is None:
        raise InvalidImageError("Could not decode image — the file may not be a valid image.")

    image = _resize_if_large(image)
    image = _enhance_contrast(image)
    return image


def _resize_if_large(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= MAX_DIMENSION:
        return image
    scale = MAX_DIMENSION / longest
    return cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def _enhance_contrast(image: np.ndarray) -> np.ndarray:
    """CLAHE (contrast-limited adaptive histogram equalization) on the
    lightness channel — helps with uneven shelf lighting without
    blowing out or crushing color, unlike a flat contrast stretch."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
