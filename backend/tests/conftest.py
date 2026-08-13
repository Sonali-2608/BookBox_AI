import os

# Force a throwaway SQLite DB for the entire test session, before any
# app module (which reads settings at import time) gets imported.
os.environ["DATABASE_URL"] = "sqlite:///./test_lexora.db"
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_lexora.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_lexora.db"):
        os.remove("./test_lexora.db")


@pytest.fixture()
def db_session():
    """Each test runs inside its own connection + transaction, rolled
    back at teardown, so tests never see leftover rows from a previous
    test. The FastAPI app's get_db is overridden to use this SAME
    connection for the duration of the test (see the `client` fixture),
    so API calls and direct DB assertions in a test see consistent data."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """A TestClient bound to the same per-test transaction as db_session,
    so nothing written via HTTP calls leaks into the next test."""
    return TestClient(app)


@pytest.fixture()
def clean_faiss_index(tmp_path, monkeypatch):
    """Points the FAISS index at a fresh temp file and resets the
    in-memory singleton, so each test gets an empty index instead of
    sharing (or polluting) the real app's index_store/books.faiss."""
    from app.recommendation import faiss_index

    monkeypatch.setattr(faiss_index, "INDEX_PATH", str(tmp_path / "test.faiss"))
    monkeypatch.setattr(faiss_index, "_index", None)
    yield faiss_index
    monkeypatch.setattr(faiss_index, "_index", None)
