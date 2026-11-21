"""SQLAlchemy 2 + psycopg 3 workload, engine and pool at their defaults.

create_engine("postgresql+psycopg://...") gives a QueuePool (pool_size 5,
max_overflow 10, pool_timeout 30 s, pool_pre_ping off).

Env: DATABASE_URL, CLIENT, RUN_TAG, RATE, DURATION_S, TIMEOUT_MS, OUT.

Each request runs on a worker thread, the way a threaded web server would
run it. SQLAlchemy's sync API has no per-call cancellation, so the 2 s
deadline belongs to the caller: a reaper writes a timeout line at the
deadline and the work is abandoned. If it finishes later, a second line with
op "late_<op>" records the real outcome.
"""
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import sqlalchemy
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
# PlanetScale docs show postgresql://; SQLAlchemy needs the dialect+driver.
if url.startswith("postgresql://"):
    url = "postgresql+psycopg://" + url[len("postgresql://"):]
client = os.environ["CLIENT"]
tag = client + "/" + os.environ.get("RUN_TAG", "")
rate = int(os.environ.get("RATE", "50"))
dur = float(os.environ.get("DURATION_S", "90"))
timeout = int(os.environ.get("TIMEOUT_MS", "2000")) / 1000.0

engine = create_engine(url)
p = engine.pool
print(f"sqlalchemy {sqlalchemy.__version__} pool={type(p).__name__} size={p.size()} "
      f"overflow={p._max_overflow} timeout={p._timeout} pre_ping={p._pre_ping}", flush=True)

out = open(os.environ["OUT"], "w")
lock = threading.Lock()


def write(r):
    with lock:
        out.write(json.dumps(r) + "\n")


def classify(e):
    orig = getattr(e, "orig", None) or e
    state = getattr(orig, "sqlstate", None)
    if state:
        return "pg_" + state
    return type(orig).__name__


def message(e):
    orig = getattr(e, "orig", None)
    return str(orig if orig is not None else e).strip()


outstanding = {}  # id -> (base record, deadline)


def reaper(stop):
    while not stop.is_set() or outstanding:
        now = time.time()
        with lock:
            expired = [k for k, (_, dl) in outstanding.items() if dl <= now]
            items = [(k, outstanding.pop(k)[0]) for k in expired]
        for _, base in items:
            write(dict(base, ok=False, latency_ms=round((now - base["ts_ms"] / 1000) * 1000, 3),
                       error_class="timeout",
                       error_message_verbatim=f"client deadline {int(timeout * 1000)}ms exceeded"))
        if stop.is_set() and not outstanding:
            break
        time.sleep(0.05)


def do(i, base):
    err = None
    try:
        with engine.begin() as conn:
            if base["op"] == "insert":
                conn.execute(text("INSERT INTO ledger (client, seq, ts) VALUES (:c, :s, now())"),
                             {"c": tag, "s": base["seq"]})
            else:
                conn.execute(text("SELECT coalesce(max(id), 0) FROM ledger")).scalar()
    except Exception as e:  # noqa: BLE001 - every failure is data here
        err = e
    lat = round((time.time() - base["ts_ms"] / 1000) * 1000, 3)
    with lock:
        mine = outstanding.pop(i, None) is not None
    rec = dict(base, ok=err is None, latency_ms=lat,
               error_class=classify(err) if err else "",
               error_message_verbatim=message(err) if err else "")
    if not mine:
        rec["op"] = "late_" + base["op"]
    write(rec)


def main():
    stop = threading.Event()
    t = threading.Thread(target=reaper, args=(stop,), daemon=True)
    t.start()
    pool = ThreadPoolExecutor(max_workers=256)
    interval = 1.0 / rate
    start = time.time()
    seq = 0
    i = 0
    while True:
        sched = start + i * interval
        if sched - start >= dur:
            break
        d = sched - time.time()
        if d > 0:
            time.sleep(d)
        op = "insert" if i % 2 == 0 else "select"
        s = None
        if op == "insert":
            seq += 1
            s = seq
        base = {"ts": datetime.fromtimestamp(sched, timezone.utc).isoformat(timespec="milliseconds"),
                "ts_ms": int(sched * 1000), "client": client, "op": op, "seq": s}
        with lock:
            outstanding[i] = (base, sched + timeout)
        pool.submit(do, i, base)
        i += 1
    # Wait for the deadlines to pass, then give late results a few seconds.
    time.sleep(timeout + 0.2)
    stop.set()
    t.join()
    end_by = time.time() + 3
    while pool._work_queue.qsize() > 0 and time.time() < end_by:
        time.sleep(0.1)
    with lock:
        out.flush()
    os._exit(0)


main()
