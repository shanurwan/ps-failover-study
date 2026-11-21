#!/usr/bin/env python3
"""Summarise workload runs.

  report.py run <results/round/client/run>   one run -> summary.json (+ one line)
  report.py round <results/round>            all runs -> report.md + report.json

Definitions (all times relative to the event start, i.e. the moment the
switchover command or the lock was started, using each request's scheduled
start time):
  first_error_s   first failed request at or after the event start
  error_window_s  first failed request to the last failed request before recovery
  recovered_s     first successful request after which 30 s pass with no failure
                  (null if that never happens inside the run: never_recovered)
  last_error_s    last failed request in the run
  acked_missing   inserts acknowledged to the caller whose seq is not in ledger
  duplicates      seqs with more than one ledger row
  unacked_present inserts that failed or timed out for the caller, but whose
                  row exists (ambiguous commits)
Stdlib only; runs on Python 3.9+.
"""
import csv
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime


def iso_epoch(v):
    if not v:
        return None
    v = re.sub(r"(\.\d{6})\d+", r"\1", str(v).replace("Z", "+00:00"))
    try:
        return datetime.fromisoformat(v).timestamp()
    except ValueError:
        return None


def switchover_steps(path, ev_start_s):
    """Step times (s from event start) from switchover.out: the local script's
    step lines, or PlanetScale's own created_at/started_at/completed_at."""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("PS_RESULT "):
                try:
                    o = json.loads(line[len("PS_RESULT "):])
                except ValueError:
                    continue
                out["ps_id"] = o.get("id")
                out["ps_state"] = o.get("state")
                out["ps_method"] = o.get("method")
                for k in ("created_at", "started_at", "completed_at"):
                    t = iso_epoch(o.get(k))
                    if t is not None:
                        out["ps_" + k + "_s"] = round(t - ev_start_s, 2)
                continue
            if line.startswith("{") and '"step"' in line:
                try:
                    o = json.loads(line)
                    out[o["step"] + "_s"] = round(float(o["ts"]) - ev_start_s, 2)
                except (ValueError, KeyError):
                    pass
    return out

STEADY_MS = 30000


def load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out


def load_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def ledger_counts(path):
    counts = {}
    if os.path.exists(path):
        with open(path) as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[0].strip().isdigit():
                    counts[int(row[0])] = int(row[1])
    return counts


def sessions_stats(path, ev_start, ev_end):
    """Per-second new Postgres sessions from the sampler (it adds 1/s itself)."""
    rows = []
    if os.path.exists(path):
        with open(path) as f:
            for row in csv.reader(f):
                try:
                    rows.append((float(row[0]), int(row[1]), int(row[2]), int(row[3]), int(row[4])))
                except (ValueError, IndexError):
                    pass
    if len(rows) < 2:
        return None
    rates = []
    for a, b in zip(rows, rows[1:]):
        dt = b[0] - a[0]
        dn = b[1] - a[1]
        if dt <= 0 or dn < 0:  # counter reset: a new primary
            continue
        rates.append((b[0], max(0.0, (dn - 1) / dt), b[2], b[3], b[4]))

    def window(lo, hi):
        return [r for r in rates if lo <= r[0] < hi]

    def mx(ws, i):
        return round(max((w[i] for w in ws), default=0), 1)

    before = window(rows[0][0], ev_start)
    during = window(ev_start, ev_end + 1)
    after = window(ev_end + 1, rows[-1][0] + 1)
    tail = window(rows[-1][0] - 20, rows[-1][0] + 1)
    return {
        "new_sessions_per_s_max_before": mx(before, 1),
        "new_sessions_per_s_max_during": mx(during, 1),
        "new_sessions_per_s_max_after": mx(after, 1),
        "new_sessions_per_s_mean_last_20s": round(sum(w[1] for w in tail) / len(tail), 1) if tail else None,
        "backends_max": mx(rates, 2),
        "lock_waiters_max": mx(rates, 3),
        "active_max": mx(rates, 4),
    }


PGB_PATTERNS = [
    "client disconnect while server was not ready",
    "server conn crashed?",
    "client unexpected eof",
    "query_wait_timeout",
    "pooler error",
    "server login failed",
]


def pgbouncer_stats(path):
    if not os.path.exists(path):
        return None
    c = Counter()
    reasons = Counter()
    with open(path, errors="replace") as f:
        for line in f:
            for p in PGB_PATTERNS:
                if p in line:
                    c[p] += 1
            m = re.search(r"closing because: (.*?)(?: \(age=|$)", line)
            if m:
                reasons[m.group(1).strip()] += 1
            m = re.search(r"pooler error: (.*)$", line)
            if m:
                reasons["pooler error: " + m.group(1).strip()] += 1
    return {"patterns": dict(c), "closing_reasons": dict(reasons.most_common(15))}


def summarize(d):
    meta = load_json(os.path.join(d, "meta.json"), {}) or {}
    ev = load_json(os.path.join(d, "event.json"), {}) or {}
    recs = load_jsonl(os.path.join(d, "requests.jsonl"))
    main = [r for r in recs if r.get("op") in ("insert", "select")]
    late = [r for r in recs if str(r.get("op", "")).startswith("late_")]
    proc = [r for r in recs if r.get("op") in ("uncaught_exception", "unhandled_rejection")]
    main.sort(key=lambda r: r["ts_ms"])
    ev_start = float(ev.get("start", 0)) * 1000
    ev_end = float(ev.get("end", ev.get("start", 0))) * 1000
    run_end = main[-1]["ts_ms"] if main else 0

    pre_err = [r for r in main if r["ts_ms"] < ev_start and not r["ok"]]
    post = [r for r in main if r["ts_ms"] >= ev_start]
    errs = [r for r in post if not r["ok"]]

    first_error_s = error_window_s = recovered_s = None
    never = False
    relapse = 0
    if not errs:
        recovered_s = 0.0
        error_window_s = 0.0
    else:
        first_error_s = (errs[0]["ts_ms"] - ev_start) / 1000
        err_ts = [r["ts_ms"] for r in errs]
        ok_ts = [r["ts_ms"] for r in post if r["ok"]]
        rec_at = None
        last_err_before = None
        oi = 0
        for j, e in enumerate(err_ts):
            while oi < len(ok_ts) and ok_ts[oi] <= e:
                oi += 1
            if oi >= len(ok_ts):
                break
            cand = ok_ts[oi]
            nxt = err_ts[j + 1] if j + 1 < len(err_ts) else None
            if nxt is not None and nxt < cand:
                continue
            horizon = nxt if nxt is not None else run_end + 1
            if horizon - cand >= STEADY_MS and run_end - cand >= STEADY_MS - 1000:
                rec_at = cand
                last_err_before = e
                break
        if rec_at is None:
            never = True
            error_window_s = (err_ts[-1] - err_ts[0]) / 1000
        else:
            recovered_s = (rec_at - ev_start) / 1000
            error_window_s = (last_err_before - err_ts[0]) / 1000
            relapse = sum(1 for t in err_ts if t > rec_at)

    errors = Counter((r.get("error_class", ""), r.get("error_message_verbatim", "")) for r in main if not r["ok"])
    proc_errors = Counter((r.get("op"), r.get("error_message_verbatim", "")) for r in proc)

    ledger = ledger_counts(os.path.join(d, "ledger.csv"))
    inserts = [r for r in main if r["op"] == "insert"]
    acked = {r["seq"] for r in inserts if r["ok"]}
    unacked = {r["seq"] for r in inserts if not r["ok"]}
    present = set(ledger)
    late_ok = {r["seq"] for r in late if r.get("op") == "late_insert" and r.get("ok")}
    lat = sorted(r["latency_ms"] for r in main if r["ok"])

    def pct(p):
        return round(lat[min(len(lat) - 1, int(p * len(lat)))], 1) if lat else None

    s = {
        "dir": d,
        "round": meta.get("round"),
        "client": meta.get("client"),
        "run": meta.get("run"),
        "endpoint": meta.get("endpoint"),
        "target": meta.get("target"),
        "rate": meta.get("rate"),
        "client_env": meta.get("client_env", ""),
        "event": ev,
        "switchover_steps": switchover_steps(os.path.join(d, "switchover.out"), ev_start / 1000),
        "requests": len(main),
        "ok": sum(1 for r in main if r["ok"]),
        "errors": len([r for r in main if not r["ok"]]),
        "errors_before_event": len(pre_err),
        "errors_after_event": len(errs),
        "first_error_s": first_error_s,
        "error_window_s": error_window_s,
        "recovered_s": recovered_s,
        "never_recovered": never,
        "errors_after_recovery": relapse,
        "last_error_s": (errs[-1]["ts_ms"] - ev_start) / 1000 if errs else None,
        "inserts_attempted": len(inserts),
        "inserts_acked": len(acked),
        "ledger_rows": sum(ledger.values()),
        "acked_missing": sorted(acked - present),
        "duplicates": sorted(k for k, v in ledger.items() if v > 1),
        "unacked_present": len(unacked & present),
        "late_insert_ok": len(late_ok),
        "latency_ok_ms_p50": pct(0.50),
        "latency_ok_ms_p99": pct(0.99),
        "distinct_errors": [{"error_class": k[0], "message": k[1], "count": v} for k, v in errors.most_common()],
        "process_errors": [{"kind": k[0], "message": k[1], "count": v} for k, v in proc_errors.most_common()],
        "sessions": sessions_stats(os.path.join(d, "sessions.csv"), ev_start / 1000, ev_end / 1000),
        "pgbouncer": pgbouncer_stats(os.path.join(d, "pgbouncer.log")),
    }
    if not main:
        s["no_data"] = True
    return s


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return "%.1f" % v
    return str(v)


def one_line(s):
    return ("%s/%s %s: %d req, %d err (%d before event), first_err=%s s, window=%s s, recovered=%s s%s, "
            "acked_missing=%d, dup=%d, unacked_present=%d" % (
                s["client"], s["run"], s["endpoint"], s["requests"], s["errors"], s["errors_before_event"],
                fmt(s["first_error_s"]), fmt(s["error_window_s"]), fmt(s["recovered_s"]),
                " NEVER RECOVERED" if s["never_recovered"] else "",
                len(s["acked_missing"]), len(s["duplicates"]), s["unacked_present"]))


def md_escape(t):
    return t.replace("|", "\\|").replace("\n", " ")


def round_report(root):
    sums = []
    for client in sorted(os.listdir(root)):
        cd = os.path.join(root, client)
        if client.startswith("_") or not os.path.isdir(cd):
            continue
        for run in sorted(os.listdir(cd)):
            rd = os.path.join(cd, run)
            if os.path.exists(os.path.join(rd, "requests.jsonl")) and os.path.exists(os.path.join(rd, "meta.json")):
                s = summarize(rd)
                with open(os.path.join(rd, "summary.json"), "w") as f:
                    json.dump(s, f, indent=1)
                sums.append(s)
    rnd = os.path.basename(os.path.normpath(root))
    lock = rnd.startswith("lock")
    lines = ["# Round `%s`" % rnd, "",
             "Times are seconds from the event start (%s). One row per run." % (
                 "lock acquired" if lock else "switchover command started"), ""]
    hdr = ["client", "run", "endpoint", "requests", "errors", "first error", "error window", "recovered", "last error",
           "never recovered", "acked-but-missing", "duplicates", "unacked-but-present"]
    if lock:
        hdr += ["new sessions/s max (lock / after / last 20 s mean)", "lock waiters max",
                "PgBouncer 'client disconnect while server was not ready'"]
    if not lock:
        hdr += ["switchover steps (s)"]
    hdr += ["top error"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for s in sums:
        top = s["distinct_errors"][0] if s["distinct_errors"] else None
        row = [s["client"], s["run"], s["endpoint"], str(s["requests"]), str(s["errors"]),
               fmt(s["first_error_s"]), fmt(s["error_window_s"]), fmt(s["recovered_s"]), fmt(s["last_error_s"]),
               "yes" if s["never_recovered"] else "no", str(len(s["acked_missing"])),
               str(len(s["duplicates"])), str(s["unacked_present"])]
        if lock:
            ss = s.get("sessions") or {}
            pg = (s.get("pgbouncer") or {}).get("patterns", {})
            row += ["%s / %s / %s" % (fmt(ss.get("new_sessions_per_s_max_during")),
                                      fmt(ss.get("new_sessions_per_s_max_after")),
                                      fmt(ss.get("new_sessions_per_s_mean_last_20s"))),
                    fmt(ss.get("lock_waiters_max")),
                    str(pg.get("client disconnect while server was not ready", 0)) if s.get("pgbouncer") else "-"]
        if not lock:
            st = s.get("switchover_steps") or {}
            if "ps_completed_at_s" in st:
                keys = ["ps_created_at_s", "ps_started_at_s", "ps_completed_at_s"]
            else:
                keys = ["old_primary_stopped_s", "promoted_s", "pgbouncer_repointed_s", "pgbouncer_restarted_s"]
            row.append(", ".join("%s=%s" % (k[:-2].replace("ps_", "ps "), st[k]) for k in keys if k in st) or "-")
        row.append(md_escape("%s x%d: %s" % (top["error_class"], top["count"], top["message"][:120])) if top else "")
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    lines += ["", "## Distinct verbatim errors per client (all runs of the round)", ""]
    by_client = {}
    for s in sums:
        by_client.setdefault(s["client"], []).append(s)
    for client, ss in by_client.items():
        lines.append("### %s" % client)
        lines.append("")
        agg = Counter()
        for s in ss:
            for e in s["distinct_errors"]:
                agg[(s["endpoint"], e["error_class"], e["message"])] += e["count"]
            for e in s["process_errors"]:
                agg[(s["endpoint"], "process:" + e["kind"], e["message"])] += e["count"]
        if not agg:
            lines += ["No errors.", ""]
            continue
        lines.append("| endpoint | class | count | verbatim message |")
        lines.append("|---|---|---|---|")
        for (ep, cls, msg), n in sorted(agg.items(), key=lambda kv: (kv[0][0], -kv[1])):
            lines.append("| %s | %s | %d | `%s` |" % (ep, cls, n, md_escape(msg)[:400]))
        lines.append("")
    with open(os.path.join(root, "report.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(root, "report.json"), "w") as f:
        json.dump(sums, f, indent=1)
    for s in sums:
        print(one_line(s))


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("run", "round"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "run":
        s = summarize(sys.argv[2])
        with open(os.path.join(sys.argv[2], "summary.json"), "w") as f:
            json.dump(s, f, indent=1)
        print(one_line(s))
    else:
        round_report(sys.argv[2])


if __name__ == "__main__":
    main()
