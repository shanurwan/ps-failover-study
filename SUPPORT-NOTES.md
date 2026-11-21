# Support notes: PlanetScale Postgres

Ticket-ready notes built from the measurements in [FINDINGS.md](FINDINGS.md). Each note covers: the customer's report, what to ask, the cause, and the fix.

---

### "We saw duplicate rows after a failover / maintenance window"

- **Ask:**
  - Which client library do you use?
  - Does the app retry writes that time out?
  - Do the duplicates share a timestamp near the switchover?
- **Cause:** the app gave up on a write that later committed. In our runs, 39–55 writes per switchover committed after a 2 s client timeout with node-postgres, Prisma, Drizzle/postgres-js, SQLAlchemy and Rails. Direct pgx lost 12–13 acknowledgements in transit. The database lost and duplicated nothing.
- **Fix:**
  - Make retried writes idempotent: a client-generated key with `ON CONFLICT DO NOTHING`, or an idempotency table.
  - In Go, pgx's context cancellation stops most late commits.
- **Escalate if:** duplicates appear without any client retry. We never saw that.

### "Errors for ~15–20 seconds during a switchover. Is that normal?"

- **Ask:** the timestamps of the first and last error, and the switchover ID (`pscale branch switchover list`).
- **What we measured:** every stack recovered 14–20 s after the switchover command. Errors lasted ~2–4 s in most runs. Direct connections had the shortest window (1.8 s).
- **Tune:**
  - Use a request timeout plus retry with backoff on idempotent work.
  - Alert on error rate over ~30 s, not on single errors.
- **Escalate if:** recovery takes far longer than the switchover's own `completed_at`.

### "No errors, just hangs during the switchover"

- **Cause:** through PgBouncer, every stack we tested saw **only timeouts**. No Postgres error reached the app.
- **Fix:** without a client-side deadline, requests wait as long as the library lets them. Set statement or request timeouts in the app.

### "psql / migrations / cron can't connect: `remaining connection slots are reserved for roles with the SUPERUSER attribute`"

- **Ask:**
  - Which cluster size?
  - What is `max_connections` (`SHOW max_connections`)?
  - Does it happen shortly after a traffic spike?
- **Cause:** the PS-5 cluster allows 25 connections. PgBouncer keeps its server connections for ~10 minutes after load stops; we saw 13–18 held. That leaves no room for direct connections.
- **Fix, pick one:**
  - Route the job through 6432.
  - Wait.
  - Lower the PgBouncer pool size or raise `max_connections` in cluster parameters.
  - Size up.
- **If clients get `server login has been failing, cached error: …`:** PgBouncer is replaying a recent login failure. It clears on its own once a login succeeds.

### "LISTEN/NOTIFY stopped working after we moved to PlanetScale"

- **Ask:** port 6432 or 5432?
- **Cause:** in transaction pooling, `LISTEN` succeeds but notifications never arrive. We got 0/3, with no error.
- **Fix:** use a direct 5432 connection for the listener.

### "Advisory locks / temp tables / `SET` behave randomly"

- **Cause:** through 6432 each transaction may land on a different server connection. We saw:
  - another client inherit a `statement_timeout`
  - B "acquire" A's advisory lock
  - a leaked lock (`you don't own a lock of type ExclusiveLock`)
  - temp-table and `PREPARE` errors, `42P07` and `42P05`
- **Fix:**
  - Use `SET LOCAL` inside a transaction.
  - Use transaction-level advisory locks (`pg_advisory_xact_lock`).
  - Use a direct connection for session state.
- **Fine through 6432:** `search_path` and `application_name` were kept correctly. Protocol-level prepared statements worked 10/10.

### "`ENOENT: no such file or directory, open 'system'`" (Node)

- **Cause:** `sslrootcert=system` is a libpq keyword. node-postgres and Prisma's adapter-pg read it as a file path.
- **Fix:** remove `sslrootcert=system` from the URL, or pass `ssl: { rejectUnauthorized: true }` / a CA file. Keep verification on.

### "`certificate verify failed` from inside Docker"

- **Cause:** slim base images have no CA bundle.
- **Fix:** install `ca-certificates` in the image. Don't downgrade `sslmode`.

### "Our CDC pipeline (Debezium/Airbyte/…) lost its position after a switchover"

- **Ask:**
  - Does the slot have `failover = true` (`SELECT slot_name, failover FROM pg_replication_slots`)?
  - Are `sync_replication_slots` and `hot_standby_feedback` on?
  - Was the consumer running before the switchover?
  - Did you get the "Logical replication needs your attention" email?
- **What we measured:**
  - **Configured as documented, consumer active:** the replica copy became persistent in 25 s, and the slot came through a 35 s switchover with every change.
  - **Settings off:** the slot was lost.
  - **Settings on but consumer idle:** the replica copy was still temporary and the slot was lost.
- **Fix:**
  - Set both parameters.
  - Create slots with `failover = true`.
  - Keep the consumer running before planned changes.
- **To confirm the replica has a persistent copy,** check on a replica:
  `SELECT synced, temporary FROM pg_replication_slots`. You want `synced = t` and `temporary = f`.
