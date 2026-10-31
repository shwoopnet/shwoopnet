'use strict';
// SA1 to SA6: the low-money-on-an-exchange alert (the owner, Oct 31, 2026: "low-balance alert per exchange shard").
// Consequence: when a live market is skipped because its own exchange shard is short of money, the owner's phone gets one alert (not one a minute) telling them which exchange and how much; a normal minute reads and writes nothing extra; and the alert can never change an order.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const fx = require('./fixtures/offEquivalenceScenarios');
const live = require('../functions/kalshiLiveLib.js');
const lib = require('../functions/kalshiShardAlertLib.js');
const push = require('../functions/kalshiPushLib.js');
const root = path.join(__dirname, '..');
const gates = {};
const H = 3600 * 1000;

gates.SA1 = () => {
  assert.strictEqual(lib.worst(undefined), null); assert.strictEqual(lib.worst([]), null); assert.strictEqual(lib.worst([{ shard: '2' }, null, { avail: 'x', need: 1 }]), null, 'junk is ignored');
  const w = lib.worst([{ shard: '2', avail: 12.5, need: 20 }, { shard: '0', avail: 3.1, need: 18, ticker: 'KXGOLD15M-X' }, { shard: '2', avail: 7, need: 9 }]);
  assert.strictEqual(w.shard, '0', 'the shard with the least money is reported'); assert.strictEqual(w.avail, 3.1);
};
gates.SA2 = async () => {
  const calls = [];
  const io = (over) => Object.assign({ claim: async (at) => { calls.push('claim'); return null; }, release: async (p) => { calls.push('release:' + p); }, raise: async (a) => { calls.push('raise:' + JSON.stringify(a)); } }, over || {});
  assert.strictEqual(await lib.runShardAlert({ now: 1, short: undefined, ...io() }), 'none'); assert.deepStrictEqual(calls, [], 'a normal minute reads and writes nothing');
  assert.strictEqual(await lib.runShardAlert({ now: 5, short: [{ shard: '2', avail: 4.2, need: 19.5, ticker: 'KXDOGE15M-26OCT301745-45' }], ...io() }), 'alerted');
  assert.deepStrictEqual(calls, ['claim', 'raise:' + JSON.stringify({ at: 5, shard: '2', avail: 4.2, need: 19.5, market: 'KXDOGE15M' })], 'one claim, then one alert with the figures and no order id');
  calls.length = 0; assert.strictEqual(await lib.runShardAlert({ now: 6, short: [{ shard: '2', avail: 4, need: 19 }], ...io({ claim: async () => false }) }), 'already alerted'); assert.deepStrictEqual(calls, [], 'inside the cooldown nothing is sent');
  calls.length = 0; assert.strictEqual(await lib.runShardAlert({ now: 7, short: [{ shard: '2', avail: 4, need: 19 }], ...io({ claim: async () => 123, raise: async () => { throw new Error('boom'); } }) }), 'alert failed'); assert.deepStrictEqual(calls, ['release:123'], 'a failed alert puts the previous alert time back so the next minute can try again');
  assert.ok(/^error/.test(await lib.runShardAlert({ now: 8, short: [{ shard: '2', avail: 4, need: 19 }], ...io({ claim: async () => { throw new Error('x'); } }) })), 'an I/O error is swallowed and reported as a string');
};
gates.SA3 = () => {
  assert.strictEqual(lib.claimable(10 * H, null), true, 'first ever');
  assert.strictEqual(lib.claimable(10 * H, 10 * H - 1000), false, 'a minute later: no');
  assert.strictEqual(lib.claimable(10 * H, 10 * H - lib.SHARD_ALERT_COOLDOWN_MS + 1), false);
  assert.strictEqual(lib.claimable(10 * H, 10 * H - lib.SHARD_ALERT_COOLDOWN_MS), true, 'after six hours it may alert again');
};
gates.SA4 = async () => {
  // a real tick with almost no money on the exchange: the skip is reported to the alert and the order is NOT sent
  const w = fx.l1World({});
  const real = w.common.fetchFn;
  w.common.fetchFn = async (url, o) => (String(url).endsWith('/portfolio/balance') ? fx.reply(200, { balance_breakdown: [{ balance: '0.5000', exchange_index: 2 }, { balance: '0.5000', exchange_index: 0 }] }) : real(url, o));
  const out = await live.runL1Tick({ ...w.common, quotes: [fx.q('KXBTC15M', fx.T)] });
  assert.ok(Array.isArray(out.shardShort) && out.shardShort.length >= 1 && out.shardShort[0].avail <= 0.5 && out.shardShort[0].need > 0.5 && /KXBTC15M/.test(out.shardShort[0].ticker), 'the shortage is reported with the shard, the money there and what the order needed');
  assert.ok(/only \$0\.50 on its shard/.test(out.results.join(' ')), 'the skip message is unchanged');
  assert.strictEqual(w.r.log.filter((x) => x.kind === 'fetch' && x.method === 'POST').length, 0, 'no order is sent when the shard is short');
  const ok = await live.runL1Tick({ ...fx.l1World({}).common, quotes: [fx.q('KXBTC15M', fx.T)] });
  assert.ok(!('shardShort' in ok), 'a normal minute returns exactly what it returned before (the off-equivalence fixtures depend on it)');
};
gates.SA5 = () => {
  const base = { active: true };
  assert.deepStrictEqual(push.sessionKinds(base, { ...base, shardAlert: { at: 5, shard: '2', avail: 4, need: 19 } }), ['shard'], 'a new stamp alerts');
  assert.deepStrictEqual(push.sessionKinds({ ...base, shardAlert: { at: 5 } }, { ...base, shardAlert: { at: 5 }, lastNote: 'x' }), [], 'rewriting the document for another reason never repeats it');
  assert.deepStrictEqual(push.sessionKinds({ active: false }, { active: false, shardAlert: { at: 5 } }), [], 'only while the bot is on');
  assert.deepStrictEqual(push.sessionKinds(base, { ...base, exitWatchAlert: { at: 1 }, shardAlert: { at: 2 } }), ['exitwatch', 'shard'], 'both alerts can fire together');
  const m = push.message('shard', { shardAlert: { shard: '2', avail: 4.2, need: 19.5 } });
  assert.ok(/low money on exchange 2/.test(m.title) && /\$4\.20/.test(m.body) && /\$19\.50/.test(m.body) && /Transfers/.test(m.body) && m.tag === 'issue-shard', 'the words name the exchange, the two amounts and what to do');
  assert.ok(!/orderId|clientOrderId/.test(JSON.stringify(m)));
};
gates.SA6 = () => {
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(/shardAlertLib\.runShardAlert\(\{\s*now, short: l1Result && l1Result\.shardShort,/.test(idx), 'the alert runs only from what the tick reported');
  assert.ok(/claim: \(at\) => db\.runTransaction\(/.test(idx) && /shardAlertLib\.claimable\(at, last\)/.test(idx), 'the cooldown is claimed in a transaction (two instances during a deploy cannot both alert)');
  assert.ok(/try \{\s*const shardRef/.test(idx) && /kalshiLiveArmed: shard alert failed/.test(idx), 'fenced off: it can never fail the tick');
  assert.ok(/raise: \(a\) => sessRef\.set\(\{ shardAlert: a \}, \{ merge: true \}\)/.test(idx), 'its one write is a field on the session document');
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiShardAlertLib.js'), 'utf8');
  assert.ok(!/require\(|fetch|firestore|KALSHI_LIVE|liveRequest|https?:\/\//i.test(src.replace(/\/\/[^\n]*/g, '')), 'the library has no import, no network, no key and no Firestore of its own');
  assert.ok(!/shardAlert/.test(fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8').replace(/shardShort/g, '')), 'the order code only reports the shortage; it never imports or calls the alert');
};
(async () => { let failed = 0; for (const [n, g] of Object.entries(gates)) { try { await g(); console.log('ok   ' + n); } catch (e) { failed++; console.log('FAIL ' + n + ': ' + e.message); } } process.exit(failed ? 1 : 0); })();
