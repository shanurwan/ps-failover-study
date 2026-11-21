#!/usr/bin/env python3
"""Render results/session-features/*/<endpoint>-<mode>/result.json as report.md."""
import glob
import json
import os
import sys


def first(t):
    return (t or "").strip().splitlines()[0] if (t or "").strip() else ""

root = sys.argv[1]
res = {}
for p in sorted(glob.glob(os.path.join(root, "*", "*", "result.json"))):
    with open(p) as f:
        r = json.load(f)
    res["%s-%s" % (r["endpoint"], r["mode"])] = r
cols = [c for c in ("direct-quiet", "direct-busy", "pooled-quiet", "pooled-busy") if c in res]


def err(r):
    if r is None:
        return "-"
    if r.get("ok"):
        return "ok " + (",".join(x[0] for x in r["rows"]) if r.get("rows") else "")
    return "ERROR %s: %s" % (r.get("sqlstate"), first(r.get("error")))


def cell(name, t):
    if "crashed" in t:
        return "crashed: " + t["crashed"]
    if name == "set_session":
        return ("A kept statement_timeout %d/%d, search_path %d/%d, application_name %d/%d; "
                "B saw A's statement_timeout %d/%d, search_path %d/%d, application_name %d/%d; A used %d backend(s)" % (
                    t["A_kept_setting"], t["of"], t["A_kept_search_path"], t["of"], t["A_kept_application_name"], t["of"],
                    t["B_saw_A_statement_timeout"], t["of"], t["B_saw_A_search_path"], t["of"],
                    t["B_saw_A_application_name"], t["of"], t["A_distinct_backends"]))
    if name == "advisory_lock":
        return ("A lock: %s; B got the lock while A held it %d/%d; A unlock: %s; B lock after A's unlock: %s; "
                "advisory locks still held at the end: %s; notices A: %s" % (
                    err(t["A_lock"]), t["B_try_while_A_holds_got_lock"], t["of"], err(t["A_unlock"]),
                    err(t["B_try_after_A_unlocked"]), err(t["advisory_locks_still_held_after_test"]),
                    "; ".join(sorted(set(t.get("notices_A", [])))) or "none"))
    if name == "listen_notify":
        return "LISTEN: %s; A received %d/%d notifications" % (err(t["listen"]), len([x for x in t["A_received"] if not str(x).startswith("error")]), t["expected"])
    if name == "temp_table":
        counts = [first(c) for c in t["A_select_counts"]]
        return ("create: %s; A insert failed %d/%d %s; A count(*) results: %s; B create same name: %s" % (
            err(t["A_create"]), t["A_insert_failed"], t["of"],
            ("(" + first(t["A_insert_errors"][0]["error"]) + ")") if t["A_insert_errors"] else "",
            ",".join(counts), err(t["B_create_same_name"])))
    if name == "sql_prepare":
        return "PREPARE: %s; EXECUTE failed %d/%d %s; B PREPARE same name: %s" % (
            err(t["A_prepare"]), t["A_execute_failed"], t["of"], "; ".join(t["A_execute_errors"]), err(t["B_prepare_same_name"]))
    if name == "protocol_prepare":
        return "ok %d/%d %s" % (t["ok"], t["of"], "; ".join(t["errors"]))
    return json.dumps(t)


names = ["set_session", "advisory_lock", "listen_notify", "temp_table", "sql_prepare", "protocol_prepare"]
lines = ["# Round `session-features`", "",
         "psycopg %s, autocommit, two client connections A and B. `busy` = 8 extra connections running "
         "short queries. Counts are out of 10 repetitions." % (next(iter(res.values()))["psycopg"] if res else "?"), ""]
for n in names:
    lines.append("## %s" % n)
    lines.append("")
    lines.append("| endpoint-mode | observed |")
    lines.append("|---|---|")
    for c in cols:
        t = res[c]["tests"].get(n)
        lines.append("| %s | %s |" % (c, cell(n, t).replace("|", "\\|") if t else "-"))
    lines.append("")
with open(os.path.join(root, "report.md"), "w") as f:
    f.write("\n".join(lines) + "\n")
with open(os.path.join(root, "report.json"), "w") as f:
    json.dump(res, f, indent=1)
print("\n".join(lines))
