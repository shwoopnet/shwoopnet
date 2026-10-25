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
  assert.deepStrictEqual(names(rail[1]), ['account', 'status', 'positions'], 'the rail holds the account strip, the bot status (which carries the loss stop and risk meter), and the positions');
  const main = seg.slice(seg.indexOf('<div class="kal-main">'));
  assert.deepStrictEqual(names(main), ['pnl', 'trades'], 'the main column is the trades only: the market list left the Bot page on Oct 23, 2026 (the owner: Bot is the overview and live watch, Data is for deep dives, the Brief is for markets) (the Performance card moved to the Data page on Oct 21, 2026 at the owner\'s request; the bot card is gone, its controls sit in the account card)');
  const acct = /data-card="account">([\s\S]*?)\n      <div class="kal-card" data-card="positions">/.exec(rail[1])[1];
  for (const id of ['kalL1Pill', 'kalL1Start', 'kalBotHalt', 'kalFlatten', 'kalL1Status']) assert.ok(acct.indexOf('id="' + id + '"') > -1, id + ' lives in the account card, so start, pause and flatten are always one click away');
  assert.ok(/data-card="account">\s*<div class="kal-card-head kal-acct-head">[\s\S]*?id="kalL1Pill"/.test(rail[1]), 'the running pill sits at the top right of the account card');
  assert.ok(!/data-card="session"/.test(html), 'there is no separate bot card any more');
  const dataPage0 = html.slice(html.indexOf('id="page-data"'), html.indexOf('id="page-settings"'));
  assert.ok(!/data-card="performance"/.test(html) && !/id="kalChartRange"/.test(html) && !/id="kalChartLine"/.test(html), 'and the Performance card, its range choice and its duplicate line are gone from the Bot page');
  // Oct 21, 2026 cleanup: the stat tiles and tables left the account card (a tall column) and live in the Data page's "All the numbers" fold; the account card is the status and the controls.
  assert.ok(!/id="kalPerf"/.test(rail[1]), 'the stat tiles and tables are not in the rail');
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
  const f = lift(['kalTime', 'kalDate', 'kalDateTime', 'kalDayKey', 'kalshiShortTicker', 'kalshiWhen', 'kalshiOrderPnl', 'kalshiOutcomeCounts', 'kalshiMarketName']);
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
};

// The performance tracker: a loss is settled and drawn like a win, even when the server never marked it, and the numbers are the plain arithmetic of the trades.
gates.Y14 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalshiOrderPnl', 'kalshiOutcomeCounts', 'kalshiMarketName', 'kalshiTradePnl', 'kalDateTime', 'kalshiResolveOrders', 'kalshiPerfStats']);
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
  // In this palette --ink is the page background and --paper is the text colour (inverted names), and --card does not exist: a select styled with them showed dark text on dark in dark mode.
  // This used to read one named rule (.kal-perf-head select), which no markup used, so it guarded nothing; it now reads every rule that touches a select.
  const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
  const selectRules = css.match(/[^{}]*\bselect\b[^{}]*\{[^}]*\}/g) || [];
  assert.ok(selectRules.length > 0 && selectRules.every((r) => !/--card|color:\s*var\(--ink\)/.test(r)), 'no rule on a select uses the page background as its text colour');
  assert.ok(!/var\(--card\)/.test(html), 'no rule uses a variable that is not defined');
  assert.ok(/kalshiResolveOrders\(kalshiLiveOrders, kalshiLiveAcct && kalshiLiveAcct\.results\)/.test(html), 'the charts read orders settled against the account read');
};

// Open positions, one readable row each: the side from the sign, cost from the bot's own fill, what it can win and lose, the chance now and the time left from
// the live books. "Realized" and "Fees" are gone (an open position has no realized result). Show more / Show fewer are quiet links, not filled buttons.
// PC1: an open position's row draws the chance of the side bought as a chart, from the reads the page has made. Consequence: with fewer than two points there is no chart (nothing invented); a quiet market is zoomed so it is not a flat line; the paid line is drawn at the entry; a chance is not a dollar figure, so the chart carries none.
// TP1: the trade list shows each result as a share of what the trade cost, beside the dollar figure. Consequence: a percentage that is not the pnl over the money put in would mislead, so it is checked on a win, a loss and a trade with no known cost.
gates.TP1 = () => {
  const m = /(function kalshiPctText\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html); assert.ok(m, 'kalshiPctText not found');
  const f = new Function(m[1] + '; return kalshiPctText;')();
  assert.ok(/\+6\.2%$/.test(f(0.58, 9.3)) && !/\(/.test(f(0.58, 9.3)), 'a win of 58c on 9.30 at risk is +6.2%, plain, same strength as the dollars: ' + f(0.58, 9.3));
  assert.ok(/-100\.0%$/.test(f(-9.3, 9.3)), 'a full loss is -100.0%: ' + f(-9.3, 9.3));
  assert.strictEqual(f(1, 0), '', 'no known cost: no percentage'); assert.strictEqual(f(NaN, 5), '', 'no result: no percentage');
  assert.ok(/kalshiMoney\(Math\.abs\(tp\.pnl\)\) \+ kalshiPctText\(/.test(html) && /kalshiMoney\(Math\.abs\(pnl\)\) \+ kalshiPctText\(/.test(html), 'both kinds of row carry it, after the dollar figure, so Privacy view masks the dollars and leaves the percentage');
};
// TS1: the Recent trades card opens with four monitoring figures for the last 24 hours that do not repeat the account strip (no result in dollars). Consequence: wrong win counts or a streak counted past a break would mislead.
gates.TS1 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const names = ['kalshiOrderPnl', 'kalshiTradeStats', 'kalshiTradeStatsHtml'];
  const f = new Function(names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const now = Date.parse('2026-10-23T18:00:00Z');
  const o = (min, side, result, extra) => Object.assign({ strategy: 'L1', ts: now - min * 60000, side, fillCount: 1, count: 1, maxCost: 0.9, settled: true, result, settledPnl: result === side ? 0.07 : -0.9, averageFeePaid: 0.01 }, extra || {});
  const orders = [o(10, 'yes', 'yes'), o(40, 'yes', 'yes'), o(70, 'yes', 'no'), o(100, 'no', 'no'), o(130, 'yes', 'exit', { settledPnl: -0.7 }), o(2000, 'yes', 'yes')];
  const st = f.kalshiTradeStats(orders, now);
  assert.ok(st.total === 5 && st.settled === 5 && st.wins === 3, 'the order from over 24 hours ago is left out: ' + JSON.stringify(st));
  assert.ok(st.streak === 2 && st.streakKind === 'win', 'the streak is the newest run: ' + st.streak + ' ' + st.streakKind);
  assert.strictEqual(st.early, 1, 'one early sell');
  assert.strictEqual(st.fees, 0.05, 'fees are what was charged on the filled orders');
  assert.strictEqual(f.kalshiTradeStats([o(10, 'yes', 'no'), o(20, 'yes', 'yes')], now).streakKind, 'loss', 'a loss streak is named as one');
  assert.strictEqual(f.kalshiTradeStatsHtml(f.kalshiTradeStats([], now), (x) => '$' + x), '', 'no trades: no tiles');
  const h = f.kalshiTradeStatsHtml(st, (x) => '$' + x.toFixed(2));
  assert.ok(/Win rate/.test(h) && /60%/.test(h) && /Streak/.test(h) && /Early sells/.test(h) && /Fees paid/.test(h) && !/Net|Today/.test(h), 'four tiles and no result figure (it is in the account strip already)');
};
gates.PC1 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const names = ['kalshiShortTicker', 'kalshiSecsLeft', 'kalshiFmtLeft', 'kalshiPositionChartHtml', 'kalshiPositionsHtml'];
  const f = new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const base = { ticker: 'KXGOLD15M-26OCT231215-15', title: 'GOLD 12:15 PM CT', side: 'no', count: 15, entry: 0.906, cost: 13.59, ifWin: 1.41, ifLose: -13.59, chance: 0.943, cashOut: 14.12, left: 145, bot: true };
  assert.strictEqual(f.kalshiPositionChartHtml(Object.assign({}, base, { path: [] })), '', 'no reads yet: no chart');
  assert.strictEqual(f.kalshiPositionChartHtml(Object.assign({}, base, { path: [0.9] })), '', 'one read is not a line');
  const c = f.kalshiPositionChartHtml(Object.assign({}, base, { path: [0.9, 0.91, 0.93, 0.943] }));
  assert.ok(/kal-hc-line/.test(c) && !/kal-hc-paid|Closes in|Dashed line|Since this page opened/.test(c) && /<span>94%<\/span><span>90%<\/span>/.test(c), 'a plain chart: the line, and the high and low as percentages down the side, no captions and no paid line (the owner, Oct 24, 2026)');
  assert.ok(!/\$|\*\*\*\*/.test(c), 'it carries no dollar figure, so Privacy view has nothing to mask in it');
  const ys = (/class="kal-hc-line" d="([^"]*)"/.exec(c)[1].match(/ ([\d.]+)/g) || []).map((x) => Number(x));
  const flatC = f.kalshiPositionChartHtml(Object.assign({}, base, { entry: 0.94, path: [0.94, 0.9401, 0.94, 0.9401] }));
  const fy = (/class="kal-hc-line" d="([^"]*)"/.exec(flatC)[1].match(/ ([\d.]+)/g) || []).map((x) => Number(x));
  assert.ok(Math.max(...fy) - Math.min(...fy) < 40 && fy.every((y) => y > 20 && y < 90), 'a market that barely moved stays mid-chart instead of being stretched to the full height');
  assert.ok(ys.length === 4 && ys[3] < ys[0], 'a rising chance rises on the chart (smaller y is higher)');
  const html1 = f.kalshiPositionsHtml([Object.assign({}, base, { path: [0.9, 0.95] })], (x) => String(x), (x) => '$' + x);
  assert.ok(/kal-hold-body/.test(html1) && /kal-hold-stats/.test(html1), 'the row is figures plus chart');
  const html0 = f.kalshiPositionsHtml([Object.assign({}, base, { path: [] })], (x) => String(x), (x) => '$' + x);
  assert.ok(!/kal-hold-body/.test(html0) && /kal-hold-stats/.test(html0), 'with no path the row is exactly the figures as before');
};
gates.Y15 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function("var KAL_TZ = 'America/Chicago';\n" + names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalshiShortTicker', 'kalshiSecsLeft', 'kalshiFmtLeft', 'kalshiGroupFills', 'kalshiOrderFor', 'kalshiPositionRows', 'kalshiPositionChartHtml', 'kalshiPositionsHtml']);
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
  assert.ok(/NO x 2/.test(out) && /Cost[\s\S]*\$1\.92/.test(out) && /\+\$0\.08/.test(out) && /-\$1\.92/.test(out) && /Chance now 99\.6%/.test(out) && !/closes in|waiting for the result/.test(out) && !/before fees/.test(out), 'the row says it all');
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
  const acct = html.slice(html.indexOf('// What one order risks right now:'), html.indexOf("    el.innerHTML = h;"));
  assert.ok(!/BOT_SHARDS|shardLow|DATA_SHARD_LOW/.test(html) && !/Shard '|shardRows/.test(acct), 'no shard balances or low-shard warning on the page (removed Oct 24, 2026, the owner: the shard stuff can go)');
  assert.ok(/a\.liveSwitch \? '' : '<div class="kal-rows"><div><span class="kal-k">Order switch<\/span><b class="kal-neg">OFF/.test(acct), 'the order switch is a line only when it is off');
  const head = html.slice(html.indexOf('id="page-kalshi"'), html.indexOf('id="kalTabBot"'));
  assert.ok(/id="kalLayout"/.test(head), 'the Layout menu is in the page header, not on a row of its own');
  assert.ok(!/kal-layout-bar/.test(html), 'no leftover row for it');
  assert.ok(/var doneLine = running \? 'Next look ' \+/.test(html) && /' filled, ' \+/.test(html) && !/kalL1Facts/.test(html), 'when it looks next, orders sent and filled against no fill are one line of the status, not a row of facts');
  assert.ok(/var sizeText = running \?/.test(html) && /Stops if down/.test(html), 'size and stop are part of the status line inside the bot menu, not a line on the page');
};

// The all-orders export (Oct 20, 2026): every order the BOT sent, oldest first, with its saved result. Manual trades never have an order document, so they are not in it; nothing is invented (an open order has no P/L).
gates.Y11b = () => {
  const grab = (n) => { const m = new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html); assert.ok(m, 'missing ' + n); return m[1]; };
  const csv = new Function(['kalshiOrderPnl', 'kalshiAllOrdersCsv'].map(grab).join('\n') + '; return kalshiAllOrdersCsv;')();
  const rows = (t) => t.split('\n');
  assert.deepStrictEqual(rows(csv([])), [rows(csv([]))[0]], 'a header even with no orders');
  const out = rows(csv([
    { ts: 3000, ticker: 'B', series: 'KXGOLD15M', side: 'yes', price: 0.93, count: 4, fillCount: '4.00', maxCost: 3.9, status: 'filled', settled: true, result: 'yes', settledPnl: 0.24, strategy: 'L1', seen: { bid: 0.91, ask: 0.94 } },
    { ts: 1000, ticker: 'A', series: 'KXBTC15M', side: 'no', price: 0.9, count: 1, fillCount: '1.00', maxCost: 0.92, status: 'filled', strategy: 'L1' },
    { ts: 2000, ticker: 'C', series: 'KXETH15M', side: 'yes', status: 'no fill', fillCount: '0.00', strategy: 'L1' },
  ]));
  const head = out[0].split(',');
  const col = (r, name) => r.split(',')[head.indexOf(name)];
  assert.strictEqual(out.length, 4, 'one row per order, none dropped (this is not capped at 150)');
  assert.deepStrictEqual([1, 2, 3].map((i) => col(out[i], 'ticker')), ['A', 'C', 'B'], 'oldest first');
  assert.strictEqual(col(out[3], 'pnl'), '0.24', 'a settled order carries the bot\'s saved P/L');
  assert.strictEqual(col(out[1], 'pnl'), '', 'an open order has none');
  assert.ok(['entryLead', 'avgFill', 'avgFee', 'bidSize', 'askSize', 'rise3', 'rng5', 'minStep', 'climb', 'smooth', 'flips', 'flips0', 'earlierCandles', 'askAtDecision', 'twoStageLeft', 'ask10', 'inBand6'].every((c) => head.includes(c)), 'the full export carries the entry lead and what the research reads need');
  assert.deepStrictEqual([col(out[3], 'seenBid'), col(out[3], 'seenAsk'), col(out[1], 'seenAsk')], ['0.91', '0.94', ''], 'the quote the bot saw is exported (the spread forward test reads it); an order with none leaves it empty');
  assert.ok(/id="kalOrdersCopy"/.test(html) && /kalshiAllOrdersCsv\(kalshiLiveOrders\)/.test(html), 'a button, built from the bot\'s own orders');
};

// Presentation view (Oct 21, 2026): one Layout-menu switch that only HIDES the balance, the stake and pool rows, the open positions and recent trades cards, the By price paid table and the Tools menu. It is a page
// attribute kept in this browser (Oct 23, 2026), so a reload cannot reveal amounts; no number is changed.
gates.Y11c = () => {
  const m = /(function kalshiSetPresent\(on\)\{[\s\S]*?\n  \})\n/.exec(html); assert.ok(m, 'kalshiSetPresent not found');
  const attrs = {}; const doc = { documentElement: { setAttribute: (k, v) => { attrs[k] = v; }, removeAttribute: (k) => { delete attrs[k]; } } };
  const mk = () => new Function('document', 'var kalshiMasked = false;' + m[1] + '; return { set: kalshiSetPresent, masked: function(){ return kalshiMasked; } };')(doc);
  const set = mk();
  set.set(true); assert.deepStrictEqual(attrs, { 'data-present': 'on' }, 'on sets the page attribute'); assert.strictEqual(set.masked(), true, 'and masks the amounts');
  set.set(false); assert.deepStrictEqual(attrs, {}, 'off removes it, back to the full page'); assert.strictEqual(set.masked(), false);
  // All or nothing (the owner, Oct 23, 2026): one flag masks every dollar amount, and only dollar amounts. A percentage or a chance is never masked.
  assert.ok(!/kalshiPrivacyChoice|privacyOpts|kalshiMoneyK/.test(html), 'no per-figure choices any more');
  // Oct 23, 2026 (the owner: "we don't want to accidentally leak anything"): the view now survives a reload, in this browser only (never the account), and is applied by a head script BEFORE anything draws.
  assert.ok(!/syncUserSetting\('(kalPresent|privacy)/.test(html), 'the view is never saved to the account');
  const head = html.slice(0, html.indexOf('</head>'));
  assert.ok(/getItem\('shwoopnet:privacy'\) === 'on'[\s\S]*?setAttribute\('data-present', 'on'\)/.test(head), 'a head script restores the view before first paint, so a reload never flashes an amount');
  assert.ok(/var kalshiMasked = document\.documentElement\.getAttribute\('data-present'\) === 'on'/.test(html), 'and the amount flag starts from that attribute, so the very first draw is already masked');
  assert.ok(/setItem\('shwoopnet:privacy', 'on'\)[\s\S]{0,60}removeItem\('shwoopnet:privacy'\)/.test(m[1]), 'switching it on stores it and switching it off clears it');
  assert.ok(/kalshiPrivacyUi\(kalshiMasked\);/.test(html), 'a reload shows the switch and the button already on');
  assert.ok(!/id="kalPresent"/.test(html), 'the Layout menu no longer carries a privacy checkbox');
  for(const id of ['privacyToggle']){ assert.ok(new RegExp('id="' + id + '" role="switch"').test(html), id + ' is a switch in Settings'); }
  assert.ok(/<button class="kal-mini" id="kalPresentBtn"[^>]*>Privacy<\/button>\s*<details class="kal-layout" id="kalTools">/.test(html), 'the same switch is a button in the page header called Privacy, outside the Tools menu so the privacy view cannot hide it; there is no Data button (the sidebar has it)');
  assert.ok(!/id="kalDataBtn"/.test(html) && !/<div class="trades-title">Bot<\/div>/.test(html), 'and no big Bot title next to the updated time');
  assert.ok(!/html\[data-present="on"\] #kalPresentBtn/.test(html), 'and nothing hides the button that turns it off');
  // Oct 21, 2026 (the owner: "instead of hide, turn sensitive information into ****"): nothing is hidden any more except the Tools menu, which holds the raw account read; amounts are masked.
  const css = /html\[data-present="on"\][^{]*\{[^}]*\}/.exec(html); assert.ok(css && /^html\[data-present="on"\] #kalTools\{ display:none; \}$/.test(css[0]), 'only the Tools menu is hidden: ' + (css && css[0]));
  assert.ok(!/data-present="on"\] \.kal-acct-total|kal-perf-band/.test(html.slice(html.indexOf('<style>'), html.indexOf('</style>')).replace(/\/\*[\s\S]*?\*\//g, '')), 'no card or figure is hidden by the page attribute');
  // The amounts: one formatter masks every dollar figure and keeps the sign; the export formatter never masks.
  const f = new Function('var kalshiMasked = false;' + [/(function kalshiMoneyRaw\([^)]*\)\{[\s\S]*?\n  \})\n/, /(function kalshiMoney\([^)]*\)\{[\s\S]*?\n  \})\n/].map((re) => re.exec(html)[1]).join('\n') + '; return { money: kalshiMoney, raw: kalshiMoneyRaw, mask: function(v){ kalshiMasked = v; } };')();
  assert.strictEqual(f.money(-3.5), '-$3.50'); f.mask(true);
  assert.deepStrictEqual([f.money(-3.5), f.money(12.34), f.raw(-3.5)], ['-****', '****', '-$3.50'], 'masked: the sign stays, the figure does not, and the raw formatter used by the exports is unchanged');
};

// The order diagnostics export: one row per order with what the bot saw when it decided, nothing invented, nothing secret, safe to paste.
gates.Y11 = () => {
  const m = /(function kalshiDiagnosticsCsv\(orders, limit\)\{[\s\S]*?\n  \})\n/.exec(html);
  assert.ok(m, 'builder not found');
  const csv = new Function(m[1] + '; return kalshiDiagnosticsCsv;')();
  const rows = (t) => t.split('\n');
  const head = rows(csv([]))[0].split(',');
  assert.deepStrictEqual(head.slice(0, 2), ['time', 'ticker'], 'a header even with no orders');
  assert.ok(['series', 'entryLead', 'count'].every((c) => head.includes(c)), 'the series, the entry lead (10m or 6m) and the size are exported so the forward reads can split orders');
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
  // The Bot page has no price charts (the owner, Oct 23, 2026: "remove charts from the bot page entirely"). Consequence: no market row draws a line, and the page calls no price feed (Coinbase, gold-api) from the browser.
  assert.ok(!/kalshiSparkSvg|kalshiSparkFor|kal-spark|kalshiFetchSpot|kalshiFetchAlt|kalshiFetchGold|kalshiCandles|kalshiTicker/.test(html), 'the chart code is gone');
  assert.ok(!/coinbase\.com|gold-api\.com/.test(html), 'and so are the price feeds it read');
};

// The default landing page can be Kalshi, for the admin only: the button is hidden until the account is known to be the admin, and because that is
// known only after the first screen is up, a Kalshi preference shows the brief first and moves to Kalshi when the admin check comes back.
gates.Y17 = () => {
  assert.ok(/<button class="tf-btn" data-value="kalshi" id="landingKalshiBtn" hidden>Bot<\/button>/.test(html), 'a Bot choice exists and starts hidden');
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
  assert.ok(!/tile\('Per trade'/.test(html), 'no tile reuses the stake row name (the expectancy tile itself left with the duplicate tiles in the fold, Oct 23, 2026; Average trade is on the Data page)');
  assert.ok(/kalshiMoney\(0\.12 \* base\)/.test(html), 'the status line quotes the 12% stop (through the money formatter, so presentation view masks it)');
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
  assert.ok(!/data-skin|skinChoice|applySkinPref|applyDarkModePref|data-theme="dark"/.test(html), 'there is one theme, black and white: no skin, no dark-mode switch (the owner, Oct 23, 2026)');
  assert.ok(/--gain: #0F9D58;/.test(html) && /--loss: #D93025;/.test(html), 'gain and loss stay fixed colours (--loss is the live trading safety color)');
};

// Y23: the Kalshi page uses more width on a wide monitor, and the other pages keep the 1400px column.
gates.Y23 = () => {
  assert.ok(/\.app\.app-wide\{ max-width: 1800px; \}/.test(html) && /\.app\{ margin-left: 0; margin-right: auto; max-width: 1800px; \}/.test(html), 'the base column and the wide class are both 1800px (widened Oct 23, 2026, the owner: the page stopped short on a wide screen)');
  assert.ok(/appEl\.classList\.toggle\('app-wide', name === 'kalshi'\)/.test(html), 'only the Kalshi page turns it on, and every other page turns it off');
};

// Y24 (retired Oct 21, 2026): the bouncing logo cube and its ground flash were dead CSS (no markup used them) and were removed in the tidy-up; this gate now says they stay gone.
gates.Y24 = () => {
  assert.ok(!/brand-ground|brand-impact-ring|brand-mark|brandBounce/.test(html), 'the unused logo animation CSS is gone');
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

// Y26: the stats card shows the six tiles, By market and By price paid and nothing else; every other stat is copied with the Copy all stats button instead of being shown.
{
  assert.ok(!/kalshiMoreOpen|kal-more|More stats/.test(html), 'the More stats fold and its open/closed state are gone');
  assert.ok(!/id="kalStatsCopy"|kalshiStatsText|kalshiExitReport|id="kalStmtPrint"|kalshiStatementHtml/.test(html), 'Copy all stats and Print statement are gone (removed Oct 24, 2026, the owner)');
}

// Y31: ETH and SOL appear on the Live books tab as read-only cards fed by Coinbase, labelled as simulated only, and the shared series list the live bot and recorder read is untouched.
gates.Y31 = () => {
  const lib = require('../functions/kalshiLib.js');
  assert.deepStrictEqual(lib.KALSHI_SERIES, ['KXBTC15M', 'KXGOLD15M'], 'the list the live bot and recorder read is unchanged');
  assert.deepStrictEqual(lib.KALSHI_EXTRA_SERIES, ['KXETH15M', 'KXXRP15M', 'KXDOGE15M', 'KXAUDUSD15M', 'KXUSDCAD15M', 'KXNATGAS15M'], 'every market the bot can hold has a price on the relay, so its open position can draw a chance and a chart');
  const fnSrc = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'index.js'), 'utf8');
  const relay = fnSrc.slice(fnSrc.indexOf('exports.kalshiBooks = onCall'), fnSrc.indexOf('exports.kalshiBooks = onCall') + 1600);
  assert.ok(/for \(const series of kalshi\.KALSHI_EXTRA_SERIES\) \{\s+try \{/.test(relay) && /skipped/.test(relay), 'a failure on the extra series is skipped, never taking the Bitcoin and gold cards down');
};

// Y32 and Y33: the exit watch has no switch on the page (the owner removed it on Oct 12, 2026: fixed at 50c, always selling), and how an exited trade is shown (its realised result, not "held to settlement"; the sell fill is not a trade of its own).
gates.Y32 = () => {
  assert.ok(!/kalExitMode|kalExitMsg|kal-exitrow|kalshiExitMode/.test(html), 'the exit selector, its saver and its callable are gone from the page, so it cannot be turned down in a bad hour');
  assert.ok(!/want === 'sell' && !window\.confirm|Log only|Sell mode/.test(html), 'and so is the old confirm dialog and the log only wording');
  assert.ok(/<b>Exit at 25c \(fixed, always on\)\.<\/b>/.test(html), 'the rules and limits fold says the exit is 25c and always on');
  assert.ok(!/Exit at 70c|falls to 70c/.test(html), 'no page text still describes the old 70c line');
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

// Y34: the pool rule has no switch on the page (removed Oct 12, 2026: it always rebuilds after every win). The page no longer reports a rule at all (Oct 12, 2026 cleanup).
gates.Y34 = () => {
  assert.ok(!/kalPoolRule|kalPoolMsg|kal-poolrow|kalshiPoolRule/.test(html), 'the pool selector, its saver and its callable are gone from the page');
  assert.ok(!/want === 'wins' && !window\.confirm/.test(html), 'and so is its confirm dialog');
  assert.ok(/<b>Reinvest pool rebuilds after every win \(fixed, always on\)\.<\/b>/.test(html), 'the rules and limits fold says so');
  assert.ok(!/ses\.sizePoolRule|after new profit highs/.test(html), 'the page no longer reports a rule: there is only one, and a row for it described a setting that does not exist');
};

// Y35: Ethereum live on the page: a named-preset select (never a number), it asks before any size above off, the profit stats call an Ethereum trade Ethereum (not Bitcoin).
gates.Y35 = () => {
  assert.ok(!/kalEthLive|kalEthMsg|kalshiExtraSeries|liveExtra/.test(html), 'the Ethereum size dropdown, its handler and its callable are gone from the page');
  assert.ok(/return \/GOLD\/\.test\(s\) \? 'Gold' : \/ETH\/\.test\(s\) \? 'Ethereum' : \/XRP\/\.test\(s\) \? 'XRP' : \/DOGE\/\.test\(s\) \? 'Dogecoin' : \/AUDUSD\/\.test\(s\) \? 'AUD\/USD' : \/USDCAD\/\.test\(s\) \? 'USD\/CAD' : \/NATGAS\/\.test\(s\) \? 'Natural gas' : 'Bitcoin';/.test(html), 'an Ethereum, XRP, Dogecoin or probe-market trade is counted under its own name in the performance table, never under Bitcoin');
  // Run the real function: a probe trade must never be labelled Bitcoin, because Bitcoin is the fallback for an unknown ticker.
  const m = /(function kalshiMarketName\(o\)\{[\s\S]*?\n  \})\n/.exec(html); assert.ok(m, 'missing kalshiMarketName');
  const name = new Function(m[1] + '; return kalshiMarketName;')();
  assert.deepStrictEqual(['KXAUDUSD15M-26OCT201615-T1', 'KXUSDCAD15M-X', 'KXNATGAS15M-X', 'KXBTC15M-X', 'KXETH15M-X'].map((t) => name({ ticker: t })), ['AUD/USD', 'USD/CAD', 'Natural gas', 'Bitcoin', 'Ethereum']);
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

// Y39: a market the page does not know is never shown. The deployed relay can lag the page by a deploy, and Solana once appeared as a bare "KXSOL15M" card after it was removed.
gates.Y39 = () => {
  assert.ok(!/var rows = \(\(data && data\.markets\)/.test(html) && !/KXBTC15M', 'KXGOLD15M', 'KXETH15M', 'KXXRP15M', 'KXDOGE15M'\]\.indexOf/.test(html), 'the page draws no market cards at all (Oct 23, 2026): the Bot page is the overview and live watch');
};

// Y42: depth. Market rows show the contracts waiting at the best bid and ask with a bar, only when both sizes are known, and the card shadows are layered tokens that the Mono Ink skin turns off.
gates.Y42 = () => {
  assert.ok(/--card-shadow-lift:/.test(html), 'a lift shadow exists');
  assert.ok(!/kalshiDepthHtml|kal-depth/.test(html), 'the book-size bar went with the market rows');
};

// Y43: on a phone (700px and narrower) the price line under each market is hidden; the Performance card is shown again (the owner, Oct 21, 2026, after the calm view); the stats card is not touched.
gates.Y43 = () => {
  const m = /@media \(max-width:700px\)\{([\s\S]*?)\n  \}/.exec(html);
  assert.ok(m, 'a 700px block exists');
  assert.ok(!/data-card="performance"\]\{ display:none/.test(html), 'the Performance card is not hidden on a phone');
  assert.ok(!/\.kal-charts\b/.test(html), 'the old Performance charts grid is gone (the charts live on the Data page, whose grid stacks to one column on a narrow screen)');
  assert.ok(!/kalPerfWrapC|kal-perf\b/.test(m[1]) && !/data-card="account"/.test(m[1]), 'the stats card stays');
};

// Y44: a market's price chart shows only while the account holds a position in it (the owner's request, Oct 20, 2026). "In a trade" is a real position, not an order that was sent; positions that
// could not be read, or a position of zero, mean no chart.
gates.Y44 = () => {
  assert.ok(!/kalshiInTrade|kal-brow-held/.test(html), 'no market row exists to mark, so a held position is shown only in the Open positions card (the owner, Oct 23, 2026)');
};

// Y45: on a phone the Tools menu is a full-width sheet above the bottom bar. Anchored to its button it ran off the left edge and cut the buttons in half (owner's screenshot, Oct 20, 2026).
gates.Y45 = () => {
  const m = /@media \(max-width:700px\)\{([\s\S]*?)\n  \}/.exec(html);
  assert.ok(m, 'a 700px block exists');
  const rule = /\.kal-tools-body\{([^}]*)\}/.exec(m[1]);
  assert.ok(rule, 'the phone block restyles the Tools menu');
  assert.ok(/position:fixed/.test(rule[1]) && /left:12px/.test(rule[1]) && /right:12px/.test(rule[1]), 'it is pinned to both sides of the screen, so it cannot run off either edge');
  assert.ok(/min-width:0/.test(rule[1]) && /max-height:65vh/.test(rule[1]), 'it keeps no minimum width and scrolls instead of growing past the screen');
};

// Y40: the hover on the settled-trade bars. Placement is pure, so its edges are tested: centred on the column, just above the pointer, inside the window at both sides, flipped below the
// pointer when there is no room above. The tip is filled as text (the values come from attributes, never markup), shown for a mouse over a column and for a tap, hidden when a mouse leaves but
// NOT when a touch "leaves" (a touch has no hover, so hiding on leave would close the tip the instant the finger lifts), and the chart is only rebuilt when its markup changes, because
// replacing it under the pointer closed the tip. Gain and loss text share the bars' tokens: one green, one red.
gates.Y40 = () => {
  assert.ok(/\.kal-pos\{ color:var\(--gain\); \}/.test(html) && /\.kal-neg\{ color:var\(--loss-text\); \}/.test(html) && /--loss-text: #F0554B;/.test(html), 'loss text uses a lighter red (5.4:1 on the cards, the bars keep the 3.9:1 safety red), gain text matches the bars');
  assert.ok(!/#1f9d55|#d64545/i.test(html), 'and the two stray hard-coded copies of them are gone');
};

// Y41: the page shows the live bot (L1, "closing") and nothing else. The opening window paper strategy, its Closing / Opening / Both switch, its lane table and its paper rows were removed on
// Oct 12, 2026 at the owner's request ("lets go back to only L1 for now": the strategies must not overlap in mindset or position). Live and paper never shared a column, and now there is no paper.
gates.Y41 = () => {
  assert.ok(!/id="kalLens"|data-lens=|kalshiLens|kal-lens|kalPaperNote|kal-paper-note/.test(html), 'no strategy switch, no paper note, no view state');
  assert.ok(!/kalshiOpening|watchKalshiOpening|kalshiLane|kalChartsO|kalBotOpenO|kalBotClosedO|kalBotTotalsO|kalPerfWrapO|kalPerfO|kalChartLineO|kalChartPieO|kalChartBarsO/.test(html), 'no opening records, lane table, opening paper rows or paper charts (the PAPER1 candidates card, Oct 20, 2026, is a different thing: kalshiPaperOrders, kalPaperCard)');
  assert.ok(!/Opening strategy|early favourite|early underdog|paper F|paper U/.test(html), 'no opening wording is left on the page');
  assert.ok(/if\(ses && ses\.active === true\)\{/.test(html), 'the live stake row follows the live session alone');
};

// The runner is LAST on purpose: a gate defined after it is never run (Y20 and the simulation gates were once silently skipped that way).
// AK1: a refused account read (Kalshi's 429) does not wipe a good account card. Consequence: the balance, stake and today stay on screen with a note instead of turning into an error for a minute.
gates.AK1 = () => {
  const m = /(function kalshiKeepLastRead\(prev, next\)\{[\s\S]*?\n  \})\n/.exec(html); assert.ok(m, 'kalshiKeepLastRead not found');
  const keep = new Function(m[1] + '; return kalshiKeepLastRead;')();
  const good = { at: 1000000, balance: { ok: true, totalDollars: 500 } }, bad = (at) => ({ at, balance: { ok: false, status: 429 } });
  const k = keep(good, bad(1060000));
  assert.ok(k && k.balance.ok === true && k.busyAt === 1060000 && k.at === 1000000, 'a refused read keeps the last good one and notes when it was refused');
  assert.strictEqual(keep(good, { at: 1060000, balance: { ok: true, totalDollars: 501 } }), null, 'a read that worked always replaces it');
  assert.strictEqual(keep(good, bad(1000000 + 700000)), null, 'after 10 minutes the failure is shown, not hidden');
  assert.strictEqual(keep(null, bad(5)), null, 'with nothing good to keep the failure is shown');
  assert.strictEqual(keep(bad(1), bad(2)), null, 'a failed read is never kept');
  assert.ok(/Kalshi is busy \(too many requests\)/.test(html), 'a 429 says so in plain words, not as raw JSON');
};

// BS1 to BS3: the Bot page's status and risk cards (Oct 23, 2026, the owner chose "heartbeat and what it's doing" and "loss stop and risk meter"). Pure functions of the session, the orders and the clock.
const liftBs = (names, pre) => new Function((pre || '') + names.map((n) => (new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n').exec(html) || assert.fail(n + ' not found'))[1]).join('\n') + '; return {' + names.join(',') + '};')();
gates.BS1 = () => {
  const f = liftBs(['kalshiHeartbeat', 'kalshiNextEntry']);
  const T0 = 10 * 900000;   // a quarter hour boundary
  assert.strictEqual(f.kalshiHeartbeat(null, T0).state, 'off', 'no session: not running');
  assert.strictEqual(f.kalshiHeartbeat({ active: false }, T0).state, 'off');
  assert.strictEqual(f.kalshiHeartbeat({ active: true, lastTickAt: T0 - 40000 }, T0).state, 'ok', 'a check 40 seconds ago is alive');
  assert.strictEqual(f.kalshiHeartbeat({ active: true, lastTickAt: T0 - 200000 }, T0).state, 'quiet', 'over 2.5 minutes is quiet');
  assert.strictEqual(f.kalshiHeartbeat({ active: true, lastTickAt: T0 - 400000 }, T0).state, 'down', 'over 5 minutes means the function is not running');
  assert.strictEqual(f.kalshiHeartbeat({ active: true }, T0).state, 'quiet', 'running with no check recorded yet is waiting, not alive');
  const a = f.kalshiNextEntry(T0 + 60000);
  assert.deepStrictEqual([a.at, /10 minute/.test(a.label)], [T0 + 300000, true], 'a minute into a quarter the next look is the 10 minute one at minute 5');
  const b = f.kalshiNextEntry(T0 + 330000);
  assert.deepStrictEqual([b.at, /6 minute/.test(b.label)], [T0 + 540000, true], 'then the 6 minute one at minute 9');
  const c = f.kalshiNextEntry(T0 + 600000);
  assert.deepStrictEqual([c.at, /10 minute/.test(c.label)], [T0 + 900000 + 300000, true], 'after minute 9 it rolls to the next quarter');
};
gates.BS2 = () => {
  const f = liftBs(['kalshiRiskMeter']);
  const NOW = Date.parse('2026-10-23T15:00:00Z'), s = { sizing: true, sizeBase: 500 };
  const o = (over) => Object.assign({ strategy: 'L1', ts: NOW - 3600000, fillCount: '1.00', count: 1, maxCost: 0.93, side: 'yes', ticker: 'KXBTC15M-26OCT231015-15', settled: true, result: 'yes' }, over);
  let m = f.kalshiRiskMeter([], s, NOW);
  assert.deepStrictEqual([m.used, m.limit, m.fraction], [0, 60, 0], 'nothing yet: 12% of a $500 base is the $60 limit and none is used');
  m = f.kalshiRiskMeter([o({ result: 'no' }), o({ result: 'no' })], s, NOW);
  assert.ok(Math.abs(m.used - 1.86) < 1e-9 && Math.abs(m.fraction - 1.86 / 60) < 1e-9, 'two lost orders use their whole cost: ' + m.used);
  m = f.kalshiRiskMeter([o({ settled: false, result: undefined })], s, NOW);
  assert.ok(Math.abs(m.used - 0.93) < 1e-9 && Math.abs(m.openCost - 0.93) < 1e-9, 'an open order counts as lost, and as money at risk now');
  m = f.kalshiRiskMeter([o({ settled: false, result: undefined, count: 3, fillCount: '3.00', maxCost: 2.79, addonCost: 0.93 })], s, NOW);
  assert.ok(Math.abs(m.limit - 60.93) < 1e-9 && Math.abs(m.used - 2.79) < 1e-9, 'the profit-funded part raises the limit instead of using it');
  m = f.kalshiRiskMeter([o({ result: 'yes' }), o({ result: 'no' })], s, NOW);
  assert.ok(Math.abs(m.used - 0.93 + 0.07) < 1e-9 || m.used === 0, 'a win offsets a loss (net 0.07 - 0.93)');
  m = f.kalshiRiskMeter([o({ ts: NOW - 90000000, result: 'no' }), o({ settled: true, result: 'hand' })], s, NOW);
  assert.strictEqual(m.used, 0, 'an order older than 24 hours and one closed by hand are not counted');
  m = f.kalshiRiskMeter([o({ settled: true, result: 'exit', settledPnl: -0.75 })], s, NOW);
  assert.ok(Math.abs(m.used - 0.75) < 1e-9, 'a sold-early order counts its realised result');
  m = f.kalshiRiskMeter([o({ settled: false, result: undefined, ticker: 'KXBTC15M-26OCT231015-15' }), o({ settled: false, result: undefined, ticker: 'KXXRP15M-26OCT231015-15' })], s, NOW);
  assert.ok(Math.abs(m.windowUsed - 1.86) < 1e-9 && Math.abs(m.windowCap - 27.5) < 1e-9, 'open orders in one window add up against the 5.5% window limit');
  assert.strictEqual(f.kalshiRiskMeter([], { sizing: false, startCash: 100 }, NOW).limit, 10, 'without sizing the stop is $10');
};
gates.BS3 = () => {
  assert.ok(/id="kalStatusBody"/.test(html) && /id="kalRiskBody"/.test(html) && /data-card="status"/.test(html) && !/data-card="risk"/.test(html), 'the loss stop meter lives inside the status card (Oct 24, 2026: the separate card was mostly empty space), on the page');
  assert.ok(/kalshiStatusTimer = setInterval\(function\(\)\{ if\(!document\.hidden\)\{ kalshiStatusTick\(\); \} \}, 1000\)/.test(html) && /clearInterval\(kalshiStatusTimer\)/.test(html), 'a one second tick moves the two live lines, only while the page is visible, and stops when it is left');
  const src = require('fs').readFileSync(require('path').join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/const L1_SIZED_STOP_FRACTION = 0\.12;/.test(src) && /const L1_WINDOW_CAP_FRACTION = 0\.055;/.test(src) && /const L1_LOSS_STOP = 10\.0;/.test(src), 'the meter quotes the same 12%, 5.5% and $10 the bot uses; change one and this gate names the other');
  assert.ok(/0\.12 \* base/.test(html) && /0\.055 \* base/.test(html), 'and the page uses those numbers');
};

// BS4: the heartbeat monitor strip. Consequence: one beat per observed check, scrolling left and gone after two minutes; no beat for a while is a flat dashed line in the state's colour; a page that has not seen a beat draws a flat line, not an invented one.
gates.BS4 = () => {
  const f = liftBs(['kalshiBeatNote', 'kalshiEcgShapeAt', 'kalshiEcgNoise', 'kalshiHeartbeatPath', 'kalshiHeartbeatSvg'], 'var KAL_ECG = { W: 600, H: 70, B: 46, SPAN: 60000 }; var KAL_ECG_SHAPES = { beat: [[-14, 0], [-11, -3], [-8, 0], [-3, 0], [-1.5, 5], [0, -36], [2, 10], [4, 0], [9, 0], [13, -8], [17, 0]], read: [[-2, 0], [0, -9], [2, 3], [4, 0]], order: [[-6, 0], [-3, 8], [0, -44], [3, 14], [6, -16], [9, 0]] };');
  const NOW = 1000000000;
  const ys = (svg) => (svg.split('kal-ecg-line')[0].split('<path d="')[1] || '').match(/[ML][\d.]+ (-?[\d.]+)/g).map((x) => Number(x.split(' ')[1]));
  const tall = (svg, below) => { let runs = 0, inRun = false; for (const y of ys(svg)) { if (y < below && !inRun) runs++; inRun = y < below; } return runs; };
  // Consequence: the line is never dead while the bot is checking in, and never invents a beat.
  const flat = f.kalshiHeartbeatSvg([], NOW, 'ok');
  assert.ok(/kal-ecg ok/.test(flat) && ys(flat).every((y) => y === 46), 'no beats seen: a perfectly flat line, nothing invented');
  const one = f.kalshiHeartbeatSvg([NOW - 20000], NOW, 'ok');
  assert.ok(/<path d="M0\.0 4\d\.\d/.test(one) && tall(one, 14) === 1, 'one check is one tall beat: ' + tall(one, 14));
  assert.ok(new Set(ys(one).filter((y) => y > 44 && y < 48)).size > 5, 'while checks arrive the baseline has a small tremor, so the line is alive');
  const three = f.kalshiHeartbeatSvg([NOW - 10000, NOW - 30000, NOW - 50000], NOW, 'ok');
  assert.strictEqual(tall(three, 14), 3, 'three checks, three beats, oldest to the left');
  assert.strictEqual(tall(f.kalshiHeartbeatSvg([NOW - 400000], NOW, 'down'), 14), 0, 'a check older than a minute has scrolled off');
  assert.ok(ys(f.kalshiHeartbeatSvg([NOW - 400000], NOW, 'down')).every((y) => y === 46), 'and with no recent check the line is flat, no tremor');
  assert.ok(/kal-ecg-gap down/.test(f.kalshiHeartbeatSvg([NOW - 400000], NOW, 'down')) && /kal-ecg-gap quiet/.test(f.kalshiHeartbeatSvg([NOW - 200000], NOW, 'quiet')) && !/kal-ecg-gap/.test(one), 'a quiet or down state draws the flat dashed gap, a healthy one does not');
  // Market reads are small ticks and orders are tall spikes, each only where they really happened.
  const reads = [NOW - 5000, NOW - 10000, NOW - 15000, NOW - 20000];
  const withReads = f.kalshiHeartbeatSvg([NOW - 30000], NOW, 'ok', reads, []);
  assert.strictEqual(tall(withReads, 14), 1, 'market reads are small ticks, not beats');
  assert.ok(ys(withReads).filter((y) => y < 43).length >= reads.length, 'but each one is visible');
  const withOrder = f.kalshiHeartbeatSvg([NOW - 30000], NOW, 'ok', [], [NOW - 12000]);
  assert.ok(ys(withOrder).some((y) => y < 6), 'an order is a taller spike than a check (46 - 44)');
  const b = f.kalshiBeatNote([], 5); f.kalshiBeatNote(b, 5); f.kalshiBeatNote(b, 65);
  assert.deepStrictEqual(b, [5, 65], 'a check time is noted once, and a new one is added');
  assert.deepStrictEqual(f.kalshiBeatNote([1], NaN), [1], 'no check time, nothing added');
  const big = []; for (let i = 0; i < 40; i++) f.kalshiBeatNote(big, i);
  assert.strictEqual(big.length, 30, 'the list stays short');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
