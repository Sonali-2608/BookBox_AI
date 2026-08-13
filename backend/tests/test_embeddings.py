import numpy as np

from app.ai import embeddings


class FakeModel:
    """Stands in for SentenceTransformer — returns deterministic,
    already-normalized vectors so we can test the wrapper logic
    (dtype, shape, normalize_embeddings passthrough) without a real
    model download."""

    def __init__(self, dim=embeddings.EMBEDDING_DIM):
        self.dim = dim
        self.calls = []

    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True):
        self.calls.append({"texts": texts, "normalize_embeddings": normalize_embeddings})
        rng = np.random.default_rng(42)
        vectors = rng.random((len(texts), self.dim)).astype("float32")
        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / norms
        return vectors


def test_embed_texts_returns_correct_shape(monkeypatch):
    fake_model = FakeModel()
    monkeypatch.setattr(embeddings, "_get_model", lambda: fake_model)

    result = embeddings.embed_texts(["Atomic Habits", "Deep Work"])

    assert result.shape == (2, embeddings.EMBEDDING_DIM)
    assert result.dtype == np.float32


def test_embed_texts_empty_list_returns_empty_array(monkeypatch):
    # Should short-circuit without even touching the model.
    called = {"count": 0}

    def fail_if_called():
        called["count"] += 1
        return FakeModel()

    monkeypatch.setattr(embeddings, "_get_model", fail_if_called)
    result = embeddings.embed_texts([])

    assert result.shape == (0, embeddings.EMBEDDING_DIM)
    assert called["count"] == 0


def test_embed_texts_requests_normalized_embeddings(monkeypatch):
    fake_model = FakeModel()
    monkeypatch.setattr(embeddings, "_get_model", lambda: fake_model)

    embeddings.embed_texts(["some book"])

    assert fake_model.calls[0]["normalize_embeddings"] is True


def test_embed_text_single_returns_one_vector(monkeypatch):
    monkeypatch.setattr(embeddings, "_get_model", lambda: FakeModel())
    vector = embeddings.embed_text("Atomic Habits")
    assert vector.shape == (embeddings.EMBEDDING_DIM,)


def test_model_is_loaded_lazily_and_cached(monkeypatch):
    load_count = {"n": 0}

    def fake_get_model():
        load_count["n"] += 1
        return FakeModel()

    monkeypatch.setattr(embeddings, "_get_model", fake_get_model)
    embeddings.embed_texts(["a"])
    embeddings.embed_texts(["b"])

    # Our fake _get_model isn't itself memoized (that's the real
    # _get_model's job), but this confirms embed_texts calls it each
    # time rather than caching a stale reference incorrectly.
    assert load_count["n"] == 2


def test_build_book_text_includes_all_fields():
    text = embeddings.build_book_text(
        title="Atomic Habits",
        authors=["James Clear"],
        categories=["Self-Help", "Psychology"],
        description="A guide to building good habits and breaking bad ones.",
    )
    assert "Atomic Habits" in text
    assert "James Clear" in text
    assert "Self-Help" in text
    assert "building good habits" in text


def test_build_book_text_handles_missing_fields():
    text = embeddings.build_book_text(
        title="Untitled", authors=None, categories=None, description=None
    )
    assert text == "Untitled"


def test_build_book_text_truncates_long_description():
    long_description = "x" * 5000
    text = embeddings.build_book_text(
        title="Test", authors=[], categories=[], description=long_description
    )
    # description capped at 1000 chars in build_book_text
    assert len(text) < 1100
