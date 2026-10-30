'use strict';
// ST1 to ST7: the one Overall Bot page (the owner, Oct 29 to 30, 2026: "build the entire page to be overall with maybe some identifiers and one module that displays the unique strategies").
// Consequence: every order the bot placed shows on the page, a chip says which strategy it came from, the second strategy's orders are never counted as L1's in the Strategies module, and nothing on the page can change a strategy.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const block = (n) => { const m = new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'not found: ' + n); return m[1]; };
const names = ['kalshiSlotIds', 'kalshiStrategyOf', 'kalshiChipHtml', 'kalshiOrdersSummary', 'kalshiStrategiesTableHtml'];
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
  assert.ok(/kal-chip-slot/.test(f.kalshiChipHtml('OICORE', esc)) && !/kal-chip-slot/.test(f.kalshiChipHtml('L1', esc)), 'the second strategy is marked differently from L1');
  assert.deepStrictEqual(f.kalshiSlotIds([{ ts: 1, slotId: 'A' }, { ts: 2, slotId: 'A' }, { ts: 3 }, { slotId: 'B' }]), ['A'], 'only orders with an id and a time name a strategy');
};
gates.ST2 = () => {
  const s = f.kalshiOrdersSummary([{ ts: 2, slotId: 'X', fillCount: 1, settledPnl: -0.9 }, { ts: 3, slotId: 'X', fillCount: 1, settled: false }, { ts: 4, slotId: 'X', fillCount: 2, settledPnl: 1.2 }], 5);
  assert.strictEqual(s.n, 2); assert.strictEqual(s.lost, 1); assert.strictEqual(s.won, 1); assert.strictEqual(s.open.length, 1); assert.strictEqual(s.net, 0.3);
  const rows = [{ id: 'L1', info: { name: 'Closing buy', markets: 'Gold', note: '' }, sum: s, status: 'Running', ageText: '1m ago' }, { id: '<b>X</b>', info: { name: 'N<i>', markets: 'M', note: 'a note' }, sum: f.kalshiOrdersSummary([], 5), status: 'Waiting for a signal', ageText: 'No order yet' }];
  const h = f.kalshiStrategiesTableHtml(rows, esc, money);
  assert.ok(/Strategies/.test(h) && /50\.0%/.test(h) && /No order yet/.test(h) && /Waiting for a signal/.test(h) && /a note/.test(h), 'the module shows status, win rate, last order and the strategy note');
  assert.ok(!/<b>X<\/b>|<i>/.test(h), 'names are escaped');
  assert.ok(/kal-pill-run/.test(h), 'a running strategy is marked');
};
gates.ST3 = () => {
  assert.ok(!/id="kalStrat"|id="kalProbe"|data-strat=|shwoopnet:kalStrategy|kalshiViewSelection|kalshiViewOrders|kalshiProbeHtml|kalshiStrategySwitchHtml|data-strategy/.test(html), 'there is no strategy switch: the page is one Overall view');
  assert.ok(/id="kalStrategies"/.test(html), 'the one Strategies module');
};
gates.ST4 = () => {
  assert.ok(/watchKalshiSlot: function/.test(html) && /collection\(db, 'kalshiSlotOrders'\)/.test(html), 'the page listens to the slot orders');
  assert.ok(!/(setDoc|addDoc|updateDoc|deleteDoc)\([^)]*kalshiSlot/.test(html), 'and never writes them');
};
gates.ST5 = () => {
  // A second-slot fill must be recognised as the bot's (never a manual trade or an unmatched position), its dollars must be in the Stop Loss and Risk meter, and every row says which strategy it came from.
  assert.ok(/function kalshiAllOrders\(\)\{ return \(kalshiLiveOrders \|\| \[\]\)\.concat\(kalshiSlotOrders \|\| \[\]\); \}/.test(html));
  assert.ok(/kalshiPositionRows\(a\.positions\.positions, kalshiAllOrders\(\),/.test(html), 'open positions know the slot orders');
  assert.ok(/t\.strategy !== 'L1' && t\.strategy !== 'SLOT'/.test(html) && /kalshiRiskMeter\(kalshiResolveOrders\(kalshiAllOrders\(\)/.test(html), 'the risk meter counts slot orders');
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
    assert.ok(new RegExp('<span id="kalRulesSlot">' + id + ',').test(html), 'Rules and limits describes ' + id);
    assert.ok(new RegExp(id + ': \\{ name: ').test(html), 'the Strategies module describes ' + id);
  }
  const l1m = /L1: \{ name: 'Closing buy', markets: '([^']+)'/.exec(html); assert.ok(l1m, 'L1 markets are listed');
  const NAMES = { KXGOLD15M: 'Gold', KXDOGE15M: 'Dogecoin', KXETH15M: 'Ethereum', KXBTC15M: 'Bitcoin', KXXRP15M: 'XRP', KXAUDUSD15M: 'AUD/USD', KXUSDCAD15M: 'USD/CAD', KXNATGAS15M: 'Natural gas' };
  const tradingNow = live.L1_SERIES.filter((x) => !live.PAUSED_SERIES.includes(x)).map((x) => NAMES[x]);
  assert.deepStrictEqual(l1m[1].split(', ').sort(), tradingNow.sort(), 'the L1 markets in the module are the ones the code trades (not paused)');
};
gates.ST7 = () => {
  assert.ok(/source = source\.concat\(kalshiSlotOrders \|\| \[\]\);/.test(html), 'the Account result line counts the second strategy too');
  assert.ok(/renderKalshiStrategies\(\);\n    renderKalshiPnl\(\);/.test(html), 'the module is drawn with the rest of the page');
};
gates.ST8 = () => {
  // The owner (Oct 30, 2026): "pnl doesnt match". The Strategies rows and the Account card's Today must be worked out from the same orders and the same fills, so the rows add up to Today.
  assert.ok(/var l1 = kalshiOrdersSummary\(kalshiResolveOrders\(l1src, acct && acct\.results, fills\), now, since\);/.test(html), 'the L1 row uses the account fills');
  assert.ok(/kalshiResolveOrders\(kalshiSlotOrders\.filter\(function\(o\)\{ return o && o\.slotId === id; \}\), acct && acct\.results, fills\), now, since\)/.test(html), 'and so does every second-strategy row');
  assert.ok(/var botOrders = kalshiResolveOrders\(kalshiAllOrders\(\), a\.results, a\.fills && a\.fills\.ok \? kalshiGroupFills\(a\.fills\.fills\) : \[\]\);/.test(html), 'the Account card counts L1 and the second strategy, with the same fills');
};
gates.ST9 = () => {
  // The owner (Oct 30, 2026): "mobile ui isnt great". On a phone each strategy is a card with every figure visible, not a nine column table behind a sideways scroll.
  const h = f.kalshiStrategiesTableHtml([{ id: 'L1', info: { name: 'Closing buy', markets: 'Gold', note: '' }, sum: f.kalshiOrdersSummary([], 5), status: 'Running', ageText: 'No order yet' }], esc, money);
  for (const label of ['Strategy', 'Markets', 'Status', 'Today', 'Result', 'Settled', 'Win rate', 'Open', 'Last order']) assert.ok(h.includes('data-label="' + label + '"'), label + ' has its label for the phone card');
  const css = html.slice(html.indexOf('.kal-strat-tbl, .kal-strat-tbl tbody'), html.indexOf('.kal-strat-tbl, .kal-strat-tbl tbody') + 1400);
  assert.ok(/display:none/.test(css) && /attr\(data-label\)/.test(css) && /grid-template-columns:repeat\(2/.test(css), 'the phone layout hides the header row and shows label over value in two columns');
  assert.ok(/@media screen and \(max-width:900px\)\{\n    \.kal-strat-tbl, /.test(html), 'on phones and tablets (a nine column table is cramped at 768 too)');
};
gates.ST10 = () => {
  const r = /function renderKalshiStrategies\(\)\{[\s\S]*?\n  \}\n/.exec(html); assert.ok(r);
  assert.ok(!/kalshiAgeText\([^;]*\) \+ ' ago'/.test(r[0]), 'the age text already ends in "ago": it must not be added twice ("2 hours ago ago" showed on the owner\'s phone render, Oct 30, 2026)');
  assert.ok(/td:nth-child\(3\)\{ grid-column:1 \/ -1; \}/.test(html) && /\.kal-strat-tbl td \.kal-pill\{ white-space:nowrap/.test(html), 'the status pill gets a whole row on a phone and never wraps');
};
gates.ST11 = () => {
  // The owner (Oct 30, 2026): "i dont think the strategies card matches our pnl results". Result follows the same range as the Account result card, with a total row that equals it.
  const mk = (ts, pnl) => ({ ts, fillCount: 1, settledPnl: pnl });
  const day = 86400000, NOW = Date.parse('2026-10-30T20:00:00Z');
  const orders = [mk(NOW - 40 * day, 5), mk(NOW - 10 * day, -2), mk(NOW - 1000, 1.5)];
  const since = NOW - 30 * day;
  const all = f.kalshiOrdersSummary(orders, NOW), ranged = f.kalshiOrdersSummary(orders, NOW, since);
  assert.strictEqual(all.net, 4.5); assert.strictEqual(ranged.net, -0.5, 'a range leaves out older orders, like the Account result card');
  assert.strictEqual(ranged.n, 2); assert.strictEqual(ranged.today, 1.5, 'Today always counts today');
  assert.strictEqual(ranged.lastTs, NOW - 1000, 'the last order is the latest of all, not only of the range');
  const row = (id, sum) => ({ id, info: { name: id, markets: 'M', note: '' }, sum, status: 'Running', ageText: 'x' });
  const h = f.kalshiStrategiesTableHtml([row('L1', ranged), row('OICORE', f.kalshiOrdersSummary([mk(NOW - 2000, -0.95)], NOW, since))], esc, money, { rangeLabel: '1M', age: () => 'x', partial: false });
  assert.ok(/All strategies/.test(h) && /kal-strat-total/.test(h), 'a total row');
  assert.ok(h.includes('-$1.45') || h.includes('-$1.45'.replace('$', '$')), 'the total row is the sum of the rows: -0.50 and -0.95 make -1.45');
  assert.ok(/Result \(1M\)/.test(h), 'the Result column names its range');
  assert.ok(/renderKalshiPnl\(\); renderKalshiStrategies\(\);/.test(html), 'changing the range redraws the Strategies card');
};
gates.ST12 = () => {
  // The owner, Oct 30, 2026: OICORE showed "No order yet" after it bought, because the page could not read the second strategy's orders and said nothing.
  const esc = (x) => String(x), money = (x) => '$' + Number(x).toFixed(2);
  const row = { id: 'OICORE', info: { name: 'x', markets: 'M', note: '' }, sum: f.kalshiOrdersSummary([], Date.now()), status: 'Waiting for a signal', ageText: 'No order yet' };
  const bad = f.kalshiStrategiesTableHtml([row], esc, money, { slotError: 'permission-denied' });
  assert.ok(/cannot be read \(permission-denied\)/.test(bad), 'an unreadable slot feed is said on the card');
  assert.ok(!/cannot be read/.test(f.kalshiStrategiesTableHtml([row], esc, money, {})), 'no warning when the feed is fine');
  assert.ok(/kalshiSlotError = ''/.test(html) && /kalshiSlotError = String\(/.test(html), 'the page sets and clears the error');
  assert.ok(/settled, last 24 hours/.test(html) && /'last 24 hours'\)/.test(html), 'the Recent trades tiles name their window');
  assert.ok(/kal-loading-note/.test(html), 'a longer range keeps the old chart, dimmed, while it loads');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
