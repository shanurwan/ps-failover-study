# Round `switchover`

Times are seconds from the event start (switchover command started). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | switchover steps (s) | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pgx-cancelreq | pooled-1 | pooled | 7000 | 653 | 0.2 | 13.0 | 13.3 | 13.3 | no | 0 | 0 | 0 | old_primary_stopped=0.52, promoted=1.0, pgbouncer_repointed=1.56 | timeout x594: context deadline exceeded |
| pgx-default | direct-1 | direct | 7000 | 47 | 0.3 | 0.9 | 1.3 | 1.3 | no | 0 | 0 | 0 | old_primary_stopped=0.63, promoted=1.17, pgbouncer_repointed=1.73 | dns x36: failed to connect to `user=app database=app`: 	hostname resolving error: lookup pg-primary on 127.0.0.11:53: no such hos |
| pgx-default | pooled-1 | pooled | 7000 | 662 | 0.3 | 13.2 | 13.6 | 13.5 | no | 0 | 0 | 1 | old_primary_stopped=0.58, promoted=1.09, pgbouncer_repointed=1.59 | timeout x601: context deadline exceeded |

## Distinct verbatim errors per client (all runs of the round)

### pgx-cancelreq

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 594 | `context deadline exceeded` |
| pooled | pg_08P01 | 58 | `FATAL: server login has been failing, cached error: the database system is shutting down (server_login_retry) (SQLSTATE 08P01)` |
| pooled | timeout | 1 | `timeout: context deadline exceeded` |

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| direct | dns | 36 | `failed to connect to `user=app database=app`: 	hostname resolving error: lookup pg-primary on 127.0.0.11:53: no such host 	lookup pg-primary on 127.0.0.11:53: no such host` |
| direct | net_dial | 7 | `failed to connect to `user=app database=app`: 	192.168.64.2:5432 (pg-primary): dial error: dial tcp 192.168.64.2:5432: connect: connection refused 	192.168.64.2:5432 (pg-primary): dial error: dial tcp 192.168.64.2:5432: connect: connection refused` |
| direct | pg_57P03 | 2 | `failed to connect to `user=app database=app`: 	192.168.64.2:5432 (pg-primary): tls error: server refused TLS connection 	192.168.64.2:5432 (pg-primary): server error: FATAL: the database system is shutting down (SQLSTATE 57P03)` |
| direct | pg_57P01 | 1 | `FATAL: terminating connection due to administrator command (SQLSTATE 57P01)` |
| direct | timeout | 1 | `context deadline exceeded` |
| pooled | timeout | 601 | `context deadline exceeded` |
| pooled | pg_08P01 | 56 | `FATAL: server login has been failing, cached error: the database system is shutting down (server_login_retry) (SQLSTATE 08P01)` |
| pooled | timeout | 4 | `timeout: context deadline exceeded` |
| pooled | timeout | 1 | `completed after client deadline` |

