from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import items
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
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
app.include_router(items.router, prefix="/api/v1/items", tags=["items"])


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Plannen Fast API",
        "version": settings.APP_VERSION
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
