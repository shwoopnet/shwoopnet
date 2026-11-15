// Shadow scaling (Nov 13, 2026, phase P2). Each gate states the consequence: adding rules must not multiply public reads, settling must not read a market once per row, a rule may only name a reviewed market,
// and with the one registered rule nothing observable changed. Log only: nothing here can place an order.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const sh = require('../functions/kalshiShadowLib.js');
const live = require('../functions/kalshiLiveLib.js');
const gates = {};
const root = path.join(__dirname, '..');
const NOW = Date.parse('2026-11-13T16:00:00Z') ; // a quarter hour mark
const CLOSE = NOW + 360000, CS = CLOSE / 1000;
const SERIES = ['KXGOLD15M', 'KXXRP15M', 'KXBTC15M', 'KXETH15M'];
const rule = (id, series, extra) => ({ id, readme: 'kalshi-scalper/README.md#SHADOW-' + id, series: [series], entry: Object.assign({ sideRule: 'favourite', priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }, extra), contracts: 1, registeredAt: '2026-11-13', forwardReadDate: '2026-12-14' });
const quote = (series, t) => ({ series, m: { ticker: t, status: 'open', close_time: new Date(CLOSE).toISOString(), yes_bid_dollars: '0.9200', yes_ask_dollars: '0.9300', yes_ask_size_fp: '50', yes_bid_size_fp: '50' } });
const candles = [{ end_period_ts: CS - 180, open_interest_fp: '5000' }, { end_period_ts: CS - 360, open_interest_fp: '1000' }];

gates.SC1 = async () => {
  // 30 invented rules over 8 markets: public reads stay at one per market (candles) plus one per market (second look), never one per rule, and never above the hard per-minute budget.
  const ids = []; const quotes = [];
  const rules = [];
  for (let m = 0; m < 8; m++) { const s = SERIES[m % 4]; quotes.push(quote(s, s + '-T' + m)); }
  const rowsOf = [];
  // rules are bound to a series; 8 tickers across 4 series, so every rule sees 2 tickers
  for (let i = 0; i < 30; i++) rules.push(rule('R' + String(i).padStart(2, '0'), SERIES[i % 4], { oiRiseMin: 1000 + i, secondRead: true }));
  let candleReads = 0, marketReads = 0;
  const budget = sh.makeReadBudget(1000);   // capped to the hard constant inside
  assert.strictEqual(budget.left(), sh.SHADOW_READS_PER_MINUTE, 'the budget is capped at the hard constant whatever is asked');
  const out = await sh.runShadowTick({ now: NOW, quotes, rules, allowedSeries: SERIES, record: async (d) => { rowsOf.push(d); }, seen: new Set(), budget,
    candles: async () => { candleReads++; return candles; }, market: async () => { marketReads++; return quotes[0].m; }, update: async () => {}, sleep: async () => {}, candleCache: {} });
  assert.ok(out.written >= 8, 'many rules logged rows');
  const distinct = new Set(rowsOf.map((d) => d.ticker)).size;
  assert.ok(candleReads <= distinct && marketReads <= distinct, 'at most one candle read and one second look per market, not per rule (' + candleReads + ', ' + marketReads + ' for ' + distinct + ' markets)');
  assert.ok(candleReads + marketReads <= sh.SHADOW_READS_PER_MINUTE, 'and never above the hard per-minute budget');
};
gates.SC2 = async () => {
  // Two rules needing the same market's open interest share ONE candle read, in the same minute and in the next (a successful answer is kept); a missing candle is NOT kept, so it is retried.
  let reads = 0; const cache = {};
  const rules = [rule('SCA', 'KXGOLD15M', { oiRiseMin: 1000 }), rule('SCB', 'KXGOLD15M', { oiRiseMin: 2000 })];
  const go = (now, cs) => sh.runShadowTick({ now, quotes: [quote('KXGOLD15M', 'KXGOLD15M-Z')], rules, allowedSeries: SERIES, record: async () => {}, seen: new Set(), budget: sh.makeReadBudget(3), candleCache: cache, candles: async () => { reads++; return cs; } });
  await go(NOW, candles); assert.strictEqual(reads, 1, 'two rules, one read');
  await go(NOW + 20000, candles); assert.strictEqual(reads, 1, 'the next look reuses the answer');
  for (const k of Object.keys(cache)) delete cache[k]; reads = 0;
  await go(NOW, []); await go(NOW + 20000, []);
  assert.strictEqual(reads, 2, 'a missing candle is retried, never cached as an answer');
};
gates.SC3 = async () => {
  // Settling reads each distinct ticker once and settles every row of it; the oldest close is read first so none starves; the per-sweep read budget still holds.
  const row = (rl, t, closeMs) => ({ rule: rl, ticker: t, side: 'yes', price: 0.9, settled: false, closeMs, atMs: closeMs - 400000 });
  const rows = [row('A', 'T3', NOW - 200000), row('B', 'T3', NOW - 200000), row('C', 'T3', NOW - 200000), row('A', 'T1', NOW - 900000), row('B', 'T1', NOW - 900000), row('A', 'T2', NOW - 500000)];
  const reads = [], ups = [];
  const r = await sh.settleShadowRows({ now: NOW, max: 2, readOpen: async () => rows, market: async (t) => { reads.push(t); return { result: 'yes' }; }, update: async (id) => { ups.push(id); } });
  assert.deepStrictEqual(reads, ['T1', 'T2'], 'the two oldest markets, one read each');
  assert.deepStrictEqual(ups.sort(), ['A_T1', 'A_T2', 'B_T1'], 'every row of a read market is settled');
  assert.strictEqual(r.checked, 2); assert.strictEqual(r.settled, 3);
  // a failed read leaves that ticker for the next sweep and does not stop the others
  const r2 = await sh.settleShadowRows({ now: NOW, max: 5, readOpen: async () => rows, market: async (t) => { if (t === 'T1') throw new Error('x'); return { result: 'no' }; }, update: async () => {} });
  assert.strictEqual(r2.settled, 4, 'T1 failed, the other four rows settled');
};
gates.SC4 = () => {
  // A rule may only name a market on the reviewed list; today the list is the L1 four, so behaviour is unchanged, and the list is frozen.
  assert.ok(Object.isFrozen(sh.SHADOW_ALLOWED_SERIES));
  assert.deepStrictEqual(sh.SHADOW_ALLOWED_SERIES.slice().sort(), live.L1_SERIES.slice().sort(), 'today the shadow list equals the L1 list');
  assert.strictEqual(sh.validateShadowRule(rule('OKAY', 'KXGOLD15M', {}), sh.SHADOW_ALLOWED_SERIES).ok, true);
  assert.strictEqual(sh.validateShadowRule(rule('NOPE', 'KXSOL15M', {}), sh.SHADOW_ALLOWED_SERIES).ok, false, 'an unlisted market is refused');
  const idx = fs.readFileSync(path.join(root, 'functions/index.js'), 'utf8');
  assert.ok(/allowedSeries: shadowLib\.SHADOW_ALLOWED_SERIES/.test(idx), 'index.js passes the reviewed list');
};
gates.SC5 = () => {
  // The registry is unchanged: one rule, GOLDOFF, and the registry file text for rules has no new entry.
  assert.deepStrictEqual(sh.SHADOW_RULES.map((r) => r.id), ['GOLDOFF']);
};
gates.SC6 = async () => {
  // With the single registered rule the tick makes exactly the writes it made: one row, no read of any kind, no second-look fields on the row.
  const rows = []; let reads = 0;
  const f = async () => { reads++; return []; };
  const out = await sh.runShadowTick({ now: NOW, quotes: [quote('KXGOLD15M', 'KXGOLD15M-Q')], rules: sh.SHADOW_RULES, allowedSeries: sh.SHADOW_ALLOWED_SERIES, record: async (d) => { rows.push(d); }, seen: new Set(), candles: f, market: f, update: f, sleep: async () => {} });
  assert.deepStrictEqual(out, { signals: 1, written: 1 });
  assert.strictEqual(reads, 0, 'no candle read, no second look');
  assert.ok(!('askAfter' in rows[0]) && !('oiRiseSeen' in rows[0]), 'the row has no extra fields');
};
gates.SC7 = async () => {
  // A second look is one read per ticker even when several rules logged a row on it; the lane's second look fields (askAfter, wouldFillAfter) already exist behind entry.secondRead and are written with no new field here.
  let reads = 0; const upd = [];
  const rules = [rule('SLA', 'KXGOLD15M', { secondRead: true }), rule('SLB', 'KXGOLD15M', { secondRead: true })];
  await sh.runShadowTick({ now: NOW, quotes: [quote('KXGOLD15M', 'KXGOLD15M-S')], rules, allowedSeries: SERIES, record: async () => {}, seen: new Set(), budget: sh.makeReadBudget(3), sleep: async () => {},
    market: async () => { reads++; return quote('KXGOLD15M', 'KXGOLD15M-S').m; }, update: async (id, p) => { upd.push([id, p]); } });
  assert.strictEqual(reads, 1, 'one second look serves both rules');
  assert.deepStrictEqual(upd.map((u) => u[0]).sort(), ['SLA_KXGOLD15M-S', 'SLB_KXGOLD15M-S']);
  assert.ok(upd.every((u) => 'askAfter' in u[1] && 'wouldFillAfter' in u[1]), 'each row gets its own fields');
};
gates.SC8 = () => {
  // The off-equivalence fixtures are byte identical to main: this change touches none of them.
  let diff = '';
  try { diff = execFileSync('git', ['diff', '--name-only', 'origin/main', '--', 'test/fixtures'], { cwd: root, encoding: 'utf8' }); } catch (e) { return; }
  assert.strictEqual(diff.trim(), '', 'fixtures unchanged');
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
