'use strict';
// TT1 to TT4: the Recent trades card shows when a trade opened AND when it closed (the owner, Oct 31, 2026: "recent trade timestamps should probably show when opened and when closed").
// Consequence: a trade's row says when it was bought and either when it closed (the early sell's own fill time, or the market's close) or that the market has not closed yet; a time is never invented.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const fn = (name) => { const m = new RegExp('  function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const lib = () => new Function('escapeHtml', 'Intl', 'Date', 'Number', 'Array', 'Math', 'String', 'Object',
  "var KAL_TZ = 'America/Chicago';\n" + fn('kalDayKey') + fn('kalTime') + fn('kalshiWhen') + fn('kalDate') + fn('kalshiCloseFromTicker') + fn('kalshiTradeTimes') + fn('kalshiEscapedTradeWhen') + '; return { kalshiTradeTimes, kalshiEscapedTradeWhen, kalshiCloseFromTicker };')((x) => String(x), Intl, Date, Number, Array, Math, String, Object);
// KXDOGE15M-26OCT301315-15 closes 13:15 Eastern = 12:15 PM Central Oct 30 = 17:15Z
const T = 'KXDOGE15M-26OCT301315-15', CLOSE = Date.parse('2026-10-30T17:15:00Z'), OPEN = Date.parse('2026-10-30T17:09:11Z');

gates.TT1 = () => {
  const l = lib();
  assert.strictEqual(l.kalshiCloseFromTicker(T), CLOSE, 'the ticker close is 12:15 PM Central');
  let t = l.kalshiTradeTimes({ settled: true }, T, [], CLOSE + 60000);
  assert.deepStrictEqual([t.how, t.closedMs], ['Closed', CLOSE], 'a held trade closes at the market close');
  t = l.kalshiTradeTimes({}, T, [], OPEN);
  assert.deepStrictEqual([t.how, t.closedMs], ['Closes', CLOSE], 'before the close it says Closes, with the close time');
  t = l.kalshiTradeTimes({}, 'MANUAL-TICKER', [], OPEN);
  assert.deepStrictEqual([t.how, t.closedMs], ['', null], 'a ticker with no readable time shows no close at all');
};
gates.TT2 = () => {
  const l = lib(), sold = Date.parse('2026-10-30T17:12:40Z');
  const ord = { exitStatus: 'sold', exitOrderId: 'x-1' };
  let t = l.kalshiTradeTimes(ord, T, [{ orderId: 'other', time: '2026-10-30T17:00:00Z' }, { orderId: 'x-1', time: '2026-10-30T17:12:40Z' }], CLOSE + 1);
  assert.deepStrictEqual([t.how, t.closedMs], ['Sold', sold], 'an early sell closes at its own fill time, not at the market close');
  t = l.kalshiTradeTimes(ord, T, [], CLOSE + 1);
  assert.deepStrictEqual([t.how, t.closedMs], ['Sold early', null], 'the account no longer lists the sell: no time is invented');
  t = l.kalshiTradeTimes({ exitStatus: 'partly sold', exitOrderId: 'x-1' }, T, [{ orderId: 'x-1', time: '2026-10-30T17:12:40Z' }], CLOSE + 1);
  assert.strictEqual(t.how, 'Sold');
  t = l.kalshiTradeTimes({ settled: true, result: 'hand' }, T, [], CLOSE + 1);
  assert.deepStrictEqual([t.how, t.closedMs], ['Sold by hand', null], 'a trade closed by hand has no known time');
};
gates.TT3 = () => {
  const l = lib(), now = Date.parse('2026-10-30T20:00:00Z');
  const h = l.kalshiEscapedTradeWhen(OPEN, { settled: true }, T, [], now);
  assert.ok(/<span>Opened \d{1,2}:\d{2} (AM|PM)<\/span><span class="kal-tr-sub">Closed 12:15 PM<\/span>/.test(h), 'two lines: when it opened, when it closed: ' + h);
  const nextDay = l.kalshiEscapedTradeWhen(Date.parse('2026-10-30T17:09:11Z'), { settled: true }, 'KXDOGE15M-26OCT311315-15', [], Date.parse('2026-11-01T00:00:00Z'));
  assert.ok(/Closed [A-Za-z]{3} 31 12:15 PM/.test(nextDay.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ')) || /Closed [^<]*31[^<]*12:15 PM/.test(nextDay), 'a close on another day than the open always shows its date, even when that day is today: ' + nextDay);
  assert.ok(!/Opened/.test(l.kalshiEscapedTradeWhen(NaN, {}, T, [], now)) && /Closed|Closes/.test(l.kalshiEscapedTradeWhen(NaN, {}, T, [], now)), 'no opened time: no made-up one, the close still shows');
  assert.ok(!/</.test(l.kalshiEscapedTradeWhen(OPEN, { exitStatus: 'sold', exitOrderId: '<b>' }, T, [{ orderId: '<b>', time: 'x' }], now).replace(/<\/?(span)[^>]*>/g, '')), 'markup in the data cannot become markup');
};
gates.TT4 = () => {
  assert.ok(/<span>Opened and closed<\/span>/.test(html) && !/kal-tr-head"><span>Time<\/span>/.test(html), 'the column is headed Opened and closed');
  const rows = html.slice(html.indexOf('var rowsHtml = fillsShown.map'), html.indexOf('var foot = []'));
  assert.strictEqual((rows.match(/kalshiEscapedTradeWhen\(/g) || []).length, 2, 'both kinds of row (a live fill and an older saved order) show both times');
  assert.ok(!/kalshiWhen\(o\.ts|kalshiWhen\(x\.time/.test(rows), 'the old single time is gone');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
