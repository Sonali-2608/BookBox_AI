import numpy as np
import pytest

from app.ai import chat_assistant
from app.ai.gemini_client import GeminiError
from app.models.book import Book
from app.models.chat_history import ChatHistory, ChatRole
from app.models.user import User


def unit_vector(dim, seed):
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype("float32")
    return v / np.linalg.norm(v)


@pytest.fixture(autouse=True)
def default_embed_text(monkeypatch):
    """_retrieve_candidates always calls embed_text() regardless of
    whether the index has anything in it, so every test needs this
    mocked — individual tests override it further when the specific
    vector matters."""
    monkeypatch.setattr(chat_assistant, "embed_text", lambda text: unit_vector(384, 0))


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_book(db, **overrides):
    defaults = dict(title="Atomic Habits", authors=["James Clear"], categories=["Self-Help"])
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def test_no_candidates_skips_gemini_entirely(db_session, clean_faiss_index, monkeypatch):
    user = make_user(db_session)
    calls = {"n": 0}
    monkeypatch.setattr(
        chat_assistant, "generate_json", lambda *a, **k: calls.update(n=calls["n"] + 1)
    )

    reply, books = chat_assistant.send_chat_message(db_session, user, "recommend a mystery")

    assert calls["n"] == 0  # never called Gemini — nothing to ground a reply in
    assert books == []
    assert "catalog" in reply.lower() or "search" in reply.lower()


def test_persists_user_and_assistant_messages(db_session, clean_faiss_index, monkeypatch):
    user = make_user(db_session)
    book = make_book(db_session, google_books_id="gb-1")
    clean_faiss_index.add_vectors([book.id], unit_vector(384, 0).reshape(1, -1))
    monkeypatch.setattr(
        chat_assistant, "generate_json", lambda *a, **k: {"reply": "hi", "book_ids": []}
    )

    chat_assistant.send_chat_message(db_session, user, "hello")

    messages = db_session.query(ChatHistory).filter(ChatHistory.user_id == user.id).all()
    assert len(messages) == 2
    assert messages[0].role == ChatRole.user
    assert messages[0].message == "hello"
    assert messages[1].role == ChatRole.assistant
    assert messages[1].message == "hi"


def test_retrieves_and_grounds_on_semantically_close_books(
    db_session, clean_faiss_index, monkeypatch
):
    user = make_user(db_session)
    book = make_book(db_session, google_books_id="gb-1")
    unrelated = make_book(db_session, google_books_id="gb-2", title="Unrelated Book")

    query_vector = unit_vector(384, 1)
    close_vector = query_vector + np.random.default_rng(2).normal(0, 0.01, 384).astype("float32")
    close_vector = close_vector / np.linalg.norm(close_vector)
    far_vector = unit_vector(384, 999)

    clean_faiss_index.add_vectors([book.id, unrelated.id], np.stack([close_vector, far_vector]))
    monkeypatch.setattr(chat_assistant, "embed_text", lambda text: query_vector)

    captured_prompt = {}

    def fake_generate_json(prompt, system_instruction=None):
        captured_prompt["prompt"] = prompt
        return {"reply": "Try this one!", "book_ids": [book.id]}

    monkeypatch.setattr(chat_assistant, "generate_json", fake_generate_json)

    reply, books = chat_assistant.send_chat_message(db_session, user, "habit building books")

    assert reply == "Try this one!"
    assert [b.id for b in books] == [book.id]
    assert "Atomic Habits" in captured_prompt["prompt"]


def test_gemini_failure_falls_back_to_deterministic_reply(
    db_session, clean_faiss_index, monkeypatch
):
    user = make_user(db_session)
    book = make_book(db_session, google_books_id="gb-1")
    vector = unit_vector(384, 1)
    clean_faiss_index.add_vectors([book.id], vector.reshape(1, -1))
    monkeypatch.setattr(chat_assistant, "embed_text", lambda text: vector)

    def raise_error(*a, **k):
        raise GeminiError("down")

    monkeypatch.setattr(chat_assistant, "generate_json", raise_error)

    reply, books = chat_assistant.send_chat_message(db_session, user, "habit books")

    assert reply  # some deterministic, non-empty message
    assert [b.id for b in books] == [book.id]  # falls back to showing the retrieved books


def test_ignores_book_ids_gemini_invents_outside_shortlist(
    db_session, clean_faiss_index, monkeypatch
):
    user = make_user(db_session)
    book = make_book(db_session, google_books_id="gb-1")
    vector = unit_vector(384, 1)
    clean_faiss_index.add_vectors([book.id], vector.reshape(1, -1))
    monkeypatch.setattr(chat_assistant, "embed_text", lambda text: vector)
    monkeypatch.setattr(
        chat_assistant,
        "generate_json",
        lambda *a, **k: {"reply": "here", "book_ids": [book.id, 999999]},
    )

    reply, books = chat_assistant.send_chat_message(db_session, user, "habit books")

    assert [b.id for b in books] == [book.id]  # the invented id 999999 is dropped


def test_get_chat_history_returns_messages_in_order(db_session, clean_faiss_index, monkeypatch):
    user = make_user(db_session)
    book = make_book(db_session, google_books_id="gb-1")
    clean_faiss_index.add_vectors([book.id], unit_vector(384, 0).reshape(1, -1))
    monkeypatch.setattr(
        chat_assistant, "generate_json", lambda *a, **k: {"reply": "a1", "book_ids": []}
    )
    chat_assistant.send_chat_message(db_session, user, "q1")
    chat_assistant.send_chat_message(db_session, user, "q2")

    history = chat_assistant.get_chat_history(db_session, user)

    assert [m.message for m in history] == ["q1", "a1", "q2", "a1"]
