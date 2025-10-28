from contextlib import asynccontextmanager
from typing import Callable
from typing import Optional
from typing import Type
from typing import TypeVar

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from oe_utils.search.searchengine import SearchEngine
from oeauth.openid import OpenIDHelper
from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from storageprovider.client import StorageProviderClient
from storageprovider.providers.minio import MinioProvider

from app.constants import settings
from app.core.config import get_settings
from app.models import Plan
from app.models import PlanBestand
from app.models import PlanStatus
from app.search.index import setup_indexer
from app.search.indexer import Indexer
from app.storage.conent_manager import ContentManager

# Create database engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DEBUG)
# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global instances (initialized on startup)
_storage_provider: StorageProviderClient | None = None
_content_manager: ContentManager | None = None
_token_provider: OpenIDHelper | None = None
_indexer: Indexer | None = None
_redis: Redis | None = None
_search_engine: SearchEngine | None = None

def _redis_from_settings() -> Redis:
    """
    Prefer a full REDIS_URL; fall back to host/port/db if that’s how your settings are structured.
    """
    return Redis.from_url(
        settings.REDIS_SESSIONS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.db = SessionLocal()

        try:
            response = await call_next(request)
            # Only commit if response is successful (2xx)
            if 200 <= response.status_code < 300:
                request.state.db.commit()
            else:
                request.state.db.rollback()
            return response

        except Exception:
            request.state.db.rollback()
            raise
        finally:
            request.state.db.close()


# Dependency injection via FastAPI's lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    global _storage_provider, _content_manager, _token_provider, _indexer, _redis, _search_engine

    # Initialize Redis (shared pool-managed client)
    _redis = _redis_from_settings()

    # Initialize token provider
    _token_provider = OpenIDHelper(
        client_id=settings.OEAUTH_CLIENT_ID,
        client_secret=settings.OEAUTH_CLIENT_SECRET,
        systemuser_secret=settings.OEAUTH_SYSTEMUSER_SECRET,
        keycloak_public_key=settings.OEAUTH_KEYCLOAK_PUBLIC_KEY,
        **{
            "cache.backend": settings.OEAUTH_CACHE_BACKEND,
            "cache.arguments.host": settings.OEAUTH_CACHE_ARGUMENTS_HOST,
            "cache.arguments.redis.expiration.time": settings.OEAUTH_CACHE_ARGUMENTS_REDIS_EXPIRATION_TIME,
            "cache.arguments.distributed_lock": settings.OEAUTH_CACHE_ARGUMENTS_DISTRIBUTED_LOCK,
            "cache.arguments.thread.local.lock": settings.OEAUTH_CACHE_ARGUMENTS_THREAD_LOCAL_LOCK,
            "cache.arguments.lock.timeout": settings.OEAUTH_CACHE_ARGUMENTS_LOCK_TIMEOUT,
            "cache.expiration.time": settings.OEAUTH_CACHE_EXPIRATION_TIME,
        }
    )

    # Initialize storage provider
    provider = MinioProvider(
        server_url=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        bucket_name=settings.MINIO_BUCKET_NAME,
    )
    _storage_provider = StorageProviderClient(provider)

    # Initialize content manager
    _content_manager = ContentManager(
        temp_container=settings.STORAGEPROVIDER_TMP_CONTAINER,
        storage_provider=_storage_provider,
        system_token=_token_provider.get_system_token,
    )

    # Initialize search indexer for use in request lifecycle
    _indexer = setup_indexer(app, settings)

    # Initialize search engine
    _search_engine = SearchEngine(
            settings.ELASTICSEARCH_URL,
            settings.ELASTICSEARCH_INDEX,
            es_version="8",
            api_key=settings.ELASTICSEARCH_API_KEY,
        )

    yield  # Application runs here

    # Cleanup on shutdown (if needed)
    # if hasattr(_token_provider, 'close'):
    #     await _token_provider.close()
    # if hasattr(_storage_provider, 'close'):
    #     await _storage_provider.close()

    _storage_provider = None
    _content_manager = None
    _token_provider = None
    _indexer = None
    _redis = None


# Dependency functions
def get_storage_provider() -> StorageProviderClient:
    if _storage_provider is None:
        raise HTTPException(status_code=503, detail="Storage provider not initialized")
    return _storage_provider


def get_content_manager() -> ContentManager:
    if _content_manager is None:
        raise HTTPException(status_code=503, detail="Content manager not initialized")
    return _content_manager


def get_token_provider() -> OpenIDHelper:
    if _token_provider is None:
        raise HTTPException(status_code=503, detail="Token provider not initialized")
    return _token_provider


def get_redis() -> Redis:
    if _redis is None:
        raise HTTPException(status_code=503, detail="Redis not initialized")
    return _redis


def get_indexer() -> Indexer:
    if _indexer is None:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    return _indexer

def get_searchengine() -> SearchEngine:
    if _search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    return _search_engine

T = TypeVar("T")


def get_db(
        content_manager: "ContentManager" = Depends(get_content_manager),
        redis: Redis = Depends(get_redis),
        indexer: Indexer = Depends(get_indexer)
):
    """Dependency to get database session."""
    db_session = SessionLocal()
    db_session.info['content_manager'] = content_manager
    indexer.register_session(db_session, redis)

    try:
        yield db_session
    finally:
        db_session.close()


def get_object_or_404(
        model: Type[T],
        id_field: str = "id",
        error_message: Optional[str] = None
) -> Callable[[int, Session], T]:
    """
    Generic dependency to get an object by ID or raise 404 if not found.
    :param model:
    :param id_field:
    :param error_message:
    :return:
    """

    def dependency(
            object_id: int,
            db: Session = Depends(get_db)
    ) -> T:
        query = db.query(model).filter(
            getattr(model, id_field) == object_id
        )
        obj = query.first()

        if obj is None:
            msg = error_message or f"{model.__name__} with id {object_id} not found"
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=msg
            )

        return obj

    return dependency


get_plan_or_404 = get_object_or_404(model=Plan)
get_bestand_or_404 = get_object_or_404(model=PlanBestand)
get_status_or_404 = get_object_or_404(model=PlanStatus)
