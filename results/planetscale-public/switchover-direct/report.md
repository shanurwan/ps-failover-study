# Round `switchover-direct`

Times are seconds from the event start (switchover command started). One row per run.

| client | run | endpoint | requests | errors | first error | error window | recovered | last error | never recovered | acked-but-missing | duplicates | unacked-but-present | switchover steps (s) | top error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pgx-default | direct-1 | direct | 7000 | 80 | 17.1 | 1.8 | 18.9 | 18.9 | no | 0 | 0 | 13 | ps created_at=4.21, ps started_at=4.28, ps completed_at=44.88 | timeout x58: context deadline exceeded |
| pgx-default | direct-2 | direct | 7000 | 81 | 12.7 | 1.8 | 14.5 | 14.5 | no | 0 | 0 | 12 | ps created_at=4.35, ps started_at=4.63, ps completed_at=38.65 | timeout x61: context deadline exceeded |

## Distinct verbatim errors per client (all runs of the round)

### pgx-default

| endpoint | class | count | verbatim message |
|---|---|---|---|
| direct | timeout | 119 | `context deadline exceeded` |
| direct | timeout | 32 | `timeout: context deadline exceeded` |
| direct | pg_57P01 | 2 | `FATAL: terminating connection due to administrator command (SQLSTATE 57P01)` |
| direct | pg_57P03 | 2 | `failed to connect to `user=<role> database=postgres`: 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.` |
| direct | pg_57P03 | 2 | `failed to connect to `user=<role> database=postgres`: 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.` |
| direct | pg_57P03 | 1 | `failed to connect to `user=<role> database=postgres`: 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.` |
| direct | pg_57P03 | 1 | `failed to connect to `user=<role> database=postgres`: 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.` |
| direct | pg_57P03 | 1 | `failed to connect to `user=<role> database=postgres`: 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.cloud): server error: FATAL: the database system is shutting down (SQLSTATE 57P03) 	<ip>:5432 (aws-ap-southeast-1-2.pg.psdb.` |
| direct | timeout | 1 | `timeout: context already done: context deadline exceeded` |

