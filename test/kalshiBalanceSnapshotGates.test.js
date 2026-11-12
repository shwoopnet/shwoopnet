// Hourly balance snapshot (Nov 12, 2026): a read-only record of total and per-shard cash, for the bank-side check of booked results. Synthetic numbers only.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const lib = require('../functions/kalshiBalanceSnapshotLib');
const report = require('../functions/kalshiReportLib');
const crypto = require('crypto');
const gates = {};
const NOW = Date.parse('2026-11-12T14:20:00Z');
const { privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const PEM = privateKey.export({ type: 'pkcs8', format: 'pem' });
const src = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const code = (s) => s.replace(/^\s*\/\/.*$/gm, '');

const bodyOk = { balance_breakdown: [{ exchange_index: 0, balance: '10.50' }, { exchange_index: 2, balance: '20.25' }], balance: 3075, portfolio_value: '1.00' };
const world = (o = {}) => {
  const w = { calls: [], written: [], pruned: [] };
  w.fetchFn = async (url, init) => { w.calls.push({ url: String(url), method: (init && init.method) || 'GET', body: init && init.body }); if (o.throws) throw new Error('network down'); return { status: o.status || 200, text: async () => JSON.stringify(o.body || bodyOk), json: async () => o.body || bodyOk }; };
  w.run = (extra = {}) => lib.runBalanceSnapshot({ now: NOW, fetchFn: w.fetchFn, keyId: 'k', pem: PEM,
    write: async (id, doc) => { if (o.writeThrows) throw new Error('write failed'); w.written.push({ id, doc }); },
    prune: async (before, limit) => { if (o.pruneThrows) throw new Error('prune failed'); w.pruned.push({ before, limit }); }, ...extra });
  return w;
};

gates.BS1 = async () => {   // a failed read, a failed write or a failed prune never throws, and a failed read writes nothing (a gap is fine)
  for (const o of [{ throws: true }, { status: 500 }, { status: 429 }, { body: 'junk' }, { body: {} }, { writeThrows: true }, { pruneThrows: true }]) {
    const w = world(o);
    const r = await w.run({ now: Date.parse('2026-11-12T03:05:00Z') });
    assert.strictEqual(typeof r, 'string');
    if (o.throws || o.status || o.body) assert.strictEqual(w.written.length, 0, 'no snapshot from a failed read');
  }
  const w = world({ throws: true });
  assert.ok(/error|unreadable/.test(await w.run()));
  assert.doesNotThrow(() => lib.snapshotDoc(null, NOW));
  assert.strictEqual(lib.snapshotDoc({ ok: true, totalDollars: null, shards: [] }, NOW), null);
};
gates.BS2 = async () => {   // the document holds only the allowed fields: no order data, no ids, no keys
  const w = world(); await w.run();
  assert.strictEqual(w.written.length, 1);
  const d = w.written[0].doc;
  assert.deepStrictEqual(Object.keys(d).sort(), lib.ALLOWED_FIELDS.slice().sort());
  assert.deepStrictEqual(d.shards, [{ shard: 0, dollars: 10.5 }, { shard: 2, dollars: 20.25 }]);
  assert.strictEqual(d.total, 30.75);
  assert.strictEqual(d.ts, Date.parse('2026-11-12T14:00:00Z'));
  assert.ok(!/order|client|position|fill|key|pem|portfolio/i.test(JSON.stringify(d)));
  // extra junk on the input never reaches the document
  const j = lib.snapshotDoc({ ok: true, totalDollars: 5, shards: [{ shard: 1, dollars: 5, orderId: 'X', positions: [1] }], orderId: 'SECRET' }, NOW);
  assert.deepStrictEqual(Object.keys(j.shards[0]).sort(), ['dollars', 'shard']);
  assert.ok(!JSON.stringify(j).includes('SECRET'));
};
gates.BS3 = async () => {   // idempotent: the document id is the UTC hour, so two instances in one hour write the same document, and merge
  const a = world(), b = world();
  await a.run({ now: Date.parse('2026-11-12T14:01:00Z') }); await b.run({ now: Date.parse('2026-11-12T14:59:59Z') });
  assert.strictEqual(a.written[0].id, '2026-11-12T14'); assert.strictEqual(a.written[0].id, b.written[0].id);
  assert.notStrictEqual(lib.hourId(Date.parse('2026-11-12T15:00:00Z')), '2026-11-12T14');
  const idx = code(src('functions/index.js'));
  const fn = idx.slice(idx.indexOf('exports.kalshiBalanceSnapshot = onSchedule('), idx.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/col\.doc\(id\)\.set\(doc, \{ merge: true \}\)/.test(fn), 'set with merge on the hour id');
};
gates.BS4 = async () => {   // retention: 90 days, once a day, bounded, and a failed read does not stop it
  assert.strictEqual(lib.RETENTION_DAYS, 90);
  const at3 = Date.parse('2026-11-12T03:30:00Z');
  const w = world({ throws: true }); await w.run({ now: at3 });
  assert.deepStrictEqual(w.pruned, [{ before: at3 - 90 * 86400000, limit: lib.PRUNE_BATCH }]);
  assert.ok(lib.PRUNE_BATCH > 0 && lib.PRUNE_BATCH <= 500);
  const other = world(); await other.run({ now: NOW }); assert.strictEqual(other.pruned.length, 0, 'not on the other 23 runs');
  const idx = code(src('functions/index.js'));
  const fn = idx.slice(idx.indexOf('exports.kalshiBalanceSnapshot = onSchedule('), idx.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/\.where\("ts", "<", beforeMs\)\.limit\(limit\)/.test(fn), 'the delete query is bounded');
};
gates.BS5 = async () => {   // GET only, one request, only the balance path; no order code anywhere in the snapshot path
  const w = world(); await w.run();
  assert.strictEqual(w.calls.length, 1);
  assert.strictEqual(w.calls[0].method, 'GET');
  assert.ok(/\/portfolio\/balance$/.test(w.calls[0].url.split('?')[0]));
  assert.ok(!w.calls[0].body);
  const l = code(src('functions/kalshiBalanceSnapshotLib.js'));
  assert.ok(!/POST|PUT|DELETE|PATCH|\/orders|placeOrder|sellOrder|createOrder/.test(l), 'no write verb or order path in the library');
  assert.ok(/method: "GET"/.test(l));
  const idx = code(src('functions/index.js'));
  const fn = idx.slice(idx.indexOf('exports.kalshiBalanceSnapshot = onSchedule('), idx.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/secrets: \[KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(fn) && !/KALSHI_REPORT_TOKEN|VAPID/.test(fn), 'only the two secrets the account read already uses');
  assert.ok(!/kalshiLiveOrders|kalshiLiveControl|runL1Tick|runExitWatch/.test(fn), 'it touches no order, session or control data');
};
gates.BS6 = () => {   // rules: admin read, no client write
  const rules = src('firestore.rules');
  const m = /match \/kalshiBalanceSnaps\/\{id\} \{([\s\S]*?)\n    \}/.exec(rules);
  assert.ok(m, 'a rule block exists');
  assert.ok(/allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]));
};
gates.BS7 = async () => {   // the report: section present, bounded, whitelisted, empty history is an empty list; token rules unchanged
  const TOKEN = 'a'.repeat(32);
  const call = async (readBalances, req = {}) => {
    const out = { code: null, body: null };
    const res = { set() {}, status: (c) => { out.code = c; return res; }, json: (b) => { out.body = b; } };
    await report.makeReportHandler({ getToken: () => TOKEN, now: () => NOW, readOrders: async () => [], readBalances })(Object.assign({ method: 'GET', headers: { authorization: 'Bearer ' + TOKEN }, query: {} }, req), res);
    return out;
  };
  assert.deepStrictEqual((await call(async () => [])).body.balanceHistory, { count: 0, rows: [] }, 'empty history is an empty list');
  const docs = [{ ts: NOW - 7200000, at: NOW, total: 30.75, shards: [{ shard: 0, dollars: 10.5, orderId: 'LEAK' }], orderId: 'LEAK2' }, { ts: NOW - 3600000, total: 31, shards: [] }, { ts: 'bad', total: 1 }];
  const r = (await call(async () => docs)).body.balanceHistory;
  assert.strictEqual(r.count, 2);
  assert.deepStrictEqual(Object.keys(r.rows[0]).sort(), ['shards', 'total', 'ts']);
  assert.deepStrictEqual(r.rows[0].shards, [{ shard: 0, dollars: 10.5 }]);
  assert.ok(!JSON.stringify(r).includes('LEAK'));
  assert.ok(r.rows[0].ts < r.rows[1].ts, 'oldest first');
  const many = Array.from({ length: report.MAX_BALANCE_ROWS + 50 }, (_, i) => ({ ts: NOW - (i + 1) * 60000, total: 1, shards: [] }));
  assert.strictEqual(report.balanceSection(many).count, report.MAX_BALANCE_ROWS, 'bounded');
  const bad = await call(async () => { throw new Error('x'); });
  assert.strictEqual(bad.code, 200); assert.strictEqual(bad.body.balanceHistory, undefined, 'a failed read leaves the field out, the report stands');
  assert.strictEqual((await call(async () => [], { headers: {} })).code, 401, 'token rules unchanged');
  const asked = []; await call(async (since) => { asked.push(since); return []; }, { query: { hours: '48' } });
  assert.strictEqual(asked[0], NOW - 48 * 3600000, 'the asked window');
  const idx = src('functions/index.js');
  const rep = idx.slice(idx.indexOf('exports.kalshiNightlyReport'));
  assert.ok(/readBalances: async \(sinceMs\) => \{[^}]*kalshiBalanceSnapshotLib|readBalances: async \(sinceMs\) => \{ ensureDefaultAdminApp\(\); return \(await getFirestore\(\)\.collection\(balanceSnap\.COLLECTION\)\.where/.test(rep), 'the report only reads the collection');
};
gates.BS8 = () => {   // deploy and page text: the sizing deploy carries the function; the changelog and CLAUDE.md say so; no live figures
  assert.ok(/functions:kalshiBalanceSnapshot/.test(src('functions/deploy-sizing.sh')));
  assert.ok(/Hourly balance snapshot/.test(src('CLAUDE.md')));
  assert.ok(/balance snapshot/i.test(src('index.html')));
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
