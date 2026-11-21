// Drizzle ORM on postgres-js with library defaults (postgres() defaults:
// max 10, prepare: true). POSTGRES_JS_PREPARE=false sets prepare: false.
import postgres from 'postgres';
import { drizzle } from 'drizzle-orm/postgres-js';
import { pgTable, bigserial, bigint, text, timestamp } from 'drizzle-orm/pg-core';
import { desc, sql as dsql } from 'drizzle-orm';
import { run } from './harness.mjs';

const ledger = pgTable('ledger', {
  id: bigserial('id', { mode: 'number' }).primaryKey(),
  client: text('client').notNull(),
  seq: bigint('seq', { mode: 'number' }).notNull(),
  ts: timestamp('ts', { withTimezone: true }).notNull().defaultNow(),
});

const opts = {};
if (process.env.POSTGRES_JS_PREPARE === 'false') opts.prepare = false;
const client = postgres(process.env.DATABASE_URL, opts);
const db = drizzle(client);
console.error(`drizzle-postgresjs prepare=${client.options.prepare} max=${client.options.max}`);

await run({
  insert: (tag, seq) => db.insert(ledger).values({ client: tag, seq, ts: dsql`now()` }),
  select: () => db.select({ id: ledger.id }).from(ledger).orderBy(desc(ledger.id)).limit(1),
  close: () => client.end({ timeout: 1 }),
});
