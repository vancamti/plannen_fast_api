import sys
from collections.abc import Generator
from pathlib import Path

import anyio
import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_db
from app.main import app
from app.models import Base

sys.path.append(str(Path(__file__).resolve().parents[1]))


def pytest_configure(config: pytest.Config) -> None:
    if not getattr(config.option, "anyio_backend", None):
        config.option.anyio_backend = ["asyncio"]


class SyncASGITransport(httpx.BaseTransport):
    def __init__(self, app):
        self._transport = httpx.ASGITransport(app=app)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        async def send_request() -> httpx.Response:
            response = await self._transport.handle_async_request(request)
            try:
                content = await response.aread()
            finally:
                await response.aclose()

            return httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=content,
                extensions=response.extensions,
                request=request,
            )

        return anyio.run(send_request)

    def close(self) -> None:
        anyio.run(self._transport.aclose)


@pytest.fixture()
def db_engine() -> Generator:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def test_client(db_session: Session) -> Generator[httpx.Client, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    transport = SyncASGITransport(app=app)
    client = httpx.Client(transport=transport, base_url="http://testserver")
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
