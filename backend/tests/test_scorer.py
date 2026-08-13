import numpy as np

from app.models.book import Book
from app.models.preference import UserPreference
from app.models.user import User
from app.models.wishlist import Wishlist
from app.recommendation import scorer


def make_user(db, google_id="g-1", email="reader@example.com"):
    user = User(google_id=google_id, name="Ada Reader", email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_book(db, **overrides):
    defaults = dict(
        title="Book",
        authors=["Author"],
        categories=["Fiction"],
        rating=4.0,
        embedding_generated=0,
    )
    defaults.update(overrides)
    book = Book(**defaults)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def unit_vector(dim, seed):
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype("float32")
    return v / np.linalg.norm(v)


def test_cold_start_returns_empty_with_no_signal(db_session, clean_faiss_index):
    user = make_user(db_session)
    result = scorer.get_recommendations(db_session, user)
    assert result == []


def test_genre_preference_alone_produces_recommendations(db_session, clean_faiss_index):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=["Fantasy"], favorite_authors=[])
    )
    db_session.commit()

    matching_book = make_book(db_session, google_books_id="gb-1", categories=["Fantasy"])
    non_matching = make_book(db_session, google_books_id="gb-2", categories=["Biography"])

    results = scorer.get_recommendations(db_session, user)
    result_ids = [b.id for b, _, _ in results]

    assert matching_book.id in result_ids
    assert non_matching.id not in result_ids


def test_author_preference_alone_produces_recommendations(db_session, clean_faiss_index):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=[], favorite_authors=["James Clear"])
    )
    db_session.commit()

    matching_book = make_book(db_session, google_books_id="gb-1", authors=["James Clear"])
    non_matching = make_book(db_session, google_books_id="gb-2", authors=["Someone Else"])

    results = scorer.get_recommendations(db_session, user)
    result_ids = [b.id for b, _, _ in results]

    assert matching_book.id in result_ids
    assert non_matching.id not in result_ids


def test_wishlist_builds_taste_vector_and_excludes_wishlisted_books(
    db_session, clean_faiss_index
):
    user = make_user(db_session)
    wishlisted = make_book(db_session, google_books_id="gb-1")
    other = make_book(db_session, google_books_id="gb-2")

    v_wishlisted = unit_vector(384, 1)
    v_other_close = v_wishlisted + np.random.default_rng(5).normal(0, 0.01, 384).astype("float32")
    v_other_close = v_other_close / np.linalg.norm(v_other_close)
    v_unrelated = unit_vector(384, 999)

    third = make_book(db_session, google_books_id="gb-3")

    clean_faiss_index.add_vectors(
        [wishlisted.id, other.id, third.id],
        np.stack([v_wishlisted, v_other_close, v_unrelated]),
    )

    db_session.add(Wishlist(user_id=user.id, book_id=wishlisted.id))
    db_session.commit()

    results = scorer.get_recommendations(db_session, user)
    result_ids = [b.id for b, _, _ in results]

    # The wishlisted book itself should never be recommended back.
    assert wishlisted.id not in result_ids
    # The semantically-close book should rank above the unrelated one.
    assert result_ids.index(other.id) < result_ids.index(third.id)


def test_scoring_combines_genre_and_author_and_rating(db_session, clean_faiss_index):
    user = make_user(db_session)
    db_session.add(
        UserPreference(
            user_id=user.id, favorite_genres=["Fantasy"], favorite_authors=["Brandon Sanderson"]
        )
    )
    db_session.commit()

    both_match = make_book(
        db_session,
        google_books_id="gb-1",
        categories=["Fantasy"],
        authors=["Brandon Sanderson"],
        rating=5.0,
    )
    genre_only = make_book(
        db_session, google_books_id="gb-2", categories=["Fantasy"], authors=["Nobody"], rating=3.0
    )

    results = scorer.get_recommendations(db_session, user)
    result_ids = [b.id for b, _, _ in results]
    scores = {b.id: score for b, score, _ in results}

    assert result_ids.index(both_match.id) < result_ids.index(genre_only.id)
    assert scores[both_match.id] > scores[genre_only.id]


def test_reason_text_reflects_matched_signals(db_session, clean_faiss_index):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=["Fantasy"], favorite_authors=[])
    )
    db_session.commit()

    book = make_book(db_session, google_books_id="gb-1", categories=["Fantasy"])

    results = scorer.get_recommendations(db_session, user)
    _, _, reason = results[0]

    assert "genre" in reason.lower()


def test_results_respect_limit(db_session, clean_faiss_index):
    user = make_user(db_session)
    db_session.add(
        UserPreference(user_id=user.id, favorite_genres=["Fantasy"], favorite_authors=[])
    )
    db_session.commit()

    for i in range(5):
        make_book(db_session, google_books_id=f"gb-{i}", categories=["Fantasy"])

    results = scorer.get_recommendations(db_session, user, limit=2)
    assert len(results) == 2
