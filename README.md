# ps-failover-study

A reproducible harness to see how common Postgres client libraries behave on
PlanetScale Postgres during a primary switchover, and through its built-in
PgBouncer. PlanetScale's PgBouncer runs in transaction pooling mode only, on
port 6432. Direct Postgres is on port 5432.

The harness runs against a local stand-in (Docker Compose) or against a real
PlanetScale branch. Moving between the two means changing environment
variables only.

## Method

Each client is a small, long-running workload process that uses its library
with **default settings**. Defaults are what most applications run, so
nothing is tuned for resilience. Every workload does the same things:

- It sends requests on an open loop at `RATE` requests per second (default 50,
  hard-capped at 200). Requests alternate between two kinds:
  - an `INSERT INTO ledger (client, seq, ts)`, with a client-side `seq` that
    only goes up;
  - a small `SELECT coalesce(max(id), 0) FROM ledger`.
- Each request has a 2 s deadline, measured from its scheduled start, so
  time spent waiting in the pool counts towards it.
- Each request writes one JSON line: `ts`, `client`, `op`, `seq`, `ok`,
  `latency_ms`, `error_class`, `error_message_verbatim`.
- An insert counts as **acknowledged** only if it returned success before the
  deadline.

How the deadline is enforced is part of what is measured.

- **Go (pgx):** the deadline is a `context.WithDeadline`, which is the
  idiomatic way. pgx reacts to the context:
  - `pgx-default` keeps pgconn's default `DeadlineContextWatcherHandler`. On
    cancel it breaks the socket, and the connection is closed.
  - `pgx-cancelreq` installs `CancelRequestContextWatcherHandler{DeadlineDelay: 1s}`,
    which sends a Postgres CancelRequest and keeps the connection.
- **Node, Python and Ruby:** these libraries have no per-call cancellation in
  their default API. The deadline belongs to the caller: a timeout line is
  written at 2 s and the operation is abandoned, as a request handler with a
  timeout would do. If the abandoned operation finishes later, a second line
  with `op: "late_insert"` or `"late_select"` records its real outcome.

The report checks for lost and duplicated writes. It reads the `ledger` rows
for the run's tag after the run, and compares them with the acknowledged
`seq` values.

### Clients

| name | library | how it is built | non-default settings |
|---|---|---|---|
| `pgx-default` | pgx v5.13.0 `pgxpool` | `pgxpool.ParseConfig(url)` | none |
| `pgx-cancelreq` | pgx v5.13.0 `pgxpool` | same | `BuildContextWatcherHandler` → `CancelRequestContextWatcherHandler` |
| `node-pg` | pg 8.23.1 `Pool` | `new Pool({ connectionString })` | `pool.on('error', …)` listener (node-postgres docs require it; without it an idle-client error kills the process) |
| `prisma` | Prisma ORM 7.10.1 + `@prisma/adapter-pg` | `new PrismaClient({ adapter: new PrismaPg({ connectionString }) })` | none |
| `drizzle-postgresjs` | drizzle-orm 0.45.4 on postgres 4.1.1 | `drizzle(postgres(url))` | none |
| `sqlalchemy-psycopg` | SQLAlchemy 2.1.9 + psycopg 3.3.9 | `create_engine("postgresql+psycopg://…")` (QueuePool 5+10) | none; the URL scheme is rewritten from `postgresql://` |
| `rails-activerecord` | ActiveRecord 8.1.4.1 + pg 1.7.0 | `establish_connection(DATABASE_URL)` | none (pool 5, `prepared_statements` true) |

The connection strings follow PlanetScale's docs:
`postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=verify-full`,
with port 6432 for the pooled endpoint and 5432 for direct. Some PlanetScale
examples differ from what this harness runs:

- Their Drizzle tutorial uses `drizzle-orm/node-postgres`. This harness runs
  Drizzle on postgres-js.
- Their Node example uses a single `Client`. This harness uses `Pool`, as a
  long-running service would.
- There are no pgx or SQLAlchemy pages, so both use their library's
  documented defaults.

### Rounds

| round | what happens | result directory |
|---|---|---|
| `switchover` | Each client runs `PRE_S` (20 s), then `SWITCHOVER_CMD` runs, then the client keeps going for `POST_S` (120 s). This is done for each endpoint (`pooled`, `direct`) and for each of `RUNS` (2). | `results/switchover/<client>/<endpoint>-<n>/` |
| `lock-storm` | There is no switchover. One transaction holds `LOCK TABLE ledger IN ACCESS EXCLUSIVE MODE` for `LOCK_S` (30 s) while the clients' 2 s deadlines expire. A sampler records new Postgres sessions per second. The PgBouncer log is scanned for `client disconnect while server was not ready`. | `results/lock-storm/<client>/<run>/` |
| `session-features` | Two connections, A and B, use `SET` (session), a session advisory lock, `LISTEN`/`NOTIFY`, a temp table, SQL `PREPARE` and protocol-level prepared statements. This is done on 5432 and on 6432, with a quiet pool and with a busy pool (8 extra connections). | `results/session-features/psycopg/<endpoint>-<mode>/` |
| `slot-failover` | A logical slot is created with `failover = true` and another with `failover = false`. Rows are consumed and the run waits for the standby's synced copy. Rows are left unconsumed, the primary switches over, and the slots are read on the new primary. Locally, a second run turns off `sync_replication_slots` on the standby. | `results/slot-failover/slots/<run>/` |

Every workload run directory contains these files:

- `requests.jsonl`: one line per request.
- `ledger.csv`: `seq` and row count, read after the run.
- `event.json`: start and end of the switchover or lock.
- `switchover.out`: the steps the switchover command printed.
- `sessions.csv`: the sampler's output, one row per second (epoch, `pg_stat_database.sessions`, backends, lock waiters, active).
- `client.log`: library versions and the effective pool settings.
- `meta.json`
- `summary.json`
- Locally only: `pgbouncer.log`, `pg1.log`, `pg2.log` and `pgbouncer-config.txt` (`SHOW CONFIG`).

### Metrics (`report/report.py`)

All times are seconds from the event start, based on each request's
scheduled start.

- **first error**: the first failed request at or after the event start.
- **error window**: from the first failed request to the last failed request before recovery.
- **recovered**: the first successful request after which 30 s pass with no failure.
- **never recovered**: there were errors, and no 30 s error-free stretch followed inside the run.
- **last error**: the last failed request in the run.
- **distinct errors**: each verbatim error message with its count.
- **acked-but-missing**: acknowledged `seq` values that have no row in `ledger`.
- **duplicates**: `seq` values that have more than one row.
- **unacked-but-present**: inserts that failed or timed out for the caller, but whose row exists. These are ambiguous commits.

`report.py round results/<round>` writes `report.md` (tables) and
`report.json` (all summaries).

## Local stand-in

`deploy/compose.yaml` defines three services:

- `pg1`: the Postgres 17 primary. It runs with `wal_level=logical` and
  `synchronized_standby_slots=pg2_slot`.
- `pg2`: a streaming replica, cloned with `pg_basebackup` through the physical
  slot `pg2_slot`. It runs with `hot_standby_feedback=on` and
  `sync_replication_slots=on`, and its `primary_conninfo` includes `dbname`, as
  Postgres 17 slot sync requires.
- `pgbouncer`: PgBouncer 1.24.0 (Alpine 3.22 package) with
  `pool_mode=transaction` on port 6432. It uses the values PlanetScale
  documents as its PgBouncer defaults: `max_prepared_statements=200`,
  `default_pool_size=20`, `max_client_conn=100`, `server_lifetime=3600`,
  `query_wait_timeout=120` and `server_check_query=select 1`.

Clients join the `front` network.

- On `front`, the current primary carries the alias `pg-primary`, so
  `pg-primary:5432` acts as a direct endpoint that follows the primary.
- `pgbouncer:6432` is the pooled endpoint.

`scripts/local-switchover.sh` performs one switchover:

1. Fast-stop the primary (SIGINT). Its sessions get `57P01`, and the
   walsender ships the remaining WAL.
2. Run `pg_promote()` on the standby.
3. Move the `pg-primary` alias to the new primary.
4. Repoint PgBouncer: rewrite `databases.ini`, then `RELOAD` and `RECONNECT`.

`PGB_MODE` changes step 4:

- `reload`: the default, as above.
- `pause`: `PAUSE` before step 1 and `RESUME` after step 4. This is close to
  PlanetScale's dedicated PgBouncer, which uses `PAUSE` during planned
  failovers.
- `restart`: PgBouncer goes down with the old primary, and a fresh one starts
  pointing at the new primary. This is close to PlanetScale's local
  PgBouncer, which runs on the primary node.

`scripts/local-reset.sh` rebuilds the stand-in from scratch. When
`TARGET=local`, it runs before every run, so each run starts with pg1 as
primary and pg2 streaming.

### What the stand-in does not represent

- There is no TLS. PlanetScale requires `sslmode=verify-full`, so handshakes,
  certificate checks and `sslnegotiation=direct` are not exercised locally.
- The stand-in runs Postgres 17, with `max_connections=100`.
- The stand-in's PgBouncer tracks only its default `track_extra_parameters`
  (`IntervalStyle`). A PgBouncer that also tracks `search_path` behaves
  differently in the `session-features` round.
- The local PgBouncer keeps a failed server login in its `server_login_retry`
  cache, which defaults to 15 s. `RELOAD` and `RECONNECT` do not clear that
  cache, so in `PGB_MODE=reload` pooled clients keep getting the cached
  error after the new primary is up.
- There is no PlanetScale proxy layer. On PlanetScale, connections go through
  their edge proxy. It has its own errors, for example `08006 no primary
  available for branch …` or `connection retry timeout`, and it may hold or
  retry new connections during a switchover. Locally, during the gap, a new
  direct connection gets a DNS failure or a refusal.
- The local switchover is a script. PlanetScale's real ordering, its timing,
  and its hard cancel of queries after 30 s are not reproduced.
  PlanetScale's dedicated PgBouncer and its cross-AZ topology are only
  approximated, by `PGB_MODE=pause`.
- Replication is asynchronous and there is one replica. PlanetScale runs
  semi-synchronous replication. Because the local switchover is a clean fast
  shutdown, no WAL is lost either way. An unplanned failover (kill -9) is not
  part of the rounds.
- Slot sync. A synced slot copy stays `temporary` until the primary's slot
  moves past what the standby can reserve. Locally, the round calls
  `pg_log_standby_snapshot()` and advances the fully consumed slots, standing
  in for a live consumer. On PlanetScale, the standby is only reachable
  through `|replica`.
- Everything runs on one shared host. Timing varies with whatever else the
  host is doing, so compare the shape of the results across runs, not
  single-run numbers.

## Running it

Requirements: Docker with Compose v2 (the scripts use `$DOCKER`, by default
`~/bin/docker`), bash and python3 (3.9+, standard library only). Node, Go,
Python libraries and Ruby all run in containers.

```sh
scripts/study build                  # client images + PgBouncer image
scripts/study switchover             # main round, all clients, both endpoints, 2 runs
scripts/study lock-storm
scripts/study session-features
scripts/study slot-failover
scripts/study report switchover      # rebuild results/switchover/report.md
```

Useful knobs:

- Select clients, endpoints and runs:
  `CLIENTS="pgx-default pgx-cancelreq" ENDPOINTS=pooled RUNS=1`
- Change the PgBouncer behaviour of the local switchover:
  `PGB_MODE=pause|restart`
- Put runs into separately named directories: `RUN_PREFIX=pause-`
- Pass extra environment to every client:
  `CLIENT_ENV="POSTGRES_JS_PREPARE=false"`
- Lock-storm only: `LOCK_S`, `RUNS_LOCK`, `ENDPOINTS_LOCK`, `POST_S_LOCK`.

### Pointing it at PlanetScale

Create `~/.config/ps-study.env`. It is not in this repository. `scripts/study`
reads it as plain `KEY=VALUE` lines and never executes it, so an unquoted `&`
in a URL is safe. A variable that is already set in the environment takes
precedence over the file, and an explicit `TARGET=local` skips the file
entirely. Fill in the values for your branch:

```sh
TARGET=planetscale
PG_DIRECT_URL='postgresql://postgres.<branch_id>:<password>@<host>.horizon.psdb.cloud:5432/postgres?sslmode=verify-full&sslrootcert=system'
PG_POOLED_URL='postgresql://postgres.<branch_id>:<password>@<host>.horizon.psdb.cloud:6432/postgres?sslmode=verify-full&sslrootcert=system'
PS_ORG=<org>
PS_DB=<database>
PS_BRANCH=<branch>
PLANETSCALE_SERVICE_TOKEN_ID=<id>
PLANETSCALE_SERVICE_TOKEN=<token>
# optional: PG_ADMIN_URL, PS_CANDIDATE, COOLDOWN_S (default 60)
```

The default `SWITCHOVER_CMD` is `scripts/planetscale-switchover.sh`. It runs:

```
pscale branch switchover <PS_DB> <PS_BRANCH> --org <PS_ORG> --format json [--candidate <PS_CANDIDATE>]
```

That command returns as soon as the switchover has started, so the script
then polls `pscale branch switchover show <db> <branch> <id>` every 2 s until
the state is `succeeded` or `failed`. It uses a local `pscale` if one is
installed, and otherwise runs the `planetscale/pscale:v0.355.0` image.

Before it starts anything, the wrapper checks `pscale branch switchover list`:

- It waits while a switchover is pending or running.
- It waits until `PS_MIN_GAP_S` (300) seconds have passed since the last one
  completed.
- It refuses once the branch has `PS_MAX_SWITCHOVERS` (12) switchovers.

`scripts/study` runs these checks (`--guard-only`) before starting the
workloads, so any waiting happens outside the measured window. The wrapper
records `pscale branch infra` before and after, which shows the primary
moving. It ends with a `PS_RESULT` line, and the report turns PlanetScale's
own `created_at`, `started_at` and `completed_at` into seconds from the
event start.

With `TARGET=planetscale`:

- Results go to `results/planetscale/<round>/…`.
- Workloads run concurrently, sharing one switchover per run
  (`CONCURRENT=1`). `RATE` defaults to `200 / N` per workload.
- Containers use the default Docker network. The host CA bundle
  (`CA_BUNDLE`) is mounted at `/etc/ssl/certs/ca-certificates.crt`, because
  the slim images have none and `sslmode=verify-full` needs one.
- node-postgres, and Prisma through `@prisma/adapter-pg`, read `sslrootcert`
  as a file path. With `sslrootcert=system` they fail with `ENOENT: no such
  file or directory, open 'system'`, so for those two clients the parameter
  is removed from the URL. `sslmode=verify-full` then verifies against
  Node's built-in CA store. The other clients take the URL unchanged.
- No reset is done. The `ledger` table is created if it is missing, and rows
  are told apart by a per-run tag.
- Each run waits `COOLDOWN_S` after it finishes.

Mind the branch's `max_connections` when choosing workloads. A PS-5 has 25.
A direct pgx pool defaults to the container's CPU count, and the pooled
endpoint can use up to `default_pool_size` server connections, so a direct
workload and the pooled workloads together can use up every slot. The
symptom is `remaining connection slots are reserved for roles with the
SUPERUSER attribute` (53300). Run the direct workloads in a separate round
(`WORKLOADS=pgx-default:direct ROUND=switchover-direct`).

Other helpers:

- `scripts/study target-info` writes the server version, role and the
  relevant settings to `target-info.txt`.
- `scripts/smoke-clients.sh` connects every client to both endpoints for
  3 s at 4 req/s.
- `ROUND=` names the result directory of a `switchover` or `lock-storm`
  round.
- `RUN_START=` sets the first run number, for adding runs to a round.

On PlanetScale, `slot-failover` cannot query the standby directly. It reads
replica state through the `|replica` username suffix (URL-encoded as
`%7Creplica`), which reaches one of the replicas. The round drops its
`sf_*` slots, publication and table at the end, because a logical slot left
behind retains WAL.

PlanetScale accepts one switchover per branch at a time, and a branch needs
replicas for a real switchover. On a single-node branch, `switchover`
restarts the instance in place.

### Load

The harness runs one client at a time, at 50 requests per second by default.
`RATE` above 200 is clamped to 200. PlanetScale's acceptable use policy
forbids use that "unduly burdens or disrupts" the service, and allows
benchmarks that are "conducted in good faith" with a "fair and transparent
methodology". If you publish results, the policy requires you to disclose
the information needed to replicate them.

## Layout

```
deploy/compose.yaml                 stand-in: pg1, pg2, pgbouncer
deploy/postgres/                    primary init, replica bootstrap
deploy/pgbouncer/                   PgBouncer 1.24 image and config
clients/go-pgx/                     pgx workload
clients/node/                       node-pg, Prisma, Drizzle/postgres-js workloads
clients/python/                     SQLAlchemy/psycopg workload, session-feature probe
clients/ruby/                       ActiveRecord workload
scripts/study                       round runner
scripts/local-switchover.sh         local switchover
scripts/local-reset.sh              rebuild the stand-in
scripts/planetscale-switchover.sh   pscale switchover: guards, wait, PlanetScale timings
scripts/smoke-clients.sh            3 s connectivity check of every client
scripts/target-info.sql             settings recorded by `study target-info`
scripts/rounds/                     session-features, slot-failover
report/report.py, report/features.py
results/                            one directory per round
```
