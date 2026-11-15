// OIREL1 (Nov 15, 2026): a log only 7g VERSION of OICORE. The consequences these gates pin: it never places an order, it logs only when the RELATIVE open interest rise is STRICTLY above the registered number, it takes its side from the
// signal candle (180 s before the close) and its price from the fill candle (120 s before the close), missing data means no row, and it shares one candle read per window.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sh = require('../functions/kalshiShadowLib');
const slot = require('../functions/kalshiSlotLib');
const root = path.join(__dirname, '..');
const gates = {};
const CLOSE = Date.parse('2026-11-16T15:00:00Z'), CS = CLOSE / 1000;
// OIREL1 went LIVE as a trial seat on Nov 15, 2026 (the owner's answer "Live now, trial size"), so it is no longer in SHADOW_RULES; the shadow logger keeps the oiRelMin support, and these gates drive it with the rule as it was registered.
const RULE = Object.freeze({ id: 'OIREL1', readme: 'kalshi-scalper/workers/OIREL_SHADOW_SPEC_NOV15.md', series: Object.freeze(['KXBTC15M']), entry: Object.freeze({ sideRule: 'cheap', priceMin: 0.05, priceMax: 0.5, leftMaxSec: 125, leftMinSec: 60, oiRelMin: 0.26764675317954373 }), contracts: 1, registeredAt: '2026-11-15', forwardReadDate: '2026-12-01' });
const rule = () => RULE;
const cand = (end, oi, bid, ask) => ({ end_period_ts: end, open_interest_fp: String(oi), yes_bid: { close_dollars: String(bid) }, yes_ask: { close_dollars: String(ask) } });
const good = (level, end, sigBid, sigAsk, fillBid, fillAsk) => [cand(CS - 360, level, 0.2, 0.25), cand(CS - 180, end, sigBid, sigAsk), cand(CS - 120, end, fillBid, fillAsk)];
const quotes = () => [{ series: 'KXBTC15M', m: { ticker: 'KXBTC15M-26NOV161000-00', status: 'open', close_time: new Date(CLOSE).toISOString(), yes_bid_dollars: '0.40', yes_ask_dollars: '0.45', yes_ask_size_fp: '300', yes_bid_size_fp: '200' } }];
async function run(candlesFn, extra) {
  const written = [], reads = [];
  const r = await sh.runShadowTick(Object.assign({ now: CLOSE - 122000, quotes: quotes(), rules: [rule()], allowedSeries: sh.SHADOW_ALLOWED_SERIES, record: async (d) => { written.push(d); },
    candles: async (...a) => { reads.push(a); return candlesFn(); }, seen: new Set(), candleCache: {} }, extra || {}));
  return { r, written, reads };
}

gates['OR1 the shadow rule shape is valid and log only, on Bitcoin only; the production shadow registry no longer holds it (it is a live seat)'] = () => {
  const r = rule();
  assert.ok(!sh.SHADOW_RULES.some((x) => x.id === 'OIREL1'), 'OIREL1 runs live now, not as a shadow rule');
  assert.ok(r && Object.isFrozen(r) && Object.isFrozen(r.entry));
  assert.strictEqual(sh.validateShadowRule(r, sh.SHADOW_ALLOWED_SERIES).ok, true);
  assert.deepStrictEqual([r.series, r.contracts, r.entry.sideRule, r.entry.priceMin, r.entry.priceMax, r.entry.oiRelMin], [['KXBTC15M'], 1, 'cheap', 0.05, 0.5, 0.26764675317954373]);
  assert.ok(fs.existsSync(path.join(root, r.readme)), 'its pre-registration is in the repo');
  const bad = (patch) => sh.validateShadowRule(Object.assign({}, r, { entry: Object.assign({}, r.entry, patch) }), sh.SHADOW_ALLOWED_SERIES).ok;
  assert.strictEqual(bad({ oiRiseMin: 5000 }), false, 'cannot be combined with the absolute rise');
  assert.strictEqual(bad({ oiRelMin: 0.01 }), false);
  assert.strictEqual(bad({ oiRelMin: 1.5 }), false);
  assert.strictEqual(bad({ sideRule: 'yes' }), false, 'the cheaper side only');
  assert.strictEqual(bad({ leftMinSec: 130, leftMaxSec: 400 }), false, 'its look must reach the 120 s candle');
};

gates['OR2 the OICORE line copied into the logger equals the slot library\'s'] = () => {
  const oicore = slot.SLOT_STRATEGIES.find((s) => s.id === 'OICORE');
  assert.strictEqual(sh.OICORE_OI_LINE, oicore.entry.oiRiseMin);
};

gates['OR3 a relative rise strictly above the line logs one row: side from the 180 s candle, price from the 120 s candle, both quotes and the OICORE comparison'] = async () => {
  // level 100000, end 130000: rel 0.30 > 0.2676; YES ask on the signal candle 0.30 is in the band, the fill candle ask is 0.32
  const { written, reads } = await run(() => good(100000, 130000, 0.28, 0.30, 0.30, 0.32));
  assert.strictEqual(reads.length, 1, 'one candle read');
  assert.strictEqual(written.length, 1);
  const d = written[0];
  assert.deepStrictEqual([d.rule, d.side, d.price, d.signalPrice, d.size, d.sigAsk, d.ask, d.oiLevel, d.oiDoi], ['OIREL1', 'yes', 0.32, 0.3, 1, 0.3, 0.32, 100000, 30000]);
  assert.ok(Math.abs(d.oiRel - 0.3) < 1e-12);
  assert.strictEqual(d.oicoreCrossed, false, 'a 30,000 rise is under OICORE\'s 86,300 line: the pair can be compared on this window');
  assert.strictEqual(d.depth, 300, 'depth at the touch of the YES side from the live quote');
  assert.ok(!('_depthYes' in d) && !('_depthNo' in d), 'scratch fields are not stored');
};

gates['OR4 just under the line is NOT a signal and just over it is (strictly greater than 0.26764675317954373)'] = async () => {
  // level 100000: a rise of 26764 gives 0.26764 (under), 26765 gives 0.26765 (over)
  const under = await run(() => good(100000, 126764, 0.28, 0.30, 0.30, 0.32));
  assert.strictEqual(under.written.length, 0);
  const over = await run(() => good(100000, 126765, 0.28, 0.30, 0.30, 0.32));
  assert.strictEqual(over.written.length, 1);
  assert.ok(over.written[0].oiRel > 0.26764675317954373);
};

gates['OR5 when YES is out of the band the side is NO at 1 minus the YES bid, priced from the fill candle'] = async () => {
  // signal candle YES ask 0.60 (out of band), YES bid 0.55 so NO costs 0.45 (in band); fill candle YES bid 0.52 so NO costs 0.48
  const { written } = await run(() => good(100000, 140000, 0.55, 0.60, 0.52, 0.56));
  assert.strictEqual(written.length, 1);
  assert.deepStrictEqual([written[0].side, written[0].signalPrice, written[0].price], ['no', 0.45, 0.48]);
  // neither side in the band: no row
  const none = await run(() => good(100000, 140000, 0.30, 0.55, 0.30, 0.55));
  assert.strictEqual(none.written.length, 0);
};

gates['OR6 missing data is no row and no memory: a missing 120 s candle, a zero open interest or a one sided quote'] = async () => {
  const noFill = () => good(100000, 130000, 0.28, 0.30, 0.30, 0.32).slice(0, 2);
  const a = await run(noFill);
  assert.strictEqual(a.written.length, 0);
  assert.strictEqual(sh.oiRelFromCandles(noFill(), CS), null);
  assert.strictEqual(sh.oiRelFromCandles(good(0, 130000, 0.28, 0.3, 0.3, 0.32), CS), null, 'level 0 is no data');
  assert.strictEqual(sh.oiRelFromCandles(good(100000, 130000, 0.28, 0.3, 0.32, 0.31), CS), null, 'a crossed fill quote is no data');
  assert.strictEqual(sh.oiRelFromCandles(good(100000, 130000, 0, 0.3, 0.3, 0.32), CS), null, 'a zero bid is not two sided');
  // the same window may be tried again once the candle exists (a failed read caches nothing)
  const seen = new Set(), candleCache = {}, written = [];
  const args = (fn) => ({ now: CLOSE - 122000, quotes: quotes(), rules: [rule()], allowedSeries: sh.SHADOW_ALLOWED_SERIES, record: async (d) => { written.push(d); }, candles: async () => fn(), seen, candleCache });
  await sh.runShadowTick(args(noFill));
  await sh.runShadowTick(args(() => good(100000, 130000, 0.28, 0.30, 0.30, 0.32)));
  assert.strictEqual(written.length, 1);
};

gates['OR7 it shares the read budget and the cache: a second look in the same window makes no second candle read; an empty budget makes no read at all'] = async () => {
  const cache = {}, seen = new Set(), reads = [];
  const mk = (budget) => ({ now: CLOSE - 122000, quotes: quotes(), rules: [rule()], allowedSeries: sh.SHADOW_ALLOWED_SERIES, record: async () => {}, candles: async () => { reads.push(1); return good(100000, 90000, 0.28, 0.30, 0.30, 0.32); }, seen: new Set(), candleCache: cache, budget });
  await sh.runShadowTick(mk(sh.makeReadBudget(3)));
  await sh.runShadowTick(mk(sh.makeReadBudget(3)));
  assert.strictEqual(reads.length, 1, 'the cached answer serves the next minute');
  const r2 = []; 
  await sh.runShadowTick({ now: CLOSE - 122000, quotes: quotes(), rules: [rule()], allowedSeries: sh.SHADOW_ALLOWED_SERIES, record: async () => {}, candles: async () => { r2.push(1); return []; }, seen, candleCache: {}, budget: sh.makeReadBudget(0) });
  assert.strictEqual(r2.length, 0);
};

gates['OR8 it can place no order: the library names no order, sizing or signing code'] = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiShadowLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/require\(/.test(src), 'no imports');
  assert.ok(!/createOrder|\/portfolio\/orders|signRequest|placeOrder/i.test(src));
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
