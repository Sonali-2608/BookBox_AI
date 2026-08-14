from app.ocr import easyocr_pipeline


class FakeReader:
    def __init__(self, results):
        self._results = results

    def readtext(self, image):
        return self._results


def test_detect_text_returns_clean_results(monkeypatch):
    monkeypatch.setattr(
        easyocr_pipeline,
        "_get_reader",
        lambda: FakeReader([([0, 0, 10, 10], "Atomic Habits", 0.95)]),
    )
    results = easyocr_pipeline.detect_text(object())
    assert results == [{"text": "Atomic Habits", "confidence": 0.95}]


def test_detect_text_strips_whitespace(monkeypatch):
    monkeypatch.setattr(
        easyocr_pipeline,
        "_get_reader",
        lambda: FakeReader([([0, 0, 10, 10], "  Deep Work  ", 0.9)]),
    )
    results = easyocr_pipeline.detect_text(object())
    assert results[0]["text"] == "Deep Work"


def test_detect_text_filters_low_confidence(monkeypatch):
    monkeypatch.setattr(
        easyocr_pipeline,
        "_get_reader",
        lambda: FakeReader(
            [
                ([0, 0, 10, 10], "Confident Title", 0.9),
                ([0, 0, 10, 10], "Noise", 0.1),
            ]
        ),
    )
    results = easyocr_pipeline.detect_text(object())
    assert len(results) == 1
    assert results[0]["text"] == "Confident Title"


def test_detect_text_filters_short_fragments(monkeypatch):
    monkeypatch.setattr(
        easyocr_pipeline,
        "_get_reader",
        lambda: FakeReader(
            [
                ([0, 0, 10, 10], "AB", 0.99),  # too short, likely noise
                ([0, 0, 10, 10], "Real Title", 0.99),
            ]
        ),
    )
    results = easyocr_pipeline.detect_text(object())
    assert len(results) == 1
    assert results[0]["text"] == "Real Title"


def test_detect_text_returns_empty_list_for_no_detections(monkeypatch):
    monkeypatch.setattr(easyocr_pipeline, "_get_reader", lambda: FakeReader([]))
    assert easyocr_pipeline.detect_text(object()) == []
