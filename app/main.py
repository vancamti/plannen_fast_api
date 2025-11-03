from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import plannen
from app.constants import settings
from app.core.dependencies import DBSessionMiddleware
from app.core.dependencies import lifespan
from app.exceptions import register_exception_handlers
from app.models.listeners import receive_after_flush  # noqa: F401
from app.models.listeners import receive_after_flush_delete  # noqa: F401
from app.openapi.schema import apply_custom_openapi

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)
register_exception_handlers(app)
apply_custom_openapi(
    app, title="Plannen API", version="1.0.0", description="Plannen API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(plannen.router, prefix="/api/v1/plannen", tags=["plannen"])
app.add_middleware(DBSessionMiddleware)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to Plannen Fast API", "version": settings.APP_VERSION}


# Health check endpoint kan in gemeenschappelijk lib komen voor alle services
# Routers kunnen gewoon toegevoegd worden in main.py van elke service
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/version")
def version():
    """Health check endpoint."""
    return {
        "app_name": "healthy",
        "latest_commit": settings.LATEST_COMMIT,
    }
