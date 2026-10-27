'use strict';
// "Where the edge is" (the owner, Oct 27, 2026): the bot's settled trades by price paid and time of day, as a heatmap or turnable columns. It is a reading tool: it must never draw what the data cannot support, and it must never touch an order.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) {
    if (html[i] === '{') depth++;
    else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  throw new Error('unbalanced ' + name);
}
const VARS = /var KAL_SURF_MIN = [^\n]*\n/.exec(html)[0] + /var KAL_SURF_DETAIL = \{[\s\S]*?\n  \};\n/.exec(html)[0];
const f = new Function("var KAL_TZ = 'America/Chicago';\n" + VARS + ['kalCentralHour', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPricePaid', 'kalshiEdgeModel'].map(fnSource).join('\n') + '; return { kalshiEdgeModel, kalshiPricePaid };')();
const T0 = Date.parse('2026-10-26T18:00:00Z');   // 1 PM Central, inside the 12p block
const mk = (over) => Object.assign({ strategy: 'L1', series: 'KXGOLD15M', side: 'yes', count: 1, fillCount: '1', averageFillPrice: '0.93', maxCost: 0.93, settled: true, settledPnl: 0.06, result: 'yes', ts: T0, entryLead: '6m' }, over);
const many = (n, over) => Array.from({ length: n }, () => mk(over));
const FINE = { detail: 'fine' };
const cell = (m, hourBlock, cents) => m.cells[hourBlock][cents === 88 ? 0 : cents - 88];   // fine bins: 88c or less, then 89 to 96, then 97c or more

gates.S1 = () => {
  // A NO buy is written by Kalshi at the YES price: 7c on the book is 93c paid. Read as it stands it would sit in the 7c column, which does not exist, and the whole NO side of the record would vanish from the chart.
  assert.strictEqual(Math.round(f.kalshiPricePaid(mk({ side: 'no', averageFillPrice: '0.07' })) * 100), 93);
  const m = f.kalshiEdgeModel(many(10, { side: 'no', averageFillPrice: '0.07', result: 'no' }), FINE);
  assert.strictEqual(cell(m, 4, 93).n, 10, 'ten NO orders at 93c paid land in the 93c column at 12p');
  assert.strictEqual(m.outside, 0);
};
gates.S2 = () => {
  // The honest part: a cell under the minimum carries no edge and is not readable, so the page never draws a hill out of a handful of trades.
  const m = f.kalshiEdgeModel(many(9, {}), FINE);
  const c = cell(m, 4, 93);
  assert.deepStrictEqual([c.n, c.ok, c.edge, c.win], [9, false, null, null]);
  assert.strictEqual(m.okCells, 0);
  const m2 = f.kalshiEdgeModel(many(10, {}), FINE);
  assert.strictEqual(cell(m2, 4, 93).ok, true);
};
gates.S3 = () => {
  // Height is the net result per contract: 8 wins of 6c and 2 losses of 93c over 10 one-contract orders is (0.48 - 1.86) / 10 = -13.8c.
  const o = many(8, {}).concat(many(2, { settledPnl: -0.93, result: 'no' }));
  const c = cell(f.kalshiEdgeModel(o, FINE), 4, 93);
  assert.ok(Math.abs(c.edge - (-13.8)) < 1e-9, 'edge ' + c.edge);
  assert.strictEqual(c.win, 80);
};
gates.S4 = () => {
  // Orders that are not the bot's outcome stay out: hand closed, unsettled, another strategy, outside the band.
  const o = many(10, {}).concat([mk({ result: 'hand' }), mk({ settled: false, settledPnl: null }), mk({ strategy: 'OW1' }), mk({ averageFillPrice: '0.5', maxCost: 0.5 })]);
  const m = f.kalshiEdgeModel(o, FINE);
  assert.strictEqual(m.n, 10);
  assert.strictEqual(m.outside, 1);
};
gates.S5 = () => {
  // The market and entry-time choices filter; an order with no entryLead is a 6 minute order, as the server wrote them before the field existed.
  const o = many(10, {}).concat(many(10, { series: 'KXXRP15M' }), many(10, { entryLead: '10m' }), many(10, { entryLead: undefined }));
  assert.strictEqual(f.kalshiEdgeModel(o, { market: 'XRP' }).n, 10);
  assert.strictEqual(f.kalshiEdgeModel(o, { market: 'Gold', lead: '10m' }).n, 10);
  assert.strictEqual(f.kalshiEdgeModel(o, { market: 'Gold', lead: '6m' }).n, 20);
};
gates.S6 = () => {
  // Time of day is US Central, not the browser's: 1 PM Central is the 12p block wherever the page is opened.
  const m = f.kalshiEdgeModel(many(10, { ts: Date.parse('2026-10-26T18:00:00Z') }), FINE);
  assert.strictEqual(cell(m, 4, 93).n, 10);
  const m2 = f.kalshiEdgeModel(many(10, { ts: Date.parse('2026-10-27T05:30:00Z') }), FINE);   // 12:30 AM Central
  assert.strictEqual(cell(m2, 0, 93).n, 10);
};
gates.S9 = () => {
  // The default is wide cells (the live record is a few hundred trades, and at 10 by 8 nearly every cell was a hole): 5 price bands by 4 parts of the day. The end bands take every price beyond them, so a trade bought at 86c or 99c is kept.
  const o = many(10, {}).concat(many(10, { averageFillPrice: '0.86', maxCost: 0.86 }), many(10, { averageFillPrice: '0.99', maxCost: 0.99 }));
  const m = f.kalshiEdgeModel(o);
  assert.deepStrictEqual([m.cols.length, m.rows.length], [5, 4]);
  assert.strictEqual(m.cells[2][2].n, 10, '93c at 1 PM Central is the 92 to 93c band in the 12p block');
  assert.strictEqual(m.cells[2][0].n, 10, '86c lands in the 88c or less band');
  assert.strictEqual(m.cells[2][4].n, 10, '99c lands in the 96c or more band');
  assert.strictEqual(m.n, 30);
  assert.strictEqual(m.outside, 0);
};
gates.S7 = () => {
  // It reads and draws and nothing else: no call to the server API, no storage, no timers, no animation, no order or setting words, and the card sits in the console grid.
  const start = html.indexOf('var KAL_SURF_MIN');
  const code = html.slice(start, html.indexOf('// ---- server bot tab', start)).replace(/\/\/[^\n]*/g, '');
  assert.ok(!/__shwoopAPI|fetch\(|localStorage|setInterval|setTimeout|requestAnimationFrame|firebase|setDoc|httpsCallable/.test(code), 'no network, storage, timer or animation');
  assert.ok(/data-card="surface"/.test(html) && /grid-area:sf/.test(html) && /"fp fp" "sf sf" "trd trd"/.test(html), 'the card has its own place in the console grid');
};
gates.S8 = () => {
  // Calm view: the only colours are the paper white and the loss red, and a figure is never set in the wordmark font.
  const css = html.slice(html.indexOf('.kal-sf-cv{'), html.indexOf('.kal-fp-n{'));
  assert.ok(!/#[0-9a-fA-F]{3,6}|rgb\(/.test(css.replace(/rgba\(0,0,0/g, '')), 'the card styles use the design tokens only');
  assert.ok(!/Titan One/.test(css));
};

let failed = 0;
for (const k of Object.keys(gates)) { try { gates[k](); console.log(k + ' PASS'); } catch (e) { failed++; console.log(k + ' FAIL ' + e.message); } }
process.exit(failed ? 1 : 0);
