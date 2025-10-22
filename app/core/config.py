from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Plannen Fast API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/plannen_fastapi"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "plannen_fastapi"

    # Minio S3
    MINIO_ENDPOINT : str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "vioe-plannen-bestanden"
    MINIO_SECURE: bool = False
    STORAGEPROVIDER_TMP_CONTAINER: str = "temp"

    WEBIDM_URL: str
    OEAUTH_CLIENT_ID: str
    OEAUTH_CLIENT_SECRET : str
    OEAUTH_SYSTEMUSER_SECRET: str
    OEAUTH_SERVER_URL: str
    OEAUTH_REALM_NAME: str
    OEAUTH_PROVIDER: str
    OEAUTH_POST_LOGOUT_REDIRECT_URI: str
    OEAUTH_CACHE_ACTOREN_EXPIRATION_TIME: int = 14400
    OEAUTH_CACHE_ACCESS_TOKEN_EXPIRATION_TIME: int = 240
    OEAUTH_CACHE_REFRESH_TOKEN_EXPIRATION_TIME: int = 9000
    OEAUTH_KEYCLOAK_PUBLIC_KEY : str
    OEAUTH_CONSUMER_KEY : str
    OEAUTH_CONSUMER_SECRET : str
    OEAUTH_OAUTH_HOST : str
    OEAUTH_CALLBACK_URL : str
    OEAUTH_AUTHORIZE_URL : str
    OEAUTH_ALLOW_ROLELESS_USERS: bool = True
    OEAUTH_ROLE_INHERITOR : str
    OEAUTH_MOCK_USER: bool = True
    OEAUTH_MOCK_USER_USERID : str
    OEAUTH_MOCK_USER_GROUPS : str
    OEAUTH_CACHE_BACKEND : str
    OEAUTH_CACHE_ARGUMENTS_HOST : str
    OEAUTH_CACHE_ARGUMENTS_REDIS_EXPIRATION_TIME: int = 15000
    OEAUTH_CACHE_ARGUMENTS_DISTRIBUTED_LOCK: bool = True
    OEAUTH_CACHE_ARGUMENTS_THREAD_LOCAL_LOCK : bool = False
    OEAUTH_CACHE_ARGUMENTS_LOCK_TIMEOUT: int = 30
    OEAUTH_CACHE_EXPIRATION_TIME: int = 3600
    OEAUTH_ACTOR_URL: str
    OEAUTH_GET_ACTOR: bool = True
    OEAUTH_ALLOW_ACTORLESS_USER: bool = False

    # Uri
    PLANNEN_URI: str = "https://dev-id.erfgoed.net/plannen/{id}"

    class Config:
        env_file = ".env"
        case_sensitive = False
        ignore_extra = True
        extra="allow"


# Dependency injection for lightweight services
@lru_cache()
def get_settings() -> Settings:
    return Settings()
