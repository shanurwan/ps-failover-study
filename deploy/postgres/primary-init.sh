#!/bin/bash
# Runs once, on first start of pg1 (docker-entrypoint-initdb.d).
set -euo pipefail

psql -v ON_ERROR_STOP=1 -U postgres <<'SQL'
CREATE ROLE replicator WITH LOGIN REPLICATION PASSWORD 'replicator';
CREATE ROLE app WITH LOGIN PASSWORD 'app';
CREATE DATABASE app OWNER app;
SELECT pg_create_physical_replication_slot('pg2_slot');
SQL

psql -v ON_ERROR_STOP=1 -U postgres -d app <<'SQL'
GRANT ALL ON SCHEMA public TO app;
SQL

# Replication connections from the replica (and, after a switchover, the other way).
echo "host replication replicator all scram-sha-256" >> "$PGDATA/pg_hba.conf"
