'use strict';
// ST1 to ST7: the one Overall Bot page (the owner, Oct 29 to 30, 2026: "build the entire page to be overall with maybe some identifiers and one module that displays the unique strategies").
// Consequence: every order the bot placed shows on the page, a chip says which strategy it came from, the second strategy's orders are never counted as L1's in the Strategies module, and nothing on the page can change a strategy.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const block = (n) => { const m = new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'not found: ' + n); return m[1]; };
const names = ['kalshiSlotIds', 'kalshiStrategyOf', 'kalshiChipHtml', 'kalshiOrdersSummary'];
const stubs = 'var KAL_SLOT_REGISTERED = [];\nfunction kalDayKey(ms){ return new Date(ms).toISOString().slice(0,10); }\nfunction kalshiOrderPnl(o){ return typeof o.settledPnl === "number" ? o.settledPnl : null; }\n';
let f;
try { f = new Function(stubs + names.map(block).join('\n') + '; return { ' + names.join(', ') + ' };')(); } catch (e) { console.log('FAIL setup: ' + e.message); process.exit(1); }
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const money = (v) => '$' + v.toFixed(2);
gates.ST1 = () => {
  assert.strictEqual(f.kalshiStrategyOf({ strategy: 'L1' }), 'L1');
  assert.strictEqual(f.kalshiStrategyOf({ strategy: 'SLOT', slotId: 'OICORE' }), 'OICORE');
  assert.strictEqual(f.kalshiStrategyOf({ strategy: 'SLOT' }), 'L1', 'a slot order with no id is not given a made-up label');
  assert.strictEqual(f.kalshiStrategyOf(null), 'L1');
  assert.ok(!/<img/.test(f.kalshiChipHtml('<img src=x>', esc)), 'a chip label is escaped');
  assert.strictEqual(f.kalshiChipHtml('OICORE', esc).replace('OICORE', 'L1'), f.kalshiChipHtml('L1', esc), 'every strategy chip has the same style (the owner, Oct 30, 2026: match L1)');
  assert.ok(!/kal-chip-slot/.test(html) && /\.kal-chip\{[^}]*color:var\(--muted\)/.test(html), 'the chip is a quiet muted label: the bright treatment is for figures and urgent items');
  assert.deepStrictEqual(f.kalshiSlotIds([{ ts: 1, slotId: 'A' }, { ts: 2, slotId: 'A' }, { ts: 3 }, { slotId: 'B' }]), ['A'], 'only orders with an id and a time name a strategy');
};
gates.ST2 = () => {
  const s = f.kalshiOrdersSummary([{ ts: 2, slotId: 'X', fillCount: 1, settledPnl: -0.9 }, { ts: 3, slotId: 'X', fillCount: 1, settled: false }, { ts: 4, slotId: 'X', fillCount: 2, settledPnl: 1.2 }], 5);
  assert.strictEqual(s.n, 2); assert.strictEqual(s.lost, 1); assert.strictEqual(s.won, 1); assert.strictEqual(s.open.length, 1); assert.strictEqual(s.net, 0.3);
};
gates.ST3 = () => {
  assert.ok(!/id="kalStrat"|id="kalProbe"|data-strat=|shwoopnet:kalStrategy|kalshiViewSelection|kalshiViewOrders|kalshiProbeHtml|kalshiStrategySwitchHtml|data-strategy/.test(html), 'there is no strategy switch: the page is one Overall view');
  assert.ok(!/id="kalStrategies"/.test(html), 'no per-strategy table on the Bot page (Nov 16, 2026); strategy results live on the Strategies page');
};
gates.ST4 = () => {
  assert.ok(/watchKalshiSlot: function/.test(html) && /collection\(db, 'kalshiSlotOrders'\)/.test(html), 'the page listens to the slot orders');
  assert.ok(!/(setDoc|addDoc|updateDoc|deleteDoc)\([^)]*kalshiSlot/.test(html), 'and never writes them');
};
gates.ST5 = () => {
  // A second-slot fill must be recognised as the bot's (never a manual trade or an unmatched position), its dollars must be in the Stop Loss and Risk meter, and every row says which strategy it came from.
  assert.ok(/function kalshiAllOrders\(\)\{ return \(kalshiLiveOrders \|\| \[\]\)\.concat\(kalshiSlotOrders \|\| \[\]\); \}/.test(html));
  assert.ok(/kalshiPositionRows\(a\.positions\.positions, kalshiAllOrders\(\),/.test(html), 'open positions know the slot orders');
  assert.ok(/t\.strategy !== 'L1' && t\.strategy !== 'SLOT'/.test(html) && /all = kalshiAllOrders\(\)/.test(html) && /kalshiRiskMeter\(all, kalshiLiveCtl/.test(html), 'the risk figure (at risk now, on the Strategies page) counts slot orders');
  assert.ok(!/kalshiIsExitFill\(x, kalshiLiveOrders\)/.test(html), 'a slot exit fill is not shown as a trade either');
  assert.ok(/strategy: order \? kalshiStrategyOf\(order\) : ''/.test(html) && /r\.strategy \? kalshiChipHtml\(r\.strategy, esc\)/.test(html), 'open positions carry the chip');
  assert.ok(/kalshiChipHtml\(kalshiStrategyOf\(o\), escapeHtml\)/.test(html) && /kalshiChipHtml\(kalshiStrategyOf\(ord\), escapeHtml\)/.test(html), 'recent trades carry the chip');
};
gates.ST6 = () => {
  // The Strategies module and the Rules text must agree with the bot's code: the registered second strategies, and the markets L1 trades.
  const slotLib = require('../functions/kalshiSlotLib'), live = require('../functions/kalshiLiveLib');
  const m = /var KAL_SLOT_REGISTERED = \[([^\]]*)\];/.exec(html); assert.ok(m, 'the page lists the registered strategies');
  const pageIds = m[1].split(',').map((x) => x.trim().replace(/'/g, '')).filter(Boolean);
  assert.deepStrictEqual(pageIds, slotLib.SLOT_STRATEGIES.map((x) => x.id), 'the page names exactly the strategies the code registers');
  for (const id of pageIds) {
    assert.ok(new RegExp('<span id="kalRulesSlot[A-Za-z]*">' + id + ',').test(html), 'Rules and limits describes ' + id);
    assert.ok(new RegExp(id + ': \\{ name: ').test(html), 'the Strategies module describes ' + id);
  }
  const l1m = /L1: \{ name: 'Closing buy', markets: '([^']+)'/.exec(html); assert.ok(l1m, 'L1 markets are listed');
  assert.ok(!/L1E:/.test(html), 'L1E is gone (the owner, Oct 30, 2026: "remove L1E altogether"; Ethereum is paused)');
  const NAMES = { KXGOLD15M: 'Gold', KXDOGE15M: 'Dogecoin', KXETH15M: 'Ethereum', KXBTC15M: 'Bitcoin', KXXRP15M: 'XRP', KXAUDUSD15M: 'AUD/USD', KXUSDCAD15M: 'USD/CAD', KXNATGAS15M: 'Natural gas' };
  const tradingNow = live.L1_SERIES.filter((x) => !live.PAUSED_SERIES.includes(x)).map((x) => NAMES[x]);
  assert.deepStrictEqual(l1m[1].split(', ').sort(), tradingNow.sort(), 'L1 lists the markets the code trades under the L1 rule (not paused)');
};
gates.ST7 = () => {
  assert.ok(/source = source\.concat\(kalshiSlotOrders \|\| \[\]\);/.test(html), 'the Account result line counts the second strategy too');
};
gates.ST8 = () => {
  // The owner (Oct 30, 2026): "pnl doesnt match". The Strategies rows and the Account card's Today must be worked out from the same orders and the same fills, so the rows add up to Today.
  assert.ok(/var botOrders = kalshiResolveOrders\(kalshiAllOrders\(\), a\.results, a\.fills && a\.fills\.ok \? kalshiGroupFills\(a\.fills\.fills\) : \[\]\);/.test(html), 'the Account card counts L1 and the second strategy, with the same fills');
};
gates.ST12 = () => {
  // The owner, Oct 30, 2026: OICORE showed "No order yet" after it bought, because the page could not read the second strategy's orders and said nothing.
  assert.ok(/kalshiSlotError = ''/.test(html) && /kalshiSlotError = String\(/.test(html), 'the page sets and clears the error');
  assert.ok(/settled, last 24 hours/.test(html) && /'last 24 hours'\)/.test(html), 'the Recent trades tiles name their window');
  assert.ok(/kal-loading-note/.test(html), 'a longer range keeps the old chart, dimmed, while it loads');
};
gates.ST13 = () => {
  // The owner, Oct 30, 2026: the Recent trades tiles ignored the OICORE trade ("this should be including all strategies"). The cause was a card counting only L1's orders. Every tally now reads kalshiAllOrders(); only the readers that are L1 by nature may read L1's list alone, and a new one has to be added here on purpose.
  const lines = html.split('\n').filter((l) => /kalshiLiveOrders/.test(l) && !/^\s*\/\//.test(l) && !/collection\(db, 'kalshiLiveOrders'\)/.test(l));
  const allowed = [
    /^\s*var kalshiLiveOrders = \[\];/,                                  // the state
    /kalshiLiveOrders = o; kalshiOrdersLoaded/,                          // the listener
    /function kalshiAllOrders\(\)/,                                      // the union
    /var loaded = \(kalshiLiveOrders/, /var source = kalshiLiveOrders, partial/, /kalshiPnlSource\(kalshiLiveOrders, hit\)/, /l1src = kalshiLiveOrders/,   // the older-orders read pages L1's own collection
    /var live = \(kalshiLiveOrders \|\| \[\]\)\.filter[^\n]*slot = \(kalshiSlotOrders/,   // the Strategies page's older-orders read (Nov 13, 2026): it sizes L1's own list and the slot's, then returns the union
    /KAL_ECG\.SPAN/,                                                     // the heartbeat strip is L1's
    /var orders = kalshiResolveOrders\(kalshiLiveOrders, a && a\.results/   // the silent market warning: L1's markets
  ];
  const stray = lines.filter((l) => !allowed.some((re) => re.test(l)));
  assert.deepStrictEqual(stray.map((l) => l.trim().slice(0, 90)), [], 'every card that tallies orders reads kalshiAllOrders(), so a second strategy is never left out');
  const tradeStats = new Function('kalshiOrderPnl', block('kalshiTradeStats') + '; return kalshiTradeStats;')(f.kalshiOrderPnl || ((o) => (typeof o.settledPnl === 'number' ? o.settledPnl : null)));
  const tiles = tradeStats([
    { strategy: 'L1', fillCount: '5', ts: Date.now() - 3600000, settled: true, result: 'yes', side: 'yes', settledPnl: 0.3 },
    { strategy: 'SLOT', slotId: 'OICORE', fillCount: '5', ts: Date.now() - 7200000, settled: true, result: 'no', side: 'yes', settledPnl: -0.27 }
  ], Date.now());
  assert.strictEqual(tiles.total, 2, 'the tiles count a second strategy order as a trade');
};
gates.ST15 = () => {
  // The owner, Oct 30, 2026: Worst market comes back, but the WHOLE Bot status card counts only the markets actively in the Strategies list, for every strategy. XRP is paused and Bitcoin's old L1 orders are not active (the second strategy trades Bitcoin now).
  const info = /var KAL_STRATEGY_INFO = \{[\s\S]*?\n  \};/.exec(html)[0];
  const lift = (n) => block(n);
  const pick = (name) => new RegExp('  function ' + name + '\\(\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html)[0];
  const kmn = /  function kalshiMarketName\(o\)\{[\s\S]*?\n  \}\n/.exec(html)[0];
  const sof = /  function kalshiStrategyOf\(o\)\{[^\n]*\n/.exec(html)[0];
  const act = /  function kalshiActivePairs\(\)\{[\s\S]*?\n  \}\n/.exec(html)[0];
  const isa = /  function kalshiIsActive\(o\)\{[^\n]*\n/.exec(html)[0];
  const g = new Function(info + '\n' + kmn + '\n' + sof + '\n' + act + '\n' + isa + '; return { kalshiIsActive, kalshiActivePairs };')();
  const o = (strategy, series, slotId) => ({ strategy, series, slotId });
  assert.ok(g.kalshiIsActive(o('L1', 'KXGOLD15M')) && !g.kalshiIsActive(o('L1', 'KXDOGE15M')), 'L1 counts on gold; Dogecoin is paused (Nov 3, 2026)');
  assert.ok(g.kalshiIsActive(o('SLOT', 'KXBTC15M', 'OICORE')), 'the second strategy counts on Bitcoin');
  assert.ok(!g.kalshiIsActive(o('L1', 'KXETH15M')), 'Ethereum is paused and not on the list');
  assert.ok(!g.kalshiIsActive(o('L1', 'KXXRP15M')), 'XRP is paused and not on the list');
  assert.ok(!g.kalshiIsActive(o('L1', 'KXBTC15M')), "Bitcoin's old L1 orders are not active: L1 no longer trades it");
  // Oct 31, 2026 (the owner: the Bot status card is redone, "too much to read"): the win rate, edge, best and worst market rows left that card, so they are no longer asserted here. Orders today and Last order below are still on it.
  assert.ok(/kalshiIsActive\(o\) \|\| !Number\.isFinite\(o\.ts\)|!kalshiIsActive\(o\) \|\| !Number\.isFinite\(o\.ts\)/.test(html), 'Orders today and Last order count both strategies on active markets');
};
gates.ST16 = () => {
  // The owner, Oct 30, 2026: L1E was removed again the same day; the label is gone and every L1 order is L1. Display only: the order is still an L1 order in the bot and nothing about how it trades changes.
  const sof = /  function kalshiStrategyOf\(o\)\{[^\n]*\n/.exec(html)[0];
  const g = new Function(sof + '; return kalshiStrategyOf;')();
  assert.strictEqual(g({ strategy: 'L1', series: 'KXETH15M' }), 'L1', 'no L1E any more: an Ethereum order is plain L1');
  assert.strictEqual(g({ strategy: 'L1', series: 'KXGOLD15M' }), 'L1', 'gold stays L1');
  assert.strictEqual(g({ strategy: 'L1', ticker: 'KXDOGE15M-26OCT30' }), 'L1', 'Dogecoin stays L1');
  assert.strictEqual(g({ strategy: 'SLOT', slotId: 'OICORE', series: 'KXBTC15M' }), 'OICORE', 'the second strategy keeps its own id');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
