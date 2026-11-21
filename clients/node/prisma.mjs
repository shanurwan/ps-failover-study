// Prisma ORM 7 with the pg driver adapter, which Prisma 7 requires
// (new PrismaClient({ adapter })). Pool settings are adapter-pg's defaults.
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from './generated/prisma/client.ts';
import { run } from './harness.mjs';

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

await run({
  insert: (tag, seq) => prisma.ledger.create({ data: { client: tag, seq: BigInt(seq) }, select: { id: true } }),
  select: () => prisma.ledger.findFirst({ orderBy: { id: 'desc' }, select: { id: true } }),
  close: () => prisma.$disconnect(),
});
