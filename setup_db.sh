#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DB_NAME="${1:-plannen_fastapi}"
CONTAINER_NAME="${POSTGIS_CONTAINER_NAME:-postgis}"
DB_USER="${POSTGIS_DB_USER:-postgres}"
VENV_PATH="${VENV_PATH:-$SCRIPT_DIR/venv}"

if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    # shellcheck disable=SC1090
    source "$VENV_PATH/bin/activate"
fi

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/.env"
    set +a
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command not found. Please install Docker before running this script."
    exit 1
fi

if ! docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
    echo "Container '$CONTAINER_NAME' is not running. Start it with 'docker-compose up -d postgis'."
    exit 1
fi

echo "Checking if database '$DB_NAME' exists in container '$CONTAINER_NAME'..."
DB_EXISTS="$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")"

if [[ "$DB_EXISTS" == "1" ]]; then
    echo "Database '$DB_NAME' already exists; no action taken."
else
    echo "Creating database '$DB_NAME'..."
    docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE \"${DB_NAME}\""
    echo "Database '$DB_NAME' created successfully."
fi

if ! command -v alembic >/dev/null 2>&1; then
    echo "alembic command not found. Install project dependencies or activate your virtual environment."
    exit 1
fi

echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied successfully."
