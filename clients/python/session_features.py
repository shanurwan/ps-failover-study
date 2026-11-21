"""Session-state features through transaction pooling vs a direct connection.

Usage: session_features.py <endpoint-label> <url> <quiet|busy> <out.json>

Two client connections, A and B, stand for two requests (or two app
instances) sharing one database endpoint. Both use psycopg 3 in autocommit
mode, so every statement is its own transaction, which is how ORMs outside
an explicit transaction run. In "busy" mode, 8 extra connections run short
queries in a loop (about 160 queries/s in total), so PgBouncer hands A and B whichever server connection is
free, as it does in production. In "quiet" mode PgBouncer tends to give a
lone client the same server again, which hides most of the breakage.

For each feature the script records what a session-mode app expects, what it
saw, every NOTICE/WARNING, and every error verbatim.
"""
import json
import sys
import threading
import time

import psycopg

label, url, mode, out_path = sys.argv[1:5]
N = 10  # repetitions of each observation


def connect(name):
    c = psycopg.connect(url, autocommit=True, application_name=name)
    c.notices = []
    c.add_notice_handler(lambda d: c.notices.append(f"{d.severity}: {d.message_primary}"))
    return c


def q(c, sql, params=None):
    try:
        cur = c.execute(sql, params)
        try:
            rows = cur.fetchall()
        except psycopg.ProgrammingError:
            rows = None
        return {"ok": True, "rows": [list(map(str, r)) for r in rows] if rows is not None else None}
    except psycopg.Error as e:
        return {"ok": False, "sqlstate": e.sqlstate, "error": str(e).strip()}


def backend(c):
    r = q(c, "select pg_backend_pid()")
    return r["rows"][0][0] if r["ok"] else None


stop = threading.Event()


def noise():
    try:
        c = psycopg.connect(url, autocommit=True, application_name="noise")
    except psycopg.Error:
        return
    # About 20 queries/s per thread, 160/s for all 8: enough to keep
    # PgBouncer handing out different server connections, and under the
    # study's 200 req/s ceiling.
    while not stop.is_set():
        try:
            c.execute("select pg_sleep(0.02)")
        except psycopg.Error:
            pass
        time.sleep(0.03)


threads = []
if mode == "busy":
    for _ in range(8):
        t = threading.Thread(target=noise, daemon=True)
        t.start()
        threads.append(t)
    time.sleep(0.5)

results = {"endpoint": label, "mode": mode, "psycopg": psycopg.__version__, "tests": {}}


def run_test(name, fn):
    A, B = connect("A"), connect("B")
    try:
        res = fn(A, B)
    except Exception as e:  # noqa: BLE001
        res = {"crashed": f"{type(e).__name__}: {e}"}
    res["notices_A"] = A.notices
    res["notices_B"] = B.notices
    results["tests"][name] = res
    A.close()
    B.close()


def t_set(A, B):
    """SET (session) statement_timeout and search_path on A; read back on A and B."""
    q(A, "create schema if not exists sf_schema")
    s1 = q(A, "set statement_timeout = '4321ms'")
    s2 = q(A, "set search_path = sf_schema, public")
    s3 = q(A, "set application_name = 'A-renamed'")  # PgBouncer tracks this one
    a_vals, b_vals, a_pids = [], [], set()
    for _ in range(N):
        a_vals.append((q(A, "show statement_timeout")["rows"][0][0],
                       q(A, "show search_path")["rows"][0][0],
                       q(A, "show application_name")["rows"][0][0]))
        b_vals.append((q(B, "show statement_timeout")["rows"][0][0],
                       q(B, "show search_path")["rows"][0][0],
                       q(B, "show application_name")["rows"][0][0]))
        a_pids.add(backend(A))
    exp_a = ("4321ms", "sf_schema, public", "A-renamed")
    return {
        "set_results": [s1, s2, s3],
        "A_kept_setting": sum(1 for v in a_vals if v[0] == exp_a[0]),
        "A_kept_search_path": sum(1 for v in a_vals if v[1] == exp_a[1]),
        "A_kept_application_name": sum(1 for v in a_vals if v[2] == exp_a[2]),
        "B_saw_A_statement_timeout": sum(1 for v in b_vals if v[0] == exp_a[0]),
        "B_saw_A_search_path": sum(1 for v in b_vals if v[1] == exp_a[1]),
        "B_saw_A_application_name": sum(1 for v in b_vals if v[2] == exp_a[2]),
        "of": N,
        "A_distinct_backends": len(a_pids),
        "A_values_sample": a_vals[:3],
        "B_values_sample": b_vals[:3],
    }


def t_advisory(A, B):
    """Session advisory lock taken by A, contended by B, released by A."""
    key = 424242
    take = q(A, "select pg_advisory_lock(%s)", (key,))
    b_try_while_held = [q(B, "select pg_try_advisory_lock(%s)", (key,)) for _ in range(N)]
    b_got = [r for r in b_try_while_held if r["ok"] and r["rows"][0][0] == "True"]
    # B releases anything it got, so the next step is about A only.
    for _ in b_got:
        q(B, "select pg_advisory_unlock(%s)", (key,))
    unlock = q(A, "select pg_advisory_unlock(%s)", (key,))
    after = q(B, "select pg_try_advisory_lock(%s)", (key,))
    if after["ok"] and after["rows"][0][0] == "True":
        q(B, "select pg_advisory_unlock(%s)", (key,))
    leaked = q(B, "select count(*) from pg_locks where locktype = 'advisory' and objid = %s", (key,))
    return {
        "A_lock": take,
        "B_try_while_A_holds_got_lock": len(b_got), "of": N,
        "A_unlock": unlock,
        "B_try_after_A_unlocked": after,
        "advisory_locks_still_held_after_test": leaked,
    }


def t_listen(A, B):
    """LISTEN on A, NOTIFY from B, wait 3 s for A to receive it."""
    lst = q(A, "listen sf_channel")
    time.sleep(0.2)
    sent = [q(B, "notify sf_channel, 'hello-%s'" % i) for i in range(3)]
    got = []
    deadline = time.time() + 3
    try:
        gen = A.notifies(timeout=3, stop_after=3)
        for n in gen:
            got.append(n.payload)
            if time.time() > deadline:
                break
    except psycopg.Error as e:
        got.append("error: " + str(e))
    # A session-mode client would also see the notification on its next query.
    q(A, "select 1")
    return {"listen": lst, "notify": sent, "A_received": got, "expected": 3}


def t_temp(A, B):
    """Temp table created by A, then used by A; B creates one with the same name."""
    c = q(A, "create temp table sf_tmp (x int)")
    ins = [q(A, "insert into sf_tmp values (1)") for _ in range(N)]
    sel = [q(A, "select count(*) from sf_tmp") for _ in range(N)]
    b_create = q(B, "create temp table sf_tmp (x int)")
    b_sel = q(B, "select count(*) from sf_tmp")
    return {
        "A_create": c,
        "A_insert_errors": [r for r in ins if not r["ok"]][:3],
        "A_insert_failed": sum(1 for r in ins if not r["ok"]),
        "A_select_counts": [r["rows"][0][0] if r["ok"] else r.get("error") for r in sel],
        "of": N,
        "B_create_same_name": b_create,
        "B_select": b_sel,
    }


def t_prepare_sql(A, B):
    """SQL-level PREPARE / EXECUTE (not protocol-level)."""
    p = q(A, "prepare sf_stmt as select 42")
    ex = [q(A, "execute sf_stmt") for _ in range(N)]
    b = q(B, "prepare sf_stmt as select 42")
    return {"A_prepare": p, "A_execute_failed": sum(1 for r in ex if not r["ok"]),
            "A_execute_errors": sorted({r.get("error", "") for r in ex if not r["ok"]}), "of": N,
            "B_prepare_same_name": b}


def t_prepare_protocol(A, B):
    """Protocol-level named prepared statements (psycopg prepare=True)."""
    errs = []
    ok = 0
    for i in range(N):
        try:
            A.execute("select %s::int + 1", (i,), prepare=True).fetchone()
            ok += 1
        except psycopg.Error as e:
            errs.append(str(e).strip())
    return {"ok": ok, "of": N, "errors": sorted(set(errs))}


for name, fn in [("set_session", t_set), ("advisory_lock", t_advisory), ("listen_notify", t_listen),
                 ("temp_table", t_temp), ("sql_prepare", t_prepare_sql), ("protocol_prepare", t_prepare_protocol)]:
    run_test(name, fn)

stop.set()
with open(out_path, "w") as f:
    json.dump(results, f, indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if not kk.startswith("notices")} for k, v in results["tests"].items()})[:3000])
