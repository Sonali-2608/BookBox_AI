# Lexora

*Your AI-powered literary companion.*

> This README is a placeholder for active development. A full, polished
> README (architecture, setup, API docs, screenshots) will be written in
> Phase 11 once the whole app is built.

## Current status

- ✅ Phase 1 — Project inspected, structure agreed
- ✅ Phase 2 — Backend scaffold: FastAPI, PostgreSQL, SQLAlchemy models, config, JWT/auth foundation
- ⬜ Phase 3 — Google OAuth + JWT auth flow
- ⬜ Phase 4 — React frontend + design system
- ⬜ Phase 5 — Book search (Google Books / Open Library)
- ⬜ Phase 6 — Recommendation engine (embeddings + FAISS)
- ⬜ Phase 7 — Gemini AI reading assistant
- ⬜ Phase 8 — Bookshelf OCR scanner
- ⬜ Phase 9 — Wishlist, reading tracker, analytics
- ⬜ Phase 10 — Testing, error handling, performance, security review
- ⬜ Phase 11 — Docker, deployment config, final README

## Running the backend locally (Phase 2)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp ../.env.example ../.env   # then fill in real values
# You need a running PostgreSQL instance and DATABASE_URL set for real use.
# The test suite below uses an isolated SQLite DB and needs no setup.

# Apply the initial migration (requires PostgreSQL to be running):
alembic upgrade head

# Run the API:
uvicorn app.main:app --reload
# -> http://localhost:8000/docs
```

## Running backend tests

```bash
cd backend
pytest -v
```

No live PostgreSQL connection is required to run tests — they use an
isolated, throwaway SQLite database automatically.
