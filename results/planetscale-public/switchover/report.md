# Round `switchover`

Times are seconds from the event start (switchover command started). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | switchover steps (s) | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drizzle-postgresjs | pooled-1 | pooled | 3920 | 78 | 16.1 | 2.8 | 19.0 | 19.0 | no | 0 | 0 | 40 | ps created_at=6.22, ps completed_at=77.87 | timeout x78: client deadline 2000ms exceeded |
| drizzle-postgresjs | pooled-2 | pooled | 3920 | 79 | 11.2 | 2.9 | 14.1 | 14.1 | no | 0 | 0 | 39 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x79: client deadline 2000ms exceeded |
| node-pg | pooled-1 | pooled | 3920 | 95 | 1.9 | 17.4 | 19.3 | 19.3 | no | 0 | 0 | 48 | ps created_at=6.22, ps completed_at=77.87 | timeout x95: client deadline 2000ms exceeded |
| node-pg | pooled-2 | pooled | 3920 | 93 | 11.2 | 3.3 | 14.5 | 14.4 | no | 0 | 0 | 46 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x93: client deadline 2000ms exceeded |
| pgx-cancelreq | pooled-1 | pooled | 3921 | 81 | 16.1 | 2.9 | 19.0 | 19.0 | no | 0 | 0 | 0 | ps created_at=6.22, ps completed_at=77.87 | timeout x71: context deadline exceeded |
| pgx-cancelreq | pooled-2 | pooled | 3921 | 81 | 11.1 | 2.9 | 14.0 | 14.0 | no | 0 | 0 | 3 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x65: context deadline exceeded |
| pgx-default | pooled-1 | pooled | 3921 | 86 | 2.2 | 16.9 | 19.2 | 19.1 | no | 0 | 0 | 2 | ps created_at=6.22, ps completed_at=77.87 | timeout x74: context deadline exceeded |
| pgx-default | pooled-2 | pooled | 3921 | 86 | 11.2 | 3.0 | 14.2 | 14.2 | no | 0 | 0 | 1 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x72: context deadline exceeded |
| prisma | pooled-1 | pooled | 3920 | 97 | 1.8 | 17.4 | 19.3 | 19.3 | no | 0 | 0 | 48 | ps created_at=6.22, ps completed_at=77.87 | timeout x97: client deadline 2000ms exceeded |
| prisma | pooled-2 | pooled | 3920 | 94 | 11.1 | 3.3 | 14.5 | 14.5 | no | 0 | 0 | 47 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x94: client deadline 2000ms exceeded |
| rails-activerecord | pooled-1 | pooled | 3920 | 103 | 16.1 | 3.6 | 19.8 | 19.8 | no | 0 | 0 | 52 | ps created_at=6.22, ps completed_at=77.87 | timeout x103: client deadline 2000ms exceeded |
| rails-activerecord | pooled-2 | pooled | 3920 | 110 | 11.1 | 3.9 | 15.1 | 15.0 | no | 0 | 0 | 55 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x110: client deadline 2000ms exceeded |
| sqlalchemy-psycopg | pooled-1 | pooled | 3920 | 94 | 2.2 | 17.0 | 19.3 | 100.1 | no | 0 | 0 | 46 | ps created_at=6.22, ps completed_at=77.87 | timeout x94: client deadline 2000ms exceeded |
| sqlalchemy-psycopg | pooled-2 | pooled | 3920 | 93 | 11.1 | 3.3 | 14.5 | 14.4 | no | 0 | 0 | 46 | ps created_at=4.28, ps started_at=4.34, ps completed_at=34.21 | timeout x93: client deadline 2000ms exceeded |

## Distinct verbatim errors per client (all runs of the round)

### drizzle-postgresjs

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 157 | `client deadline 2000ms exceeded` |

### node-pg

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 188 | `client deadline 2000ms exceeded` |

### pgx-cancelreq

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 136 | `context deadline exceeded` |
| pooled | timeout | 17 | `timeout: context already done: context deadline exceeded` |
| pooled | timeout | 5 | `completed after client deadline` |
| pooled | timeout | 4 | `timeout: context deadline exceeded` |

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 146 | `context deadline exceeded` |
| pooled | timeout | 26 | `timeout: context deadline exceeded` |

### prisma

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 191 | `client deadline 2000ms exceeded` |

### rails-activerecord

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 213 | `client deadline 2000ms exceeded` |

### sqlalchemy-psycopg

| endpoint | class | count | verbatim message |
|---|---|---|---|
| pooled | timeout | 187 | `client deadline 2000ms exceeded` |

