# FastAPI Setup Snapshot ✅

The Plannen FastAPI application is wired up and running with the same modules that back the plannen domain: SQLAlchemy models for plannen, MinIO-backed storage for bestanden, OE-auth/Redis plumbing, and Elasticsearch integration via `oe_utils`. This document captures the state of the codebase after the bootstrap scripts have been executed.

## Stack At A Glance

- **FastAPI 0.120.1** with **Uvicorn 0.24.0** (ASGI server) and permissive CORS middleware.
- **Pydantic 2.5 / pydantic-settings 2.1** for request/response validation and configuration loading.
- **SQLAlchemy 2.0**, **GeoAlchemy2**, and **Alembic 1.12** targeting PostgreSQL/PostGIS.
- **Elasticsearch 8.11** accessed through `oe_utils.search.SearchEngine`, plus domain query builders.
- **Redis** + `rq` for background indexing queues and session-bound Redis hooks.
- **storageprovider-client 3.0.1** (MinIO provider) with a custom `ContentManager`.
- Domain utilities: `oeauth`, `oe-utils`, `oe-geoutils`, `skosprovider`, `skosprovider_atramhasis`, `storageprovider-client`.

## Project Layout

```
plannen_fast_api/
├── app/
│   ├── api/v1/plannen.py            # REST endpoints for plannen, bestanden, statussen
│   ├── core/config.py               # Pydantic settings
│   ├── core/dependencies.py         # Lifespan wiring, DB sessions, Redis, search, storage
│   ├── exceptions/handlers.py       # 422→400 validation response mapping
│   ├── main.py                      # FastAPI app, routers, middleware, OpenAPI patching
│   ├── mappers/plannen.py           # SQLAlchemy ↔ Pydantic conversion helpers
│   ├── models/                      # SQLAlchemy models, enums, session listeners
│   ├── schemas/plannen.py           # Pydantic DTOs and validators
│   ├── search/                      # ES mapping, query builders, indexer integration
│   ├── storage/conent_manager.py    # MinIO-backed storage abstraction
│   └── scripts/                     # ES indexing and storage sync utilities
├── alembic/                         # Migration environment and versions
├── requirements.txt                 # Runtime dependencies (FastAPI-focused)
├── pyproject.toml                   # Legacy Pyramid metadata (kept for reference)
├── setup.sh                         # Bootstrap virtualenv, install deps, create .env
├── setup_db.sh                      # Ensure PostGIS DB exists, then run Alembic migrations
├── run.sh                           # Convenience wrapper around `uvicorn app.main:app`
├── verify_setup.py                  # Sanity checks for imports + minimal structure
├── development.ini                  # Original Pyramid configuration (reference only)
├── tests/conftest.py                # HTTPX test client + in-memory SQLite fixtures
├── .env.example                     # Required environment variables
└── SETUP_COMPLETE.md                # This document
```

## API Surface

- Core routes: `GET /` (welcome message), `GET /health`, `GET /version`, plus FastAPI docs at `/docs` and `/redoc`.
- Plannen collection: `POST /api/v1/plannen/`, `GET /api/v1/plannen/` (delegates to Elasticsearch via `PlannenQueryBuilder`, filters, and aggregations), `GET /api/v1/plannen/{plan_id}`, `PUT /api/v1/plannen/{object_id}`, `DELETE /api/v1/plannen/{plan_id}`.
- Bestanden workflow:
  - `POST /api/v1/plannen/temp/bestanden` uploads to temporary MinIO storage.
  - `POST /api/v1/plannen/{plan_id}/bestanden` validates payload (including MinIO metadata) then persists via SQLAlchemy + storage listeners.
  - `GET /api/v1/plannen/{plan_id}/bestanden/{object_id}` streams individual files.
  - `GET /api/v1/plannen/{object_id}/bestanden` responds with JSON or ZIP aggregates depending on the `Accept` header.
  - `PUT`/`DELETE` counterparts keep bestanden in sync.
- Status endpoints: `GET /api/v1/plannen/{object_id}/statussen` and `GET /api/v1/plannen/{plan_id}/statussen/{object_id}` expose status history (enum-backed) with hooks for future create/update operations.

## Domain & Infrastructure Highlights

- SQLAlchemy models (`app/models/plan.py`) cover plannen, relaties, statussen, bestanden, locatie-elementen, and geometry handling via `geoalchemy2`.
- Session middleware (`DBSessionMiddleware`) couples request lifecycle to SQLAlchemy sessions, while `app/models/listeners.py` mirrors bestand changes to MinIO using the shared `ContentManager`.
- `app/core/dependencies.py` centralises lifespan bootstrapping: Redis connections, `OpenIDHelper`, `StorageProviderClient`, Elasticsearch `SearchEngine`, and the custom indexing pipeline.
- Elasticsearch indexing is orchestrated through `app/search/indexer.py`, with mapping definitions in `app/search/mapping/plannen.py` and CLI support in `app/scripts/index_es.py`.
- SKOS vocabularies are preloaded in `app/skos/__init__.py` to resolve plantypes and aanduidingsobjecttypes.
- Custom OpenAPI schema adjustments (`app/openapi/schema.py`) replace 422 validation responses with documented 400 responses, while `app/exceptions/handlers.py` formats validation errors.
- `tests/conftest.py` provides HTTPX-based integration tests using an in-memory SQLite database and dependency overrides.

## Setup & Usage

1. `./setup.sh` – creates a `venv`, installs `requirements.txt`, and seeds `.env` from `.env.example` if needed.
2. Edit `.env` to supply connection details for PostgreSQL/PostGIS, Redis, Elasticsearch, MinIO, and OE-auth credentials.
3. Start infrastructure services (PostgreSQL/PostGIS, Redis, Elasticsearch 8, MinIO) using your preferred tooling; the repository does not ship a docker-compose file.
4. Optionally run `./setup_db.sh` once your PostGIS container (defaults to `postgis`) is up to create the database and apply migrations.
5. If you skip `setup_db.sh`, run `alembic upgrade head` manually after exporting the same environment variables.
6. Launch the API with `./run.sh` or `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.
7. (Optional) Execute `python verify_setup.py` to confirm key imports and module wiring.
8. Run `pytest` when you start extending the test suite (fixtures are already in place).

## Tooling & Scripts

- `app/scripts/index_es.py` – rebuilds the Elasticsearch index and reindexes plannen records (supports batch processing and OE-auth lookup).
- `app/scripts/upgrade_storage.py` – helper for migrating legacy bestanden storage layouts.
- `setup_db.sh` – ensures the target database exists inside a PostGIS container and runs Alembic migrations.
- `verify_setup.py` – quick verification script for CI or manual runs, validating imports, structure, and FastAPI loading.

With the above in place the FastAPI stack mirrors the legacy plannen domain while remaining ready for further endpoint development, search tuning, and storage integration work.
