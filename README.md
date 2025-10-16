# Plannen Fast API

A mini clone of OE Plannen without security using FastAPI, Pydantic, SQLAlchemy, Alembic, Elasticsearch, and PostgreSQL.

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM)
- **Alembic**: Database migration tool
- **Elasticsearch**: Search and analytics engine
- **PostgreSQL**: Primary database

## Project Structure

```
plannen_fast_api/
├── alembic/                    # Database migrations
│   └── versions/               # Migration scripts
├── app/
│   ├── api/
│   │   └── v1/                 # API v1 endpoints
│   │       └── items.py        # Example item endpoints
│   ├── core/
│   │   └── config.py           # Application configuration
│   ├── db/
│   │   ├── base.py             # Database session and base
│   │   └── elasticsearch.py    # Elasticsearch client
│   ├── models/
│   │   └── item.py             # SQLAlchemy models
│   ├── schemas/
│   │   └── item.py             # Pydantic schemas
│   ├── services/
│   │   └── item_service.py     # Business logic
│   └── main.py                 # FastAPI application entry point
├── docker-compose.yml          # Docker services configuration
├── requirements.txt            # Python dependencies
└── .env.example                # Example environment variables
```

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for local development)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vancamti/plannen_fast_api.git
cd plannen_fast_api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure:
```bash
cp .env.example .env
```

### Running with Docker

1. Start PostgreSQL and Elasticsearch:
```bash
docker-compose up -d
```

2. Run database migrations:
```bash
alembic upgrade head
```

3. Start the FastAPI application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Items
- `POST /api/v1/items/` - Create a new item
- `GET /api/v1/items/` - List all items
- `GET /api/v1/items/{item_id}` - Get item by ID
- `PUT /api/v1/items/{item_id}` - Update item
- `DELETE /api/v1/items/{item_id}` - Delete item

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
```

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT
