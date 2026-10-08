'use strict';
// Bot tab layout: the latest five trades with a button for more, and cards that can be rearranged only on request.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};

gates.Y1 = () => {
  assert.ok(/var kalshiLiveShow = \{ events: 12, fills: 5 \};/.test(html), 'the trades card opens on the latest five');
  assert.ok(/data-more="fills">Show more/.test(html) && /data-less="fills">Show fewer/.test(html), 'with a way to see more and to go back');
  assert.ok(/data-less'\) === 'fills'\)\{ kalshiLiveShow\.fills = 5;/.test(html), 'show fewer returns to five');
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
  for (const id of ['kalL1Pill', 'kalL1Start', 'kalL1Stop', 'kalBotHalt', 'kalL1Status']) assert.ok(acct.indexOf('id="' + id + '"') > -1, id + ' lives in the account card, so start, stop and halt are always on screen');
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
  // Show more and Show fewer are links, not the dark filled button.
  assert.ok(!/class="kal-btn" data-(more|less)/.test(html) && (html.match(/class="kal-link" data-(more|less)/g) || []).length === 2, 'quiet links');
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
  assert.ok(/var doneLine = running \? 'Next look ' \+/.test(html) && /orders sent, ' \+/.test(html) && !/kalL1Facts/.test(html), 'when it looks next, orders sent and filled against no fill are one line of the status, not a row of facts');
  assert.ok(/var sizeText = running \?/.test(html) && /Stops if the bot is down/.test(html), 'size and stop are part of the status line inside the bot menu, not a line on the page');
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

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
