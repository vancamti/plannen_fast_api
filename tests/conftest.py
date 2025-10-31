import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from redis import Redis

from app.main import app
from app.core.dependencies import (
    get_db,
    get_redis,
    get_storage_provider,
    get_content_manager,
    get_token_provider,
    get_indexer,
    get_searchengine,
)
from app.models import Base  # assuming you have Base in models
from storageprovider.client import StorageProviderClient
from app.storage.conent_manager import ContentManager
from oeauth.openid import OpenIDHelper
from app.search.indexer import Indexer
from oe_utils.search.searchengine import SearchEngine

# -------------------------------------------------------------------------
# Load environment and setup test DB
# -------------------------------------------------------------------------
load_dotenv(Path(__file__).parent / "test.env", override=True)
TEST_DB_URL = os.environ["DATABASE_URL"]

# Use a separate engine for tests
engine = create_engine(TEST_DB_URL, future=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# -------------------------------------------------------------------------
# Run migrations once per session (or create tables if no Alembic)
# -------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# -------------------------------------------------------------------------
# DB transaction fixture (rollback per test)
# -------------------------------------------------------------------------
@pytest.fixture
def db_session():
    connection = engine.connect()
    trans = connection.begin()

    session = TestingSessionLocal(bind=connection)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        nested.rollback()
        trans.rollback()
        connection.close()


# -------------------------------------------------------------------------
# Mock external dependencies
# -------------------------------------------------------------------------
@pytest.fixture
def fake_redis():
    """Provide a fake or in-memory Redis."""
    # You could use fakeredis here if desired.
    redis = Redis.from_url("redis://localhost:6379/15", decode_responses=True)
    redis.flushdb()
    return redis


@pytest.fixture
def fake_storage_provider():
    return MagicMock()


@pytest.fixture
def fake_content_manager(fake_storage_provider):
    return MagicMock()


@pytest.fixture
def fake_token_provider():
    return MagicMock()


@pytest.fixture
def fake_indexer():
    return MagicMock()


@pytest.fixture
def fake_search_engine():
    return MagicMock()


# -------------------------------------------------------------------------
# Override FastAPI dependencies with test doubles
# -------------------------------------------------------------------------
@pytest.fixture
def test_app(
    db_session,
    fake_redis,
    fake_storage_provider,
    fake_content_manager,
    fake_token_provider,
    fake_indexer,
    fake_search_engine,
):
    """FastAPI app with dependencies overridden for testing."""

    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_storage_provider] = lambda: fake_storage_provider
    app.dependency_overrides[get_content_manager] = lambda: fake_content_manager
    app.dependency_overrides[get_token_provider] = lambda: fake_token_provider
    app.dependency_overrides[get_indexer] = lambda: fake_indexer
    app.dependency_overrides[get_searchengine] = lambda: fake_search_engine

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
