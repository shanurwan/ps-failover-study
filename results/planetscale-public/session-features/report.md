# Round `session-features`

psycopg 3.3.9, autocommit, two client connections A and B. `busy` = 8 extra connections running short queries. Counts are out of 10 repetitions.

## set_session

| endpoint-mode | observed |
|---|---|
| direct-quiet | A kept statement_timeout 10/10, search_path 10/10, application_name 10/10; B saw A's statement_timeout 0/10, search_path 0/10, application_name 0/10; A used 1 backend(s) |
| direct-busy | A kept statement_timeout 10/10, search_path 10/10, application_name 10/10; B saw A's statement_timeout 0/10, search_path 0/10, application_name 0/10; A used 1 backend(s) |
| pooled-quiet | A kept statement_timeout 10/10, search_path 10/10, application_name 10/10; B saw A's statement_timeout 10/10, search_path 0/10, application_name 0/10; A used 1 backend(s) |
| pooled-busy | A kept statement_timeout 2/10, search_path 10/10, application_name 10/10; B saw A's statement_timeout 1/10, search_path 0/10, application_name 0/10; A used 6 backend(s) |

## advisory_lock

| endpoint-mode | observed |
|---|---|
| direct-quiet | A lock: ok ; B got the lock while A held it 0/10; A unlock: ok True; B lock after A's unlock: ok True; advisory locks still held at the end: ok 0; notices A: none |
| direct-busy | A lock: ok ; B got the lock while A held it 0/10; A unlock: ok True; B lock after A's unlock: ok True; advisory locks still held at the end: ok 0; notices A: none |
| pooled-quiet | A lock: ok ; B got the lock while A held it 10/10; A unlock: ok True; B lock after A's unlock: ok True; advisory locks still held at the end: ok 0; notices A: none |
| pooled-busy | A lock: ok ; B got the lock while A held it 1/10; A unlock: ok False; B lock after A's unlock: ok False; advisory locks still held at the end: ok 1; notices A: WARNING: you don't own a lock of type ExclusiveLock |

## listen_notify

| endpoint-mode | observed |
|---|---|
| direct-quiet | LISTEN: ok ; A received 3/3 notifications |
| direct-busy | LISTEN: ok ; A received 3/3 notifications |
| pooled-quiet | LISTEN: ok ; A received 0/3 notifications |
| pooled-busy | LISTEN: ok ; A received 0/3 notifications |

## temp_table

| endpoint-mode | observed |
|---|---|
| direct-quiet | create: ok ; A insert failed 0/10 ; A count(*) results: 10,10,10,10,10,10,10,10,10,10; B create same name: ok  |
| direct-busy | create: ok ; A insert failed 0/10 ; A count(*) results: 10,10,10,10,10,10,10,10,10,10; B create same name: ok  |
| pooled-quiet | create: ok ; A insert failed 0/10 ; A count(*) results: 10,10,10,10,10,10,10,10,10,10; B create same name: ERROR 42P07: relation "sf_tmp" already exists |
| pooled-busy | create: ok ; A insert failed 8/10 (relation "sf_tmp" does not exist); A count(*) results: 2,2,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist,relation "sf_tmp" does not exist at character 22,2; B create same name: ok  |

## sql_prepare

| endpoint-mode | observed |
|---|---|
| direct-quiet | PREPARE: ok ; EXECUTE failed 0/10 ; B PREPARE same name: ok  |
| direct-busy | PREPARE: ok ; EXECUTE failed 0/10 ; B PREPARE same name: ok  |
| pooled-quiet | PREPARE: ok ; EXECUTE failed 0/10 ; B PREPARE same name: ERROR 42P05: prepared statement "sf_stmt" already exists |
| pooled-busy | PREPARE: ERROR 42P05: prepared statement "sf_stmt" already exists; EXECUTE failed 6/10 prepared statement "sf_stmt" does not exist; B PREPARE same name: ok  |

## protocol_prepare

| endpoint-mode | observed |
|---|---|
| direct-quiet | ok 10/10  |
| direct-busy | ok 10/10  |
| pooled-quiet | ok 10/10  |
| pooled-busy | ok 10/10  |

