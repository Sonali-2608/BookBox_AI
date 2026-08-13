import numpy as np

from app.models.book import Book
from app.recommendation import embedding_pipeline


def make_book(db, **overrides):
    defaults = dict(
        title="Atomic Habits",
        authors=["James Clear"],
        categories=["Self-Help"],
        description="A guide to good habits.",
        embedding_generated=0,
    )
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def fake_embed_texts(texts):
    rng = np.random.default_rng(0)
    return rng.random((len(texts), 384)).astype("float32")


def test_ensure_books_embedded_marks_flag_and_adds_to_index(
    db_session, clean_faiss_index, monkeypatch
):
    monkeypatch.setattr(embedding_pipeline, "embed_texts", fake_embed_texts)
    book = make_book(db_session)

    embedding_pipeline.ensure_books_embedded(db_session, [book])

    db_session.refresh(book)
    assert book.embedding_generated == 1
    assert clean_faiss_index.reconstruct(book.id) is not None


def test_ensure_books_embedded_skips_already_embedded(db_session, clean_faiss_index, monkeypatch):
    calls = {"n": 0}

    def counting_embed(texts):
        calls["n"] += 1
        return fake_embed_texts(texts)

    monkeypatch.setattr(embedding_pipeline, "embed_texts", counting_embed)

    already_embedded = make_book(db_session, embedding_generated=1, google_books_id="gb-1")
    embedding_pipeline.ensure_books_embedded(db_session, [already_embedded])

    assert calls["n"] == 0  # never called embed_texts for an already-embedded book


def test_ensure_books_embedded_batches_multiple_pending_books(
    db_session, clean_faiss_index, monkeypatch
):
    calls = {"batches": []}

    def counting_embed(texts):
        calls["batches"].append(len(texts))
        return fake_embed_texts(texts)

    monkeypatch.setattr(embedding_pipeline, "embed_texts", counting_embed)

    b1 = make_book(db_session, google_books_id="gb-1", title="Book One")
    b2 = make_book(db_session, google_books_id="gb-2", title="Book Two")

    embedding_pipeline.ensure_books_embedded(db_session, [b1, b2])

    assert calls["batches"] == [2]  # one batched call, not two separate ones
    db_session.refresh(b1)
    db_session.refresh(b2)
    assert b1.embedding_generated == 1
    assert b2.embedding_generated == 1


def test_ensure_books_embedded_noop_for_empty_list(db_session, clean_faiss_index, monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(
        embedding_pipeline, "embed_texts", lambda texts: calls.update(n=calls["n"] + 1) or fake_embed_texts(texts)
    )
    embedding_pipeline.ensure_books_embedded(db_session, [])
    assert calls["n"] == 0


def test_ensure_book_embedded_single_book_helper(db_session, clean_faiss_index, monkeypatch):
    monkeypatch.setattr(embedding_pipeline, "embed_texts", fake_embed_texts)
    book = make_book(db_session, google_books_id="gb-solo")

    embedding_pipeline.ensure_book_embedded(db_session, book)

    db_session.refresh(book)
    assert book.embedding_generated == 1
