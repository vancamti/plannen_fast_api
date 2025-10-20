import copy

from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pyramid.settings import aslist

from app import constants
from app.api.v1 import plan
from app.core.config import settings
from app.db.base import DBSessionMiddleware
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.exceptions import register_exception_handlers
from app.openapi.schema import apply_custom_openapi


def parse_settings(settings):
    settings.dict()
    settings = copy.deepcopy(settings)
    constants.SETTINGS.clear()
    integer_settings = []
    for setting in integer_settings:
        if setting in settings:
            settings[setting] = int(settings[setting])
    list_settings = []
    for setting in list_settings:
        if setting in settings and isinstance(settings[setting], str):
            settings[setting] = aslist(settings[setting])
    boolean_settings = []
    for setting in boolean_settings:
        if setting in settings:
            if isinstance(settings[setting], str):
                settings[setting] = settings[setting].lower() in ("1", "true")

    constants.SETTINGS.update(settings)


app = FastAPI(
    title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG
)
register_exception_handlers(app)
parse_settings(settings)
register_exception_handlers(app)
apply_custom_openapi(
    app,
    title="Plannen API",
    version="1.0.0",
    description="Plannen API"
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


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
