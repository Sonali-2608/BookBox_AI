import numpy as np
import pytest


@pytest.fixture()
def idx(clean_faiss_index):
    return clean_faiss_index


def unit_vector(dim, seed):
    rng = np.random.default_rng(seed)
    v = rng.random(dim).astype("float32")
    return v / np.linalg.norm(v)


def test_empty_index_search_returns_empty(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    result = idx.search(unit_vector(EMBEDDING_DIM, 1), k=5)
    assert result == []


def test_add_and_search_finds_closest_match(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    base = unit_vector(EMBEDDING_DIM, 1)
    # A vector very close to `base`, and one far away.
    close = base + np.random.default_rng(2).normal(0, 0.01, EMBEDDING_DIM).astype("float32")
    close = close / np.linalg.norm(close)
    far = unit_vector(EMBEDDING_DIM, 999)

    idx.add_vectors([1, 2], np.stack([close, far]))

    results = idx.search(base, k=2)
    result_ids = [r[0] for r in results]

    assert result_ids[0] == 1  # closest match ranked first
    assert set(result_ids) == {1, 2}


def test_search_excludes_ids(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    v1 = unit_vector(EMBEDDING_DIM, 1)
    v2 = unit_vector(EMBEDDING_DIM, 2)
    idx.add_vectors([1, 2], np.stack([v1, v2]))

    results = idx.search(v1, k=5, exclude_ids={1})
    result_ids = [r[0] for r in results]

    assert 1 not in result_ids
    assert 2 in result_ids


def test_search_respects_k(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    vectors = np.stack([unit_vector(EMBEDDING_DIM, i) for i in range(10)])
    idx.add_vectors(list(range(10)), vectors)

    results = idx.search(unit_vector(EMBEDDING_DIM, 0), k=3)
    assert len(results) == 3


def test_reconstruct_returns_added_vector(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    v = unit_vector(EMBEDDING_DIM, 5)
    idx.add_vectors([42], v.reshape(1, -1))

    reconstructed = idx.reconstruct(42)
    assert reconstructed is not None
    np.testing.assert_allclose(reconstructed, v, atol=1e-5)


def test_reconstruct_missing_id_returns_none(idx):
    result = idx.reconstruct(999)
    assert result is None


def test_add_vectors_with_empty_list_is_noop(idx):
    idx.add_vectors([], np.empty((0, 384), dtype="float32"))
    assert idx.get_index().ntotal == 0


def test_re_adding_same_id_replaces_not_duplicates(idx):
    from app.ai.embeddings import EMBEDDING_DIM

    v1 = unit_vector(EMBEDDING_DIM, 1)
    v2 = unit_vector(EMBEDDING_DIM, 2)

    idx.add_vectors([1], v1.reshape(1, -1))
    idx.add_vectors([1], v2.reshape(1, -1))  # re-embed same book id

    assert idx.get_index().ntotal == 1
    reconstructed = idx.reconstruct(1)
    np.testing.assert_allclose(reconstructed, v2, atol=1e-5)


def test_index_persists_across_get_index_calls(idx, tmp_path):
    from app.ai.embeddings import EMBEDDING_DIM

    v = unit_vector(EMBEDDING_DIM, 1)
    idx.add_vectors([7], v.reshape(1, -1))

    # Simulate a fresh process by clearing the in-memory singleton and
    # reloading from the saved file.
    idx._index = None
    reloaded = idx.get_index()

    assert reloaded.ntotal == 1
