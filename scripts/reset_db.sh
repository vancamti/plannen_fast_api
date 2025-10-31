#!/usr/bin/env bash

# reset the DB that is running in Docker
# run this from within THIS directory

#set -x

docker exec postgis psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'plannen_fastapi'"
docker exec postgis psql -U postgres -c "DROP DATABASE IF EXISTS plannen_fastapi;"
docker exec postgis psql -U postgres -c "SELECT 1 FROM pg_user WHERE usename = 'plannen_fastapi'" | grep -q 1 || psql -h localhost -U postgres -c "CREATE ROLE plannen_fastapi LOGIN PASSWORD 'plannen_fastapi';"
docker exec postgis psql -U postgres -c "SELECT 1 FROM pg_user WHERE usename = 'plannen_fastapi_dml'" | grep -q 1 || psql -h localhost -U postgres -c "CREATE ROLE plannen_fastapi_dml LOGIN PASSWORD 'plannen_fastapi_dml';"
docker exec postgis psql -U postgres -c "CREATE DATABASE plannen_fastapi WITH OWNER = plannen_fastapi;"
docker exec postgis psql -U postgres -d plannen_fastapi -c "CREATE EXTENSION postgis;"
docker exec postgis psql -U postgres -d plannen_fastapi -c "CREATE EXTENSION dblink;"
docker exec postgis psql -U postgres -c "ALTER DATABASE plannen_fastapi SET TimeZone = 'Europe/Brussels';"

cd  ..

#alembic downgrade base
alembic upgrade head