#!/bin/bash
# pg2: clone pg1 with pg_basebackup on first start, then run as a hot standby.
# primary_conninfo carries dbname=postgres, which Postgres 17 slot sync needs.
set -euo pipefail

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  until pg_isready -h pg1 -U postgres -q; do sleep 0.5; done
  chmod 700 "$PGDATA"
  PGPASSWORD=replicator pg_basebackup \
    -d "host=pg1 user=replicator dbname=postgres" \
    -D "$PGDATA" -X stream -S pg2_slot -R -P
  cat >> "$PGDATA/postgresql.auto.conf" <<'CONF'
primary_conninfo = 'host=pg1 user=replicator password=replicator dbname=postgres application_name=pg2'
primary_slot_name = 'pg2_slot'
sync_replication_slots = on
CONF
fi

exec docker-entrypoint.sh "$@"
