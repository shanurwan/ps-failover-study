#!/usr/bin/env bash
# Short connectivity check of every client against both endpoints of the
# configured target: 4 req/s for 3 s each. Prints lines, failures and the
# first verbatim error per client/endpoint. Uses scripts/study's settings.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
eval "$(sed -n '/^load_env()/,/^}/p; /^client_url()/,/^}/p; /^client_spec()/,/^}/p' "$ROOT/scripts/study")"
if [ "${TARGET:-}" != local ] && [ -f "$HOME/.config/ps-study.env" ]; then load_env "$HOME/.config/ps-study.env"; fi
D=${DOCKER:-$HOME/bin/docker}
if [ "${TARGET:-local}" = planetscale ]; then
  DARGS=(-v "${CA_BUNDLE:-/etc/pki/tls/certs/ca-bundle.crt}:/etc/ssl/certs/ca-certificates.crt:ro" -e SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt)
else
  DARGS=(--network psfs_front)
  PG_DIRECT_URL=${PG_DIRECT_URL:-postgresql://app:app@pg-primary:5432/app}
  PG_POOLED_URL=${PG_POOLED_URL:-postgresql://app:app@pgbouncer:6432/app}
fi
out=$(mktemp -d)
for c in ${CLIENTS:-pgx-default pgx-cancelreq node-pg prisma drizzle-postgresjs sqlalchemy-psycopg rails-activerecord}; do
  client_spec "$c"
  for ep in direct pooled; do
    u=$PG_DIRECT_URL; [ "$ep" = pooled ] && u=$PG_POOLED_URL
    u=$(client_url "$c" "$u")
    e=(); [ -z "$CENV" ] || e=(-e "$CENV")
    $D run --rm "${DARGS[@]}" ${e[@]+"${e[@]}"} -v "$out:/out" -e DATABASE_URL="$u" -e CLIENT="smoke-$c" -e RUN_TAG=smoke \
      -e RATE=4 -e DURATION_S=3 -e OUT="/out/$c-$ep.jsonl" "$IMAGE" $ENTRY > "$out/$c-$ep.log" 2>&1 || true
    f="$out/$c-$ep.jsonl"
    printf '%-20s %-6s lines=%s fail=%s %s\n' "$c" "$ep" "$(wc -l < "$f")" "$(grep -cE '"ok": ?false' "$f" || true)" \
      "$(python3 -c 'import json,sys
for l in open(sys.argv[1]):
    r=json.loads(l)
    if not r["ok"]: print(r["error_message_verbatim"][:200].replace("\n"," ")); break' "$f")"
  done
done
rm -rf "$out"
