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

// Console layout: a rail (session, account, positions) beside one main column (books, trades, detail, log), books tiles above the table.
gates.Y5 = () => {
  const i = html.indexOf('id="kalTabBot"');
  const seg = html.slice(i, html.indexOf('</main>', i));
  const rail = /<div class="kal-rail">([\s\S]*?)\n      <\/div>\n      <div class="kal-main">/.exec(seg);
  assert.ok(rail, 'the rail is there and the main column follows it');
  const names = (t) => [...t.matchAll(/data-card="(\w+)"/g)].map((m) => m[1]);
  assert.deepStrictEqual(names(rail[1]), ['session', 'account', 'positions'], 'the rail holds the session first, then the account, then positions');
  const main = seg.slice(seg.indexOf('<div class="kal-main">'));
  assert.deepStrictEqual(names(main), ['books', 'trades', 'detail', 'log'], 'the main column: books tiles, trades, then the folded detail and log');
  assert.ok(/\.kal-console\{ grid-template-columns:340px minmax\(0,1fr\);/.test(html), 'a fixed-width rail and a flexible main column');
  assert.ok(/@media \(max-width:900px\)\{\s*\.kal-console\{ grid-template-columns:minmax\(0,1fr\); \}/.test(html), 'one column on a narrow screen, the rail first');
  assert.ok(/id="kalBotHalt"/.test(rail[1]) && /id="kalL1Stop"/.test(rail[1]), 'halt and stop sit together in the session card');
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
  assert.ok(/collection\(db, 'kalshiLiveOrders'\), orderBy\('ts', 'desc'\), limit\(300\)/.test(html), 'orders are read up to the most a 24 hour session can send, not 20');
  assert.ok(!/kalshiLiveOrders'\), orderBy\('ts', 'desc'\), limit\(20\)/.test(html));
  const i = html.indexOf('var loggedOrders');
  assert.ok(i > -1 && /indexOf\(' on ' \+ String\(o\.ticker\) \+ ':'\) > -1/.test(html.slice(i, i + 600)), 'an order the log already shows is not listed a second time');
  // The same filter, run: two events and the two matching order records become two lines, and an order with no logged event stays.
  const evs = [{ ts: 2, kind: 'order', detail: 'no 1 at 89.0c on T-A: no fill' }, { ts: 3, kind: 'session ended', detail: 'x' }];
  const orders = [{ ts: 2, side: 'no', count: 1, price: 0.89, ticker: 'T-A', status: 'no fill' }, { ts: 1, side: 'yes', count: 1, price: 0.92, ticker: 'T-B', status: 'filled' }];
  const logged = evs.filter((e) => e && e.kind === 'order').map((e) => String(e.detail));
  const extra = orders.filter((o) => !logged.some((d) => d.indexOf(' on ' + String(o.ticker) + ':') > -1));
  assert.deepStrictEqual(extra.map((o) => o.ticker), ['T-B']);
};

// The helpers behind the trades table and the two charts. All pure: they read nothing from the page.
gates.Y8 = () => {
  const block = (re) => { const m = re.exec(html); assert.ok(m, 'not found: ' + re); return m[1]; };
  const lift = (names) => new Function(names.map((n) => block(new RegExp('(function ' + n + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\})\\n'))).join('\n') + '; return {' + names.join(',') + '};')();
  const f = lift(['kalshiShortTicker', 'kalshiWhen', 'kalshiOrderPnl', 'kalshiOutcomeCounts', 'kalshiPnlSeries', 'kalshiLineSvg', 'kalshiDonutHtml']);
  const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
  // Ticker to a time. An unfamiliar ticker or an impossible time is shown as it is, never invented.
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT072015-15'), 'BTC 8:15 PM ET');
  assert.strictEqual(f.kalshiShortTicker('KXGOLD15M-26OCT070000-00'), 'GOLD 12:00 AM ET');
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT071200-00'), 'BTC 12:00 PM ET');
  assert.strictEqual(f.kalshiShortTicker('SOMETHING-ELSE'), 'SOMETHING-ELSE');
  assert.strictEqual(f.kalshiShortTicker('KXBTC15M-26OCT072575-15'), 'KXBTC15M-26OCT072575-15');
  // Today, tomorrow, later; nothing for a bad date.
  const noon = new Date(2026, 9, 7, 12, 0, 0).getTime();
  assert.ok(!/Tomorrow|Oct/.test(f.kalshiWhen(noon + 3600000, noon)) && /^Tomorrow /.test(f.kalshiWhen(noon + 86400000, noon)) && /^Oct 9 /.test(f.kalshiWhen(noon + 2 * 86400000, noon)));
  assert.strictEqual(f.kalshiWhen(NaN, noon), '');
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
  assert.ok(/a\.liveSwitch \? '' : '<div><span class="kal-k">Order switch<\/span><b class="kal-neg">OFF/.test(acct), 'the order switch is a line only when it is off');
  assert.ok(!/Shard ' \+/.test(acct), 'no per-shard rows');
  const head = html.slice(html.indexOf('id="page-kalshi"'), html.indexOf('id="kalTabBot"'));
  assert.ok(/id="kalLayout"/.test(head), 'the Layout menu is in the page header, not on a row of its own');
  assert.ok(!/kal-layout-bar/.test(html), 'no leftover row for it');
  const facts = html.slice(html.indexOf("document.getElementById('kalL1Facts').innerHTML = running"), html.indexOf("var sizeNote"));
  assert.strictEqual((facts.match(/fact\('/g) || []).length, 6, 'four facts while running and two when ended');
  assert.ok(/id="kalL1Size"/.test(html) && /Stops if the bot is down/.test(html), 'size and stop are one muted line');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
