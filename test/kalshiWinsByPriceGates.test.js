// WP1: Bot status shows the win rate for each price paid (the owner, Oct 29, 2026: "92c entries win% etc"). Consequence: a NO order's fill is the YES price, so reading it as it stands would file a 92c NO entry under 8c and make the table lie
// (the same trap kalshiPricePaid exists for); wins and losses must follow the settled result, an unsettled or unfilled order must not count, and the break-even beside each price must be that price.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
const names = ['kalshiOrderPnl', 'kalshiPricePaid', 'kalshiWinsByPrice', 'kalshiWinsByPriceBands', 'kalshiWinsByPriceHtml'];
const f = new Function('var ' + /(KAL_PRICE_BANDS = [^\n]*);\n/.exec(html)[1] + ';\n' + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
const o = (side, avg, pnl, over) => Object.assign({ strategy: 'L1', side, count: 5, fillCount: 5, averageFillPrice: avg, maxCost: 4.6, settled: true, settledPnl: pnl }, over);
gates.WP1 = () => {
  const list = f.kalshiWinsByPrice([
    o('yes', 0.92, 0.35), o('yes', 0.92, 0.35), o('yes', 0.92, -4.6),
    o('no', 0.08, 0.35),                       // a 92c NO entry is written as 8c: it belongs with the 92c group
    o('yes', 0.9, 0.5), o('yes', 0.9, -4.5, { result: 'exit' }),
    o('yes', 0.95, 0.2, { settled: false, settledPnl: null }),   // not settled: left out
    o('yes', 0.95, 0.2, { fillCount: 0 }),                       // never filled: left out
    o('yes', 0.93, 0.2, { strategy: 'slot' }),                   // not the bot's L1 order: left out
  ]);
  assert.deepStrictEqual(list.map((g) => [g.cents, g.n, g.wins, g.losses]), [[90, 2, 1, 1], [92, 4, 3, 1]], 'grouped by cents paid, NO converted, only settled L1 fills counted');
  assert.strictEqual(list[1].winPct, 75, 'win rate is wins over orders');
  assert.deepStrictEqual(f.kalshiWinsByPrice([]), [], 'no orders, no rows');
  const h = f.kalshiWinsByPriceHtml(list, (x) => String(x));
  assert.ok(/92c entries/.test(h) && /4 orders, won 3 lost 1, 75\.0% \(needs 92%\)/.test(h), 'the cent rows stay, each with the counts, the win rate and the break-even: ' + h);
  assert.ok(/<details class="kal-fold" id="kalWinsByCent">/.test(h), 'the one-row-per-cent list is closed under the bands, not the first thing read');
  const bands = f.kalshiWinsByPriceBands(list);
  assert.deepStrictEqual(bands.map((g) => [g.label, g.n, g.wins]), [['88c to 90c', 2, 1], ['91c to 92c', 4, 3]], 'bands hold the cents inside them and an empty band is left out');
  assert.ok(Math.abs(bands[1].avgPaid - 92) < 1e-9 && Math.abs(bands[1].points - (75 - 92)) < 1e-9, 'a band is judged against the AVERAGE price paid in it, in points');
  assert.ok(/88c to 90c/.test(h) && /50\.0% against 90\.0% paid \(-40\.0\)/.test(h), 'the band row says the win rate, the average price and the points: ' + h);
  const wide = f.kalshiWinsByPriceBands(f.kalshiWinsByPrice([o('yes', 0.54, -2.7), o('yes', 0.96, 0.2), o('yes', 0.99, 0.05)]));
  assert.deepStrictEqual(wide.map((g) => g.label), ['Under 88c', '95c to 97c', '98c and over'], 'prices outside the band are kept in their own groups, never merged into the band');
  assert.ok(/1 order,/.test(f.kalshiWinsByPriceHtml(f.kalshiWinsByPrice([o('yes', 0.9, 0.5)]), (x) => String(x))), 'singular for one order');
  assert.strictEqual(f.kalshiWinsByPriceHtml([], (x) => x), '', 'nothing to show, nothing drawn');
  assert.ok(!/\$|\*\*\*\*/.test(h), 'percentages only, so Privacy view has nothing to mask');
  assert.ok(/kalshiWinsByPriceHtml\(kalshiWinsByPrice\(kalshiResolveOrders\(/.test(html), 'it is drawn on the Bot status card from the resolved orders');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
