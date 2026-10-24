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
  const code = ['dataMarketRows', 'dataTrial', 'dataMarketTrend', 'dataAgenda', 'dataVerdictHtml', 'dataRulesHtml', 'dataHeadline', 'dataDotsHtml', 'dataLiveTests', 'renderDataCenter'].map(fnSource).join('\n');
  assert.ok(!/api\.|window\.__shwoopAPI|fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(/.test(code), 'and its code calls nothing: it only draws what the Kalshi page already loaded');
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


// DQ: the questions and agenda (Oct 23, 2026, the owner chose "Questions + agenda"). Consequences: what needs a look is ranked by rules written in advance, a rule on trial that crosses its line goes first, a quiet account says "Nothing needs you",
// and the page is six questions that fold open, with no control in them.
const dqNames = ['kalshiOrderPnl', 'kalshiMarketName', 'kalDate', 'dataTrial', 'dataMarketTrend', 'dataAgenda', 'dataVerdictHtml', 'dataRulesHtml'];
const dqExtra = html.slice(html.indexOf('  var DATA_SMOOTH_FROM'), html.indexOf('  // The smooth-climb rule on trial')) + html.slice(html.indexOf('  var DATA_SHARD_LOW'), html.indexOf('  // The list, in the order written on the page'));
const dqLift = () => lift(dqNames, dqExtra + "\nfunction kalshiAgeText(s){ return s + ' seconds ago'; }");
const dqOrder = (series, ts, pnl, extra) => Object.assign({ ts, series, settled: true, fillCount: '1.00', settledPnl: pnl, smooth: undefined }, extra || {});

gates.DQ1 = () => {
  const f = dqLift();
  const after = Date.UTC(2026, 9, 24, 12), before = Date.UTC(2026, 9, 20, 12);
  const sm = (n, lost) => Array.from({ length: n }, (_, i) => dqOrder('KXBTC15M', after + i * 1000, i < lost ? -0.9 : 0.06, { smooth: true }));
  assert.strictEqual(f.dataTrial([...sm(10, 2), dqOrder('KXBTC15M', before, -0.9, { smooth: true }), dqOrder('KXGOLD15M', after, -3, { smooth: true })]).fills, 10, 'only Bitcoin and Ethereum smooth fills after the deploy are on trial');
  assert.strictEqual(f.dataTrial(sm(10, 2)).near, true, 'two losses is one step from the line');
  assert.strictEqual(f.dataTrial(sm(10, 3)).past, true, 'three losses in the first 40 crosses it');
  assert.strictEqual(f.dataTrial(sm(100, 0).map((o) => Object.assign(o, { settledPnl: -0.01 }))).past, true, 'a combined result under zero after 100 fills crosses it');
  const money = (v) => '$' + v.toFixed(2);
  const now = Date.UTC(2026, 9, 25);
  const quiet = f.dataAgenda({ trial: f.dataTrial([]), risk: { fraction: 0.1 }, trend: [], shards: [{ shard: 0, dollars: 100 }, { shard: 2, dollars: 300 }], hb: 'ok', now, money });
  assert.deepStrictEqual(quiet.map((x) => x.rank), [5], 'a quiet account has only the next scheduled read');
  const out = f.dataVerdictHtml(quiet, esc);
  assert.ok(/Nothing needs you/.test(out) && /Smooth-climb forward read/.test(out), 'and says so, with the date of the next read');
  const loud = f.dataVerdictHtml(f.dataAgenda({ trial: f.dataTrial(sm(10, 3)), risk: { fraction: 0.1 }, trend: [], shards: [], hb: 'ok', now, money }), esc);
  assert.ok(/Smooth climb has crossed its line/.test(loud) && !/Nothing needs you/.test(loud), 'a rule past its line is the sentence at the top');
  const busy = f.dataAgenda({ trial: f.dataTrial(sm(10, 3)), risk: { fraction: 0.8 }, trend: [{ name: 'Bitcoin', enough: true, flag: true, recent: -0.4, prior: -0.5, w: 33, n: 66 }], shards: [{ shard: 0, dollars: 0.5 }], hb: 'down', now, money });
  assert.deepStrictEqual(busy.map((x) => x.rank), [1, 2, 3, 4, 4, 5], 'a rule past its line first, then the stop, the market, the machine, the next read: ' + JSON.stringify(busy.map((x) => x.text)));
  const low = f.dataAgenda({ trial: f.dataTrial([]), risk: { fraction: 0.1 }, trend: [], shards: [{ shard: 0, dollars: 25 }, { shard: 2, dollars: 300 }], hb: 'ok', now, money });
  assert.deepStrictEqual(low.map((x) => x.rank), [4, 5], 'a shard under $30 is called out while there is still time to top it up by hand');
  assert.ok(/Shard 0 is low/.test(low[0].text) && /Transfers/.test(low[0].detail), 'and says where to top it up');
  assert.ok(/Shard 0 is low/.test(busy[3].text) && /Bitcoin is -0\.4c/.test(busy[2].text), 'the figures are in the lines');
};

gates.DQ2 = () => {
  const f = dqLift();
  const o = (i, p) => dqOrder('KXXRP15M', i * 1000, p, { ts: i * 1000 });
  const mk = (n, recent) => Array.from({ length: n }, (_, i) => o(i, i >= n / 2 ? recent : 0.05));
  const t59 = f.dataMarketTrend(mk(59, -0.1)), t60 = f.dataMarketTrend(mk(60, -0.1))[0];
  assert.strictEqual(t59[0].enough, false, 'fewer than 60 trades says nothing');
  assert.ok(t60.enough && t60.w === 30 && t60.flag === true && t60.recent < 0 && t60.prior > 0, 'a market whose latest 30 are negative against 30 positive is flagged');
  assert.strictEqual(f.dataMarketTrend(mk(60, 0.05))[0].flag, false, 'an unchanged market is not');
  assert.strictEqual(f.dataMarketTrend(mk(60, 0.02))[0].flag, true, 'a result that fell to under half of the one before is flagged');
};

// DS: the page is one screen (Oct 23, 2026, the owner: "do we need a data page?", then "shrink to one screen"). Consequences: a verdict sentence, the growth line and the rules on trial are all there is; everything else the page used to carry
// (tiles, strategy numbers, by-market table, weekly bars, order ring, each-trade bars, entry timing, price bands, the six question folds) is gone, and the page still has no control.
gates.DS1 = () => {
  const page = html.slice(html.indexOf('<main class="page" id="page-data"'), html.indexOf('<main class="page" id="page-settings"'));
  ['dataHead', 'dataVerdict', 'dataLine', 'dataDots', 'dataTrial', 'dataNote'].forEach((id) => assert.ok(page.includes('id="' + id + '"'), id + ' is on the page'));
  assert.strictEqual((page.match(/data-card="/g) || []).length, 4, 'four cards: the headline, the growth line, every trade as a dot, the rules on trial');
  ['dataTiles', 'dataWeekly', 'dataStats', 'dataMarkets', 'dataLead', 'dataLiveTests', 'kalChartPie', 'kalChartBars', 'kalPerf', 'dataQa1', 'dataAgenda'].forEach((id) => assert.ok(!page.includes('id="' + id + '"'), id + ' is gone'));
  assert.ok(!/<details/.test(page), 'nothing folds: there is nothing hidden to open');
};
gates.DS2 = () => {
  const f = lift(['kalDate', 'dataTrial', 'dataLiveTests', 'dataRulesHtml', 'kalshiOrderPnl', 'kalshiMarketName'], html.slice(html.indexOf('  var DATA_SMOOTH_FROM'), html.indexOf('  // The smooth-climb rule on trial')));
  const out = f.dataRulesHtml(f.dataTrial([]), f.dataLiveTests([]), Date.UTC(2026, 9, 25), esc);
  assert.ok(/Smooth climb, Bitcoin and Ethereum/.test(out) && /no fills yet/.test(out) && /One crypto order per window/.test(out) && /Probe markets drop rule/.test(out), 'three rules, each saying what it has so far');
  assert.ok(/Read Nov 12/.test(out) && /Export review Nov 17/.test(out) && /Check Nov 30/.test(out), 'each with the date it is read');
  assert.ok(!/<(button|input|select|a )\b/i.test(out), 'plain, no control');
};

// DT: the headline and the dots (Oct 24, 2026). Consequences: the headline is the last 30 days as a share of the account (not a dollar figure), a win is a dot that is brighter the bigger it was, a loss is a red ring, hover text goes through the money
// formatter so Privacy view masks it, and no dot is a control.
gates.DT1 = () => {
  const f = lift(['kalshiOrderPnl', 'dataHeadline']);
  const now = Date.UTC(2026, 9, 24, 12), day = 86400000;
  const o = (d, p) => ({ ts: now - d * day, settled: true, fillCount: '1.00', settledPnl: p });
  assert.strictEqual(f.dataHeadline([o(1, 10), o(2, -2), o(40, 99)], 508, now), 'Up 1.6%.', 'the 40 day old trade is left out: 8 / (508 - 8)');
  assert.strictEqual(f.dataHeadline([o(1, -5)], 495, now), 'Down 1.0%.', '-5 / (495 + 5)');
  assert.strictEqual(f.dataHeadline([o(1, 0.1)], 500, now), 'Flat.', 'under 0.05% is flat');
  assert.strictEqual(f.dataHeadline([o(40, 5)], 500, now), 'No trades in 30 days.');
  assert.strictEqual(f.dataHeadline([o(1, 1), o(2, 1)], null, now), '2 trades in 30 days.', 'an unknown balance gives a count, never a wrong percentage');
  assert.ok(!/\$/.test(f.dataHeadline([o(1, 10)], 508, now)), 'not a dollar figure, so Privacy view leaves it showing');
};
gates.DT2 = () => {
  const f = lift(['kalDateTime', 'kalshiOrderPnl', 'kalshiMarketName', 'dataDotsHtml']);
  const o = (h, series, p) => ({ ts: Date.UTC(2026, 9, 14, h), series, settled: true, fillCount: '1.00', settledPnl: p });
  const out = f.dataDotsHtml([o(18, 'KXGOLD15M', -3.8), o(16, 'KXGOLD15M', 0.4), o(17, 'KXBTC15M', 0.1)], esc, money);
  assert.strictEqual((out.match(/class="dd"/g) || []).length, 2, 'two wins are dots');
  assert.strictEqual((out.match(/class="dd dd-loss"/g) || []).length, 1, 'one loss is a ring');
  assert.ok(out.indexOf('Gold \u00b7 +$0.40') < out.indexOf('Bitcoin \u00b7 +$0.10') && out.indexOf('Bitcoin \u00b7 +$0.10') < out.indexOf('Gold \u00b7 -$3.80'), 'oldest first, each with its market and signed result');
  assert.ok(/opacity:1\.00/.test(out) && /opacity:0\.51/.test(out), 'the biggest win is fully bright, a quarter of it is dimmer: 0.35 + 0.65 * 0.25');
  assert.ok(/3 trades, 1 loss/.test(out) && !/<(button|input|select|a )\b/i.test(out), 'it says what it shows and has no control');
  assert.ok(/Dots appear after the first settled trade/.test(f.dataDotsHtml([], esc, money)), 'nothing yet says so');
  const masked = f.dataDotsHtml([o(16, 'KXGOLD15M', 0.4)], esc, (x) => '****');
  assert.ok(masked.includes('+****') && !/\$0\.40/.test(masked), 'hover text goes through the money formatter');
  assert.ok(/dataDotsHtml\(orders, escapeHtml, kalshiMoney\)/.test(html), 'and the page passes the masking formatter');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
