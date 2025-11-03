# POC Plannen Fast API

Een mini clone van OE Plannen zonder security.
Tech stack: FastAPI, Pydantic, SQLAlchemy, Alembic, Elasticsearch, and PostgreSQL.
Meeste dinge zijn geïmplemnteerd als POC en niet volledig production ready, maar zouden het wel kunnen zijn met wat extra werk.

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM)
- **Alembic**: Database migration tool
- **Elasticsearch**: Search and analytics engine
- **PostgreSQL**: Primary database


## Keuze voor FastAPI
FastAPI is gekozen vanwege de volgende redenen:
- **Snelheid**: FastAPI is een van de snelste Python web frameworks beschikbaar, wat resulteert in lage latentie en hoge doorvoer.
- **Moderne functies**: Ondersteuning voor asynchrone programmeerpatronen, type hints en API-documentatie op basis van pydantic.
- **Pydantic integratie**: integratie met Pydantic voor gegevensvalidatie en serialisatie.

## Keuze voor SQLAlchemy
SQLAlchemy is gekozen vanwege:
- **Flexibiliteit**: Ondersteunt zowel ORM als Core (SQL expressies) dus flexibeler.
- **Grote community**: Actieve community en uitgebreidere documentatie.
- **Compatibiliteit**: Werkt goed met verschillende databases, waaronder PostgreSQL, wat onze primaire database is.
- **Migraties**: Integratie met Alembic maakt database migraties eenvoudig te beheren.
    ### Waarom niet SQLModel?
  - SQLModel is niet gebruikt omdat het nog relatief nieuw is en minder volwassen dan SQLAlchemy zelf.
  - SQLModel is gebouwd bovenop SQLAlchemy, maar mist sommige geavanceerde functies en flexibiliteit die SQLAlchemy biedt.
  - Onze rest API's zijn niet standaard genoeg om volledig te profiteren van de eenvoud van SQLModel.
  - SQLAlchemy heeft een grotere community en meer bronnen beschikbaar, wat nuttig is voor ondersteuning en probleemoplossing.
  - SQLAlchemy kennen we al


## Done
- Basis CRUD operaties voor plannen
- Indexeren van plannen in elasticsearch
- elasticsearch integratie voor zoeken
- Database migraties met Alembic
- Basis validatie met Pydantic modellen
- Basis endpoints met FastAPI
- Add storage provider integratie
- Api documentatie met Swagger UI en ReDoc
- Basic setup voor testen van fastapi app
- Environment file voor settings 
- Voorbeelden van dependency injection en setup met .env variabelen

## Todo 
- Authentificatie en autorisatie
- Validatie uitbreiden
- Meer uitgebreide tests
- skos is niet volledig geïmplementeerd
- Env file opkuisen (ongebruikte variabelen en ook veel dubbele omdat veel bestande code met x.y werkt en .env eigenlijk X_Y notatie gebruikt) 
- eventueel alles async maken, maar leek mij weinig meerwaarde voor deze app
- Code verbeteringen en refactoring focus lag op proof of concept en functionaliteit

## Getting Started
### Prerequisites

- Python 3.9+
- Docker

### Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/vancamti/plannen_fast_api.git
cd plannen_fast_api
```

### Manual Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Decrypt environment file:
```bash
gpg .env.gpg
```

### Running with Docker

1. Start PostgreSQL and Elasticsearch:
```bash
docker start postgis
docker start elasticsearch
```

2. Run database migrations:
```bash
./scripts/reset_db.sh
```

3. Start the FastAPI application:
```bash
./scripts/run.sh
# or
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

## License

MIT
