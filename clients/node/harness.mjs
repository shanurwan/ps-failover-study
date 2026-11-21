// Shared open-loop driver for the Node workloads.
// Env: CLIENT, RUN_TAG, RATE, DURATION_S, TIMEOUT_MS, OUT.
//
// The Node libraries here have no per-call cancellation in their default API,
// so the 2 s deadline belongs to the caller. At the deadline a timeout line is
// written and the operation is abandoned, as a request handler with a timeout
// would do. If the abandoned operation finishes later, a second line with op
// "late_<op>" records its real outcome. A late insert may still commit, and
// the report counts those as unacknowledged-but-present.
import fs from 'node:fs';

export function classify(err) {
  if (!err) return '';
  if (err.code && /^[0-9A-Z]{5}$/.test(err.code)) return 'pg_' + err.code;
  if (err.code) return String(err.code);
  if (err.name && err.name !== 'Error') return err.name;
  return 'other';
}

function message(err) {
  if (!err) return '';
  let m = err.message || String(err);
  if (err.cause && err.cause.message && !m.includes(err.cause.message)) m += ' | cause: ' + err.cause.message;
  return m;
}

export async function run({ insert, select, close }) {
  const client = process.env.CLIENT;
  const tag = `${client}/${process.env.RUN_TAG}`;
  const rate = Number(process.env.RATE || 50);
  const durMs = Number(process.env.DURATION_S || 90) * 1000;
  const timeout = Number(process.env.TIMEOUT_MS || 2000);
  const out = fs.createWriteStream(process.env.OUT);
  const write = (r) => out.write(JSON.stringify(r) + '\n');

  // An uncaught error from an idle pooled connection would kill the process.
  // Log it instead, so the run continues and the event is visible.
  const procErr = (kind) => (e) => write({ ts: new Date().toISOString(), ts_ms: Date.now(), client, op: kind, seq: null, ok: false, latency_ms: 0, error_class: classify(e), error_message_verbatim: message(e) });
  process.on('uncaughtException', procErr('uncaught_exception'));
  process.on('unhandledRejection', procErr('unhandled_rejection'));

  const interval = 1000 / rate;
  const start = Date.now();
  let seq = 0;
  let pending = 0;
  for (let i = 0; ; i++) {
    const sched = start + i * interval;
    if (sched - start >= durMs) break;
    const wait = sched - Date.now();
    if (wait > 0) await new Promise((r) => setTimeout(r, wait));
    const isInsert = i % 2 === 0;
    const s = isInsert ? ++seq : null;
    const op = isInsert ? 'insert' : 'select';
    const base = { ts: new Date(sched).toISOString(), ts_ms: Math.round(sched), client, op, seq: s };
    pending++;
    let settled = false;
    const timer = setTimeout(() => {
      settled = true;
      write({ ...base, ok: false, latency_ms: Date.now() - sched, error_class: 'timeout', error_message_verbatim: `client deadline ${timeout}ms exceeded` });
    }, Math.max(0, sched + timeout - Date.now()));
    let p;
    try { p = Promise.resolve(isInsert ? insert(tag, s) : select()); } catch (e) { p = Promise.reject(e); }
    p.then(() => null, (e) => e || new Error('rejected without error')).then((err) => {
      pending--;
      const latency = Date.now() - sched;
      if (settled) {
        write({ ...base, op: 'late_' + op, ok: !err, latency_ms: latency, error_class: classify(err), error_message_verbatim: message(err) });
        return;
      }
      clearTimeout(timer);
      settled = true;
      write({ ...base, ok: !err, latency_ms: latency, error_class: classify(err), error_message_verbatim: message(err) });
    });
  }
  // Give abandoned operations a moment to report late outcomes.
  const endBy = Date.now() + timeout + 3000;
  while (pending > 0 && Date.now() < endBy) await new Promise((r) => setTimeout(r, 100));
  await new Promise((r) => out.end(r));
  try { await Promise.race([close(), new Promise((r) => setTimeout(r, 2000))]); } catch {}
  process.exit(0);
}
