'use strict';
// Shadow logger A and B (Nov 12, 2026). Log only: a shadow rule can never send an order, the public reads it needs share ONE budget of 3 a minute, an empty registry stays a no-op,
// a missing open interest candle means no row, and a row with no second read never gets a guessed fill answer.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib.js');
const gates = {};
const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const NOW = Date.parse('2026-11-12T14:09:00Z');
const CLOSE = NOW + 360000, CS = Math.round(CLOSE / 1000);
const ALLOWED = ['KXGOLD15M', 'KXBTC15M'];
const rule = (entry, id) => ({ id: id || 'ABTEST', readme: 'kalshi-scalper/README.md#SHADOW-ABTEST', series: ['KXGOLD15M'], entry: Object.assign({ sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, entry), contracts: 1, registeredAt: '2026-11-12', forwardReadDate: '2026-12-14' });
const quote = (t) => ({ series: 'KXGOLD15M', m: { ticker: t || 'KXGOLD15M-X', status: 'open', close_time: new Date(CLOSE).toISOString(), yes_bid_dollars: '0.9200', yes_ask_dollars: '0.9300', yes_ask_size_fp: '50', yes_bid_size_fp: '50' } });
const candles = (a, b) => [{ end_period_ts: CS - 180, open_interest_fp: String(a) }, { end_period_ts: CS - 360, open_interest_fp: String(b) }];
const tick = (r, over) => { const rows = [], upd = []; const args = Object.assign({ now: NOW, quotes: [quote()], rules: [r], allowedSeries: ALLOWED, record: async (d) => { rows.push(d); }, seen: new Set(), update: async (id, p) => { upd.push([id, p]); }, sleep: async () => {} }, over); return sh.runShadowTick(args).then((res) => ({ res, rows, upd })); };

gates.AB1 = async () => {
  // Consequence: with no rule nothing is read, written or requested, however the budget and injections look.
  let calls = 0; const f = async () => { calls++; return []; };
  const r = await sh.runShadowTick({ now: NOW, quotes: [quote()], rules: [], allowedSeries: ALLOWED, record: f, candles: f, market: f, update: f });
  assert.deepStrictEqual(r, { skipped: 'no shadow rule' }); assert.strictEqual(calls, 0);
};
gates.AB2 = async () => {
  // Consequence: reads of non-bot markets in one minute never exceed 3 across all rules; the oldest unread series goes first; the budget never waits.
  const b = sh.makeReadBudget(99);
  assert.deepStrictEqual([b.take(), b.take(), b.take(), b.take()], [true, true, true, false]);
  const rules = ['A', 'B', 'C', 'D'].map((s) => ({ entry: { leftMinSec: 330, leftMaxSec: 400 }, series: ['KX' + s] }));
  const last = new Map([['KXA', 5], ['KXB', 1], ['KXD', 3]]);
  assert.deepStrictEqual(sh.planShadowReads(rules, NOW, last), ['KXC', 'KXB', 'KXD', 'KXA'], 'never read first, then oldest read first');
  // candle reads draw from the same budget: with it empty an open interest rule logs nothing and reads nothing
  let reads = 0; const empty = sh.makeReadBudget(0);
  const t = await tick(rule({ oiRiseMin: 1000 }), { budget: empty, candles: async () => { reads++; return candles(2000, 500); } });
  assert.strictEqual(reads, 0); assert.strictEqual(t.rows.length, 0);
  // two rules and three signals under one budget of 3: at most 3 candle reads in the minute
  let n = 0; const bud = sh.makeReadBudget(3);
  const quotes = ['T1', 'T2', 'T3', 'T4', 'T5'].map(quote);
  await tick(rule({ oiRiseMin: 1000 }), { quotes, budget: bud, candles: async () => { n++; return candles(2000, 500); } });
  assert.strictEqual(n, 3);
};
gates.AB3 = async () => {
  // Consequence: missing open interest means no row; a rise under the line is no signal; a rise at the line logs the row with the rise.
  const miss = await tick(rule({ oiRiseMin: 1000 }), { candles: async () => [{ end_period_ts: CS - 180, open_interest_fp: '3000' }] });
  assert.strictEqual(miss.rows.length, 0, 'one candle missing');
  const thrown = await tick(rule({ oiRiseMin: 1000 }), { candles: async () => { throw new Error('x'); } });
  assert.strictEqual(thrown.rows.length, 0); assert.ok(thrown.res.signals === 1);
  assert.strictEqual((await tick(rule({ oiRiseMin: 1000 }), { candles: async () => candles(1500, 1000) })).rows.length, 0, 'rise 500 under 1000');
  const ok = await tick(rule({ oiRiseMin: 1000 }), { candles: async () => candles(2600, 1000) });
  assert.deepStrictEqual([ok.rows.length, ok.rows[0].oiRiseSeen], [1, 1600]);
  assert.strictEqual(sh.validateShadowRule(rule({ oiRiseMin: 10 }), ALLOWED).ok, false, 'a tiny line is refused');
};
gates.AB4 = async () => {
  // Consequence: a calendar rule logs only a market closing at a listed time.
  const on = rule({ calendar: [new Date(CLOSE).toISOString().replace('.000Z', 'Z')] }), off = rule({ calendar: ['2026-11-13T13:30:00Z'] });
  assert.strictEqual(sh.validateShadowRule(on, ALLOWED).ok, true);
  assert.strictEqual((await tick(on)).rows.length, 1); assert.strictEqual((await tick(off)).rows.length, 0);
  assert.strictEqual(sh.validateShadowRule(rule({ calendar: [] }), ALLOWED).ok, false);
};
gates.AB5 = async () => {
  // Consequence: the second look is about 4 seconds after the row, inside the budget; a row without one keeps wouldFillAfter null, never a guess.
  assert.strictEqual(sh.SECOND_LOOK_MS, 4000);
  const r = rule({ secondRead: true }); let slept = null; const ask = '0.9300';
  const t = await tick(r, { sleep: async (ms) => { slept = ms; }, market: async () => ({ yes_bid_dollars: '0.9200', yes_ask_dollars: ask }) });
  assert.strictEqual(slept, 4000);
  assert.deepStrictEqual([t.rows[0].askAfter, t.rows[0].wouldFillAfter], [null, null], 'null until a second read happens');
  assert.deepStrictEqual([t.upd[0][1].askAfter, t.upd[0][1].wouldFillAfter], [0.93, true]);
  const late = await tick(r, { market: async () => ({ yes_bid_dollars: '0.9800', yes_ask_dollars: '0.9900' }) });
  assert.strictEqual(late.upd[0][1].wouldFillAfter, false, 'ask moved past the limit');
  const none = await tick(r, { budget: sh.makeReadBudget(0), market: async () => { throw new Error('no read'); } });
  assert.strictEqual(none.upd.length, 0); assert.strictEqual(none.rows[0].wouldFillAfter, null);
  const err = await tick(r, { market: async () => { throw new Error('x'); } });
  assert.strictEqual(err.upd.length, 0); assert.strictEqual(err.rows[0].wouldFillAfter, null);
  const plain = await tick(rule({}), {}); assert.ok(!('wouldFillAfter' in plain.rows[0]) && plain.upd.length === 0, 'a rule without secondRead logs exactly what it did before');
};
gates.AB6 = () => {
  // Consequence: no order path. The library still has no request, key or order code; index.js shares one budget and the shipped registry gains no OI, calendar or second read field.
  const own = code(read('functions', 'kalshiShadowLib.js')).replace(/args\.(update|record|market|readOpen|candles|sleep)\(/g, 'inject(');
  assert.ok(!/fetch|liveRequest|submitOrder|\/orders|keyId|pem|process\.env|secret|runTransaction|\.update\(|\.delete\(|\.set\(/.test(own));
  const idx = code(read('functions', 'index.js')), i = idx.indexOf('if (shadowLib.SHADOW_RULES.length && !armedOn)');
  assert.ok(i > idx.indexOf('slotRun.runSlotTick'), 'last step, after everything that trades');
  const block = idx.slice(i, idx.indexOf('failure = e', i));
  assert.ok(/makeReadBudget/.test(block) && /budget: shadowBudget/.test(block) && /shadowBudget\.take\(\)/.test(block));
  assert.ok(!/submit|liveRequest|keyId|pem|POST/.test(block));
  assert.ok(sh.SHADOW_RULES.every((r) => !('oiRiseMin' in r.entry) && !('calendar' in r.entry) && !('secondRead' in r.entry)), 'registered GOLDOFF is unchanged');
};
(async () => { for (const [k, f] of Object.entries(gates)) { await f(); console.log('ok   ' + k); } })().catch((e) => { console.error(e); process.exit(1); });
