'use strict';
// The Data page (Oct 21, 2026, the owner's request: "start building out a data center page"). It is a read-only view of the bot's settled orders. These gates state what that means as consequences.
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
const lift = (names, extra) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map(fnSource).join('\n') + '\n' + (extra || '') + '; return {' + names.join(',') + '};')();
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const money = (v) => '$' + v.toFixed(2);

// Nothing on the page can send an order or change a setting: the page has no button, input, select, textarea or form inside it.
gates.D1 = () => {
  const page = html.slice(html.indexOf('<main class="page" id="page-data"'), html.indexOf('<main class="page" id="page-settings"'));
  assert.ok(page.length > 200);
  assert.ok(!/<(button|input|select|textarea|form|a )\b/i.test(page), 'the Data page has no control in it');
  const code = ['dataWeekKey', 'dataWeeklyRows', 'dataWeekBarsSvg', 'dataMarketRows', 'dataShareDonutHtml', 'dataTilesHtml', 'dataMarketsHtml', 'dataLeadRows', 'dataLeadHtml', 'dataStatsHtml', 'dataLiveTests', 'dataLiveHtml', 'renderDataCenter'].map(fnSource).join('\n');
  assert.ok(!/api\.|window\.__shwoopAPI|fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(/.test(code), 'and its code calls nothing: it only draws what the Kalshi page already loaded');
};

// A trade belongs to the week it was made in on the clock the page uses (US Central, weeks start Monday): Sunday 11pm Central is still last week even though it is Monday in UTC.
gates.D2 = () => {
  const f = lift(['kalshiOrderPnl', 'dataWeekKey', 'dataWeeklyRows']);
  assert.strictEqual(f.dataWeekKey(Date.UTC(2026, 9, 19, 4, 59)), '2026-10-12', 'Monday 04:59 UTC is Sunday 11:59pm in Chicago: the week of Oct 12');
  assert.strictEqual(f.dataWeekKey(Date.UTC(2026, 9, 19, 16, 0)), '2026-10-19', 'Monday midday is the week of Oct 19');
  const o = (ts, p) => ({ ts, settled: true, fillCount: '1.00', settledPnl: p });
  const rows = f.dataWeeklyRows([o(Date.UTC(2026, 9, 19, 16), 0.05), o(Date.UTC(2026, 9, 20, 16), -0.93), o(Date.UTC(2026, 9, 14, 16), 0.1), { ts: Date.UTC(2026, 9, 20), settled: true, fillCount: '1.00', result: 'hand' }]);
  assert.deepStrictEqual(rows.map((r) => [r.key, r.net, r.n]), [['2026-10-12', 0.1, 1], ['2026-10-19', -0.88, 2]], 'weeks oldest first, results summed, a hand-closed order (no saved result) is not counted');
};

// Per contract is the settled result over the contracts that FILLED, so a 4 contract trade is not 4 trades; trades closed by hand are not in the table at all.
gates.D3 = () => {
  const f = lift(['kalshiOrderPnl', 'kalshiMarketName', 'dataMarketRows', 'dataMarketsHtml']);
  const now = Date.UTC(2026, 9, 21, 12);
  const g = (ts, c, p) => ({ ts, series: 'KXGOLD15M', settled: true, fillCount: c, settledPnl: p });
  const rows = f.dataMarketRows([g(now - 1000, '4.00', 0.24), g(now - 8 * 86400000, '1.00', -0.93), { ts: now, series: 'KXBTC15M', settled: true, fillCount: '1.00' }], now);
  assert.strictEqual(rows.length, 1, 'only settled trades with a saved result');
  assert.deepStrictEqual([rows[0].name, rows[0].n, rows[0].contracts, rows[0].wins], ['Gold', 2, 5, 1]);
  assert.ok(Math.abs(rows[0].net - (-0.69)) < 1e-9 && Math.abs(rows[0].week - 0.24) < 1e-9, 'net over all, and the last 7 days on their own');
  const out = f.dataMarketsHtml(rows, esc, money);
  assert.ok(out.includes('-13.8c'), 'per contract is net over contracts filled: -0.69 / 5 = -13.8c');
};

// The entry timing test (FWD8): Bitcoin, XRP and natural gas split by the entry time each order recorded. An order with no entryLead is an older 6 minute entry, a pairing with nothing settled says so, other markets are not in it, and a hand-closed order is not counted.
gates.D7 = () => {
  const f = lift(['kalshiOrderPnl', 'kalshiMarketName', 'dataLeadRows', 'dataLeadHtml']);
  const o = (series, lead, c, p, extra) => Object.assign({ ts: 1000, series, entryLead: lead, settled: true, fillCount: c, settledPnl: p }, extra || {});
  const rows = f.dataLeadRows([o('KXXRP15M', '10m', '1.00', 0.1), o('KXXRP15M', '10m', '1.00', -0.9), o('KXXRP15M', undefined, '1.00', 0.05), o('KXGOLD15M', undefined, '5.00', 0.4),
    o('KXBTC15M', '10m', '1.00', 0.2, { result: 'hand', settledPnl: undefined }), { ts: 1, series: 'KXNATGAS15M', entryLead: '10m', settled: false, fillCount: '1.00' }]);
  assert.deepStrictEqual(rows.map((r) => r.name + ' ' + r.lead), ['Bitcoin 10 min', 'Bitcoin 6 min', 'XRP 10 min', 'XRP 6 min', 'Natural gas 10 min', 'Natural gas 6 min'], 'three markets, both entry times each, in the bot\'s order; gold is not in it');
  const x10 = rows[2], x6 = rows[3];
  assert.deepStrictEqual([x10.n, x10.wins, x10.contracts], [2, 1, 2], 'two 10 minute XRP trades, one won');
  assert.ok(Math.abs(x10.net - (-0.8)) < 1e-9, 'result summed');
  assert.deepStrictEqual([x6.n, x6.wins], [1, 1], 'an order with no entryLead counts as a 6 minute entry');
  assert.deepStrictEqual([rows[0].n, rows[4].n], [0, 0], 'a hand-closed order and an unsettled one are not counted');
  const out = f.dataLeadHtml(rows, esc, money);
  assert.ok(out.includes('-40.0c') && out.includes('none yet'), 'per contract is net over contracts filled (-0.80 / 2 = -40.0c) and an empty pairing says none yet, not zero');
  assert.ok(/takes weeks to mean anything/.test(out) && !/<(button|input|select)/.test(out), 'it says it is a view, not a verdict, and has no control');
};

// The share ring is a count: its slices add to the whole, and with no trades it says so instead of drawing an empty ring.
gates.D4 = () => {
  const f = lift(['dataShareDonutHtml']);
  assert.ok(/No settled trades yet/.test(f.dataShareDonutHtml([], esc)));
  const out = f.dataShareDonutHtml([{ name: 'Gold', n: 3 }, { name: 'Bitcoin', n: 1 }], esc);
  assert.ok(out.includes('stroke-dasharray="75.000 25.000"') && out.includes('>4</text>') && out.includes('75%') && out.includes('25%'));
  assert.ok(!/var\(--gain\)|var\(--loss\)/.test(out), 'a count is not a result: no red or green');
};

// Weekly bars: a losing week is the red bar below the line with its value under it, a winning week the muted bar above, and only the last 8 weeks are drawn.
gates.D5 = () => {
  const f = lift(['dataWeekLabel', 'dataWeekBarsSvg']);
  assert.ok(/Bars appear after the first settled trade/.test(f.dataWeekBarsSvg([], esc, money)));
  const weeks = Array.from({ length: 10 }, (_, i) => ({ key: '2026-09-' + String(7 + i).padStart(2, '0'), net: i === 9 ? -1.5 : 0.3, n: 20 }));
  const out = f.dataWeekBarsSvg(weeks, esc, money);
  assert.strictEqual((out.match(/<rect /g) || []).length, 8, 'the last 8 weeks');
  assert.ok(out.includes('-$1.50') && out.includes('var(--loss)') && out.includes('+$0.30'));
};

// Cost (Oct 21, 2026): Bot and Data share one set of live listeners. Moving between them must not stop and restart them (every restart re-reads the last 1,000 orders and the events, about 1,200 billed reads), and leaving both stops them.
gates.D6 = () => {
  const calls = [];
  const page = () => ({ hidden: true, classList: { add() {}, remove() {}, toggle() {} }, querySelectorAll: () => [], offsetWidth: 1 });
  const pages = { 'page-brief': page(), 'page-kalshi': page(), 'page-data': page(), 'page-settings': page() };
  const f = new Function('document', 'window', 'history', 'calls', 'var currentUserIsAdmin = true; var kalshiWatching = false; var pageEnterTimer = null;\nfunction kalshiOnShow(){ calls.push("show"); } function kalshiOnHide(){ calls.push("hide"); } function renderDataCenter(){} function pageEnter(){} var currentPageName; function setPageTitle(){}\n' + fnSource('showPage') + '; return showPage;')(
    { getElementById: (id) => pages[id] || null, querySelectorAll: () => [], querySelector: () => null }, { scrollTo() {} }, { replaceState() {} }, calls);
  f('kalshi'); f('data'); f('kalshi');
  assert.deepStrictEqual(calls, ['show'], 'one start for any number of switches between Bot and Data');
  f('brief');
  assert.deepStrictEqual(calls, ['show', 'hide'], 'leaving both stops them');
  f('data');
  assert.deepStrictEqual(calls, ['show', 'hide', 'show'], 'and coming back starts them once');
};

// D8: the strategy in numbers. Consequence: the figure the owner asks for most (is it losing?) is on the page, computed the way the health check computes it.
gates.D8 = () => {
  const f = lift(['dataStatsHtml']);
  // 9 wins of $0.40, 1 loss of $5.00: profit factor 3.6/5 = 0.72, win rate 90%, break-even 5 / (0.4 + 5) = 92.6%
  const st = { n: 10, wins: 9, losses: 1, winRate: 0.9, avgWin: 0.4, avgLoss: -5, profitFactor: 0.72, maxDrawdown: 5, longestLoss: 1 };
  const out = f.dataStatsHtml(st, esc, money);
  assert.ok(out.includes('0.72') && out.includes('90.0%') && out.includes('92.6%'), 'profit factor, win rate and break-even win rate are shown: ' + out.replace(/<[^>]*>/g, ' ').slice(0, 200));
  assert.ok(out.includes('+$0.40') && out.includes('-$5.00') && out.includes('Deepest drawdown'), 'average win, average loss and drawdown are shown');
  assert.ok(!/var\(--gain\)|var\(--loss\)|<(button|input|select)/.test(out), 'plain text, no new colour, no control');
  assert.ok(/No settled trades yet/.test(f.dataStatsHtml({ n: 0 }, esc, money)), 'with no trades it says so');
  assert.ok(f.dataStatsHtml({ n: 3, wins: 3, losses: 0, winRate: 1, avgWin: 0.1, avgLoss: null, profitFactor: null, maxDrawdown: 0, longestLoss: 0 }, esc, money).includes('no losses yet'), 'no loss yet is said, never a fake number');
};

// D9: the by-market table carries profit factor, and a market with fewer than 30 settled trades is a count, not a result.
gates.D9 = () => {
  const f = lift(['kalshiOrderPnl', 'kalshiMarketName', 'dataMarketRows', 'dataMarketsHtml']);
  const o = (series, p) => ({ ts: 1000, series, settled: true, fillCount: '1.00', settledPnl: p });
  const orders = [];
  for (let i = 0; i < 30; i++) orders.push(o('KXGOLD15M', i === 0 ? -1 : 0.1));      // 29 wins of 0.1 = 2.9, one loss of 1.0: profit factor 2.90
  orders.push(o('KXBTC15M', -0.5), o('KXBTC15M', 0.1));
  const rows = f.dataMarketRows(orders, 2000);
  const gold = rows.find((r) => r.name === 'Gold'), btc = rows.find((r) => r.name === 'Bitcoin');
  assert.ok(Math.abs(gold.gw - 2.9) < 1e-9 && Math.abs(gold.gl - 1) < 1e-9, 'gross win and gross loss are kept per market');
  const out = f.dataMarketsHtml(rows, esc, money);
  assert.ok(out.includes('2.90'), 'a market with 30 trades shows its profit factor');
  assert.ok(out.includes('too few') && !/0\.20</.test(out), 'a market with fewer than 30 shows "too few", not a ratio');
  assert.ok(out.includes('Profit factor') && out.includes('data-row7'), 'the column is there');
};

// D10: the live tests card. Consequence: if two crypto orders ever fill in one window after the rule, it shows; and the rng5 log is confirmed on the page.
gates.D10 = () => {
  const f = lift(['dataLiveTests', 'dataLiveHtml']);
  const after = Date.UTC(2026, 9, 22, 18, 0), before = Date.UTC(2026, 9, 22, 1, 0);
  const o = (ticker, c, ts, rng) => ({ ts, ticker, fillCount: c, rng5: rng });
  const r = f.dataLiveTests([
    o('KXBTC15M-26OCT221500-00', '1.00', after, '0.05'), o('KXETH15M-26OCT221500-00', '0.00', after, ''),        // an unfilled second order does not count
    o('KXBTC15M-26OCT221515-15', '1.00', after, '0.10'), o('KXDOGE15M-26OCT221515-15', '1.00', after, undefined),   // two filled in one window: counted
    o('KXGOLD15M-26OCT221515-15', '4.00', after, '0.2'),                                                              // gold is not part of the rule
    o('KXBTC15M-26OCT211500-00', '1.00', before, ''), o('KXETH15M-26OCT211500-00', '1.00', before, '')]);               // before the rule: not counted
  assert.deepStrictEqual([r.windows, r.twoFill], [2, 1], 'windows with a crypto fill and windows with two: ' + JSON.stringify(r));
  assert.deepStrictEqual([r.rngLogged, r.rngOrders], [3, 5], 'rng5 is counted over orders sent after its deploy only');
  const out = f.dataLiveHtml(r, esc);
  assert.ok(out.includes('1 of 2') && out.includes('3 of 5') && /change nothing/.test(out) && !/<(button|input|select)/.test(out), 'plain, read only');
  assert.ok(f.dataLiveHtml(f.dataLiveTests([]), esc).split('none yet').length === 3, 'nothing yet says none yet');
};

// D11: a skipped minute is said plainly on the Bot page, a 429 explains itself, and every other note is untouched.
gates.D11 = () => {
  const f = lift(['kalTime', 'kalDate', 'kalDayKey', 'kalshiWhen', 'kalshiSkipNote']);
  const now = Date.UTC(2026, 9, 22, 17, 0), tick = Date.UTC(2026, 9, 22, 16, 58);
  const skip = f.kalshiSkipNote('The balance could not be read (HTTP 429), so nothing was sent.', tick, now);
  assert.ok(/^Skipped a minute/.test(skip) && skip.includes('HTTP 429') && /asked once more/.test(skip) && /looks again every minute/.test(skip), 'a refused read is explained: ' + skip);
  const other = f.kalshiSkipNote('The balance could not be read (HTTP 500), so nothing was sent.', tick, now);
  assert.ok(/^Skipped a minute/.test(other) && !/asked once more/.test(other), 'another failure is a skip too, without the 429 line');
  const watching = 'Watching. Orders go in about 6 minutes before a close, and no market is at that point right now.';
  assert.strictEqual(f.kalshiSkipNote(watching, tick, now), watching, 'an ordinary note is shown as written');
  assert.strictEqual(f.kalshiSkipNote(undefined, tick, now), '', 'no note, no line');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
