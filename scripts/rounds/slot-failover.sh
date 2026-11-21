#!/usr/bin/env bash
# Round "slot-failover": does a logical replication slot survive a switchover?
#
# Run "sync-on":  slots sf_failover (failover = true) and sf_nofailover
#                 (failover = false); the standby has sync_replication_slots=on.
# Run "sync-off": slot sf_failover (failover = true); the standby has
#                 sync_replication_slots=off (local target only).
#
# Each run: create the slots, insert 5 rows and consume them, wait for the
# standby to show a synced copy, insert 5 more rows (left unconsumed),
# switch over, insert 5 more, then read the slots on the new primary. A slot
# that continued correctly returns exactly pre-unconsumed-1..5 and post-1..5.
# Called by scripts/study.
set -euo pipefail
: "${ROOT:?}" "${D:?}" "${PG_ADMIN_URL:?}" "${SWITCHOVER_CMD:?}"
read -r -a NETARGS <<<"${NETARGS_STR:-}"
OUTROOT="${RESULTS:-$ROOT/results}/slot-failover/slots"
RUNS_SLOT=${RUNS_SLOT:-"sync-on sync-off"}
[ "$TARGET" = local ] || RUNS_SLOT=${RUNS_SLOT_PS:-sync-on}

adm() { $D run --rm -i ${NETARGS[@]+"${NETARGS[@]}"} postgres:17 psql "$PG_ADMIN_URL" -X -At -v ON_ERROR_STOP=1 "$@"; }
adm_retry() { local i; for i in $(seq 1 60); do adm "$@" 2>/dev/null && return 0; sleep 1; done; adm "$@"; }
node_sql() { $D exec "psfs-$1" psql -h 127.0.0.1 -U postgres -d app -X -At -v ON_ERROR_STOP=1 -c "$2"; }
in_recovery() { node_sql "$1" 'select pg_is_in_recovery()' 2>/dev/null || echo down; }
standby() { if [ "$(in_recovery pg1)" = t ]; then echo pg1; elif [ "$(in_recovery pg2)" = t ]; then echo pg2; fi; }
SLOTS_SQL="select slot_name, slot_type, failover, synced, temporary, conflicting, coalesce(invalidation_reason,''), restart_lsn, confirmed_flush_lsn from pg_replication_slots where slot_name like 'sf_%' order by 1"
changes_sql() { echo "select encode(data, 'escape') from pg_logical_slot_get_binary_changes('$1', NULL, NULL, 'proto_version', '1', 'publication_names', 'sf_pub') where substr(data, 1, 1) = 'I'"; }
labels() { grep -oE '(pre-consumed|pre-unconsumed|post)-[0-9]+' | sort -V | tr '\n' ' '; }

for run in $RUNS_SLOT; do
  dir="$OUTROOT/$run"; rm -rf "$dir"; mkdir -p "$dir"
  L="$dir/log.txt"
  say() { echo "$*" | tee -a "$L" >&2; }
  if [ "$TARGET" = local ]; then "$ROOT/scripts/local-reset.sh"; fi
  slots=(sf_failover); [ "$run" = sync-on ] && slots+=(sf_nofailover)
  say "== $run ($(date -u +%FT%TZ))"

  if [ "$TARGET" = local ]; then
    sb=$(standby)
    if [ "$run" = sync-off ]; then
      node_sql "$sb" "alter system set sync_replication_slots = off" >/dev/null
      node_sql "$sb" "select pg_reload_conf()" >/dev/null
    fi
    say "standby $sb: sync_replication_slots=$(node_sql "$sb" 'show sync_replication_slots') hot_standby_feedback=$(node_sql "$sb" 'show hot_standby_feedback') primary_slot_name=$(node_sql "$sb" 'show primary_slot_name')"
  fi
  say "primary: wal_level=$(adm -c 'show wal_level') synchronized_standby_slots=$(adm -c 'show synchronized_standby_slots' 2>&1)"

  adm -c "drop table if exists sf_t" -c "create table sf_t (id serial primary key, v text)" \
      -c "drop publication if exists sf_pub" -c "create publication sf_pub for table sf_t" >/dev/null
  for s in "${slots[@]}"; do
    adm -c "select pg_drop_replication_slot('$s') from pg_replication_slots where slot_name = '$s'" >/dev/null
    fo=true; [ "$s" = sf_nofailover ] && fo=false
    # pg_create_logical_replication_slot(name, plugin, temporary, twophase, failover)
    say "create $s: $(adm -c "select slot_name, lsn from pg_create_logical_replication_slot('$s', 'pgoutput', false, false, $fo)" 2>&1)"
  done
  adm -c "insert into sf_t (v) select 'pre-consumed-' || g from generate_series(1, 5) g" >/dev/null
  for s in "${slots[@]}"; do say "consume $s before switchover: $(adm -c "$(changes_sql "$s")" 2>&1 | labels)"; done

  sync_wait=""
  if [ "$TARGET" = local ]; then
    t0=$(date +%s)
    for i in $(seq 1 90); do
      # A synced copy stays "temporary" until the primary's slot moves past
      # the point the standby can reserve. A standby snapshot record plus an
      # advance of the (already fully consumed) slots moves it along, as a
      # live consumer would.
      adm -c "select pg_log_standby_snapshot()" >/dev/null
      for s in "${slots[@]}"; do adm -c "select pg_replication_slot_advance('$s', pg_current_wal_lsn())" >/dev/null 2>&1 || true; done
      st=$(node_sql "$sb" "select synced::text || '/' || temporary::text from pg_replication_slots where slot_name = 'sf_failover'" 2>/dev/null || true)
      if [ "$st" = "true/false" ]; then sync_wait=$(( $(date +%s) - t0 )); break; fi
      [ "$run" = sync-off ] && [ "$i" -ge 35 ] && break
      sleep 1
    done
    say "standby slot copy became synced and caught up after: ${sync_wait:-never (waited $(( $(date +%s) - t0 ))s)}"
    say "standby slots before switchover:"; node_sql "$sb" "$SLOTS_SQL" | tee -a "$L" >&2 || true
  else
    # PlanetScale routes a username with the suffix "|replica" to a replica.
    # With several replicas this sees one of them.
    rep_url=${PG_REPLICA_URL:-$(echo "$PG_ADMIN_URL" | sed -E 's#^(postgres(ql)?://)([^:@]+)#\1\3%7Creplica#')}
    rq() { $D run --rm -i ${NETARGS[@]+"${NETARGS[@]}"} postgres:17 psql "$rep_url" -X -At -v ON_ERROR_STOP=1 "$@"; }
    say "replica reached via |replica: in_recovery=$(rq -c 'select pg_is_in_recovery()' 2>&1 | tr '\n' ' ') sync_replication_slots=$(rq -c 'show sync_replication_slots' 2>&1) hot_standby_feedback=$(rq -c 'show hot_standby_feedback' 2>&1)"
    t0=$(date +%s)
    for i in $(seq 1 ${SLOT_SYNC_WAIT_S:-90}); do
      st=$(rq -c "select synced::text || '/' || temporary::text from pg_replication_slots where slot_name = 'sf_failover'" 2>/dev/null || true)
      if [ "$st" = "true/false" ]; then sync_wait=$(( $(date +%s) - t0 )); break; fi
      sleep 1
    done
    say "replica slot copy synced (not temporary) after: ${sync_wait:-never (waited $(( $(date +%s) - t0 ))s)}"
    say "replica slots before switchover:"; rq -c "$SLOTS_SQL" 2>&1 | tee -a "$L" >&2 || true
  fi

  adm -c "insert into sf_t (v) select 'pre-unconsumed-' || g from generate_series(1, 5) g" >/dev/null
  say "primary slots before switchover:"; adm -c "$SLOTS_SQL" | tee -a "$L" >&2
  t0=$(date +%s.%3N)
  $SWITCHOVER_CMD > "$dir/switchover.out" 2>&1 || say "switchover command exit $?"
  say "switchover took $(awk "BEGIN{print $(date +%s.%3N) - $t0}")s"
  adm_retry -c "insert into sf_t (v) select 'post-' || g from generate_series(1, 5) g" >/dev/null
  say "new primary slots after switchover:"; adm -c "$SLOTS_SQL" | tee -a "$L" >&2
  result="{\"run\":\"$run\",\"target\":\"$TARGET\",\"sync_wait_s\":\"${sync_wait:-}\",\"slots\":{"
  first=1
  for s in "${slots[@]}"; do
    exists=$(adm -c "select count(*) from pg_replication_slots where slot_name = '$s'")
    got=""; err=""
    if [ "$exists" = 1 ]; then
      got=$(adm -c "$(changes_sql "$s")" 2> "$dir/err.txt" | labels) || true
      err=$(tr '\n' ' ' < "$dir/err.txt" | sed 's/"/\\"/g')
    fi
    say "after switchover $s: exists=$exists changes=[$got] ${err:+error: $err}"
    [ $first = 1 ] || result+=","
    first=0
    result+="\"$s\":{\"exists_on_new_primary\":$([ "$exists" = 1 ] && echo true || echo false),\"changes_after\":\"${got% }\",\"error\":\"$err\"}"
  done
  result+="}}"
  echo "$result" > "$dir/result.json"
  rm -f "$dir/err.txt"
  # A logical slot left behind retains WAL forever: drop everything.
  adm_retry -c "select pg_drop_replication_slot(slot_name) from pg_replication_slots where slot_name like 'sf_%' and not active" \
      -c "drop publication if exists sf_pub" -c "drop table if exists sf_t" >/dev/null || say "cleanup failed: drop sf_* slots by hand"
  say "cleanup: remaining sf_ slots on primary: $(adm -c "select count(*) from pg_replication_slots where slot_name like 'sf_%'")"
done

python3 - "$OUTROOT" <<'PY'
import glob, json, os, sys
root = sys.argv[1]
exp = " ".join(["pre-unconsumed-%d" % i for i in range(1, 6)] + ["post-%d" % i for i in range(1, 6)])
lines = ["# Round `slot-failover`", "",
         "Expected for a slot that continued correctly: `%s`." % exp, "",
         "| run | slot | standby sync wait (s) | exists on new primary | changes read after switchover | error |", "|---|---|---|---|---|---|"]
for p in sorted(glob.glob(os.path.join(root, "*", "result.json"))):
    r = json.load(open(p))
    for s, v in r["slots"].items():
        lines.append("| %s | %s | %s | %s | `%s` | %s |" % (r["run"], s, r["sync_wait_s"] or "-", v["exists_on_new_primary"],
                     v["changes_after"] or "", v["error"]))
out = os.path.join(os.path.dirname(root), "report.md")
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
PY
