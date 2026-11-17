const assert = require('assert');
const lib = require('../functions/kalshiReportLib');
const NOW = Date.parse('2026-11-17T12:00:00Z');
const H = 3600000;
const iso = (ms) => new Date(ms).toISOString();
const row = (hoursAgo, total, perpsTotal) => ({ ts: iso(NOW - hoursAgo * H), total, shards: [], ...(perpsTotal === undefined ? {} : { perpsTotal }) });
const fresh = (over = {}) => ({ at: NOW - 60000, equity: 600, maintenance: 120, count: 1, ...over });

// RA1: the total is the latest hourly prediction balance plus a FRESH perps equity; the cushion is equity minus maintenance
let a = lib.accountSection([row(2, 200), row(0.5, 210, 600)], fresh(), NOW);
assert.strictEqual(a.predictions, 210); assert.strictEqual(a.perpsEquity, 600); assert.strictEqual(a.total, 810); assert.strictEqual(a.totalIncludesPerps, true);
assert.deepStrictEqual(a.cushion, { dollars: 480, pct: 80 });

// RA2: a stale, future dated or missing perps document never enters the total (predictions only, said plainly)
for (const bad of [fresh({ at: NOW - 21 * 60000 }), fresh({ at: NOW + 5 * 60000 }), fresh({ equity: null }), fresh({ equity: 'x' }), null, undefined]) {
  a = lib.accountSection([row(0.5, 210, 600)], bad, NOW);
  assert.strictEqual(a.total, 210, 'predictions only'); assert.strictEqual(a.perpsFresh, false); assert.strictEqual(a.totalIncludesPerps, false); assert.strictEqual(a.perpsEquity, null); assert.strictEqual(a.cushion, null);
}
// exactly 20 minutes old is still fresh (the same line the OICORE base uses)
assert.strictEqual(lib.accountSection([row(0.5, 210)], fresh({ at: NOW - 20 * 60000 }), NOW).perpsFresh, true);

// RA3: with no prediction snapshot there is no total (never a perps only figure)
a = lib.accountSection([], fresh(), NOW);
assert.strictEqual(a.total, null); assert.strictEqual(a.predictions, null); assert.strictEqual(a.day, null);

// RA4: the day change compares the newest snapshot with the oldest inside 24 hours; the perps part needs both to carry a perps total
a = lib.accountSection([row(30, 100, 500), row(20, 190, 550), row(1, 200, 580)], fresh(), NOW);
assert.deepStrictEqual(a.day, { from: iso(NOW - 20 * H), to: iso(NOW - 1 * H), predictions: 10, perps: 30, total: 40, includesPerps: true, note: 'balance change, includes any deposit or withdrawal' });
a = lib.accountSection([row(20, 190), row(1, 200, 580)], fresh(), NOW);
assert.strictEqual(a.day.perps, null); assert.strictEqual(a.day.includesPerps, false); assert.strictEqual(a.day.total, 10, 'no perps history before the first snapshot that carries it, nothing invented');
assert.strictEqual(lib.accountSection([row(1, 200, 580)], fresh(), NOW).day, null, 'one snapshot is no change');

// RA5: balance history rows carry accountTotal only when both parts exist
const bs = lib.balanceSection([{ ts: NOW - H, total: 200, perpsTotal: 580.5 }, { ts: NOW - 2 * H, total: 190 }]);
assert.strictEqual(bs.rows[1].accountTotal, 780.5); assert.strictEqual(bs.rows[0].accountTotal, undefined);

// RA6: through the real handler: the field is added after the perps section and a failing balance read leaves it out; the report stands
(async () => {
  const mk = (deps) => lib.makeReportHandler(Object.assign({ getToken: () => 'x'.repeat(30), now: () => NOW, readOrders: async () => [] }, deps));
  const call = async (deps) => { let code, body; const res = { set() {}, status(c) { code = c; return this; }, json(b) { body = b; } }; await mk(deps)({ method: 'GET', headers: { authorization: 'Bearer ' + 'x'.repeat(30) }, query: {} }, res); return { code, body }; };
  let r = await call({ readBalances: async () => [{ ts: NOW - H, total: 210, perpsTotal: 600 }], readPerpsAccount: async () => fresh() });
  assert.strictEqual(r.code, 200); assert.strictEqual(r.body.account.total, 810); assert.strictEqual(r.body.account.cushion.pct, 80);
  r = await call({ readBalances: async () => { throw new Error('x'); } });
  assert.strictEqual(r.code, 200); assert.strictEqual(r.body.account, undefined, 'no balance history, no account section');
  r = await call({ readBalances: async () => [{ ts: NOW - H, total: 210 }] });
  assert.strictEqual(r.body.account.total, 210); assert.strictEqual(r.body.account.perpsFresh, false);

  // RA7: read only and display only: the report library holds no key, order or write, and nothing that decides a trade names the new field
  const fs = require('fs');
  const src = fs.readFileSync(__dirname + '/../functions/kalshiReportLib.js', 'utf8').split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');
  assert(!/liveRequest|\.add\(|\.delete\(|getFirestore|POST|signature/i.test(src), 'RA7 the report stays read only');
  console.log('reportAccountGates ok');
})().catch((e) => { console.error(e); process.exit(1); });
