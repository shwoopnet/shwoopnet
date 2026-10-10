'use strict';
// Bot tab layout: the latest five trades with a button for more, and cards that can be rearranged only on request.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

gates.Y1 = () => {
  assert.ok(/var kalshiLiveShow = \{ events: 12, fills: 5, page: 0, pageSize: 10 \};/.test(html), 'the trades card pages ten at a time, newest first');
  assert.ok(/data-trstep="newer"/.test(html) && /data-trstep="older"/.test(html) && !/data-more="fills"/.test(html), 'with Newer and Older page controls instead of Show more');
  assert.ok(/getAttribute\('data-trstep'\)/.test(html) && /kalshiLiveShow\.page \+= 1/.test(html) && /Math\.max\(0, kalshiLiveShow\.page - 1\)/.test(html), 'the buttons step the page, never below the first'); assert.ok(/o\.ts < oldestFill/.test(html) && /!\(o\.orderId && seenIds\[o\.orderId\]\)/.test(html), 'history adds the bot\'s older saved orders, never repeating one already shown from a fill');
};

gates.Y2 = () => {
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  assert.ok(/id="kalLayoutUnlock"/.test(html) && !/id="kalLayoutUnlock"[^>]*checked/.test(html), 'rearranging starts locked');
  assert.ok(!/unlock/.test(/function save\(skipSync\)\{([\s\S]*?)\n    \}/.exec(iife)[1]), 'the unlocked state is never saved, so a normal visit cannot be dragged by accident');
  assert.ok(/e\.target\.closest\(\x27\[data-card\]\x27\)/.test(iife) && /grid\.classList\.contains\('kal-unlocked'\)/.test(iife), 'dragging does nothing while locked');
  assert.ok(/draggable = on/.test(iife) && /data-move/.test(iife), 'cards are draggable only when unlocked, with arrows for touch screens');
  assert.ok(/DEFAULT_ORDER\.indexOf\(k\) > -1/.test(iife), 'an unknown card name in a saved order is ignored');
  assert.ok(/DEFAULT_ORDER\.forEach\(function\(k\)\{ if\(want\.indexOf\(k\) < 0\)/.test(iife), 'a card the saved order does not mention keeps its place');
  assert.ok(!/OPTIONAL = \[[^\]]*'account'/.test(html), 'the account and session cards still cannot be hidden, only moved');
};

gates.Y3 = () => {
  assert.ok(/if\(skipSync !== true && typeof syncUserSetting === 'function'\)\{ syncUserSetting\('kalBotLayout', layout, 300\); \}/.test(html), 'every change is saved to the account unless it just came from there');
  assert.ok(/kalBotLayout: \(s\.kalBotLayout && typeof s\.kalBotLayout === 'object'\) \? s\.kalBotLayout : null,/.test(html), 'and read back, only if it is an object');
  assert.ok(/window\.__kalBotLayout\.set\(shaped\.kalBotLayout\)/.test(html), 'applied on sign-in');
  assert.ok(/layout = next; apply\(\); save\(true\);/.test(html), 'without writing it straight back');
  assert.ok(/\['auto', '1', '2', '3', '4'\]\.indexOf\(String\(l\.cols\)\)/.test(html), 'a bad saved column count cannot get through');
};

// A drag must keep reordering when the pointer is in a gap between cards or over its own preview, and every dragover must accept the
// drop, or some browsers stop part way (a faded card that never makes way).
gates.Y4 = () => {
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  const over = /grid\.addEventListener\('dragover', function\(e\)\{([\s\S]*?)\n    \}\);/.exec(iife)[1];
  assert.ok(/e\.preventDefault\(\);/.test(over) && over.indexOf('e.preventDefault()') < over.indexOf('cardNear('), 'every dragover accepts the drop before anything else');
  assert.ok(/function cardNear\(x, y\)/.test(iife) && /if\(c === dragging\)\{ return; \}/.test(iife), 'the nearest other card is used when the pointer is in a gap');
  assert.ok(/dropEffect = 'move'/.test(over) && /grid\.addEventListener\('dragenter'/.test(iife), 'a move is announced on enter and over');
};

// Console layout: a rail (account, positions) beside one main column (books, the bot card with its performance, trades, detail, log), books tiles on top.
gates.Y5 = () => {
  const i = html.indexOf('id="kalTabBot"');
  const seg = html.slice(i, html.indexOf('</main>', i));
  const rail = /<div class="kal-rail">([\s\S]*?)\n      <\/div>\n      <div class="kal-main">/.exec(seg);
  assert.ok(rail, 'the rail is there and the main column follows it');
  const names = (t) => [...t.matchAll(/data-card="(\w+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(names(rail[1]), ['account', 'positions'], 'the rail holds the account (with the performance stats) and the positions');
  const main = seg.slice(seg.indexOf('<div class="kal-main">'));
  assert.deepStrictEqual(names(main), ['books', 'performance', 'trades'], 'the main column: books tiles, the charts and the trades (the bot card is gone; its controls sit in the account card)');
  const acct = /data-card="account">([\s\S]*?)\n      <div class="kal-card" data-card="positions">/.exec(rail[1])[1];
  for (const id of ['kalL1Pill', 'kalL1Start', 'kalBotHalt', 'kalFlatten', 'kalL1Status']) assert.ok(acct.indexOf('id="' + id + '"') > -1, id + ' lives in the account card, so start, pause and flatten are always one click away');
  assert.ok(/data-card="account">\s*<div class="kal-card-head kal-acct-head">[\s\S]*?id="kalL1Pill"/.test(rail[1]), 'the running pill sits at the top right of the account card');
  assert.ok(!/data-card="session"/.test(html), 'there is no separate bot card any more');
  const perf = /data-card="performance">([\s\S]*?)\n      <div class="kal-card kal-card-flush" data-card="trades">/.exec(main)[1];
  for (const id of ['kalChartLine', 'kalChartPie', 'kalChartBars', 'kalChartRange']) assert.ok(perf.indexOf('id="' + id + '"') > -1, id + ' lives in the charts card on the bot page');
  assert.ok(!/id="kalPerf"/.test(perf) && /data-card="account">[\s\S]*id="kalPerf"/.test(rail[1]), 'the stat tiles and tables sit in the account card in the rail');
  const trades = /data-card="trades">([\s\S]*)$/.exec(main)[1];
  assert.ok(!/kalChart|kalPerf/.test(trades) && /id="kalBotClosed"/.test(trades), 'the trades card is the table only');
  const page = html.slice(html.indexOf('id="page-kalshi"'), html.indexOf('id="kalTabBot"'));
  const tools = /id="kalTools"[\s\S]*?<\/details>\s*<details class="kal-layout" id="kalLayout"/.exec(page)[0];
  for (const id of ['kalAcctRefresh', 'kalDiagCopy', 'kalBookDownload', 'kalAcctStart', 'kalAcctBody']) assert.ok(tools.indexOf('id="' + id + '"') > -1, id + ' moved into the Tools menu in the header');
  assert.ok(/\.kal-console\{ grid-template-columns:340px minmax\(0,1fr\);/.test(html), 'a fixed-width rail and a flexible main column');
  assert.ok(/@media \(max-width:900px\)\{\s*\.kal-console\{ grid-template-columns:minmax\(0,1fr\); \}/.test(html), 'one column on a narrow screen, the rail first');
};

// The account re-sends its saved layout on every update to the user document. It must not undo a drag in progress, or a move that has not
// reached the account yet (the card would snap straight back), and a copy it already applied is not applied again.
gates.Y6 = () => {
  const set = /set: function\(l\)\{([\s\S]*?)\n      \}\n    \};/.exec(html)[1];
  assert.ok(/var key = JSON\.stringify\(l\);\s*if\(key === lastRemote\)\{ return; \}/.test(set), 'a copy already applied is not applied again');
  assert.ok(/if\(dragging \|\| Date\.now\(\) - localDirtyAt < 4000\)\{ return; \}/.test(set), 'ignored during a drag and just after our own change');
  assert.ok(/lastRemote = key;/.test(set) && set.indexOf('lastRemote = key') > set.indexOf('localDirtyAt'), 'only a copy that was actually applied is remembered');
  assert.ok(/if\(skipSync !== true\)\{ localDirtyAt = Date\.now\(\); \}/.test(html), 'our own changes mark the layout as ahead of the account');
  assert.ok(/kal-unlocked > \.kal-card\{[^}]*user-select:none/.test(html), 'text inside a card cannot be picked up instead of the card');
};

// The history lists each order once, and the counts cover the whole session, not the newest 20 orders.
gates.Y7 = () => {
  assert.ok(/collection\(db, 'kalshiLiveOrders'\), orderBy\('ts', 'desc'\), limit\(1000\)/.test(html), 'orders are read for several days of a 24/7 bot, not 20');
  assert.ok(!/kalshiLiveOrders'\), orderBy\('ts', 'desc'\), limit\(20\)/.test(html));
  assert.ok(!/var loggedOrders|kalBotEvents/.test(html), 'the event log, and the dedupe that only it needed, are gone');
};

// The helpers behind the trades table and the two charts. All pure: they read nothing from the page.
gates.Y8 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalTime', 'kalDate', 'kalDateTime', 'kalDayKey', 'kalshiShortTicker', 'kalshiWhen', 'kalshiOrderPnl', 'kalshiOutcomeCounts', 'kalshiPnlSeries', 'kalshiLineSvg', 'kalshiDonutHtml']);
  const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
  // Ticker to a time. An unfamiliar ticker or an impossible time is shown as it is, never invented.
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT072015-15'), 'BTC 7:15 PM CT');
  assert.strictEqual(f.kalshiShortTicker('KXGOLD15M-26OCT070000-00'), 'GOLD 11:00 PM CT');
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT071200-00'), 'BTC 11:00 AM CT');
  assert.strictEqual(f.kalshiShortTicker('SOMETHING-ELSE'), 'SOMETHING-ELSE');
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT072575-15'), 'KXBTC15M-26OCT072575-15');
  // Today, tomorrow, later; nothing for a bad date.
  const noon = new Date(2026, 9, 7, 12, 0, 0).getTime();
  assert.ok(!/Tomorrow|Oct/.test(f.kalshiWhen(noon + 3600000, noon)) && /^Tomorrow /.test(f.kalshiWhen(noon + 86400000, noon)) && /^Oct 9 /.test(f.kalshiWhen(noon + 2 * 86400000, noon)));
  assert.strictEqual(f.kalshiWhen(NaN, noon), '');
  // Times are Central whatever the browser's zone: 2026-10-07 17:15 UTC is 12:15 PM CDT, and in January 18:15 UTC is 12:15 PM CST.
  assert.strictEqual(f.kalTime(Date.UTC(2026, 9, 7, 17, 15)), '12:15 PM');
  assert.strictEqual(f.kalTime(Date.UTC(2026, 0, 7, 18, 15)), '12:15 PM');
  assert.strictEqual(f.kalDateTime(Date.UTC(2026, 9, 8, 3, 30)), 'Oct 7, 10:30 PM CT', 'a late evening Central time is still the same Central day');
  assert.strictEqual(f.kalDate(Date.UTC(2026, 9, 8, 3, 30)), 'Oct 7');
  // An order's P/L is only what the server saved once it settled; nothing is worked out from prices here.
  assert.strictEqual(f.kalshiOrderPnl({ settled: true, fillCount: '1.00', settledPnl: 0.08 }), 0.08);
  assert.strictEqual(f.kalshiOrderPnl({ settled: true, fillCount: '1.00' }), null, 'settled with no saved figure is not guessed');
  assert.strictEqual(f.kalshiOrderPnl({ settled: true, fillCount: '0.00', settledPnl: 0 }), null, 'an unfilled order has no P/L');
  assert.strictEqual(f.kalshiOrderPnl({ fillCount: '1.00', settledPnl: 0.08 }), null, 'an order that has not settled has none yet');
  // Outcome counts: won, lost, open, no fill; only the session's orders.
  const o = (ts, status, side, result, fill) => ({ ts, status, side, result, settled: result ? true : undefined, fillCount: fill });
  const c = f.kalshiOutcomeCounts([o(5, 'filled', 'no', 'no', '1'), o(6, 'filled', 'yes', 'no', '1'), o(7, 'filled', 'no', null, '1'), o(8, 'no fill', 'yes', null, '0'), o(9, 'error', 'yes', null, '0'), o(1, 'filled', 'no', 'no', '1'), null], 5);
  assert.deepStrictEqual(c, { won: 1, lost: 1, open: 1, noFill: 1, other: 1 }, 'older orders are left out, an errored one is "other"');
  // The running line: oldest first, cumulative, only settled trades.
  const ser = f.kalshiPnlSeries([{ ts: 3, settled: true, fillCount: '1', settledPnl: -0.93 }, { ts: 1, settled: true, fillCount: '1', settledPnl: 0.08 }, { ts: 2, settled: true, fillCount: '1', settledPnl: 0.09 }, { ts: 4, fillCount: '1' }], 0);
  assert.deepStrictEqual(ser.map((p) => [p.pnl, p.cum]), [[0.08, 0.08], [0.09, 0.17], [-0.93, -0.76]], 'cumulative in time order, the unsettled trade is not in it');
  // The chart: nothing to draw below two points; a loss ends red; text from the page is escaped.
  assert.ok(/two settled trades/.test(f.kalshiLineSvg([{ cum: 1, pnl: 1, t: 1 }], esc, money)));
  const svg = f.kalshiLineSvg(ser, esc, money);
  assert.ok(/<svg/.test(svg) && /stroke="var\(--loss\)"/.test(svg) && /-\$0\.76/.test(svg) && /3 settled trades/.test(svg), 'a falling line is red and labelled with where it ended');
  assert.ok(/stroke="var\(--gain\)"/.test(f.kalshiLineSvg([{ cum: 0.1, pnl: 0.1, t: 1 }, { cum: 0.2, pnl: 0.1, t: 2 }], esc, money)), 'a rising line is green');
  // The pie: no orders says so; slices add to the whole; zero slices are left out.
  assert.ok(/No orders yet/.test(f.kalshiDonutHtml({ won: 0, lost: 0, open: 0, noFill: 0, other: 0 }, esc)));
  const pie = f.kalshiDonutHtml({ won: 8, lost: 1, open: 1, noFill: 4, other: 0 }, esc);
  assert.ok(/>14<\/text>/.test(pie) && /Won<\/span><b>8<\/b>/.test(pie) && /57%/.test(pie) && (pie.match(/stroke-dasharray="/g) || []).length === 4, 'the total, each slice, its share');
  const pie2 = f.kalshiDonutHtml({ won: 3, lost: 0, open: 0, noFill: 0, other: 0 }, esc);
  assert.ok(!/Lost<\/span>/.test(pie2) && /100%/.test(pie2) && (pie2.match(/stroke-dasharray="/g) || []).length === 1, 'a slice of zero is not drawn');
};

// The performance tracker: a loss is settled and drawn like a win, even when the server never marked it, and the numbers are the plain arithmetic of the trades.
gates.Y14 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalshiOrderPnl', 'kalshiOutcomeCounts', 'kalshiPnlSeries', 'kalshiTradePnl', 'kalDateTime', 'kalshiResolveOrders', 'kalshiPerfStats', 'kalshiBarsSvg', 'kalshiPerfHtml']);
  const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
  // A filled order the server left unsettled: with the market's result known it is settled here, by the server's own rule.
  const lost = { ts: 3, ticker: 'T-L', side: 'yes', status: 'filled', fillCount: '2.00', count: 2, maxCost: 1.86, price: 0.93, series: 'KXBTC15M' };
  const won = { ts: 1, ticker: 'T-W', side: 'no', status: 'filled', fillCount: '2.00', count: 2, maxCost: 1.84, price: 0.92, series: 'KXGOLD15M' };
  const open = { ts: 4, ticker: 'T-O', side: 'yes', status: 'filled', fillCount: '1.00', count: 1, maxCost: 0.93, price: 0.93, series: 'KXBTC15M' };
  const res = f.kalshiResolveOrders([won, lost, open], { 'T-L': 'no', 'T-W': 'no' });
  assert.strictEqual(res[1].settledPnl, -1.86, 'a loss costs the whole order');
  assert.strictEqual(res[0].settledPnl, 0.16, 'a win pays $1 a contract less what was paid');
  assert.strictEqual(res[2].settled, undefined, 'a market with no known result stays open');
  assert.strictEqual(lost.settled, undefined, 'the stored order is not changed');
  const server = Object.assign({}, lost, { settled: true, result: 'no', settledPnl: -1.8 });
  assert.strictEqual(f.kalshiResolveOrders([server], { 'T-L': 'yes' })[0].settledPnl, -1.8, 'what the server saved wins');
  // The account's own fill, when the read has it, replaces the estimate: price actually paid and the fee Kalshi charged, the figure the trades table shows.
  const withId = Object.assign({}, lost, { orderId: 'ord-1', averageFeePaid: '0.0100' });
  const ex = f.kalshiResolveOrders([withId], { 'T-L': 'no' }, [{ orderId: 'ord-1', count: 2, price: '0.9300' }])[0];
  assert.strictEqual(ex.settledPnl, -1.88, 'two contracts at 93c plus a cent of fee each, lost');
  assert.ok(ex.exact === true && ex.estimated === false);
  const exWin = f.kalshiResolveOrders([Object.assign({}, withId, { side: 'no' })], { 'T-L': 'no' }, [{ orderId: 'ord-1', count: 2, price: '0.0700' }])[0];
  assert.strictEqual(exWin.settledPnl, 0.12, 'a NO bought at a 7c YES price costs 93c, pays $1 and a cent of fee, on two contracts');
  const sv = f.kalshiResolveOrders([Object.assign({}, server, { orderId: 'ord-2', averageFeePaid: '0.0100' })], null, [{ orderId: 'ord-2', count: 2, price: '0.9300' }])[0];
  assert.ok(sv.exact === true && sv.settledPnl === -1.88, 'a trade the server settled also takes the exact figure');
  assert.deepStrictEqual(f.kalshiOutcomeCounts(res, 0), { won: 1, lost: 1, open: 1, noFill: 0, other: 0 }, 'the loss reaches the pie');
  const series = f.kalshiPnlSeries(res, 0);
  assert.deepStrictEqual(series.map((p) => p.pnl), [0.16, -1.86], 'and the line');
  const bars = f.kalshiBarsSvg(series, esc, money);
  assert.ok(/fill="var\(--gain\)"/.test(bars) && /fill="var\(--loss\)"/.test(bars) && /1 won, 1 lost/.test(bars), 'a green bar for the win and a red bar for the loss');
  assert.ok(/after the first settled trade/.test(f.kalshiBarsSvg([], esc, money)));
  // The tracker's arithmetic.
  const t = (ts, pnl, series, price) => ({ ts, settled: true, fillCount: '1', settledPnl: pnl, series, price });
  const st = f.kalshiPerfStats([t(1, 0.08, 'KXBTC15M', 0.92), t(2, 0.08, 'KXGOLD15M', 0.91), t(3, -0.92, 'KXBTC15M', 0.92), t(4, -0.92, 'KXBTC15M', 0.94), t(5, 0.06, 'KXGOLD15M', 0.96), t(6, null, 'KXBTC15M', 0.9)], 0);
  assert.strictEqual(st.n, 5, 'an order with no settled figure is not a trade');
  assert.deepStrictEqual([st.wins, st.losses], [3, 2]);
  assert.strictEqual(Math.round(st.total * 100) / 100, -1.62);
  assert.strictEqual(Math.round(st.winRate * 100), 60);
  assert.strictEqual(Math.round(st.profitFactor * 100) / 100, 0.12, 'gross wins over gross losses');
  assert.strictEqual(Math.round(st.maxDrawdown * 100) / 100, 1.84, 'the deepest fall from a peak');
  assert.strictEqual(st.longestLoss, 2);
  assert.deepStrictEqual([st.streak.kind, st.streak.n], ['win', 1], 'the run in progress');
  assert.strictEqual(Math.round(st.worst * 100) / 100, -0.92);
  assert.deepStrictEqual(st.bySeries.map((r) => [r.label, r.n]), [['Bitcoin', 3], ['Gold', 2]]);
  assert.deepStrictEqual(st.byBand.map((r) => [r.label, r.n]), [['90c to 92c', 1], ['92c to 95c', 3], ['95c to 97c', 1]], 'by the price paid');
  assert.strictEqual(f.kalshiPerfStats([t(1, 0.08, 'KXBTC15M', 0.92)], 0).profitFactor, null, 'no losses: no profit factor, not an infinite one');
  assert.strictEqual(f.kalshiPerfStats([], 0).n, 0);
  assert.ok(/fills in after the first settled trade/.test(f.kalshiPerfHtml(f.kalshiPerfStats([], 0), esc, money)));
  const out = f.kalshiPerfHtml(st, esc, money);
  assert.ok(/-\$1\.62/.test(out) && /60% \(3 \/ 2\)/.test(out) && /By price paid/.test(out) && /By market/.test(out), 'the tiles and tables show the figures');
  assert.ok(/id="kalChartBars"/.test(html) && /id="kalPerf"/.test(html) && /id="kalChartRange"/.test(html), 'the page has the bar chart, the tracker and the range choice');
  // In this palette --ink is the page background and --paper is the text colour (inverted names), and --card does not exist: a select using them showed dark text on dark in dark mode.
  const sel = /\.kal-perf-head select\{ font:inherit;[^}]*\}/.exec(html)[0];
  assert.ok(/color:var\(--paper\)/.test(sel) && /background:var\(--panel\)/.test(sel) && !/--card|color:var\(--ink\)/.test(sel), 'the range choice is readable in both themes');
  assert.ok(!/var\(--card\)/.test(html), 'no rule uses a variable that is not defined');
  assert.ok(/kalshiResolveOrders\(kalshiLiveOrders, kalshiLiveAcct && kalshiLiveAcct\.results\)/.test(html), 'the charts read orders settled against the account read');
};

// Open positions, one readable row each: the side from the sign, cost from the bot's own fill, what it can win and lose, the chance now and the time left from
// the live books. "Realized" and "Fees" are gone (an open position has no realized result). Show more / Show fewer are quiet links, not filled buttons.
gates.Y15 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalshiShortTicker', 'kalshiSecsLeft', 'kalshiFmtLeft', 'kalshiGroupFills', 'kalshiOrderFor', 'kalshiPositionRows', 'kalshiPositionsHtml']);
  const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
  const NOW = Date.parse('2026-10-08T14:40:00Z');
  const T = 'KXBTC15M-26OCT081045-45';
  const orders = [{ orderId: 'o1', ticker: T, side: 'no', fillCount: '2.00' }];
  const fills = [{ ticker: T, orderId: 'o1', count: 2, price: '0.0420' }];
  const books = [{ ticker: T, closeTime: '2026-10-08T14:45:00Z', yesBid: 0.004, yesAsk: 0.005 }];
  const r = f.kalshiPositionRows([{ ticker: T, position: -2, realizedPnl: '0.000000', feesPaid: '0.005700' }], orders, fills, books, NOW)[0];
  assert.deepStrictEqual([r.side, r.count, r.entry, r.cost, r.ifWin, r.ifLose, r.bot], ['no', 2, 0.958, 1.92, 0.08, -1.92, true], 'a NO bought at a 4.2c YES price costs 95.8c a contract: $1.92, wins $0.08, loses $1.92');
  assert.strictEqual(Math.round(r.chance * 10000) / 10000, 0.9955, 'the chance now is the NO side of the live mid');
  assert.strictEqual(r.cashOut, 1.99, 'cashing out a NO sells at 1 minus the YES ask');
  assert.strictEqual(r.left, 300);
  const out = f.kalshiPositionsHtml([r], esc, money);
  assert.ok(/NO x 2/.test(out) && /Cost[\s\S]*\$1\.92/.test(out) && /\+\$0\.08/.test(out) && /-\$1\.92/.test(out) && /Chance now 99\.6%/.test(out) && /closes in 5:00/.test(out) && /about \$1\.99 before fees/.test(out), 'the row says it all');
  assert.ok(!/Realized|Fees/.test(out) && !/Realized|feesPaid/.test(html.slice(html.indexOf('function kalshiPositionsHtml'), html.indexOf('function renderKalshiBot'))), 'no realized or fee line on an open position');
  // A position the bot did not open, with no books: no invented figures.
  const manual = f.kalshiPositionRows([{ ticker: 'KXGOLD15M-26OCT081045-45', position: 3 }], orders, fills, [], NOW)[0];
  assert.deepStrictEqual([manual.side, manual.cost, manual.ifWin, manual.chance, manual.cashOut, manual.left, manual.bot], ['yes', null, null, null, null, null, false]);
  const mo = f.kalshiPositionsHtml([manual], esc, money);
  assert.ok(/n\/a/.test(mo) && /Not one of the bot/.test(mo) && !/Chance now/.test(mo));
  assert.ok(/No open positions/.test(f.kalshiPositionsHtml([], esc, money)) && f.kalshiPositionRows([{ ticker: 'X', position: 0 }], [], [], [], NOW).length === 0, 'a flat position is not a row');
  const yes = f.kalshiPositionRows([{ ticker: T, position: 1 }], [{ orderId: 'o2', ticker: T, side: 'yes' }], [{ ticker: T, orderId: 'o2', count: 1, price: '0.9300' }], [{ ticker: T, closeTime: '2026-10-08T14:45:00Z', yesBid: 0.96, yesAsk: 0.97 }], NOW)[0];
  assert.deepStrictEqual([yes.side, yes.entry, yes.cost, yes.ifWin, yes.cashOut], ['yes', 0.93, 0.93, 0.07, 0.96], 'a YES position is priced on the YES side');
  // The page keeps the positions in step with the books and the account.
  assert.ok(/kalshiBooksLast = data \|\| null;\s*renderKalshiPositions\(\);/.test(html) && /renderKalshiPositions\(\);\s*\n\s*var trEl/.test(html), 'redrawn when the books or the account update');
  // The Newer and Older page controls are quiet links, not the dark filled button.
  assert.ok(!/class="kal-btn" data-trstep/.test(html) && (html.match(/class="kal-link" data-trstep/g) || []).length === 2, 'quiet links');
  assert.ok(/\.kal-link\{ background:none; border:0;/.test(html), 'with no fill and no border');
};

// A card stays in its own column: reordering, arrows and dragging all work within the parent the card is in, never across the rail and the main column.
gates.Y9 = () => {
  const iife = html.slice(html.indexOf("var KEY = 'kalBotLayout'"), html.indexOf("document.getElementById('kalLayoutReset')"));
  assert.ok(/c\.parentNode\.appendChild\(c\)/.test(iife), 'a saved order puts each card back in its own column');
  assert.ok(/visibleCards\(card\.parentNode\)/.test(iife) && /card\.parentNode\.insertBefore\(card, cards\[j\]\)/.test(iife), 'arrows move a card within its column');
  assert.ok(/visibleCards\(dragging\.parentNode\)/.test(iife) && /dragging\.parentNode\.insertBefore\(dragging, want\)/.test(iife), 'a drag moves a card within its column');
  assert.ok(!/kalLayoutCols|colsSel/.test(html), 'no leftover column picker');
};

// Fit on a small screen: the account card lists only what the bot can spend (shard 2) and folds the rest into one line that appears only when it
// matters, the order switch only speaks up when it is off, the Layout menu sits in the header, and the session card keeps four facts.
gates.Y10 = () => {
  const acct = html.slice(html.indexOf("var useShard = "), html.indexOf("    el.innerHTML = h;"));
  assert.ok(/x\.shard === 2/.test(acct) && /Available to the bot/.test(acct), 'the line shown is the shard the bot can spend');
  assert.ok(/otherSum >= 0\.5 \?/.test(acct) && /not usable/.test(acct), 'other shards are one line, and only when there is real money on them');
  assert.ok(/a\.liveSwitch \? '' : '<div class="kal-rows"><div><span class="kal-k">Order switch<\/span><b class="kal-neg">OFF/.test(acct), 'the order switch is a line only when it is off');
  assert.ok(!/Shard ' \+/.test(acct), 'no per-shard rows');
  const head = html.slice(html.indexOf('id="page-kalshi"'), html.indexOf('id="kalTabBot"'));
  assert.ok(/id="kalLayout"/.test(head), 'the Layout menu is in the page header, not on a row of its own');
  assert.ok(!/kal-layout-bar/.test(html), 'no leftover row for it');
  assert.ok(/var doneLine = running \? 'Next look ' \+/.test(html) && /' orders: ' \+/.test(html) && !/kalL1Facts/.test(html), 'when it looks next, orders sent and filled against no fill are one line of the status, not a row of facts');
  assert.ok(/var sizeText = running \?/.test(html) && /Stops if down/.test(html), 'size and stop are part of the status line inside the bot menu, not a line on the page');
};

// The order diagnostics export: one row per order with what the bot saw when it decided, nothing invented, nothing secret, safe to paste.
gates.Y11 = () => {
  const m = /(function kalshiDiagnosticsCsv\(orders, limit\)\{[\s\S]*?\n  \})\n/.exec(html);
  assert.ok(m, 'builder not found');
  const csv = new Function(m[1] + '; return kalshiDiagnosticsCsv;')();
  const rows = (t) => t.split('\n');
  const head = rows(csv([]))[0].split(',');
  assert.deepStrictEqual(head.slice(0, 3), ['time', 'ticker', 'side'], 'a header even with no orders');
  assert.strictEqual(rows(csv([])).length, 1);
  const out = csv([
    { ts: 1000, ticker: 'T-A', side: 'no', price: 0.89, limit: 0.89, status: 'no fill', fillCount: '0.00', seen: { bid: 0.11, ask: 0.12, bidSize: 12, askSize: 3, at: 'x' } },
    { ts: 2000, ticker: 'T-B', side: 'yes', price: 0.92, limit: 0.92, status: 'filled', fillCount: '1.00', averageFeePaid: '0.0100', error: 'HTTP 400, "bad"' },
    null,
  ]);
  const r = rows(out);
  assert.strictEqual(r.length, 3, 'one row per order, junk skipped');
  assert.ok(r[1].startsWith('1970-01-01T00:00:02') && r[2].startsWith('1970-01-01T00:00:01'), 'newest first');
  const col = (line, name) => line.split(',')[head.indexOf(name)];
  assert.deepStrictEqual([col(r[2], 'seenBid'), col(r[2], 'seenAsk'), col(r[2], 'bidSize'), col(r[2], 'askSize')], ['0.11', '0.12', '12', '3'], 'what the book showed is carried through');
  assert.strictEqual(col(r[1], 'seenAsk'), '', 'a record with no book data leaves the cells empty, not zero');
  assert.strictEqual(col(r[1], 'avgFee'), '0.0100', 'the fee Kalshi charged is carried through, so the rounding of fees to the cent can be checked against real orders');
  assert.ok(/"HTTP 400, ""bad"""/.test(r[1]), 'commas and quotes in text are escaped so a row cannot break');
  const big = csv(Array.from({ length: 400 }, (_, i) => ({ ts: i, ticker: 'T' + i })), 150);
  assert.strictEqual(rows(big).length, 151, 'at most 150 rows');
  assert.ok(!/orderId|clientOrderId|key|secret/i.test(head.join(',')), 'no ids that identify the account and no keys');
  assert.ok(/id="kalDiagCopy"/.test(html) && /navigator\.clipboard\.writeText\(csv\)/.test(html) && /id="kalDiagBox"/.test(html), 'a button, with a manual fallback box');
};

// The book snapshot export: one row per snapshot, best level first, empty (never zero) where a side has no book, and only the admin can run it.
gates.Y12 = () => {
  const m = /(function kalshiBookCsv\(minuteDocs\)\{[\s\S]*?\n  \})\n/.exec(html);
  assert.ok(m, 'builder not found');
  const build = new Function(m[1] + '; return kalshiBookCsv;')();
  const head = build([]).csv.split('\n')[0].split(',');
  assert.deepStrictEqual([build([]).minutes, build([]).snaps, build([]).csv.split('\n').length], [0, 0, 1], 'a header and nothing else when empty');
  const r = build([
    { ts: 60000, snaps: [
      { t: 61000, s: 'KXBTC15M', k: 'T-A', ly: 0.82, la: 0.83, yb: 0.91, ya: 0.92, nb: 0.08, na: 0.09, yd: 30, nd: 12, yl: [{ p: 0.89, q: 5 }, { p: 0.9, q: 10 }, { p: 0.91, q: 15 }], nl: [[0.07, 4], [0.08, 8]] },
      { t: 62000, s: 'KXGOLD15M', k: 'T-B', yb: null, ya: null, nb: 0.5, na: null, yd: 0, nd: 7, yl: [], nl: [[0.5, 7]] } ] },
    { ts: 120000, snaps: 'junk' }, null, { ts: 130000 },
  ]);
  const lines = r.csv.split('\n'), col = (line, n) => line.split(',')[head.indexOf(n)];
  assert.deepStrictEqual([r.minutes, r.snaps, lines.length], [1, 2, 3], 'junk documents are skipped, one row per snapshot');
  assert.deepStrictEqual(['y1p', 'y1q', 'y2p', 'y3p'].map((n) => col(lines[1], n)), ['0.91', '15', '0.9', '0.89'], 'the best level comes first');
  assert.deepStrictEqual(['n1p', 'n2p', 'n3p', 'n3q'].map((n) => col(lines[1], n)), ['0.08', '0.07', '', ''], 'a missing level is empty');
  assert.deepStrictEqual(['yesBid', 'yesAsk', 'y1p', 'y1q'].map((n) => col(lines[2], n)), ['', '', '', ''], 'a side with no book is empty, never 0');
  assert.strictEqual(col(lines[2], 'noAsk'), '', 'an implied price that is null stays empty');
  assert.ok(/getDocs\(query\(collection\(db, 'kalshiBookSnaps'\), where\('ts', '>=', sinceMs\), orderBy\('ts', 'asc'\), limit\(1500\)\)\)/.test(html), 'reads only the recorder documents, oldest first, bounded');
  const h = html.slice(html.indexOf("document.getElementById('kalBookDownload').addEventListener"));
  assert.ok(/!currentUserIsAdmin\)\{ msg\.textContent = 'Not available/.test(h.slice(0, 600)), 'only the admin can run it');
  assert.ok(/CompressionStream\('gzip'\)/.test(h) && /kalshi-books-' \+ stamp \+ '\.csv'/.test(h), 'compressed when the browser can, plain CSV when not');
};

// An empty export says WHY: never saved, stopped, Kalshi reads failing, or saved elsewhere than expected. Nothing is guessed.
gates.Y13 = () => {
  const m = /(function kalshiBookExportNote\(docs, status, hours, now\)\{[\s\S]*?\n  \})\n/.exec(html);
  assert.ok(m, 'not found');
  const note = new Function(m[1] + '; return kalshiBookExportNote;')();
  const NOW = 10 * 3600000;
  assert.strictEqual(note([{ ts: 1, snaps: [{ t: 1 }] }], null, 6, NOW), '', 'data present: nothing to say');
  assert.ok(/never saved anything/.test(note([], null, 6, NOW)) && /kalshiBookRecorder/.test(note([], null, 6, NOW)), 'no heartbeat at all: not deployed or not running');
  assert.ok(/has stopped/.test(note([], { lastTickMs: NOW - 3600000, snaps: 0, errs: 5 }, 6, NOW)) && /60 minutes ago/.test(note([], { lastTickMs: NOW - 3600000 }, 6, NOW)), 'an old heartbeat: stopped, and when');
  assert.ok(/no minute documents/.test(note([], { lastTickMs: NOW - 60000, snaps: 12, errs: 0 }, 6, NOW)), 'a fresh heartbeat but no documents: a write problem');
  const failing = note([{ ts: 1, snaps: [], errs: [{ e: 'HTTP 403' }] }, { ts: 2, snaps: [], errs: [] }], { lastTickMs: NOW }, 6, NOW);
  assert.ok(/2 minute documents/.test(failing) && /reads are failing/.test(failing) && /HTTP 403/.test(failing), 'documents with no snapshots: the reads are failing, with the first error');
  assert.ok(/kalshiBookStatus/.test(html) && /kalshiBookExportNote\(docs, both\[1\], hours, Date\.now\(\)\)/.test(html), 'the button uses it, and reads the heartbeat');
  assert.ok(/getDoc\(doc\(db, 'kalshiBookMeta', 'status'\)\)/.test(html), 'the heartbeat is the recorder\'s own status document');
};

// The tiny chart under each market row: a line across the market's 15 minute window, the strike drawn and kept in range, and nothing drawn from too little data.
gates.Y16 = () => {
  const m = /(function kalshiSparkSvg\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html);
  assert.ok(m, 'kalshiSparkSvg found');
  const escapeHtml = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  const spark = new Function('escapeHtml', m[1] + '; return kalshiSparkSvg;')(escapeHtml);
  const from = 1000000, to = from + 900000, fmt = (v) => '$' + Math.round(v);
  const pts = [0, 1, 2, 3].map((i) => ({ t: from + i * 60000, v: 82500 + i * 10 }));
  assert.ok(/kal-empty/.test(spark([], { from, to, fmt })), 'no point draws nothing');
  const one = spark([pts[0]], { from, to, fmt });
  assert.ok(/<circle/.test(one) && !/kal-empty/.test(one) && /\$82500/.test(one), 'one reading is a dot and its price, not an empty box');
  assert.ok(/kal-empty/.test(spark(pts.map((p) => ({ t: p.t + 5e6, v: p.v })), { from, to, fmt })), 'points from outside the window are not drawn');
  const svg = spark(pts, { from, to, ref: 82676, refLabel: 'to beat', fmt });
  assert.ok(/to beat/.test(svg) && /stroke-dasharray/.test(svg) && /var\(--loss\)/.test(svg), 'strike drawn, and the line is red while the price is under it');
  assert.ok(/var\(--gain\)/.test(spark(pts, { from, to, ref: 82400, fmt })), 'green when over it');
  const ys = [...svg.matchAll(/ y1="([\d.]+)"/g)].map((x) => Number(x[1]));
  assert.ok(ys.length === 1 && ys[0] >= 0 && ys[0] <= 86, 'a strike far above the price stays inside the chart');
  assert.ok(/kalshiSparkFor\(m\) \+ '<\/div>'/.test(html), 'each market row carries its chart');
  assert.ok(/fetch\('https:\/\/api\.gold-api\.com\/price\/XAU'\)/.test(html) && /m\.series === 'KXGOLD15M' && m\.strike != null && !kalshiGold\.failed/.test(html), 'gold draws its price against the strike, and falls back to the YES line if the feed fails');
  assert.ok(/now - kalshiGold\.at < 10000/.test(html), 'the gold feed is asked at most every 10 seconds');
  // History plus live readings, so a chart is never empty right after a market opens.
  const join = new Function(/(function kalshiJoinSeries\(a, b\)\{[\s\S]*?\n  \})\n/.exec(html)[1] + '; return kalshiJoinSeries;')();
  const j = join([{ t: 3000, v: 3 }, { t: 1000, v: 1 }], [{ t: 3400, v: 99 }, { t: 5000, v: 5 }, { t: NaN, v: 1 }, { t: 6000, v: undefined }]);
  assert.deepStrictEqual(j.map((p) => p.t), [1000, 3000, 5000], 'joined in time order, one reading a second at most, junk dropped');
  assert.ok(/fetch\('https:\/\/api\.exchange\.coinbase\.com\/products\/' \+ product \+ '\/ticker'\)/.test(html) && /kalshiTicker\('BTC-USD'\)/.test(html) && /kalshiCandles\('PAXG-USD', now\)/.test(html), 'Bitcoin has a live ticker and gold has minute history, both from Coinbase');
  assert.ok(/kalshiGold\.off = v - p/.test(html) && /v: p\.v \+ off/.test(html), 'gold history is shifted so the line ends on the real gold price');
};

// The default landing page can be Kalshi, for the admin only: the button is hidden until the account is known to be the admin, and because that is
// known only after the first screen is up, a Kalshi preference shows the brief first and moves to Kalshi when the admin check comes back.
gates.Y17 = () => {
  assert.ok(/<button class="tf-btn" data-value="kalshi" id="landingKalshiBtn" hidden>Kalshi<\/button>/.test(html), 'a Kalshi choice exists and starts hidden');
  assert.ok(/landKal\.hidden = !currentUserIsAdmin/.test(html), 'it is shown only to the admin');
  const init = html.slice(html.indexOf('(function initLanding(){'));
  assert.ok(/if\(pref === 'kalshi'\)\{[\s\S]*?landingKalshiPending = true;[\s\S]*?showPage\('brief'\);[\s\S]*?return;/.test(init), 'a Kalshi preference lands on the brief and marks the move as pending');
  const admin = html.slice(html.indexOf('function applyAdminUI(){'), html.indexOf("document.getElementById('generateInviteBtn')"));
  assert.ok(/currentUserIsAdmin && landingKalshiPending/.test(admin) && /!briefPage\.hidden && Date\.now\(\) - landingLoadedAt < 20000/.test(admin) && /showPage\('kalshi'\)/.test(admin), 'the move happens only for the admin, only if still on the first screen, and only within 20 seconds of loading');
  assert.ok(/pref === 'kalshi' && currentUserIsAdmin \? 'kalshi' : 'brief'/.test(html), 'the logo takes the admin home to Kalshi too, and anyone else to the brief');
  assert.ok(/if\(name === 'kalshi' && !currentUserIsAdmin\)\{ name = 'brief'; \}/.test(html), 'a non-admin can never be shown the Kalshi page, whatever is saved');
};

// The Account card says what one order risks right now (contracts times the latest order's cost per contract), and the profit tile is named so it cannot be mistaken for it.
gates.Y18 = () => {
  assert.ok(/Stake per trade/.test(html) && /var nC = ses\.sizing === true \? baseC \+ \(Number\.isFinite\(ses\.sizeAddon\) \? ses\.sizeAddon : 0\) : 1/.test(html) && /Math\.floor\(cashNow \* 0\.02 \/ perC/.test(html), 'the stake is the account-funded part (held to 2% of cash) plus the profit add-on outside it, or 1 when scaling is off');
  assert.ok(/Number\(lastO\.maxCost\) \/ Number\(lastO\.count\) : 0\.93/.test(html) && /stake \/ tb \* 100/.test(html), 'priced at the latest order\'s cost per contract, with its share of the balance');
  assert.ok(/if\(ses && ses\.active === true\)/.test(html), 'shown only while the bot is running');
  assert.ok(/tile\('Expectancy'/.test(html) && !/tile\('Per trade'/.test(html), 'the expectancy tile does not share the stake row name');
  assert.ok(/\(0\.05 \* base\)\.toFixed\(2\)/.test(html), 'the status line quotes the 5% stop');
};

// Y21: manual trades are hidden from the Recent trades card by default, with a small dropdown to bring them back.
gates.Y21 = () => {
  assert.ok(/data-trstep="newer"[\s\S]{0,260}'>&#8249;<\/button>/.test(html) && /data-trstep="older"[\s\S]{0,260}'>&#8250;<\/button>/.test(html) && !/>Newer<|>Older</.test(html), 'the page controls are arrows, with labels for screen readers');
  assert.ok(/id="kalTradeFilter"/.test(html) && /<option value="bot">bot trades<\/option><option value="all">bot and manual<\/option>/.test(html), 'a small Showing dropdown on the trades card, bot trades first');
  assert.ok(/var kalshiTradeFilter = 'bot';/.test(html), 'manual trades are hidden until the owner asks');
  assert.ok(/kalshiTradeFilter === 'all' \? gfills : gfills\.filter\(function\(x\)\{ return kalshiFillIsBot\(x, kalshiLiveOrders\); \}\)/.test(html), 'the filter drops manual fills only');
  assert.ok(/kalshiTradeFilter = sel\.value === 'all' \? 'all' : 'bot'; kalshiLiveShow\.page = 0;/.test(html), 'changing it returns to the first page');
};

// Y22: Mono Ink is an optional skin chosen under Settings, Theme. It only re-points tokens, never the gain or loss colors, and it is applied before first paint.
gates.Y22 = () => {
  const light = /html\[data-skin="mono"\]\{([\s\S]*?)\}/.exec(html)[1], dark = /html\[data-skin="mono"\]\[data-theme="dark"\]\{([\s\S]*?)\}/.exec(html)[1];
  assert.ok(/--paper: #000000/.test(light) && /--paper: #FFFFFF/.test(dark) && /--radius: 4px/.test(light), 'a light and a dark Mono Ink, with sharp corners');
  assert.ok(!/--gain|--loss/.test(light + dark), 'gain and loss colors are never overridden by a skin (--loss is the live trading safety color)');
  assert.ok(/shwoopnet:skin'\) === 'mono'\)\{ document\.documentElement\.setAttribute\('data-skin', 'mono'\)/.test(html), 'applied by the inline script before first paint');
  assert.ok(/id="skinChoice"/.test(html) && /data-value="ledger">Ledger</.test(html) && /data-value="mono">Mono Ink</.test(html), 'a Theme choice in Settings');
  assert.ok(/syncUserSetting\('skin', skin\)/.test(html) && /skin: s\.skin === 'mono' \? 'mono' : \(s\.skin === 'ledger' \? 'ledger' : null\)/.test(html) && /if\(shaped\.skin !== null\)\{ applySkinPref\(shaped\.skin, true\); \}/.test(html), 'synced with the account, and an unsynced account keeps the device choice');
};

// Y23: the Kalshi page uses more width on a wide monitor, and the other pages keep the 1400px column.
gates.Y23 = () => {
  assert.ok(/\.app\{ max-width: 1400px;/.test(html) && /\.app\.app-wide\{ max-width: 1640px; \}/.test(html), 'the base column stays 1400px; the wide class is 1640px');
  assert.ok(/appEl\.classList\.toggle\('app-wide', name === 'kalshi'\)/.test(html), 'only the Kalshi page turns it on, and every other page turns it off');
};

// Y24: the logo's ground flash sits inside the logo row, above the tagline, not across it.
gates.Y24 = () => {
  const rule = /\.brand-ground\{([\s\S]*?)\}/.exec(html)[1];
  assert.ok(/bottom:2px/.test(rule) && !/bottom:-/.test(rule), 'the flash line is above the tagline');
};


// Y20: no guessed size before the session's first look.
gates.Y20 = () => {
  assert.ok(/var sizeKnown = ses\.sizing !== true \|\| Number\.isFinite\(ses\.sizeCap\)/.test(html) && /sized at the first look/.test(html) && !/ses\.sizeCap : 3\)/.test(html), 'a new session shows no made-up stake');
};

// Y19: the reinvest pool shows as pool / cost of the next extra contract, so progress is readable at a glance.
{
  assert.ok(/Reinvest pool/.test(html) && /\(ex \+ 1\) \* 0\.93/.test(html) && !/max extra/.test(html), 'the stake row shows the pool against the next extra contract, with no cap branch');
  // The server counts extras at a flat 0.93 (skimAddon's default). A target priced on the live fill showed 7.32 / 7.18 while the server still needed 7.44 for the 8th extra.
  const live = require('../functions/kalshiLiveLib.js');
  assert.strictEqual(live.skimAddon({ pool: 7.43 }, 5), 7, 'server: 7.43 buys 7 extras');
  assert.strictEqual(live.skimAddon({ pool: 7.44 }, 5), 8, 'server: 8 x 0.93 = 7.44 buys the 8th, which is what the page target shows');
}

// Y25: the Flatten all result is cleared when the bot is started, and does not end in a doubled period.
{
  assert.ok(/getElementById\('kalFlattenMsg'\); if\(fm\)\{ fm\.textContent = ''; \}/.test(html), 'Start clears the old Flatten all message');
  assert.ok(/'No open positions'\)\.replace\(\/\\\.\\s\*\$\/, ''\) \+ '\. The bot is halted/.test(html) && !/'No open positions\.'\) \+ '\. The bot/.test(html), 'no doubled period after "No open positions"');
}

// Y27: the end label of the profit line is right-aligned to the edge and the plot makes room for its length, so a larger total is never cut off.
{
  assert.ok(/R = Math\.max\(60, endLabel\.length \* 9 \+ 16\)/.test(html) && /x="' \+ \(W - 4\) \+ '" y="' \+ \(Y\(last\.cum\) \+ 5\)\.toFixed\(1\) \+ '" text-anchor="end"/.test(html), 'the end label is right-anchored with room reserved for it');
}

// Y26: the "More stats" fold keeps its open or closed state across the card's rebuilds instead of closing every few seconds.
{
  assert.ok(/var kalshiMoreOpen = false;/.test(html) && /classList\.contains\('kal-more'\)\)\{ kalshiMoreOpen = t\.open; \}/.test(html), 'the fold records when it is toggled');
  assert.ok(/'<details class="kal-more"' \+ \(typeof kalshiMoreOpen !== 'undefined' && kalshiMoreOpen \? ' open' : ''\) \+ '><summary>More stats/.test(html), 'the rebuilt markup restores the state');
}

// Y31: ETH and SOL appear on the Live books tab as read-only cards fed by Coinbase, labelled as simulated only, and the shared series list the live bot and recorder read is untouched.
gates.Y31 = () => {
  assert.ok(/KXETH15M: 'Ethereum 15m' \}/.test(html) && !/KXSOL15M|Solana/.test(html), 'Ethereum is an ordinary live market card; there is no Solana anywhere on the page');
  assert.ok(/kalshiAlt = \{ ETH: \{ product: 'ETH-USD'/.test(html) && !/SOL-USD/.test(html) && /kalshiFetchAlt\('ETH', now\)/.test(html) && !/kalshiFetchAlt\('SOL'/.test(html), 'Coinbase history and ticker for both');
  const lib = require('../functions/kalshiLib.js');
  assert.deepStrictEqual(lib.KALSHI_SERIES, ['KXBTC15M', 'KXGOLD15M'], 'the list the live bot and recorder read is unchanged');
  assert.deepStrictEqual(lib.KALSHI_EXTRA_SERIES, ['KXETH15M']);
  const fnSrc = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const relay = fnSrc.slice(fnSrc.indexOf('exports.kalshiBooks = onCall'), fnSrc.indexOf('exports.kalshiBooks = onCall') + 1600);
  assert.ok(/for \(const series of kalshi\.KALSHI_EXTRA_SERIES\) \{\s+try \{/.test(relay) && /skipped/.test(relay), 'a failure on the extra series is skipped, never taking the Bitcoin and gold cards down');
};

// Y32 and Y33: the exit watch's switch, and how an exited trade is shown (its realised result, not "held to settlement"; the sell fill is not a trade of its own).
gates.Y32 = () => {
  assert.ok(/<select id="kalExitMode"><option value="off">Off<\/option><option value="log">Log only<\/option><option value="sell">Sell<\/option><\/select>/.test(html), 'the three modes');
  assert.ok(/kalshiExitMode: function\(mode\)/.test(html) && /httpsCallable\(functions, 'kalshiExitMode'\)/.test(html), 'the page can set it');
  assert.ok(/want === 'sell' && !window\.confirm\(/.test(html), 'Sell asks first; Log only and Off do not');
  assert.ok(/exitSel\.value = \(s && \['off', 'log', 'sell'\]\.indexOf\(s\.exitMode\) > -1\) \? s\.exitMode : 'log'/.test(html), 'the switch shows the server\'s mode, log by default');
};
gates.Y33 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const names = ['kalshiIsExitFill', 'kalshiTradePnl'];
  const f = new Function(names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const sold = { side: 'yes', settled: true, result: 'exit', settledPnl: -5.17, orderId: 'buy-1', exitOrderId: 'sell-1', exitCount: 20 };
  assert.strictEqual(f.kalshiTradePnl({ count: 20, price: '0.915' }, sold, 'no').pnl, -5.17, 'an exited trade shows what the exit made, even though the market later settled against it');
  assert.strictEqual(f.kalshiIsExitFill({ orderId: 'sell-1' }, [sold]), true, 'the sell fill is recognised');
  assert.strictEqual(f.kalshiIsExitFill({ orderId: 'buy-1' }, [sold]), false, 'the buy is not');
  assert.strictEqual(f.kalshiIsExitFill({ orderId: 'manual-9' }, [sold]), false, 'a manual order is not');
  const held = { side: 'yes', count: 20, orderId: 'b2', averageFeePaid: 0.0057 };
  assert.ok(f.kalshiTradePnl({ count: 20, price: '0.915' }, held, 'no').pnl < -18, 'a trade held to settlement is computed as before');
};

// Y34: the pool rule's switch on the page: two rules, 'After every win' asks first, the switch shows the server's rule (the original by default).
gates.Y34 = () => {
  assert.ok(/<select id="kalPoolRule"><option value="highs">after new profit highs<\/option><option value="wins">after every win<\/option><\/select>/.test(html));
  assert.ok(/kalshiPoolRule: function\(rule\)/.test(html) && /httpsCallable\(functions, 'kalshiPoolRule'\)/.test(html), 'the page can set it');
  assert.ok(/want === 'wins' && !window\.confirm\(/.test(html), 'the riskier rule asks first');
  assert.ok(/poolSel\.value = s && s\.poolRule === 'wins' \? 'wins' : 'highs'/.test(html), 'the original rule by default');
};

// Y35: Ethereum live on the page: a named-preset select (never a number), it asks before any size above off, the profit stats call an Ethereum trade Ethereum (not Bitcoin).
gates.Y35 = () => {
  assert.ok(!/kalEthLive|kalEthMsg|kalshiExtraSeries|liveExtra/.test(html), 'the Ethereum size dropdown, its handler and its callable are gone from the page');
  assert.ok(/\/GOLD\/\.test\(String\(o\.series \|\| o\.ticker \|\| ''\)\) \? 'Gold' : \(\/ETH\/\.test\(String\(o\.series \|\| o\.ticker \|\| ''\)\) \? 'Ethereum' : 'Bitcoin'\)/.test(html), 'an Ethereum trade is counted under Ethereum in the performance table, not under Bitcoin');
};

// Y37: the exit watch read back from the bot's own order records, inside More stats. Consequences: slip is trigger bid minus fill, "better or worse than holding" is only
// computed where the market's result is known, and a logged-only order (held to settlement) counts its real outcome as the hold result.
gates.Y37 = () => {
  const grab = (n) => { const m = new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'missing ' + n); return m[1]; };
  const f = new Function(['kalshiOrderPnl', 'kalshiExitReport', 'kalshiExitHtml'].map(grab).join('\n') + '; return { kalshiExitReport, kalshiExitHtml };')();
  const base = { side: 'yes', count: 10, fillCount: '10', maxCost: 9.6, strategy: 'L1' };
  const sold = Object.assign({}, base, { ticker: 'A', exitStatus: 'sold', exitCount: 10, exitBid: 0.69, exitAvg: 0.66, settled: true, result: 'exit', settledPnl: -3.0 });
  const heldLost = Object.assign({}, base, { ticker: 'B', exitShadow: { bid: 0.68 }, settled: true, result: 'no', settledPnl: -9.6 });
  const heldWon = Object.assign({}, base, { ticker: 'C', exitShadow: { bid: 0.7 }, settled: true, result: 'yes', settledPnl: 0.4 });
  const untouched = Object.assign({}, base, { ticker: 'D', settled: true, result: 'yes', settledPnl: 0.4 });
  const r = f.kalshiExitReport([sold, heldLost, heldWon, untouched], { A: 'no' });
  assert.deepStrictEqual([r.touched, r.sold, r.loggedOnly], [3, 1, 2], 'an order the watch never touched is not counted');
  assert.ok(Math.abs(r.avgSlip - 0.03) < 1e-9, 'slip is the trigger bid minus the fill: ' + r.avgSlip);
  assert.strictEqual(r.realised, -3.0);
  assert.ok(Math.abs(r.exitMinusHold - (-3.0 - (-9.6))) < 1e-9 && r.holdKnownSold === 1, 'selling beat holding by $6.60 where the market went against us');
  assert.deepStrictEqual([r.known, r.recovered], [3, 1], 'recovered = the side won after touching 70c');
  const win = f.kalshiExitReport([Object.assign({}, sold)], { A: 'yes' });
  assert.ok(Math.abs(win.exitMinusHold - (-3.0 - 0.4)) < 1e-9, 'when the side would have won, selling was worse than holding by the win it gave up (fees included in cost)');
  assert.strictEqual(f.kalshiExitReport([Object.assign({}, sold)], null).holdKnownSold, 0, 'no market result, no hold comparison: never guessed');
  assert.strictEqual(f.kalshiExitReport([untouched], {}).touched, 0);
  const none = f.kalshiExitHtml(f.kalshiExitReport([untouched], {}), (x) => x, (x) => '$' + x.toFixed(2));
  assert.ok(/nothing to read/.test(none), 'with nothing touched it says so rather than showing zeros as a result');
  assert.ok(/kalshiExitReport\(kalshiLiveOrders/.test(html) && /table\('By price paid', st\.byBand\) \+ \(exitRep !== undefined/.test(html), 'wired into More stats');
};

// Y36: the Account card says why the bot is not trading, without opening the bot menu.
gates.Y36 = () => {
  const m = /(function kalshiStopReason\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html); assert.ok(m, 'helper present');
  const f = new Function(m[1] + '; return kalshiStopReason;')();
  const when = (ms) => 'T' + ms;
  assert.strictEqual(f({ active: true }, null, false, false, when), '', 'running: no line');
  assert.ok(/Paused by you/.test(f({ active: true }, null, true, false, when)), 'a pause is named, even with a live session');
  assert.ok(/order switch/.test(f({ active: true }, null, false, true, when)), 'the server switch being off is named');
  assert.ok(/Not started/.test(f(null, null, false, false, when)) && /Not started/.test(f({ active: false }, null, false, false, when)), 'never started');
  const stop = f({ active: false, endedBecause: 'loss stop', endedAt: 5 }, { detail: 'the bot\'s trades are down $27' }, false, false, when);
  assert.ok(/loss stop at T5/.test(stop) && /down \$27/.test(stop) && /stays off/.test(stop), 'a loss stop says when, how far down, and that it stays off: ' + stop);
  assert.ok(/Check the Kalshi account/.test(f({ active: false, endedBecause: 'attempted', endedAt: 5 }, { detail: 'the answer was lost' }, false, false, when)), 'a lost answer tells the owner to check the account first');
  assert.ok(/Switched off by you/.test(f({ active: false, endedBecause: 'switched off by the owner', endedAt: 5 }, null, false, false, when)));
  assert.ok(/Flatten all/.test(f({ active: false, endedBecause: 'flattened by the owner', endedAt: 5 }, null, false, false, when)));
  assert.ok(/mystery/.test(f({ active: false, endedBecause: 'mystery', endedAt: 5 }, null, false, false, when)), 'an unknown reason is shown as written, never guessed');
  assert.ok(/no reason recorded/.test(f({ active: false, endedAt: 5 }, null, false, false, when)), 'an end with no reason says so');
  assert.ok(/id="kalL1Why" hidden/.test(html) && /document\.getElementById\('kalL1Why'\)/.test(html), 'the line sits on the Account card, outside the menu');
};

// Y38: a slow load must not look like a broken account. "Never saved" is only said once the halt document has ARRIVED, and the trade figures say loading until the orders arrive.
gates.Y38 = () => {
  assert.ok(/var kalshiBotState = \{ control: null \};/.test(html), 'control starts as not loaded (null), not as an empty saved setting');
  assert.ok(/var haltUnset = kalshiBotState\.control !== null && kalshiBotState\.control\.halt === undefined;/.test(html), 'the never-saved warning needs a loaded document');
  assert.ok(/function stopKalshiBot\(\)\{\n    kalshiBotState\.control = null; kalshiOrdersLoaded = false;/.test(html), 'leaving the tab resets it, so the next open is loading again');
  assert.ok(/kalshiOrdersLoaded = true; renderKalshiBot\(\)/.test(html) && /<b>loading\.\.\.<\/b>/.test(html) && /Loading the bot\\'s trades\.\.\./.test(html), 'figures say loading until the orders arrive, never +$0.00');
  assert.ok(/error: function\(err\)\{ kalshiSyncError/.test(html) && /Reload the page; if it keeps happening/.test(html), 'a listener that fails is shown, not left as an endless loading state');
};

// The runner is LAST on purpose: a gate defined after it is never run (Y20 and the simulation gates were once silently skipped that way).
(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
