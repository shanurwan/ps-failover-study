-- Records the target's relevant settings (scripts/study target-info).
select version();
select current_user, current_database(), inet_server_port(), pg_is_in_recovery();
select rolname, rolsuper, rolreplication from pg_roles where rolname = current_user;
select name, setting from pg_settings
 where name in ('max_connections', 'wal_level', 'max_replication_slots', 'max_wal_senders',
                'sync_replication_slots', 'hot_standby_feedback', 'synchronized_standby_slots',
                'synchronous_standby_names', 'synchronous_commit', 'idle_session_timeout',
                'idle_in_transaction_session_timeout', 'statement_timeout', 'lock_timeout',
                'tcp_keepalives_idle', 'server_version')
    or name like '%slot_sync%'
 order by name;
select slot_name, slot_type, failover, synced, active from pg_replication_slots order by 1;
