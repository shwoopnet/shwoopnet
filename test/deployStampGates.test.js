'use strict';
// DS1 to DS6: the deploy stamp (the owner, Oct 31, 2026: "deploy check that proves the latest merge is live").
// Consequence: after any deploy the nightly report says which commit each function was deployed from, so "is the latest merge running" is a read; and the stamp can never affect an order, write in a test, or take a function down.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const lib = require('../functions/deployStampLib.js');
const report = require('../functions/kalshiReportLib.js');
const gates = {};
const COMMIT = 'a'.repeat(40);

gates.DS1 = () => {
  assert.deepStrictEqual(lib.readStamp(() => JSON.stringify({ commit: COMMIT, at: '2026-10-31T01:00:00Z' })), { commit: COMMIT, at: '2026-10-31T01:00:00Z' });
  assert.strictEqual(lib.readStamp(() => { throw new Error('ENOENT'); }), null, 'no file: no stamp, never an error');
  assert.strictEqual(lib.readStamp(() => 'not json'), null);
  assert.strictEqual(lib.readStamp(() => JSON.stringify({ commit: 'unknown' })), null, 'the script writes "unknown" outside git: shown as no stamp, not as a commit');
  assert.strictEqual(lib.readStamp(() => JSON.stringify({ commit: '<script>' })), null);
};
gates.DS2 = async () => {
  const writes = []; const db = { collection: (c) => ({ doc: (d) => ({ set: async (v, o) => { writes.push({ c, d, v, o }); } }) }) };
  assert.strictEqual(await lib.recordBoot({ db, env: {} }), false, 'outside Cloud Run (no K_SERVICE) nothing is written: no test or local run ever writes');
  assert.strictEqual(writes.length, 0);
  assert.strictEqual(await lib.recordBoot({ db, env: { K_SERVICE: 'KalshiLiveExit' }, stamp: { commit: COMMIT, at: 'x' }, nowMs: 5 }), false, 'a service name with capitals is not what Cloud Run gives: refused');
  const ok = await lib.recordBoot({ db, env: { K_SERVICE: 'kalshilivearmed' }, stamp: { commit: COMMIT, at: '2026-10-31T01:00:00Z' }, nowMs: 5 });
  assert.strictEqual(ok, true); assert.deepStrictEqual(writes[0], { c: 'kalshiDeploys', d: 'kalshilivearmed', v: { service: 'kalshilivearmed', commit: COMMIT, stampedAt: '2026-10-31T01:00:00Z', bootAt: 5 }, o: { merge: true } });
  const bad = { collection: () => ({ doc: () => ({ set: async () => { throw new Error('boom'); } }) }) };
  assert.strictEqual(await lib.recordBoot({ db: bad, env: { K_SERVICE: 'x1' }, stamp: null, nowMs: 1 }), false, 'a failed write is swallowed');
};
gates.DS3 = () => {
  const s = lib.summarize([{ service: 'b', commit: COMMIT, bootAt: 1 }, { service: 'a', commit: COMMIT, stampedAt: 't', bootAt: 9 }, { commit: 'x' }, null]);
  assert.deepStrictEqual(s.map((x) => x.service), ['a', 'b'], 'newest boot first, rows without a service dropped');
  assert.ok(!/orderId|secret|token/i.test(JSON.stringify(s)));
};
gates.DS4 = async () => {
  const run = async (deps) => { let body; const res = { set() {}, status() { return this; }, json(b) { body = b; } };
    await report.makeReportHandler({ getToken: () => 'x'.repeat(30), now: () => 1793400000000, readOrders: async () => [], ...deps })({ method: 'GET', headers: { authorization: 'Bearer ' + 'x'.repeat(30) }, query: {} }, res); return body; };
  const withD = await run({ readDeploys: async () => [{ service: 'kalshilivearmed', commit: COMMIT, bootAt: 7 }] });
  assert.deepStrictEqual(withD.deploys, [{ service: 'kalshilivearmed', commit: COMMIT, stampedAt: null, bootAt: 7 }], 'the report carries the stamps');
  const failed = await run({ readDeploys: async () => { throw new Error('boom'); } });
  assert.ok(!('deploys' in failed) && failed.total, 'a failed stamp read leaves the field out and the report intact');
  assert.ok(!('deploys' in (await run({}))), 'no reader, no field (every older caller is unchanged)');
};
gates.DS5 = () => {
  for (const f of ['deploy-push.sh', 'deploy-sizing.sh', 'deploy-report.sh']) {
    const s = fs.readFileSync(path.join(root, 'functions', f), 'utf8');
    assert.ok(/functions\/deploy-stamp\.json/.test(s) && s.indexOf('deploy-stamp.json') < s.indexOf('deploy --only'), f + ' writes the stamp before it deploys');
    assert.ok(/DRY_RUN:-\}" = "1" \]; then echo "\[dry run\] write functions\/deploy-stamp\.json"/.test(s), f + ': a dry run writes nothing');
  }
  assert.ok(/functions\/deploy-stamp\.json/.test(fs.readFileSync(path.join(root, '.gitignore'), 'utf8')), 'the per machine stamp is never committed');
};
gates.DS6 = () => {
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(/if \(deployStamp\.serviceName\(\)\) \{\s*try \{ ensureDefaultAdminApp\(\); deployStamp\.recordBoot\(\{ db: getFirestore\(\) \}\)\.catch\(\(\) => \{\}\); \} catch/.test(idx), 'the boot write is guarded by K_SERVICE, never throws and is not awaited');
  assert.ok(/readDeploys: async \(\) => \{ ensureDefaultAdminApp\(\); return \(await getFirestore\(\)\.collection\(deployStamp\.COLLECTION\)\.get\(\)\)/.test(idx), 'the report only reads the stamps');
  for (const f of fs.readdirSync(path.join(root, 'functions')).filter((x) => /^kalshi(Live|Slot|Signal)[A-Za-z]*Lib\.js$/.test(x))) assert.ok(!/deployStamp/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f + ' (order code) never imports the stamp');
};
(async () => { let failed = 0; for (const [n, fn] of Object.entries(gates)) { try { await fn(); console.log('ok   ' + n); } catch (e) { failed++; console.log('FAIL ' + n + ': ' + e.message); } } process.exit(failed ? 1 : 0); })();
