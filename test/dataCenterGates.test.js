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
  const code = ['kalshiPnlSeries', 'kalshiCtMidnight', 'kalshiPnlRangeStart', 'kalshiPnlCardHtml', 'renderKalshiPnl', 'kalshiLineSvg'].map(fnSource).join('\n');
  assert.ok(!/fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(/.test(code.replace(/api\.kalshiOrdersSince/g, '')), 'and its code writes and calls nothing: it draws what the page loaded, plus one read of older orders');
  assert.ok((code.match(/api\.\w+/g) || []).every((c) => c === 'api.kalshiOrdersSince'), 'the only API it touches is the read of older orders');
  const mod = html.slice(html.indexOf('kalshiOrdersSince: function'), html.indexOf('kalshiBookSnaps: function'));
  assert.ok(/getDocs\(query\(collection\(db, 'kalshiLiveOrders'\)/.test(mod) && !/setDoc|updateDoc|addDoc/.test(mod), 'that read is a plain query of the bot orders, admin read only by the rules');
  assert.ok(!/id="kalRecord"|data-card="record"|renderKalshiRecord/.test(html), 'the record card (headline and rules on trial) is gone (removed Oct 24, 2026, the owner)');
};

// The account result line: the range cuts the running settled result, and the line starts at zero at the start of the range, so a long range is never drawn from a total the range did not earn.
gates.PL1 = () => {
  const f = lift(['kalDayKey', 'kalDateTime', 'kalDate', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPnlSeries', 'kalshiCtMidnight', 'kalshiPnlRangeStart', 'kalTime', 'chartNiceStep', 'chartValueTicks', 'chartPctLabel', 'chartCtOffset', 'chartTimeTicks', 'kalshiPnlGeometry', 'kalshiPnlYTicks', 'kalshiPnlPct', 'kalshiLineSvg', 'kalshiPnlCardHtml'], 'var kalshiPnlScrub = null;');
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
  assert.ok(!/back to |settled trades, oldest/.test(out), 'no caption text on the card (removed Oct 24, 2026, the owner)');
  const withPct = f.kalshiPnlCardHtml(orders, '3M', now, esc, money, 506.5);
  assert.ok(/\+1\.3%/.test(withPct), 'the result as a share of the account at the start of the range: 6.50 / (506.50 - 6.50) = +1.3%: ' + withPct.replace(/<[^>]*>/g, ' '));
  const masked = f.kalshiPnlCardHtml(orders, '3M', now, esc, (v) => '****', 506.5);
  assert.ok(/\+1\.3%/.test(masked) && /\*\*\*\*/.test(masked) && !/\$/.test(masked), 'under Privacy view the dollars are masked and the percentage still shows');
  assert.ok(!/%/.test(f.kalshiPnlCardHtml(orders, '3M', now, esc, money, null).replace(/<[^>]*>/g, ' ')), 'no balance known: no percentage, never a wrong one');
  assert.ok(/\*\*\*\*/.test(f.kalshiPnlCardHtml(orders, '1M', now, esc, (v) => '****')) && !/\$/.test(f.kalshiPnlCardHtml(orders, '1M', now, esc, (v) => '****')), 'Privacy view masks every dollar figure on it');
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


// PL2: scrubbing the result line. Consequence: the percentage at any point is that point's result over the balance at the start of the range, signed, and blank when the balance is unknown; the pointer reads the same geometry the line was drawn with.
gates.PL2 = () => {
  const f = lift(['kalshiPnlGeometry', 'kalshiPnlPct']);
  assert.strictEqual(f.kalshiPnlPct(6.5, 500), '+1.3%');
  assert.strictEqual(f.kalshiPnlPct(-2.5, 250), '-1.0%');
  assert.strictEqual(f.kalshiPnlPct(1, NaN), '', 'no balance: no percentage');
  assert.strictEqual(f.kalshiPnlPct(1, 0), '', 'a start of zero: no percentage');
  const g = f.kalshiPnlGeometry([{ cum: 0 }, { cum: 5 }, { cum: -5 }], 1000, 5000);
  assert.ok(g.X(1000) === g.L && g.X(5000) === g.W - g.R, 'the start and the end of the range sit at the edges of the plot');
  assert.ok(Math.abs(g.X(3000) - (g.L + g.W - g.R) / 2) < 1e-9, 'x is time: halfway through the range is halfway across');
  assert.ok(g.Y(5) < g.Y(0) && g.Y(0) < g.Y(-5), 'a higher result is higher on the chart');
  assert.ok(/kalshiMoney\(Math\.abs\(cum\)\)/.test(html) && /kalDateTime\(pt\.t\)\)/.test(html) && !/kalDateTime\(pt\.t\) \+ ' CT'/.test(html), 'the scrubbed figure goes through the money formatter (masked in Privacy view) and shows the trade time (the formatter already says CT, once)');
  assert.ok(/#kalPnlBody svg\{ touch-action:pan-y/.test(html), 'a finger on the line still scrolls the page');
};

// PL3: the axes. Consequence: ticks are round numbers that cover the data, zero is always one of them, time ticks land on Central-clock hours or midnights, and the card shows both axes with the y labels in percent of the account.
gates.PL3 = () => {
  const f = lift(['kalTime', 'kalDate', 'kalDateTime', 'kalDayKey', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiPnlSeries', 'kalshiPnlRangeStart', 'chartNiceStep', 'chartValueTicks', 'chartPctLabel', 'chartCtOffset', 'chartTimeTicks', 'kalshiPnlGeometry', 'kalshiPnlYTicks', 'kalshiPnlPct', 'kalshiLineSvg', 'kalshiPnlCardHtml'], 'var kalshiPnlScrub = null;');
  const lift2 = f;
  assert.deepStrictEqual(lift2.chartValueTicks(-0.8, 1.2, 5), [-0.5, 0, 0.5, 1], 'round steps inside the data, with zero');
  assert.deepStrictEqual(lift2.chartValueTicks(0, 0, 5), [], 'no range, no ticks');
  assert.strictEqual(lift2.chartPctLabel(0, 0.5), '0%'); assert.strictEqual(lift2.chartPctLabel(0.5, 0.5), '+0.5%'); assert.strictEqual(lift2.chartPctLabel(-2, 2), '-2%');
  const t0 = Date.UTC(2026, 9, 22, 17, 0), day = lift2.chartTimeTicks(t0, t0 + 12 * 3600000, 5);
  assert.deepStrictEqual(day.map((x) => x.label), ['12 PM', '3 PM', '6 PM', '9 PM', '12 AM'], 'half a day: every 3 hours on the Central clock (12:00 PM CT is 17:00 UTC in October)');
  const days = lift2.chartTimeTicks(t0, t0 + 4 * 86400000, 5);
  assert.deepStrictEqual(days.map((x) => x.label), ['Oct 23', 'Oct 24', 'Oct 25', 'Oct 26'], 'four days: one tick a day, on Central midnights, as dates');
  const now = Date.UTC(2026, 9, 24, 18), d = 86400000;
  const o = (ago, p) => ({ ts: now - ago * d, series: 'KXGOLD15M', settled: true, fillCount: '1.00', settledPnl: p });
  const orders = [o(20, -1), o(10, 2), o(2, 2), o(0.1, 0.5)];
  const out = lift2.kalshiPnlCardHtml(orders, '1M', now, (x) => String(x), (v) => '$' + v.toFixed(2), 1003.5);
  assert.ok(/class="kal-yaxis"/.test(out) && /class="kal-xaxis"/.test(out), 'both axes are on the card');
  const yl = [...out.matchAll(/<div class="kal-yaxis">([\s\S]*?)<\/div>/g)][0][1];
  const ylt = yl.replace(/<[^>]*>/g, ' ');
  assert.ok(/0%/.test(ylt) && /\+[\d.]+%/.test(ylt) && !/\$/.test(ylt), 'the y labels are percentages of the account, with a 0% line: ' + ylt);
  assert.ok(/Oct \d+/.test([...out.matchAll(/<div class="kal-xaxis">([\s\S]*?)<\/div>/g)][0][1]), 'the x labels are dates');
  const noBal = lift2.kalshiPnlCardHtml(orders, '1M', now, (x) => String(x), (v) => '****', null);
  assert.ok(!/%/.test([...noBal.matchAll(/<div class="kal-yaxis">([\s\S]*?)<\/div>/g)][0][1].replace(/<[^>]*>/g, ' ')), 'no known balance: the y axis is dollars (masked), never a made-up percentage');
};

// PL4: "Today" means one thing. Consequence (the owner, Oct 25, 2026: the Account card said +$0.03 and the result line's Today said -$0.41): the result line's Today range starts at 00:00 Central exactly, in summer (05:00 UTC) and winter (06:00 UTC), so it holds the same
// orders as the Account card's Today, which counts every order whose Central date is today. It used to start at 06:00 UTC all year and dropped the first hour of every summer day.
gates.PL4 = () => {
  const f = lift(['kalDayKey', 'kalshiOrderPnl', 'kalshiMarketName', 'kalshiOutcomeCounts', 'kalshiTradePnl', 'kalDateTime', 'kalshiResolveOrders', 'kalshiPerfStats', 'kalshiPnlSeries', 'kalshiCtMidnight', 'kalshiPnlRangeStart']);
  const at = (iso) => Date.parse(iso);
  assert.strictEqual(f.kalshiPnlRangeStart('1D', at('2026-10-25T12:00:00Z')), at('2026-10-25T05:00:00Z'), 'summer: the Central day begins at 05:00 UTC');
  assert.strictEqual(f.kalshiPnlRangeStart('1D', at('2026-12-05T12:00:00Z')), at('2026-12-05T06:00:00Z'), 'winter: at 06:00 UTC');
  assert.strictEqual(f.kalshiPnlRangeStart('1D', at('2026-11-01T15:00:00Z')), at('2026-11-01T05:00:00Z'), 'the day daylight saving ends still begins at 00:00 Central');
  assert.strictEqual(f.kalshiPnlRangeStart('1D', at('2026-03-08T15:00:00Z')), at('2026-03-08T06:00:00Z'), 'and the day it starts');
  assert.strictEqual(f.kalshiPnlRangeStart('YTD', at('2026-10-25T12:00:00Z')), at('2026-01-01T06:00:00Z'), 'the year begins at 00:00 Central on Jan 1');
  const o = (iso, p) => ({ ts: at(iso), series: 'KXGOLD15M', settled: true, fillCount: '1.00', settledPnl: p });
  const orders = [o('2026-10-25T04:30:00Z', -9), o('2026-10-25T05:10:00Z', 0.44), o('2026-10-25T05:50:00Z', 0.1), o('2026-10-25T12:00:00Z', -0.51)];
  const now = at('2026-10-25T18:00:00Z'), today = f.kalDayKey(now);
  const card = f.kalshiPerfStats(orders.filter((x) => f.kalDayKey(x.ts) === today), 0).total;
  const series = f.kalshiPnlSeries(orders, f.kalshiPnlRangeStart('1D', now)), line = series.length ? series[series.length - 1].cum : 0;
  assert.ok(Math.abs(card - line) < 1e-9 && Math.abs(card - 0.03) < 1e-9, 'the Account card and the result line agree on Today: ' + card + ' vs ' + line + ' (the 04:30 UTC order is yesterday, Central, and is in neither)');
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
