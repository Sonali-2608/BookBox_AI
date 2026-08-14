import cv2
import numpy as np
import pytest

from app.ocr.preprocessing import InvalidImageError, preprocess_image


def make_image_bytes(width=400, height=300, fmt=".jpg"):
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    cv2.putText(img, "TEST", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    success, encoded = cv2.imencode(fmt, img)
    assert success
    return encoded.tobytes()


def test_preprocess_valid_jpeg_returns_array():
    result = preprocess_image(make_image_bytes(fmt=".jpg"))
    assert isinstance(result, np.ndarray)
    assert result.shape[2] == 3  # still a color image


def test_preprocess_valid_png_returns_array():
    result = preprocess_image(make_image_bytes(fmt=".png"))
    assert isinstance(result, np.ndarray)


def test_preprocess_raises_on_garbage_bytes():
    with pytest.raises(InvalidImageError):
        preprocess_image(b"this is not an image, just some random bytes")


def test_preprocess_raises_on_empty_bytes():
    with pytest.raises(InvalidImageError):
        preprocess_image(b"")


def test_preprocess_resizes_large_images():
    large_bytes = make_image_bytes(width=3000, height=2000)
    result = preprocess_image(large_bytes)
    assert max(result.shape[:2]) <= 1600


def test_preprocess_leaves_small_images_unresized():
    small_bytes = make_image_bytes(width=400, height=300)
    result = preprocess_image(small_bytes)
    assert result.shape[:2] == (300, 400)


def test_preprocess_output_still_decodable_and_sane():
    result = preprocess_image(make_image_bytes())
    # Contrast enhancement shouldn't produce NaNs/out-of-range values.
    assert result.dtype == np.uint8
    assert result.min() >= 0
    assert result.max() <= 255
