#!/usr/bin/env bash
# Round "session-features": SET, session advisory locks, LISTEN/NOTIFY, temp
# tables and PREPARE, through the pooled endpoint (6432) vs direct (5432),
# with a quiet and a busy pool. Called by scripts/study.
set -euo pipefail
: "${ROOT:?}" "${D:?}" "${PG_DIRECT_URL:?}" "${PG_POOLED_URL:?}"
read -r -a NETARGS <<<"${NETARGS_STR:-}"
OUT="${RESULTS:-$ROOT/results}/session-features/psycopg"
mkdir -p "$OUT"
for endpoint in direct pooled; do
  url=$PG_DIRECT_URL; [ "$endpoint" = pooled ] && url=$PG_POOLED_URL
  for mode in quiet busy; do
    if [ "$TARGET" = local ]; then "$ROOT/scripts/local-reset.sh"; fi
    dir="$OUT/$endpoint-$mode"; rm -rf "$dir"; mkdir -p "$dir"
    echo "[$(date +%H:%M:%S)] session-features $endpoint $mode" >&2
    $D run --rm ${NETARGS[@]+"${NETARGS[@]}"} -v "$dir:/out" psfs-py session_features.py \
      "$endpoint" "$url" "$mode" /out/result.json > "$dir/stdout.txt" 2>&1 || echo "failed, see $dir/stdout.txt" >&2
  done
done
python3 "$ROOT/report/features.py" "${RESULTS:-$ROOT/results}/session-features"
