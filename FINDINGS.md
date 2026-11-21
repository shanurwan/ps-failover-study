# Findings: PlanetScale Postgres, measured

Target: a PlanetScale Postgres database. PS-5 cluster (1 primary + 2 replicas), Postgres 18.7, AWS ap-southeast-1. Measured 22 November 2026. Load stayed at or below 200 requests/s in total. Every switchover was a documented `pscale branch switchover` (8 in total).

Times are in seconds from the moment the switchover command started. Each finding links to the raw report it comes from.

## 1. Switchovers: no acknowledged write was lost

| client | endpoint | recovered (run 1 / run 2) | error window | acknowledged-but-missing | duplicates | committed after the client gave up |
|---|---|---|---|---|---|---|
| pgx v5.13 (default) | PgBouncer 6432 | 19.2 / 14.2 | 16.9 / 3.0 | 0 | 0 | 2 / 1 |
| pgx v5.13 (CancelRequest handler) | 6432 | 19.0 / 14.0 | 2.9 / 2.9 | 0 | 0 | 0 / 3 |
| node-postgres 8.23 | 6432 | 19.3 / 14.5 | 17.4 / 3.3 | 0 | 0 | 48 / 46 |
| Prisma 7.10 (adapter-pg) | 6432 | 19.3 / 14.5 | 17.4 / 3.3 | 0 | 0 | 48 / 47 |
| Drizzle 0.45 on postgres-js 4.1 | 6432 | 19.0 / 14.1 | 2.8 / 2.9 | 0 | 0 | 40 / 39 |
| SQLAlchemy 2.1 + psycopg 3.3 | 6432 | 19.3 / 14.5 | 17.0 / 3.3 | 0 | 0 | 46 / 46 |
| Rails ActiveRecord 8.1 | 6432 | 19.8 / 15.1 | 3.6 / 3.9 | 0 | 0 | 52 / 55 |
| pgx v5.13 (default) | direct 5432 | 18.9 / 14.5 | 1.8 / 1.8 | 0 | 0 | 13 / 12 |

- **No acknowledged write was lost, and no row was duplicated,** in any of the 16 client runs.
- **All stacks recover together.** In a given switchover every client recovered within the same second. The switchover sets the pace, not the library.
- **Many writes succeed after the app has given up on them.** Each request had a 2 s deadline. The Node, Python and Ruby stacks have no per-call cancellation, so their abandoned writes were still committed: 39–55 per switchover, each confirmed by a `late_insert ok` line. pgx cancels the call, and only 0–3 of its writes landed late.
- **This is where duplicates come from.** An app that retries a timed-out write without an idempotency key creates the duplicate itself. The database did not.
- **Direct connections get real errors instead of timeouts.** Through PgBouncer every stack reported only timeouts. On 5432, pgx received `57P01 terminating connection due to administrator command` and `57P03 the database system is shutting down`. It also lost 12–13 acknowledgements in transit: the client saw an error, but the row was committed.
- **The first pooled run differs from the second.** In run 1, four stacks started failing at about 2 s and three at about 16 s. In run 2, every stack started at about 11 s. That switchover also took 71 s on PlanetScale's side, against 30–40 s for the others, so the switchover, not the library, explains the difference.

Raw data: [`switchover`](results/planetscale-public/switchover/report.md), [`switchover-direct`](results/planetscale-public/switchover-direct/report.md).

## 2. Small clusters: PgBouncer can use up every connection slot

- On a PS-5 cluster `max_connections` is 25.
- After load stops, the local PgBouncer keeps its server connections open for about 10 minutes. I measured it twice: 18 idle connections fell to 1 between 04:44 and 04:45, and 13 fell to 1 between 04:57 and 04:58, about 10 minutes after each load ended.
- While they are open, **direct connections on 5432 are refused**, even though the application is idle:
  `FATAL: remaining connection slots are reserved for roles with the SUPERUSER attribute`
- When the pool itself hits the limit, PgBouncer caches the login failure and returns it to new clients for a while:
  `FATAL: server login has been failing, cached error: remaining connection slots are reserved for roles with the SUPERUSER attribute (SQLSTATE 08P01)`
- A customer will usually report this as "migrations or a cron job can't connect, but nothing is running".

## 3. Transaction pooling breaks session features, often silently

Two connections, A and B, used psycopg 3.3. A "busy" pool had 8 extra connections. Each check was repeated 10 times.

| feature | direct 5432 | PgBouncer 6432 |
|---|---|---|
| `SET statement_timeout` | stays on A | quiet pool: B saw A's setting 10/10. Busy pool: A kept its own only 2/10 |
| `SET search_path`, `application_name` | stays on A | **stays on A**: PlanetScale's PgBouncer tracks these |
| session advisory lock | correct | B "acquired" A's held lock 10/10. Under load A's unlock failed (`you don't own a lock`) and the lock leaked |
| `LISTEN` / `NOTIFY` | 3/3 received | **0/3 received, no error** |
| temp table | correct | B: `42P07 already exists`. Under load A's inserts failed 8/10 (`does not exist`) |
| SQL `PREPARE` | correct | `42P05 already exists`. Under load EXECUTE failed 6/10 |
| protocol-level prepared statements | 10/10 | **10/10**: no client needed a prepared-statement setting |

Raw data: [`session-features`](results/planetscale-public/session-features/report.md).

## 4. A lock pile-up through PgBouncer did not cause a reconnect storm

- **Setup:** one transaction held `ACCESS EXCLUSIVE` on the table for 30.8 s while pgx clients at 50 req/s hit their 2 s deadlines.
- **Recovery:** both pgx modes recovered within 1–5 s of the lock being released.
- **New sessions:** they peaked at 3.4/s with the default pgx handler and 7.4/s with the CancelRequest handler.
- **Contrast with plain PgBouncer:** in an earlier lab on plain PgBouncer, the same pattern produced 112–121 new sessions/s and the API never recovered. That did not happen here at this rate.

Raw data: [`lock-storm`](results/planetscale-public/lock-storm/report.md).

## 5. Connection strings: `sslrootcert=system` only works where libpq reads it

- PlanetScale's psql examples use `sslmode=verify-full sslrootcert=system`, which libpq understands.
- Pasting the same URL into **node-postgres** or **Prisma (adapter-pg)** fails with:
  `ENOENT: no such file or directory, open 'system'`
- pgx, psycopg, postgres-js and Rails (pg) accepted it.
- Slim container images (`postgres:17`, `node:22-slim`, `python:3.12-slim`) ship without a CA bundle, so `verify-full` fails inside them until one is installed or mounted.

## 6. Logical replication slots across a switchover

Three runs, each with one switchover:

| setup | PlanetScale's response | result on the new primary |
|---|---|---|
| `failover = true` slot; `sync_replication_slots` and `hot_standby_feedback` **off** (defaults) | An email within ~1 minute: "Logical replication needs your attention … PlanetScale will hold some cluster changes and rollouts" | Manual switchover completed in 52 s. **Slot gone** |
| both parameters **on**; consumer **idle** (replica copy `synced = t`, `temporary = t`) | `synchronized_standby_slots` set to both replicas automatically | Switchover completed in 43 s (`logical_slot_sync_timeout` = 5 min). **Slot gone** |
| both parameters **on**; consumer **active**, one write and one read per second | The replica copy became persistent (`temporary = f`) after 25 s; the switchover then took 35 s | **Slot present, all 10 expected changes read in order** |

- **Configured as documented, with an active consumer, the slot survived the switchover with no changes missed.**
- The two losses happened outside that setup:
  - With the parameters off, a manual switchover was not held, even though the hold email had already been sent.
  - With an idle consumer, the replica's copy was synced but still temporary, and the switchover did not wait for it.
- Each case was run once.

Raw logs: [`defaults`](results/planetscale-public/slot-failover-defaults.log), [`parameters on, idle`](results/planetscale-public/slot-failover-params-on-idle.log), [`parameters on, active`](results/planetscale-public/slot-failover-params-on-active.log).

## Method and limits

- [README](README.md) covers the clients, deadlines, rounds and how to reproduce every number above.
- **One cluster size (PS-5)** and one region.
- **The direct round** used pgx only.
- **Short pauses** of about 2 s that hit several clients at once outside any switchover were seen once and are not explained.
