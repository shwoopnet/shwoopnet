'use strict';
// SF1 to SF5: the page's own words about the bot must match the bot's code (the owner, Oct 29, 2026: the Bot page still said XRP had a 10 minute look and Dogecoin traded 3 contracts after both had changed).
// Consequence: a code change that makes the page's rules, sizes, limits or market lists untrue fails here, in the pull request that changes the code, instead of reaching the owner as a stale line on a real-money control.
// Add a line here whenever new page text states a number or a market list that the bot's code decides.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const NAMES = { KXGOLD15M: 'gold', KXXRP15M: 'XRP', KXBTC15M: 'Bitcoin', KXDOGE15M: 'Dogecoin', KXETH15M: 'Ethereum', KXAUDUSD15M: 'AUD/USD', KXUSDCAD15M: 'USD/CAD', KXNATGAS15M: 'natural gas' };
const nameOf = (s) => { assert.ok(NAMES[s], s + ' is a new series: give it a name in this test and check every line of page text that lists markets'); return NAMES[s]; };
const pausedNames = live.PAUSED_SERIES.map(nameOf), liveNames = live.L1_SERIES.filter((s) => !live.PAUSED_SERIES.includes(s)).map(nameOf);
const menu = (() => { const i = html.indexOf('id="kalBotMenu"'); return html.slice(i, html.indexOf('</details>\n          </details>', i) + 20); })();
const text = (h) => h.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ');
const list = (s) => s.split(/,\s*|\s+and\s+/).map((x) => x.trim()).filter(Boolean);

gates.SF1 = () => {
  const l = /<span id="kalRulesLive">Markets trading now: ([^<.]+)\.<\/span>/.exec(menu), p = /<span id="kalRulesPaused">Paused in code: ([^<.]+)\.<\/span>/.exec(menu);
  assert.ok(l && p, 'the two market lists are in the Rules and limits text');
  assert.deepStrictEqual(list(l[1]).sort(), liveNames.slice().sort(), 'the markets the page says trade now are exactly the ones the bot can trade (L1_SERIES minus PAUSED_SERIES)');
  assert.deepStrictEqual(list(p[1]).sort(), pausedNames.slice().sort(), 'the markets the page says are paused are exactly PAUSED_SERIES');
};
gates.SF2 = () => {
  const t = text(menu);
  assert.ok(new RegExp('one contract per \\$' + live.SCALE_DOLLARS_PER_CONTRACT + ' of balance').test(t), 'the gold ladder step in dollars');
  assert.ok(new RegExp('at most ' + (live.L1_WINDOW_CAP_FRACTION * 100) + '% of the balance in one 15 minute window').test(t), 'the one window limit');
  assert.ok(new RegExp('down ' + (live.L1_SIZED_STOP_FRACTION * 100) + '% of the balance').test(t) && new RegExp('stop at ' + (live.L1_SIZED_STOP_FRACTION * 100) + '% of the balance').test(t), 'the loss stop, in the rules and in the Start confirmation');
  assert.ok(new RegExp('Exit at ' + Math.round(live.EXIT_THRESHOLD * 100) + 'c').test(t) && new RegExp('falls to ' + Math.round(live.EXIT_THRESHOLD * 100) + 'c').test(t), 'the exit line');
  const doge = live.FIXED_CONTRACTS.KXDOGE15M;
  assert.strictEqual((t.match(new RegExp('Dogecoin[^.]*always ' + doge + ' contracts', 'g')) || []).length, 2, 'Dogecoin\'s fixed size is stated twice (Size, and the Start confirmation) and both say ' + doge);
  assert.ok(/Ethereum 1\b/.test(t) && !('KXETH15M' in live.FIXED_CONTRACTS), 'Ethereum is one contract');
  assert.ok(new RegExp('at most a quarter of the base size').test(t) && live.ADDON_MAX_FRACTION === 0.25, 'the add-on cap is a quarter of the base');
  const qh = live.QUIET_HOURS_CT.KXGOLD15M;
  assert.ok(qh && qh[0] === 20 && qh[1] === 24 && /Gold places no new orders from 8 PM to midnight Central/.test(t), 'gold quiet hours: the page says what QUIET_HOURS_CT says');
};
gates.SF3 = () => {
  const rest = text(menu.replace(/<span id="kalRulesPaused">[\s\S]*?<\/span>/, ''));
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(rest), 'the Account card and its rules never name ' + n + ' as anything but paused'));
  const open = text((html.match(/id="kalL1Confirm"[\s\S]*?<\/span>/) || [''])[0]);
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(open), 'the Start confirmation does not mention paused ' + n));
};
gates.SF4 = () => {
  const label = (/label = '(6 minute look: [^']+)'/.exec(html) || [])[1];
  assert.ok(label, 'the next look label is found');
  liveNames.forEach((n) => assert.ok(new RegExp(n, 'i').test(label), 'the next look names ' + n));
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(label), 'the next look does not name paused ' + n));
  assert.ok(!/10 minute look/.test(html.slice(html.indexOf('function kalshiNextEntry'), html.indexOf('function kalshiNextEntry') + 600)) || live.EARLY_PROBE_SERIES.some((s) => !live.PAUSED_SERIES.includes(s)), 'no 10 minute look unless a market with one can trade');
};
gates.SF5 = () => {
  const watch = /var KAL_WATCH = \[([^\]]+)\];/.exec(html);
  assert.ok(watch, 'KAL_WATCH is found');
  const entries = [...watch[1].matchAll(/\{ name: '([^']+)'([^}]*)\}/g)].map((m) => ({ name: m[1], paused: /paused: true/.test(m[2]) }));
  const byName = { Gold: 'KXGOLD15M', XRP: 'KXXRP15M', Dogecoin: 'KXDOGE15M', 'AUD/USD': 'KXAUDUSD15M', 'USD/CAD': 'KXUSDCAD15M', 'Natural gas': 'KXNATGAS15M' };
  entries.forEach((e) => { assert.ok(byName[e.name], e.name + ' is a new silent-market entry: map it in this test'); assert.strictEqual(e.paused, live.PAUSED_SERIES.includes(byName[e.name]), 'the silent-market warning treats ' + e.name + (e.paused ? ' as paused' : ' as live') + ', like the bot'); });
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
