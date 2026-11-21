# Round `lock-storm`

Times are seconds from the event start (lock acquired). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | new sessions/s max (lock / after / last 20 s mean) | lock waiters max | PgBouncer 'client disconnect while server was not ready' | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pgx-cancelreq | pooled-1 | pooled | 5500 | 1493 | 1.9 | 29.8 | 31.7 | 31.7 | no | 0 | 0 | 4 | 7.4 / 0.9 / 0.0 | 12 | - | timeout x1019: context deadline exceeded |
| pgx-default | pooled-1 | pooled | 5500 | 1735 | 0.6 | 34.7 | 35.3 | 35.3 | no | 0 | 0 | 4 | 3.4 / 2.6 / 0.0 | 16 | - | timeout x1234: context deadline exceeded |

## Distinct verbatim errors per client (all runs of the round)

### pgx-cancelreq

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 1019 | `context deadline exceeded` |
| pooled | pg_08P01 | 447 | `FATAL: server login has been failing, cached error: remaining connection slots are reserved for roles with the SUPERUSER attribute (se (SQLSTATE 08P01)` |
| pooled | timeout | 25 | `timeout: context deadline exceeded` |
| pooled | timeout | 1 | `timeout: context already done: context deadline exceeded` |
| pooled | timeout | 1 | `completed after client deadline` |

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 1234 | `context deadline exceeded` |
| pooled | pg_08P01 | 478 | `FATAL: server login has been failing, cached error: remaining connection slots are reserved for roles with the SUPERUSER attribute (se (SQLSTATE 08P01)` |
| pooled | timeout | 23 | `timeout: context deadline exceeded` |

