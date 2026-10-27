'use strict';
// (Oct 27, 2026: the page's Order flow charts were removed for now, so only the server side is tested here; the function and library stay deployed.)
// The order flow (footprint) view is a READING tool (the owner, Oct 26, 2026): it sums Kalshi's public trades per minute and per price and can never place an order, sign a request or write anything.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/kalshiFootprintLib');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const server = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const libSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiFootprintLib.js'), 'utf8');
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

const T0 = Date.parse('2026-10-26T14:00:00Z');
const MIN = 60000;
const trade = (offsetMs, priceDollars, count, taker) => ({ created_time: new Date(T0 + offsetMs).toISOString(), yes_price_dollars: String(priceDollars), count_fp: String(count), taker_outcome_side: taker });

gates.F1 = () => {
  // A taker buying YES lifts the ask (a buy); a taker buying NO hits the bid (a sell). Reversing this would show the opposite market.
  assert.deepStrictEqual(lib.parseTrade(trade(0, 0.93, 5, 'yes')), { ts: T0, price: 93, size: 5, side: 1 });
  assert.deepStrictEqual(lib.parseTrade(trade(0, 0.93, 5, 'no')), { ts: T0, price: 93, size: 5, side: -1 });
};
gates.F2 = () => {
  // Per minute and per price: sells, buys, delta, the running total and the busiest price.
  const bars = lib.buildFootprint([
    trade(1000, 0.93, 10, 'yes'), trade(2000, 0.93, 4, 'no'), trade(3000, 0.94, 3, 'yes'),
    trade(MIN + 1000, 0.92, 20, 'no'),
  ], T0, T0 + 2 * MIN);
  assert.strictEqual(bars.length, 2, 'two minutes, none for the minute that starts at the end');
  assert.deepStrictEqual(bars[0].l, [[93, 4, 10], [94, 0, 3]]);
  assert.strictEqual(bars[0].delta, 9);
  assert.strictEqual(bars[0].poc, 93);
  assert.strictEqual(bars[1].delta, -20);
  assert.strictEqual(bars[1].cum, -11, 'the running total carries over');
};
gates.F3 = () => {
  // Quiet minutes stay in, so the page's columns line up with the clock.
  const bars = lib.buildFootprint([trade(5 * MIN + 1000, 0.9, 1, 'yes')], T0, T0 + 8 * MIN);
  assert.strictEqual(bars.length, 8);
  assert.strictEqual(bars[2].l.length, 0);
  assert.strictEqual(bars[2].poc, null);
};
gates.F4 = () => {
  // Only a market the bot trades is accepted, and nothing else reaches Kalshi.
  const allowed = ['KXGOLD15M', 'KXBTC15M'];
  assert.ok(lib.validTicker('KXGOLD15M-26OCT261530-30', allowed));
  assert.ok(!lib.validTicker('KXNFLGAME-26OCT261530-30', allowed), 'a series the bot does not trade');
  assert.ok(!lib.validTicker('KXGOLD15M-26OCT261530-30&limit=1', allowed), 'no extra query text');
  assert.ok(!lib.validTicker('', allowed) && !lib.validTicker(null, allowed));
};
gates.F5 = () => {
  // The read is bounded in age: never older than 48 hours, never past a minute from now.
  const now = T0;
  assert.strictEqual(lib.readWindow(now + 3600000, now).toMs, now + 60000);
  assert.strictEqual(lib.readWindow(now - 30 * 86400000, now).toMs, now - 48 * 3600000);
  assert.strictEqual(lib.readWindow('junk', now).toMs, now);
  assert.strictEqual(lib.readWindow(now, now).toMs - lib.readWindow(now, now).fromMs, lib.WINDOW_MS);
};
gates.F6 = () => {
  // Garbage is dropped, not counted: bad prices, zero sizes, unknown taker sides.
  assert.strictEqual(lib.parseTrade({ created_time: 'x', yes_price_dollars: '0.5', count_fp: '1', taker_outcome_side: 'yes' }), null);
  assert.strictEqual(lib.parseTrade(trade(0, 1.2, 1, 'yes')), null);
  assert.strictEqual(lib.parseTrade(trade(0, 0.5, 0, 'yes')), null);
  assert.strictEqual(lib.parseTrade(trade(0, 0.5, 1, 'maybe')), null);
  assert.deepStrictEqual(lib.parseTrade({ created_time: new Date(T0).toISOString(), yes_price: 93, count: 2, taker_side: 'no' }), { ts: T0, price: 93, size: 2, side: -1 }, 'the older cent fields still read');
};
gates.F9 = () => {
  // Read only, end to end. The function checks the admin first, makes only GET reads through the shared keyless helper, and the library holds no key or order code.
  const fn = server.slice(server.indexOf('exports.kalshiTape'), server.indexOf('// ---- Kalshi market reads'));
  assert.ok(fn.indexOf('assertKalshiAdmin') > 0 && fn.indexOf('assertKalshiAdmin') < fn.indexOf('validTicker'), 'admin first');
  assert.ok(/kalshiGetJson\(/.test(fn) && !/method\s*:|POST|signRequest|PRIVATE|secret|setDoc|getFirestore|collection\(|\.doc\(/i.test(fn), 'GET reads only, no writes');
  assert.ok(!/require\(|fetch\(|POST|PRIVATE|secret|sign/i.test(libSrc.replace(/\/\/.*$/gm, '')), 'the library only sums');
};
gates.F11 = () => {
  // The whole-series view: only a series the bot trades, only 30 or 60 minutes, and the window ends where the single-market window would.
  const allowed = ['KXGOLD15M', 'KXBTC15M'];
  assert.ok(lib.validSeries('KXGOLD15M', allowed) && !lib.validSeries('KXNFLGAME', allowed) && !lib.validSeries('KXGOLD15M-26OCT261045-30', allowed) && !lib.validSeries(null, allowed));
  const w60 = lib.seriesWindow(60, T0, T0), w30 = lib.seriesWindow(30, T0, T0);
  assert.strictEqual(w60.toMs - w60.fromMs, 60 * MIN);
  assert.strictEqual(w30.toMs - w30.fromMs, 30 * MIN);
  assert.strictEqual(lib.seriesWindow(1000, T0, T0).spanMin, 30, 'any other span becomes 30 minutes');
  assert.strictEqual(lib.seriesWindow(60, T0 - 30 * 86400000, T0).toMs, T0 - 48 * 3600000, 'still no older than 48 hours');
};
gates.F12 = () => {
  // The windows of a series come from Kalshi's market list: only this series, only markets that overlap the span, oldest first, at most six.
  const close = (m) => new Date(T0 + m * MIN).toISOString();
  let seq = 1000;
  const mk = (series, m) => ({ ticker: series + '-26OCT26' + (seq++) + '-30', close_time: close(m) });
  const list = [mk('KXGOLD15M', 15), mk('KXGOLD15M', 0), mk('KXGOLD15M', -15), mk('KXGOLD15M', -45), mk('KXGOLD15M', -75), mk('KXBTC15M', 0), { ticker: 'KXGOLD15M-bad', close_time: close(0) }, { ticker: 'KXGOLD15M-26OCT261045-30', close_time: 'x' }];
  const w = lib.windowsFromMarkets(list, 'KXGOLD15M', T0 - 60 * MIN, T0);
  assert.deepStrictEqual(w.map((x) => x.closeMs - T0), [-45 * MIN, -15 * MIN, 0], 'a market opens 15 minutes before it closes: it must start before the span ends and close after it begins');
  assert.ok(w.every((x) => x.ticker.startsWith('KXGOLD15M-')), 'only this series');
  const many = Array.from({ length: 12 }, (_, i) => mk('KXGOLD15M', -i * 5));
  assert.ok(lib.windowsFromMarkets(many, 'KXGOLD15M', T0 - 90 * MIN, T0 + 15 * MIN).length <= 6);
};
gates.F15 = () => {
  // Whales: a print is BIG only when it is several times the usual size AND not small in absolute terms; a quiet market's largest trade is listed but not called unusual.
  const trades = [];
  for (let i = 0; i < 20; i++) trades.push(trade(1000 + i * 1000, 0.93, 4, i % 2 ? 'yes' : 'no'));
  trades.push(trade(30000, 0.94, 300, 'yes'));
  const r = lib.bigPrints(trades, T0, T0 + MIN);
  assert.strictEqual(r.median, 4);
  assert.strictEqual(r.prints[r.prints.length - 1].size <= 300, true);
  const big = r.prints.find((p) => p.size === 300);
  assert.ok(big.big && big.times === 75 && big.side === 1 && big.price === 94, 'a 300 contract print among 4 contract trades is big');
  const quiet = lib.bigPrints([trade(1000, 0.9, 6, 'yes'), trade(2000, 0.9, 1, 'no'), trade(3000, 0.9, 1, 'no')], T0, T0 + MIN);
  assert.ok(quiet.prints.every((p) => !p.big), '6 contracts is 6 times the median but under 50, so not unusual');
};
gates.F16 = () => {
  // The list is bounded, newest first, ignores garbage and trades outside the window, and an empty window is empty, not an error.
  const many = Array.from({ length: 30 }, (_, i) => trade(i * 1000, 0.9, 10 + i, 'yes'));
  const r = lib.bigPrints(many.concat([{ created_time: 'x' }, null]), T0, T0 + MIN);
  assert.strictEqual(r.prints.length, lib.MAX_PRINTS);
  assert.ok(r.prints.every((p, i, a) => i === 0 || a[i - 1].t >= p.t), 'newest first');
  assert.deepStrictEqual(lib.bigPrints([], T0, T0 + MIN), { prints: [], median: 0 });
  assert.strictEqual(lib.bigPrints([trade(-5 * MIN, 0.9, 500, 'yes')], T0, T0 + MIN).prints.length, 0, 'outside the window');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
if (failed) process.exit(1);
