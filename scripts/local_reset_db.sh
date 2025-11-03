#!/usr/bin/env bash
set -e

application="${db_name:-premieaanvragen}"
dbname="${application}"
# Data Manipulation Language: includes most common SQL like SELECT, INSERT, UPDATE
premies_dml="${application}_dml"
# Data Definition Language: deals with database schemas and descriptions
premies_ddl="${application}_ddl"


echo "Creating roles ${premies_dml} and ${premies_ddl} if necessary..."
psql -q -U postgres -c "SELECT 1 FROM pg_user WHERE usename = '${premies_dml}'" | grep -q 1 || psql -q -U postgres -c "CREATE ROLE ${premies_dml} LOGIN PASSWORD '${premies_dml}';"
psql -q -U postgres -c "SELECT 1 FROM pg_user WHERE usename = '${premies_ddl}'" | grep -q 1 || psql -q -U postgres -c "CREATE ROLE ${premies_ddl} LOGIN PASSWORD '${premies_ddl}';"
echo " └Finished creating roles ${premies_dml} and ${premies_ddl}"

echo "Re-creating database ${dbname}..."
psql -q -U postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '${dbname}' AND pid <> pg_backend_pid()" > /dev/null
psql -q -U postgres -c "DROP DATABASE IF EXISTS ${dbname}"
psql -q -U postgres -c "CREATE DATABASE ${dbname} WITH OWNER ${premies_ddl}"
psql -q -U postgres -c "ALTER DATABASE ${dbname} SET TimeZone = 'Europe/Brussels'"
psql -q -U postgres -d ${dbname} -c "create extension postgis"
echo " └Finished creating database ${dbname}"

echo "Giving privileges to roles..."
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA oproeppremieaanvragen FOR ROLE ${premies_ddl} GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE ON TABLES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA oproeppremieaanvragen FOR ROLE ${premies_ddl} GRANT USAGE ON SEQUENCES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public FOR ROLE ${premies_ddl} GRANT USAGE ON SEQUENCES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "GRANT ALL ON SCHEMA oproeppremieaanvragen to ${premies_ddl}"
psql -q -U postgres -d ${dbname} -c "GRANT USAGE ON SCHEMA oproeppremieaanvragen to ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA oproeppremieaanvragen_v1 FOR ROLE ${premies_ddl} GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE ON TABLES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA oproeppremieaanvragen_v1 FOR ROLE ${premies_ddl} GRANT USAGE ON SEQUENCES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "GRANT ALL ON SCHEMA oproeppremieaanvragen_v1 to ${premies_ddl}"
psql -q -U postgres -d ${dbname} -c "GRANT USAGE ON SCHEMA oproeppremieaanvragen_v1 to ${premies_dml}"

psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA premieaanvragen FOR ROLE ${premies_ddl} GRANT SELECT,INSERT,UPDATE,DELETE,TRUNCATE ON TABLES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "ALTER DEFAULT PRIVILEGES IN SCHEMA premieaanvragen FOR ROLE ${premies_ddl} GRANT USAGE ON SEQUENCES TO ${premies_dml}"
psql -q -U postgres -d ${dbname} -c "GRANT ALL ON SCHEMA premieaanvragen to ${premies_ddl}"
psql -q -U postgres -d ${dbname} -c "GRANT USAGE ON SCHEMA premieaanvragen to ${premies_dml}"
echo " └Finished giving privileges"