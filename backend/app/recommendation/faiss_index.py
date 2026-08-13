"""
Manages the FAISS vector index of book embeddings, persisted to disk so
it survives process restarts without recomputing every embedding.

Uses IndexIDMap2 over IndexFlatIP so vectors can be addressed by our own
Book.id directly (no separate id-mapping table needed), and inner
product on L2-normalized vectors (see app/ai/embeddings.py) gives
cosine similarity. IndexIDMap2 (not plain IndexIDMap) is required here —
only IndexIDMap2 maintains an explicit id->vector map, which is what
makes reconstruct(book_id) work; IndexIDMap alone doesn't support
reconstruction by external id (confirmed by testing, not assumed).

INDEX_PATH and the in-memory `_index` singleton are module-level so
tests can monkeypatch both to get a clean, isolated index per test
without touching the real on-disk index in index_store/.
"""

import os
import threading
from typing import Optional

import faiss
import numpy as np

from app.ai.embeddings import EMBEDDING_DIM

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index_store")
INDEX_PATH = os.path.join(INDEX_DIR, "books.faiss")

_index: Optional["faiss.IndexIDMap2"] = None
_lock = threading.RLock()


def _new_index():
    base = faiss.IndexFlatIP(EMBEDDING_DIM)
    # IndexIDMap2 (not IndexIDMap) — it maintains an explicit id->vector
    # map, which is what makes reconstruct(book_id) work. Plain IndexIDMap
    # doesn't support reconstruction by external id.
    return faiss.IndexIDMap2(base)


def get_index():
    global _index
    if _index is None:
        with _lock:
            if _index is None:
                if os.path.exists(INDEX_PATH):
                    _index = faiss.read_index(INDEX_PATH)
                else:
                    _index = _new_index()
    return _index


def save_index() -> None:
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    faiss.write_index(get_index(), INDEX_PATH)


def add_vectors(ids: list[int], vectors: np.ndarray) -> None:
    """Adds (or re-adds) vectors under the given book ids. Existing
    entries for these ids are removed first so re-embedding a book
    (e.g. after its metadata changes) can't create duplicates."""
    if not ids:
        return
    with _lock:
        index = get_index()
        id_array = np.asarray(ids, dtype="int64")
        if index.ntotal > 0:
            index.remove_ids(id_array)
        index.add_with_ids(np.ascontiguousarray(vectors, dtype="float32"), id_array)
    save_index()


def search(
    vector: np.ndarray, k: int, exclude_ids: Optional[set[int]] = None
) -> list[tuple[int, float]]:
    """Top-k nearest neighbors as (book_id, cosine_similarity), highest
    first, excluding any ids in exclude_ids (e.g. the query book itself,
    or books the user already has)."""
    index = get_index()
    if index.ntotal == 0:
        return []

    exclude_ids = exclude_ids or set()
    fetch_k = min(index.ntotal, k + len(exclude_ids) + 5)
    query = np.ascontiguousarray(vector, dtype="float32").reshape(1, -1)
    scores, ids = index.search(query, fetch_k)

    results = []
    for book_id, score in zip(ids[0], scores[0]):
        if book_id == -1 or int(book_id) in exclude_ids:
            continue
        results.append((int(book_id), float(score)))
        if len(results) >= k:
            break
    return results


def reconstruct(book_id: int) -> Optional[np.ndarray]:
    """Retrieves a previously-added vector back out of the index — used
    e.g. to build a user's taste profile from their wishlisted books'
    embeddings. Returns None if the id isn't in the index."""
    index = get_index()
    try:
        return index.reconstruct(int(book_id))
    except RuntimeError:
        return None
