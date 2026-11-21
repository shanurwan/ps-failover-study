# Round `lock-storm`

Times are seconds from the event start (lock acquired). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | new sessions/s max (lock / after / last 20 s mean) | lock waiters max | PgBouncer 'client disconnect while server was not ready' | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pgx-cancelreq | pooled-1 | pooled | 5500 | 1413 | 0.3 | 30.1 | 30.4 | 30.4 | no | 0 | 0 | 0 | 24.0 / 1.0 / 0.9 | 12 | 609 | pg_57014 x803: ERROR: canceling statement due to user request (SQLSTATE 57014) |
| pgx-cancelreq | r150-pool40-pooled-1 | pooled | 16501 | 4209 | 0.2 | 28.1 | 28.3 | 28.3 | no | 0 | 0 | 0 | 54.2 / 1.0 / 0.9 | 20 | 173 | timeout x2722: context deadline exceeded |
| pgx-default | pooled-1 | pooled | 5500 | 1402 | 0.4 | 28.0 | 28.4 | 28.4 | no | 0 | 0 | 0 | 11.6 / 1.0 / 0.9 | 12 | 0 | timeout x1402: timeout: context deadline exceeded |
| pgx-default | r150-pool40-pooled-1 | pooled | 16501 | 5264 | 0.4 | 35.1 | 35.5 | 35.4 | no | 0 | 0 | 0 | 42.1 / 8.4 / 0.9 | 95 | 101 | pg_08P01 x4768: FATAL: server login has been failing, cached error: remaining connection slots are reserved for roles with the SUPERUSER |

## Distinct verbatim errors per client (all runs of the round)

### pgx-cancelreq

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 2722 | `context deadline exceeded` |
| pooled | pg_57014 | 1107 | `ERROR: canceling statement due to user request (SQLSTATE 57014)` |
| pooled | timeout | 949 | `timeout: context deadline exceeded` |
| pooled | pg_08P01 | 781 | `FATAL: prepared statement name is already in use (SQLSTATE 08P01)` |
| pooled | timeout | 45 | `timeout: context already done: context deadline exceeded` |
| pooled | pg_57014 | 17 | `prepare failed after ParseComplete: ERROR: canceling statement due to user request (SQLSTATE 57014)` |
| pooled | timeout | 1 | `completed after client deadline` |

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | pg_08P01 | 4768 | `FATAL: server login has been failing, cached error: remaining connection slots are reserved for roles with the SUPERUSER attribute (se (SQLSTATE 08P01)` |
| pooled | timeout | 1782 | `timeout: context deadline exceeded` |
| pooled | timeout | 116 | `context deadline exceeded` |

