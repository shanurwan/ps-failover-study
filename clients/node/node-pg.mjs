// node-postgres: pg.Pool with library defaults (max 10, no connection or
// query timeout). The 'error' listener is the one line node-postgres' docs
// require; without it an error on an idle client crashes the process.
// NODE_PG_ERROR_LISTENER=0 leaves it out, to show that crash.
import pg from 'pg';
import { createRequire } from 'node:module';
import { run } from './harness.mjs';

const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL });
let idleErrors = 0;
if (process.env.NODE_PG_ERROR_LISTENER !== '0') {
  pool.on('error', (e) => { idleErrors++; console.error('pool idle client error:', e.message); });
}
const version = createRequire(import.meta.url)('pg/package.json').version;
console.error(`node-pg pg@${version} max=${pool.options.max}`);

await run({
  insert: (tag, seq) => pool.query('INSERT INTO ledger (client, seq, ts) VALUES ($1, $2, now())', [tag, seq]),
  select: () => pool.query('SELECT coalesce(max(id), 0) AS id FROM ledger'),
  close: async () => { console.error(`idle client errors: ${idleErrors}`); await pool.end(); },
});
