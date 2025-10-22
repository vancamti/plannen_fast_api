from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import HTTPException
from oeauth.openid import OpenIDHelper
from storageprovider.client import StorageProviderClient
from storageprovider.providers.minio import MinioProvider

from app.constants import settings
from app.storage.conent_manager import ContentManager

# Global instances (initialized on startup)
_storage_provider: StorageProviderClient | None = None
_content_manager: ContentManager | None = None
_token_provider: OpenIDHelper | None = None


# Dependency injection via FastAPI's lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown."""
    global _storage_provider, _content_manager, _token_provider

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

    yield  # Application runs here

    # Cleanup on shutdown (if needed)
    # if hasattr(_token_provider, 'close'):
    #     await _token_provider.close()
    # if hasattr(_storage_provider, 'close'):
    #     await _storage_provider.close()

    _storage_provider = None
    _content_manager = None
    _token_provider = None


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
