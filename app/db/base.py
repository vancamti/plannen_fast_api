from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.core.dependencies import get_content_manager
from app.storage.conent_manager import ContentManager

settings = get_settings()

# Create database engine
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DEBUG)
# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Create base class for models
Base = declarative_base()


def get_db(content_manager: ContentManager = Depends(get_content_manager)):
    """Dependency to get database session."""
    db = SessionLocal()
    db.info['content_manager'] = content_manager
    try:
        yield db
    finally:
        db.close()

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