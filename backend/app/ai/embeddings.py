"""
Sentence-Transformers embedding generation.

The model is loaded lazily (on first call, via _get_model) rather than
at import time: it's a real download + memory cost, and most requests
(plain keyword search, auth, etc.) never need it — only the
recommendation/similarity code paths do.
"""

from typing import Optional

import numpy as np

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # fixed by the model above; change together if the model changes

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def build_book_text(
    title: str,
    authors: Optional[list[str]],
    categories: Optional[list[str]],
    description: Optional[str],
) -> str:
    """Combines a book's metadata into one string for embedding. Order
    matters a little (title first) but this doesn't need to be prose —
    the model just needs the meaningful terms present."""
    parts = [title]
    if authors:
        parts.append("by " + ", ".join(authors))
    if categories:
        parts.append("Genres: " + ", ".join(categories))
    if description:
        # Cap length so one very long description doesn't dominate the
        # embedding relative to title/genre/author signal.
        parts.append(description[:1000])
    return ". ".join(parts)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (n, EMBEDDING_DIM) float32 array of L2-normalized
    embeddings, so inner product == cosine similarity in the FAISS
    index (see app/recommendation/faiss_index.py)."""
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype="float32")

    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return np.asarray(vectors, dtype="float32")


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])[0]
