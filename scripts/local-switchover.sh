#!/usr/bin/env bash
# Simulates a primary switchover on the local stand-in (deploy/compose.yaml):
#   1. fence: stop the current primary with a fast shutdown (SIGINT). Its
#      sessions get 57P01, new connections are refused, and the walsender
#      ships the remaining WAL to the standby before it exits.
#   2. promote the standby (pg_promote, wait for it).
#   3. move the "pg-primary" network alias (the direct endpoint) to the new
#      primary.
#   4. repoint PgBouncer: rewrite databases.ini, RELOAD, RECONNECT.
#
# PGB_MODE picks how PgBouncer takes part:
#   reload  (default) one long-lived PgBouncer, repointed with RELOAD+RECONNECT.
#   pause   PAUSE before step 1, RESUME after step 4: clients wait instead of
#           failing. Closest to PlanetScale's *dedicated* PgBouncer.
#   restart PgBouncer goes down with the old primary and a fresh one comes up
#           pointing at the new primary. Closest to PlanetScale's *local*
#           PgBouncer, which runs on the primary node.
# Prints one JSON object per step on stdout.
set -euo pipefail
D=${DOCKER:-$HOME/bin/docker}
NET=${FRONT_NET:-psfs_front}
MODE=${PGB_MODE:-reload}

now() { date +%s.%3N; }
step() { printf '{"step":"%s","ts":%s%s}\n' "$1" "$(now)" "${2:-}"; }
in_recovery() { $D exec "psfs-$1" psql -h 127.0.0.1 -U postgres -tAc 'select pg_is_in_recovery()' 2>/dev/null || echo down; }
pgb() { $D exec psfs-pgbouncer psql -h 127.0.0.1 -p 6432 -U admin pgbouncer -tAc "$1" >/dev/null; }
dbini() { printf '[databases]\n* = host=%s port=5432\n' "$1"; }

if [ "$(in_recovery pg1)" = f ]; then old=pg1; new=pg2
elif [ "$(in_recovery pg2)" = f ]; then old=pg2; new=pg1
else echo "no running primary found" >&2; exit 1; fi
[ "$(in_recovery $new)" = t ] || { echo "$new is not a running standby" >&2; exit 1; }

step begin ",\"old\":\"$old\",\"new\":\"$new\",\"pgb_mode\":\"$MODE\""
if [ "$MODE" = pause ]; then pgb "PAUSE"; step pgbouncer_paused; fi

if [ "$MODE" = restart ]; then
  $D stop -s SIGINT -t 10 psfs-pgbouncer >/dev/null &
fi
$D stop -t 60 "psfs-$old" >/dev/null
wait
step old_primary_stopped

$D exec "psfs-$new" psql -h 127.0.0.1 -U postgres -v ON_ERROR_STOP=1 -tAc 'select pg_promote(true, 60)' >/dev/null
until [ "$(in_recovery $new)" = f ]; do sleep 0.1; done
step promoted

$D network disconnect "$NET" "psfs-$old" >/dev/null 2>&1 || true
$D network disconnect "$NET" "psfs-$new" >/dev/null 2>&1 || true
$D network connect --alias pg-primary "$NET" "psfs-$new"
step direct_alias_moved

if [ "$MODE" = restart ]; then
  tmp=$(mktemp)
  dbini "$new" > "$tmp"
  chmod 644 "$tmp"
  $D cp "$tmp" psfs-pgbouncer:/etc/pgbouncer/databases.ini >/dev/null
  rm -f "$tmp"
  $D start psfs-pgbouncer >/dev/null
  until pgb "SHOW VERSION" 2>/dev/null; do sleep 0.1; done
  step pgbouncer_restarted
else
  $D exec psfs-pgbouncer sh -c "printf '[databases]\n* = host=$new port=5432\n' > /etc/pgbouncer/databases.ini"
  pgb "RELOAD"
  pgb "RECONNECT"
  if [ "$MODE" = pause ]; then pgb "RESUME"; fi
  step pgbouncer_repointed
fi
step end
