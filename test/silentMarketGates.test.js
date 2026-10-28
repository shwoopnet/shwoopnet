'use strict';
// A strategy that quietly stops sending orders must be called out on the Bot page, and a market that is quiet by design must not cry wolf (the owner, Oct 24, 2026).
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const server = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiLiveLib.js'), 'utf8');
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
const watch = /var KAL_WATCH = [^\n]*\n/.exec(html)[0];
const f = new Function(watch + ['kalshiMarketName', 'kalshiCtWeekMinute', 'kalshiDurationText', 'kalshiSilentMarkets'].map(fnSource).join('\n') + '; return { kalshiSilentMarkets };')();
const H = 3600000, MIN = 60000;
const live = { active: true };
// Orders every `gap` ms for `days` days back from `lastAt`.
const every = (series, lastAt, gap, days) => { const o = []; for (let t = lastAt; t > lastAt - days * 86400000; t -= gap) o.push({ strategy: 'L1', series, ts: t }); return o; };
const T = (iso) => Date.parse(iso);

// Tuesday 2026-10-20 15:00 Central (20:00 UTC), mid week.
const TUE = T('2026-10-20T20:00:00Z');

gates.S1 = () => {
  const o = [...every('KXDOGE15M', TUE - 6 * H, 20 * MIN, 3), ...every('KXGOLD15M', TUE - 10 * MIN, 30 * MIN, 3)];
  const out = f.kalshiSilentMarkets(o, live, TUE);
  assert.strictEqual(out.length, 1, 'only the market that went quiet is named: ' + out.join(' | '));
  assert.ok(/^Dogecoin has sent no order for 6 hours/.test(out[0]) && /about every 20 minutes/.test(out[0]), out[0]);
};

gates.S2 = () => {
  const o = [...every('KXXRP15M', TUE - 20 * MIN, 20 * MIN, 3), ...every('KXGOLD15M', TUE - 10 * MIN, 30 * MIN, 3), ...every('KXDOGE15M', TUE - 2 * H, 90 * MIN, 3)];
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE), [], 'a market inside 8 times its usual gap, and 3 hours, is not called silent');
};

gates.S3 = () => {
  const o = every('KXBTC15M', TUE - 20 * H, 60 * MIN, 3).concat(every('KXETH15M', TUE - 20 * H, 60 * MIN, 3));
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE), [], 'Bitcoin and Ethereum are quiet by design (the smooth climb rule), so they are never named');
};

gates.S4 = () => {
  const o = every('KXDOGE15M', TUE - 30 * MIN, 20 * MIN, 3).slice(0, 6).concat(every('KXGOLD15M', TUE - 12 * H, 30 * MIN, 3).slice(0, 5));
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE), [], 'too few orders to know what usual is: nothing is said');
  assert.deepStrictEqual(f.kalshiSilentMarkets(every('KXDOGE15M', TUE - 9 * H, 20 * MIN, 3), { active: false }, TUE), [], 'a stopped bot is not a silent market: the page already says why it stopped');
};

gates.S5 = () => {
  // Saturday 2026-10-24 12:00 Central: gold and the forex pairs are closed, Dogecoin is not.
  const SAT = T('2026-10-24T17:00:00Z');
  const o = [...every('KXGOLD15M', SAT - 20 * H, 30 * MIN, 3), ...every('KXDOGE15M', SAT - 7 * H, 20 * MIN, 3), ...every('KXAUDUSD15M', SAT - 20 * H, 60 * MIN, 3)];
  const out = f.kalshiSilentMarkets(o, live, SAT);
  assert.strictEqual(out.length, 1, 'a closed weekend is not a stop for gold or the forex pairs, but Dogecoin is still named: ' + out.join(' | '));
  assert.ok(/^Dogecoin /.test(out[0]));
};

gates.S6 = () => {
  // Monday 2026-10-26 03:00 Central: the markets reopened Sunday 18:00, nine hours ago, and gold has sent nothing since. That IS a stop.
  const MON = T('2026-10-26T08:00:00Z');
  const o = every('KXGOLD15M', T('2026-10-23T21:00:00Z'), 30 * MIN, 3);
  const out = f.kalshiSilentMarkets(o, live, MON);
  assert.ok(out.length === 1 && /^Gold has sent no order for 9 hours/.test(out[0]), 'silence is counted from the reopening, not from Friday: ' + out.join(' | '));
  const MON_EARLY = T('2026-10-26T01:00:00Z');   // Sunday 20:00 Central, two hours after the reopen
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, MON_EARLY), [], 'two hours after the reopening is not yet a stop');
};

// The page names exactly the markets the server can trade, minus the two the smooth rule gates.
gates.S7 = () => {
  const series = /const L1_SERIES = \[([^\]]*)\]/.exec(server)[1];
  const probes = /const PROBE_SERIES = \[([^\]]*)\]/.exec(server)[1];
  const all = (series.replace('...PROBE_SERIES', probes).match(/KX[A-Z]+15M/g) || []);
  const names = { KXGOLD15M: 'Gold', KXXRP15M: 'XRP', KXDOGE15M: 'Dogecoin', KXAUDUSD15M: 'AUD/USD', KXUSDCAD15M: 'USD/CAD', KXNATGAS15M: 'Natural gas' };
  const smooth = ['KXBTC15M', 'KXETH15M'];
  all.forEach((s) => assert.ok(smooth.includes(s) || (names[s] && new RegExp("name: '" + names[s].replace('/', '\\/') + "'").test(watch)), s + ' is either watched or deliberately left out'));
  assert.ok(/kalshiSilentMarkets\(orders, s, now\)/.test(html) && /Needs a look/.test(html), 'the Bot status card shows the warning');
  assert.ok(/insertAdjacentHTML\('beforeend', '<div class="kal-warn kal-silent">/.test(html), 'it is added without redrawing the heartbeat trace');
};

gates.S8 = () => {
  // XRP is paused in the bot's code (Oct 28, 2026), so it sends no orders on purpose: the page must not warn that it went quiet.
  const o = every('KXXRP15M', TUE - 9 * H, 20 * MIN, 3);
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE), [], 'a paused market is not named as silent');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
