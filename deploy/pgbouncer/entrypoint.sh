#!/bin/sh
# databases.ini is the only file the switchover script rewrites. It is
# written on first start only, so a restarted container keeps its target.
set -eu
if [ ! -f /etc/pgbouncer/databases.ini ]; then
  printf '[databases]\n* = host=%s port=5432\n' "${PRIMARY_HOST:-pg1}" > /etc/pgbouncer/databases.ini
fi
chmod 644 /etc/pgbouncer/databases.ini
exec su -s /bin/sh nobody -c "pgbouncer /etc/pgbouncer/pgbouncer.ini"
