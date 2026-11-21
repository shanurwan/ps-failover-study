#!/usr/bin/env bash
# Default SWITCHOVER_CMD for TARGET=planetscale.
#
# Runs `pscale branch switchover <db> <branch> --org <org>` (pscale >= 0.355,
# internal/cmd/branch/switchover.go). That command returns as soon as the
# switchover has *started*, so this script then polls
# `pscale branch switchover show <db> <branch> <id>` until the state is
# succeeded or failed.
#
# Guards, checked against `pscale branch switchover list` before starting:
#   - never start while another switchover is pending/running (waits);
#   - at least PS_MIN_GAP_S (300) seconds since the last one completed (waits);
#   - at most PS_MAX_SWITCHOVERS (12) switchovers on the branch in total (refuses).
#
# Output: `pscale branch infra` before and after, one JSON line per poll, and a
# final line `PS_RESULT {...}` with PlanetScale's own record (id, state,
# method, created_at, started_at, completed_at).
#
# Needs PS_ORG, PS_DB, PS_BRANCH, and PLANETSCALE_SERVICE_TOKEN_ID +
# PLANETSCALE_SERVICE_TOKEN in the environment (or a logged-in pscale).
# Optional: PS_CANDIDATE (replica name from `pscale branch infra`).
# Uses `pscale` from PATH or ~/bin, else the planetscale/pscale image.
set -euo pipefail
: "${PS_ORG:?}" "${PS_DB:?}" "${PS_BRANCH:?}"
D=${DOCKER:-$HOME/bin/docker}
PSCALE_IMAGE=${PSCALE_IMAGE:-planetscale/pscale:v0.355.0}
MIN_GAP=${PS_MIN_GAP_S:-300}
MAX_N=${PS_MAX_SWITCHOVERS:-12}

PSCALE_BIN=$(command -v pscale 2>/dev/null || { [ -x "$HOME/bin/pscale" ] && echo "$HOME/bin/pscale"; } || true)
pscale_() {
  if [ -n "$PSCALE_BIN" ]; then
    "$PSCALE_BIN" "$@"
  else
    $D run --rm -e PLANETSCALE_SERVICE_TOKEN_ID -e PLANETSCALE_SERVICE_TOKEN "$PSCALE_IMAGE" "$@"
  fi
}
jq_() { python3 -c "import json,sys; d=json.load(sys.stdin); $1"; }

# --- guards ---------------------------------------------------------------
while :; do
  list=$(pscale_ branch switchover list "$PS_DB" "$PS_BRANCH" --org "$PS_ORG" --format json)
  read -r n busy last <<<"$(printf '%s' "$list" | jq_ '
from datetime import datetime
import re
def ts(v):
    v = re.sub(r"(\.\d{6})\d+", r"\1", (v or "").replace("Z", "+00:00"))
    try: return datetime.fromisoformat(v).timestamp()
    except ValueError: return 0
busy = sum(1 for s in d if s.get("state") in ("pending", "running"))
last = max([ts(s.get("completed_at")) for s in d] or [0])
print(len(d), busy, int(last))')"
  if [ "$n" -ge "$MAX_N" ]; then echo "refusing: branch already has $n switchovers (PS_MAX_SWITCHOVERS=$MAX_N)" >&2; exit 3; fi
  if [ "$busy" -gt 0 ]; then echo "{\"guard\":\"waiting for $busy switchover(s) in progress\"}"; sleep 15; continue; fi
  gap=$(( $(date +%s) - last ))
  if [ "$last" -gt 0 ] && [ "$gap" -lt "$MIN_GAP" ]; then
    echo "{\"guard\":\"last switchover completed ${gap}s ago; waiting $((MIN_GAP - gap))s\"}"
    sleep $((MIN_GAP - gap)); continue
  fi
  break
done
# scripts/study calls --guard-only before starting the workloads, so any
# waiting happens before the measured window rather than inside it.
[ "${1:-}" = --guard-only ] && { echo "{\"guard\":\"ok\",\"switchovers_so_far\":$n}"; exit 0; }

echo "== infra before"; pscale_ branch infra "$PS_DB" "$PS_BRANCH" --org "$PS_ORG" --format json | jq_ '
for c in d if isinstance(d, list) else d.get("components", d.get("data", [])):
    print(json.dumps({k: c.get(k) for k in ("component", "role", "name", "availability_zone", "az") if k in c}))' 2>/dev/null || true

# --- switchover -----------------------------------------------------------
args=(branch switchover "$PS_DB" "$PS_BRANCH" --org "$PS_ORG" --format json)
[ -n "${PS_CANDIDATE:-}" ] && args+=(--candidate "$PS_CANDIDATE")
printf '{"step":"pscale_invoked","ts":%s}\n' "$(date +%s.%3N)"
started=$(pscale_ "${args[@]}" 2>&1) || { echo "$started" >&2; exit 1; }
printf '{"step":"pscale_returned","ts":%s}\n' "$(date +%s.%3N)"
echo "$started" | jq_ 'print(json.dumps(d))'
id=$(printf '%s' "$started" | jq_ 'print(d["id"])')

deadline=$(( $(date +%s) + ${PS_SWITCHOVER_TIMEOUT_S:-600} ))
while :; do
  cur=$(pscale_ branch switchover show "$PS_DB" "$PS_BRANCH" "$id" --org "$PS_ORG" --format json)
  state=$(printf '%s' "$cur" | jq_ 'print(d.get("state",""))')
  printf '{"poll_ts":%s,"state":"%s"}\n' "$(date +%s.%3N)" "$state"
  case "$state" in
    succeeded|failed)
      printf '{"step":"pscale_%s_observed","ts":%s}\n' "$state" "$(date +%s.%3N)"
      echo "PS_RESULT $(printf '%s' "$cur" | jq_ 'print(json.dumps(d))')"
      echo "== infra after"; pscale_ branch infra "$PS_DB" "$PS_BRANCH" --org "$PS_ORG" --format json | jq_ '
for c in d if isinstance(d, list) else d.get("components", d.get("data", [])):
    print(json.dumps({k: c.get(k) for k in ("component", "role", "name", "availability_zone", "az") if k in c}))' 2>/dev/null || true
      # failed = unconfirmed outcome per PlanetScale docs; nothing rolled back.
      [ "$state" = succeeded ] && exit 0 || exit 1 ;;
  esac
  [ "$(date +%s)" -lt "$deadline" ] || { echo "timed out waiting for switchover $id" >&2; exit 2; }
  sleep 2
done
