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

// Nothing on the account result card can send an order or change a setting: its only controls are the range buttons, and its code calls nothing.
gates.D1 = () => {
  const card = html.slice(html.indexOf('id="kalPnl"'), html.indexOf('data-card="trades"', html.indexOf('id="kalPnl"')));
  assert.ok(card.length > 100);
  assert.ok(!/<(input|select|textarea|form|a )\b/i.test(card), 'the card has no input, select or form');
  const code = ['kalshiPnlSeries', 'kalshiPnlRangeStart', 'kalshiPnlCardHtml', 'renderKalshiPnl', 'kalshiLineSvg'].map(fnSource).join('\n');
  assert.ok(!/fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(/.test(code.replace(/api\.kalshiOrdersSince/g, '')), 'and its code writes and calls nothing: it draws what the page loaded, plus one read of older orders');
  assert.ok((code.match(/api\.\w+/g) || []).every((c) => c === 'api.kalshiOrdersSince'), 'the only API it touches is the read of older orders');
  const mod = html.slice(html.indexOf('kalshiOrdersSince: function'), html.indexOf('kalshiBookSnaps: function'));
  assert.ok(/getDocs\(query\(collection\(db, 'kalshiLiveOrders'\)/.test(mod) && !/setDoc|updateDoc|addDoc/.test(mod), 'that read is a plain query of the bot orders, admin read only by the rules');
  assert.ok(!/id="kalRecord"|data-card="record"|renderKalshiRecord/.test(html), 'the record card (headline and rules on trial) is gone (removed Oct 24, 2026, the owner)');
};

// The account result line: the range cuts the running settled result, and the line starts at zero at the start of the range, so a long range is never drawn from a total the range did not earn.
gates.PL1 = () => {
  const f = lift(['kalDayKey', 'kalDateTime', 'kalDate', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPnlSeries', 'kalshiPnlRangeStart', 'kalshiLineSvg', 'kalshiPnlCardHtml']);
  const now = Date.UTC(2026, 9, 24, 18), day = 86400000;
  const o = (d, p) => ({ ts: now - d * day, series: 'KXGOLD15M', settled: true, fillCount: '1.00', settledPnl: p });
  const orders = [o(40, 5), o(20, -1), o(2, 2), o(0.1, 0.5)];
  const total = (k) => { const s = f.kalshiPnlSeries(orders, f.kalshiPnlRangeStart(k, now)); return s.length ? s[s.length - 1].cum : null; };
  assert.strictEqual(total('1M'), 1.5, '30 days: -1 + 2 + 0.5 (the 40 day old trade is out, and the line starts at zero)');
  assert.strictEqual(total('1W'), 2.5);
  assert.strictEqual(total('1D'), 0.5, 'today only');
  assert.strictEqual(total('ALL'), 6.5);
  assert.strictEqual(total('YTD'), 6.5, 'the year to date holds all four');
  const money = (v) => '$' + v.toFixed(2);
  const out = f.kalshiPnlCardHtml(orders, '3M', now, esc, money);
  assert.ok(out.includes('+$6.50') && /<svg/.test(out), 'the total and the line');
  assert.ok(/back to /.test(f.kalshiPnlCardHtml([o(2, 2), o(0.1, 0.5)], '3M', now, esc, money)), 'a range longer than the loaded orders says how far back they go');
  assert.ok(/\*\*\*\*/.test(f.kalshiPnlCardHtml(orders, '1M', now, esc, (v) => '****')) && !/\$/.test(f.kalshiPnlCardHtml(orders, '1M', now, esc, (v) => '****')), 'Privacy view masks every dollar figure on it');
};

// Per contract is the settled result over the contracts that FILLED, so a 4 contract trade is not 4 trades; trades closed by hand are not in the table at all.
gates.D3 = () => {
  const f = lift(['kalshiOrderPnl', 'kalshiMarketName', 'dataMarketRows']);
  const now = Date.UTC(2026, 9, 21, 12);
  const g = (ts, c, p) => ({ ts, series: 'KXGOLD15M', settled: true, fillCount: c, settledPnl: p });
  const rows = f.dataMarketRows([g(now - 1000, '4.00', 0.24), g(now - 8 * 86400000, '1.00', -0.93), { ts: now, series: 'KXBTC15M', settled: true, fillCount: '1.00' }], now);
  assert.strictEqual(rows.length, 1, 'only settled trades with a saved result');
  assert.deepStrictEqual([rows[0].name, rows[0].n, rows[0].contracts, rows[0].wins], ['Gold', 2, 5, 1]);
  assert.ok(Math.abs(rows[0].net - (-0.69)) < 1e-9 && Math.abs(rows[0].week - 0.24) < 1e-9, 'net over all, and the last 7 days on their own');
  assert.ok(Math.abs(rows[0].net / rows[0].contracts * 100 - (-13.8)) < 1e-9, 'per contract is net over contracts filled: -0.69 / 5 = -13.8c (the statement prints it)');
};

// Cost (Oct 21, 2026): Bot and Data share one set of live listeners. Moving between them must not stop and restart them (every restart re-reads the last 1,000 orders and the events, about 1,200 billed reads), and leaving both stops them.
gates.D6 = () => {
  const calls = [];
  const page = () => ({ hidden: true, classList: { add() {}, remove() {}, toggle() {} }, querySelectorAll: () => [], offsetWidth: 1 });
  const pages = { 'page-brief': page(), 'page-kalshi': page(), 'page-settings': page() };
  const f = new Function('document', 'window', 'history', 'calls', 'var currentUserIsAdmin = true; var kalshiWatching = false; var pageEnterTimer = null;\nfunction kalshiOnShow(){ calls.push("show"); } function kalshiOnHide(){ calls.push("hide"); } function renderDataCenter(){} function pageEnter(){} var currentPageName; function setPageTitle(){}\n' + fnSource('showPage') + '; return showPage;')(
    { getElementById: (id) => pages[id] || null, querySelectorAll: () => [], querySelector: () => null }, { scrollTo() {} }, { replaceState() {} }, calls);
  f('kalshi'); f('kalshi');
  assert.deepStrictEqual(calls, ['show'], 'one start for the Bot page however often it is shown');
  f('brief');
  assert.deepStrictEqual(calls, ['show', 'hide'], 'leaving it stops the listeners');
  f('data');
  assert.deepStrictEqual(calls, ['show', 'hide'], 'an old #data link lands on the Brief and starts nothing');
  f('kalshi');
  assert.deepStrictEqual(calls, ['show', 'hide', 'show'], 'and coming back starts them once');
};

// D11: a skipped minute is said plainly on the Bot page, a 429 explains itself, and every other note is untouched.
gates.D11 = () => {
  const f = lift(['kalTime', 'kalDate', 'kalDayKey', 'kalshiWhen', 'kalshiMarketLines', 'kalshiSkipNote'], "var KAL_SERIES_NAMES = { GOLD: 'Gold', DOGE: 'Dogecoin' };");
  const now = Date.UTC(2026, 9, 22, 17, 0), tick = Date.UTC(2026, 9, 22, 16, 58);
  const skip = f.kalshiSkipNote('The balance could not be read (HTTP 429), so nothing was sent.', tick, now);
  assert.ok(/^Skipped a minute/.test(skip) && skip.includes('HTTP 429') && /asked once more/.test(skip) && /looks again every minute/.test(skip), 'a refused read is explained: ' + skip);
  const other = f.kalshiSkipNote('The balance could not be read (HTTP 500), so nothing was sent.', tick, now);
  assert.ok(/^Skipped a minute/.test(other) && !/asked once more/.test(other), 'another failure is a skip too, without the 429 line');
  const lines = f.kalshiSkipNote('KXGOLD15M-26OCT231200-00: filled; KXDOGE15M-26OCT231200-00: another crypto market already holds this window', tick, now);
  assert.strictEqual(lines, 'Gold: Bought\nDogecoin: Another crypto market already holds this window', 'a minute with several markets reads as one short line per market, not a wall of tickers');
  const shard = f.kalshiSkipNote('KXGOLD15M-26OCT231200-00: filled; KXDOGE15M-26OCT231200-00: only $0.00 on its shard, and money on another shard does not count; KXGOLD15M-26OCT231215-00: only $0.00 on its shard, and money on another shard does not count', tick, now);
  assert.strictEqual(shard, 'Gold: Bought\nDogecoin and Gold: no money on their account shard, so skipped. Move funds there in Kalshi to trade them.', 'markets with no money on their shard are said once, plainly, not as an alarm each minute: ' + shard);
  const watching = 'Watching. Orders go in about 6 minutes before a close, and no market is at that point right now.';
  assert.strictEqual(f.kalshiSkipNote(watching, tick, now), watching, 'an ordinary note is shown as written');
  assert.strictEqual(f.kalshiSkipNote(undefined, tick, now), '', 'no note, no line');
};

// D13: the printable statement. Consequence: a month's figures on paper are the same ones the Data page shows, only that month's settled trades are in it, it is plain (no script, no control) and says it is not advice.
gates.D13 = () => {
  const f = lift(['kalDayKey', 'kalDateTime', 'kalshiMoneyRaw', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPerfStats', 'dataMarketRows', 'kalshiStatementMonth', 'kalshiStatementHtml']);
  assert.strictEqual(f.kalshiStatementMonth(Date.UTC(2026, 9, 22, 18), 0), '2026-10', 'this month on the Central clock');
  assert.strictEqual(f.kalshiStatementMonth(Date.UTC(2026, 9, 22, 18), 1), '2026-09', 'last month');
  assert.strictEqual(f.kalshiStatementMonth(Date.UTC(2026, 0, 5, 18), 1), '2025-12', 'January looks back to December of the year before');
  assert.strictEqual(f.kalshiStatementMonth(Date.UTC(2026, 10, 1, 3), 0), '2026-10', '11pm on Oct 31 in Chicago is still October');
  const o = (ts, series, side, price, c, p) => ({ ts, series, side, price, settled: true, fillCount: c, settledPnl: p });
  const orders = [o(Date.UTC(2026, 9, 10, 15), 'KXGOLD15M', 'yes', 0.93, '4.00', 0.28), o(Date.UTC(2026, 9, 12, 15), 'KXGOLD15M', 'no', 0.9, '4.00', -3.6), o(Date.UTC(2026, 8, 30, 15), 'KXBTC15M', 'yes', 0.9, '1.00', 0.1),
    { ts: Date.UTC(2026, 9, 13, 15), series: 'KXBTC15M', settled: false, fillCount: '1.00' }];
  const html2 = f.kalshiStatementHtml(orders, '2026-10', Date.UTC(2026, 9, 22, 18), esc);
  assert.ok(/October 2026/.test(html2) && /Settled trades<\/td><td class="r">2</.test(html2), 'only the two October settled trades are in it: ' + html2.replace(/<[^>]*>/g, ' ').slice(0, 220));
  assert.ok(html2.includes('-$3.32') && html2.includes('+$0.28') && html2.includes('-$3.60'), 'the result and each trade are shown with their sign');
  assert.ok(html2.includes('0.08') && html2.includes('50.0%'), 'profit factor 0.28 / 3.60 = 0.08 and a 50% win rate');
  assert.ok(!/KXBTC|Bitcoin/.test(html2), 'a September trade and an unsettled one are not in it');
  assert.ok(!/<script|<button|<input|<select/i.test(html2), 'a plain document');
  assert.ok(/Nothing in this statement is investment, financial, legal or tax advice/.test(html2) && /substantial risk of loss/.test(html2), 'it carries the disclosure');
  assert.ok(/No settled trades in this month/.test(f.kalshiStatementHtml(orders, '2026-08', Date.UTC(2026, 9, 22, 18), esc)), 'an empty month says so');
  assert.ok(/kalStmtPrint/.test(html) && !/id="kalStmtPrint"[\s\S]{0,40}page-data/.test(html), 'the print button is in the Tools menu');
  const page = html.slice(html.indexOf('<main class="page" id="page-data"'), html.indexOf('<main class="page" id="page-settings"'));
  assert.ok(!/kalStmt/.test(page), 'and not on the read only Data page');
};

// D12: today's result as a share of the account. Consequence: a +$0.80 day on a $203.48 account is +0.39%, measured against where the day started, and an unknown balance shows nothing rather than a wrong percentage.
gates.D12 = () => {
  const f = lift(['kalshiTodayPct']);
  assert.strictEqual(f.kalshiTodayPct(0.8, 203.48), ' (+0.39%)', 'the base is the total minus today: 0.80 / 202.68');
  assert.strictEqual(f.kalshiTodayPct(-2, 200), ' (-0.99%)', 'a loss shows its sign: -2 / 202');
  assert.strictEqual(f.kalshiTodayPct(0, 200), ' (+0.00%)');
  assert.strictEqual(f.kalshiTodayPct(1, null), '', 'unknown balance: nothing');
  assert.strictEqual(f.kalshiTodayPct(5, 5), '', 'a start of zero: nothing');
  assert.ok(/kalshiTodayPct\(botNet/.test(html), 'the Today line uses it');
};


// DS: there is no Data page and no record card. Everything the Data page carried (tiles, tables, rings, folds, the headline, the rules on trial) is gone from the site.
gates.DS1 = () => {
  assert.ok(!/id="page-data"|data-page="data"/.test(html), 'there is no Data page and no nav button for it (removed Oct 24, 2026 at the owner\'s request)');
  ['dataHead', 'dataVerdict', 'dataTrial', 'dataNote', 'dataTiles', 'dataWeekly', 'dataStats', 'dataMarkets', 'dataLead', 'kalChartPie', 'kalChartBars', 'kalPerf', 'dataQa1', 'dataAgenda', 'dataLine', 'dataDots'].forEach((id) => assert.ok(!html.includes('id="' + id + '"'), id + ' is gone'));
  assert.ok(/data-card="pnl"[\s\S]*data-card="trades"/.test(html), 'the account result line sits above Recent trades on the Bot page');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
