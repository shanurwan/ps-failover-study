# Round `switchover`

Times are seconds from the event start (switchover command started). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | switchover steps (s) | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drizzle-postgresjs | pooled-1 | pooled | 3500 | 185 | 0.3 | 7.4 | 7.7 | 7.7 | no | 0 | 0 | 0 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | other x62: Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: getaddrinfo ENOTFOUND pg |
| drizzle-postgresjs | pooled-2 | pooled | 3500 | 334 | 0.5 | 13.3 | 13.8 | 13.8 | no | 0 | 0 | 148 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x296: client deadline 2000ms exceeded |
| node-pg | pooled-1 | pooled | 3500 | 25 | 0.3 | 1.0 | 1.4 | 1.3 | no | 0 | 0 | 4 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | timeout x9: client deadline 2000ms exceeded |
| node-pg | pooled-2 | pooled | 3500 | 343 | 0.5 | 13.7 | 14.2 | 14.1 | no | 0 | 0 | 154 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x308: client deadline 2000ms exceeded |
| pgx-cancelreq | pooled-1 | pooled | 3500 | 35 | 0.3 | 1.4 | 1.7 | 1.7 | no | 0 | 0 | 0 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | net_dial x17: failed to connect to `user=app database=app`: 	192.168.64.3:6432 (pgbouncer): dial error: dial tcp 192.168.64.3:6432: co |
| pgx-cancelreq | pooled-2 | pooled | 3500 | 334 | 0.5 | 13.3 | 13.8 | 13.8 | no | 0 | 0 | 1 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x297: context deadline exceeded |
| pgx-default | direct-1 | direct | 3500 | 21 | 0.4 | 0.9 | 1.3 | 1.3 | no | 0 | 0 | 0 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | timeout x9: context deadline exceeded |
| pgx-default | direct-2 | direct | 3500 | 26 | 0.5 | 1.0 | 1.5 | 1.5 | no | 0 | 0 | 0 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | dns x20: failed to connect to `user=app database=app`: 	hostname resolving error: lookup pg-primary on 127.0.0.11:53: no such hos |
| pgx-default | pooled-1 | pooled | 3500 | 70 | 0.3 | 2.8 | 3.1 | 3.1 | no | 0 | 0 | 0 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | timeout x54: context deadline exceeded |
| pgx-default | pooled-2 | pooled | 3500 | 335 | 0.4 | 13.4 | 13.8 | 13.8 | no | 0 | 0 | 1 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x298: context deadline exceeded |
| prisma | pooled-1 | pooled | 3500 | 25 | 0.3 | 1.0 | 1.4 | 1.3 | no | 0 | 0 | 4 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | timeout x9: client deadline 2000ms exceeded |
| prisma | pooled-2 | pooled | 3500 | 346 | 0.4 | 13.8 | 14.3 | 14.2 | no | 0 | 0 | 155 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x311: client deadline 2000ms exceeded |
| rails-activerecord | pooled-1 | pooled | 3500 | 14 | 0.3 | 0.6 | 0.9 | 0.9 | no | 0 | 0 | 2 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | ActiveRecord::ConnectionNotEstablished x7: connection to server at "192.168.64.3", port 6432 failed: Connection refused 	Is the server running on that host and acc |
| rails-activerecord | pooled-2 | pooled | 3500 | 343 | 0.5 | 13.7 | 14.2 | 14.1 | no | 0 | 0 | 42 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x332: client deadline 2000ms exceeded |
| sqlalchemy-psycopg | pooled-1 | pooled | 3500 | 79 | 0.3 | 3.1 | 3.5 | 3.4 | no | 0 | 0 | 23 | old_primary_stopped=0.76, promoted=1.13, pgbouncer_restarted=1.86 | timeout x61: client deadline 2000ms exceeded |
| sqlalchemy-psycopg | pooled-2 | pooled | 3500 | 338 | 0.4 | 13.5 | 14.0 | 13.9 | no | 0 | 0 | 153 | old_primary_stopped=0.74, promoted=1.28, pgbouncer_repointed=2.67 | timeout x308: client deadline 2000ms exceeded |

## Distinct verbatim errors per client (all runs of the round)

### drizzle-postgresjs

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 347 | `client deadline 2000ms exceeded` |
| pooled | other | 62 | `Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 18 | `Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 4 | `Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,267 \| cause: server shutting down` |
| pooled | other | 1 | `Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: server shutting down` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,268 \| cause: connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,269 \| cause: connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,270 \| cause: connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,271 \| cause: connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,272 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,273 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,274 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,275 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,276 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,277 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,278 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,305 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,306 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,307 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,308 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,309 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,310 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,311 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,312 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,313 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,314 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,315 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,316 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,317 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,318 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,319 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,320 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,321 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,322 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,323 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,324 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,325 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,326 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,327 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,328 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,329 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,330 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,331 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,332 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,333 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,334 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,335 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,336 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,337 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,338 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,339 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,340 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,341 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,342 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,343 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,344 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,345 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,346 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,347 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,348 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,349 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,350 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,351 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,352 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,353 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,354 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,355 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,356 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,357 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,358 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-1/pooled/1795289529,359 \| cause: getaddrinfo ENOTFOUND pgbouncer` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,265 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,266 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,267 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,268 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,269 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,270 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,271 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,272 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,273 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,274 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,275 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,276 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,277 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,278 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,279 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: select "id" from "ledger" order by "ledger"."id" desc limit $1 params: 1 \| cause: write CONNECTION_CLOSED pgbouncer:6432` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,280 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,281 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,282 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | other | 1 | `Failed query: insert into "ledger" ("id", "client", "seq", "ts") values (default, $1, $2, now()) params: drizzle-postgresjs/switchover/run-2/pooled/1795291309,283 \| cause: server login has been failing, cached error: the database system is shutting down (server_login_retry)` |

### node-pg

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 317 | `client deadline 2000ms exceeded` |
| pooled | pg_08P01 | 35 | `server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | ECONNREFUSED | 8 | `connect ECONNREFUSED 192.168.64.3:6432` |
| pooled | ENOTFOUND | 7 | `getaddrinfo ENOTFOUND pgbouncer` |
| pooled | pg_08P01 | 1 | `server shutting down` |

### pgx-cancelreq

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 308 | `context deadline exceeded` |
| pooled | pg_08P01 | 33 | `FATAL: server login has been failing, cached error: the database system is shutting down (server_login_retry) (SQLSTATE 08P01)` |
| pooled | net_dial | 17 | `failed to connect to `user=app database=app`: 	192.168.64.3:6432 (pgbouncer): dial error: dial tcp 192.168.64.3:6432: connect: connection refused 	192.168.64.3:6432 (pgbouncer): dial error: dial tcp 192.168.64.3:6432: connect: connection refused` |
| pooled | dns | 6 | `failed to connect to `user=app database=app`: 	hostname resolving error: lookup pgbouncer on 127.0.0.11:53: no such host 	lookup pgbouncer on 127.0.0.11:53: no such host` |
| pooled | timeout | 3 | `completed after client deadline` |
| pooled | pg_08P01 | 1 | `FATAL: server shutting down (SQLSTATE 08P01)` |
| pooled | timeout | 1 | `timeout: context already done: context deadline exceeded` |

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| direct | dns | 27 | `failed to connect to `user=app database=app`: 	hostname resolving error: lookup pg-primary on 127.0.0.11:53: no such host 	lookup pg-primary on 127.0.0.11:53: no such host` |
| direct | timeout | 9 | `context deadline exceeded` |
| direct | net_dial | 4 | `failed to connect to `user=app database=app`: 	192.168.64.2:5432 (pg-primary): dial error: dial tcp 192.168.64.2:5432: connect: connection refused 	192.168.64.2:5432 (pg-primary): dial error: dial tcp 192.168.64.2:5432: connect: connection refused` |
| direct | net_dial | 4 | `failed to connect to `user=app database=app`: 	192.168.32.2:5432 (pg-primary): dial error: dial tcp 192.168.32.2:5432: connect: connection refused 	192.168.32.2:5432 (pg-primary): dial error: dial tcp 192.168.32.2:5432: connect: connection refused` |
| direct | pg_57P01 | 2 | `FATAL: terminating connection due to administrator command (SQLSTATE 57P01)` |
| direct | dns | 1 | `failed to connect to `user=app database=app`: 	lookup pg-primary on 127.0.0.11:53: no such host 	192.168.32.2:5432 (pg-primary): tls error: server refused TLS connection` |
| pooled | timeout | 352 | `context deadline exceeded` |
| pooled | pg_08P01 | 32 | `FATAL: server login has been failing, cached error: the database system is shutting down (server_login_retry) (SQLSTATE 08P01)` |
| pooled | net_dial | 8 | `failed to connect to `user=app database=app`: 	192.168.64.3:6432 (pgbouncer): dial error: dial tcp 192.168.64.3:6432: connect: connection refused 	192.168.64.3:6432 (pgbouncer): dial error: dial tcp 192.168.64.3:6432: connect: connection refused` |
| pooled | dns | 6 | `failed to connect to `user=app database=app`: 	hostname resolving error: lookup pgbouncer on 127.0.0.11:53: no such host 	lookup pgbouncer on 127.0.0.11:53: no such host` |
| pooled | timeout | 6 | `timeout: context deadline exceeded` |
| pooled | pg_08P01 | 1 | `FATAL: server shutting down (SQLSTATE 08P01)` |

### prisma

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 320 | `client deadline 2000ms exceeded` |
| pooled | pg_P2039 | 18 | ` Invalid `prisma.ledger.create()` invocation:   Database error. Code: `08P01`. Message: `server login has been failing, cached error: the database system is shutting down (server_login_retry)`` |
| pooled | pg_P2039 | 17 | ` Invalid `prisma.ledger.findFirst()` invocation:   Database error. Code: `08P01`. Message: `server login has been failing, cached error: the database system is shutting down (server_login_retry)`` |
| pooled | pg_P1001 | 4 | ` Invalid `prisma.ledger.create()` invocation:   Can't reach database server at 192.168.64.3:6432` |
| pooled | pg_P1001 | 4 | ` Invalid `prisma.ledger.findFirst()` invocation:   Can't reach database server at 192.168.64.3:6432` |
| pooled | pg_P1001 | 4 | ` Invalid `prisma.ledger.findFirst()` invocation:   Can't reach database server at pgbouncer` |
| pooled | pg_P1001 | 3 | ` Invalid `prisma.ledger.create()` invocation:   Can't reach database server at pgbouncer` |
| pooled | pg_P2039 | 1 | ` Invalid `prisma.ledger.findFirst()` invocation:   Database error. Code: `08P01`. Message: `server shutting down`` |

### rails-activerecord

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 336 | `client deadline 2000ms exceeded` |
| pooled | ActiveRecord::ConnectionFailed | 11 | `PQconsumeInput() FATAL:  server login has been failing, cached error: the database system is shutting down (server_login_retry) server closed the connection unexpectedly 	This probably means the server terminated abnormally 	before or while processing the request.` |
| pooled | ActiveRecord::ConnectionNotEstablished | 7 | `connection to server at "192.168.64.3", port 6432 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections?` |
| pooled | ActiveRecord::DatabaseConnectionError | 3 | `There is an issue connecting with your hostname: pgbouncer.  Please check your database configuration and ensure there is a valid connection to your database.` |

### sqlalchemy-psycopg

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 369 | `client deadline 2000ms exceeded` |
| pooled | pg_08P01 | 30 | `server login has been failing, cached error: the database system is shutting down (server_login_retry)` |
| pooled | OperationalError | 9 | `connection failed: connection to server at "192.168.64.3", port 6432 failed: Connection refused 	Is the server running on that host and accepting TCP/IP connections?` |
| pooled | OperationalError | 8 | `failed to resolve host 'pgbouncer': [Errno -2] Name or service not known` |
| pooled | pg_08P01 | 1 | `server shutting down` |

