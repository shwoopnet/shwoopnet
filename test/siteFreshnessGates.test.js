'use strict';
// SF1 to SF7: the page's own words about the bot must match the bot's code (the owner, Oct 29, 2026: the Bot page still said XRP had a 10 minute look and Dogecoin traded 3 contracts after both had changed).
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
const menu = (() => { const i = html.indexOf('id="kalBotMenu"'); return html.slice(i, html.indexOf('L1 failed its own test', i) + 80); })();
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
  assert.ok(!('KXDOGE15M' in live.FIXED_CONTRACTS) && live.maxContractsFor('KXDOGE15M') === live.L1_ORDER_CEILING, 'Dogecoin follows the gold ladder in code');
  assert.ok(/Gold and Dogecoin grow with the account/.test(t) && /except gold and Dogecoin, whose size scales with the account/.test(t) && !/Dogecoin[^.]*always \d+ contracts/.test(t), 'the page says Dogecoin grows with the account, in the Size note and in the Start confirmation');
  assert.ok(!/Ethereum 1\b/.test(t) && live.PAUSED_SERIES.includes('KXETH15M'), 'Ethereum is paused and no longer listed with a size');
  assert.ok(new RegExp('at most a quarter of the base size').test(t) && live.ADDON_MAX_FRACTION === 0.25, 'the add-on cap is a quarter of the base');
  assert.deepStrictEqual(live.QUIET_HOURS_CT, {}, 'no quiet hours are set in code (lifted Oct 30, 2026), so the page must not promise a pause');
  assert.ok(!/place no new orders from 8 PM/.test(t) && /around the clock/.test(t), 'the page says gold and Dogecoin trade around the clock');
};
gates.SF3 = () => {
  // The one deliberate exception: the sentence about the second strategy, which trades Bitcoin through the slot (not through L1, where Bitcoin stays paused). It must name only the registered strategy's market.
  const slotSpan = (menu.match(/<span id="kalRulesSlot">[\s\S]*?<\/span>/) || [''])[0];
  assert.ok(/Bitcoin only/.test(slotSpan) && !/Ethereum|gold|Dogecoin|XRP|AUD|CAD|natural gas/i.test(slotSpan), 'the slot sentence names Bitcoin and nothing else');
  const rest = text(menu.replace(/<span id="kalRulesPaused">[\s\S]*?<\/span>/, '').replace(/<span id="kalRulesSlot">[\s\S]*?<\/span>/, ''));
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
  const watch = /var KAL_WATCH = (\[[\s\S]*?\]);\s*\n/.exec(html);
  assert.ok(watch, 'KAL_WATCH is found');
  const entries = [...watch[1].matchAll(/\{ name: '([^']+)'([^}]*)\}/g)].map((m) => ({ name: m[1], paused: /paused: true/.test(m[2]) }));
  const byName = { Gold: 'KXGOLD15M', XRP: 'KXXRP15M', Dogecoin: 'KXDOGE15M', 'AUD/USD': 'KXAUDUSD15M', 'USD/CAD': 'KXUSDCAD15M', 'Natural gas': 'KXNATGAS15M' };
  entries.forEach((e) => { assert.ok(byName[e.name], e.name + ' is a new silent-market entry: map it in this test'); assert.strictEqual(e.paused, live.PAUSED_SERIES.includes(byName[e.name]), 'the silent-market warning treats ' + e.name + (e.paused ? ' as paused' : ' as live') + ', like the bot'); });
};

gates.SF6 = () => {
  // The Rules text states the second strategy's size and the one-crypto-order rule (the owner, Oct 31, 2026: the page said 5 contracts after the owner ordered 10, and kept a window limit no live market was under).
  const slot = require('../functions/kalshiSlotLib.js');
  const strat = (slot.SLOT_STRATEGIES || []).find((x) => x.id === 'OICORE');
  assert.ok(strat, 'OICORE is registered');
  const span = text((menu.match(/<span id="kalRulesSlot">[\s\S]*?<\/span>/) || [''])[0]);
  assert.ok(new RegExp('\\b' + strat.contractsPerOrder + ' contracts').test(span), 'the page says OICORE sends ' + strat.contractsPerOrder + ' contracts, like its registry entry');
  const live1 = live.L1_SERIES.filter((s) => !live.PAUSED_SERIES.includes(s));
  if (!live1.some((s) => live.CAPPED_SERIES.includes(s))) assert.ok(!/At most one crypto order per 15 minute window/.test(text(menu)), 'no live market is under the one-crypto-order rule, so the page must not state it');
};

gates.SF7 = () => {
  // Phone alerts are closes, stops and issues; a buy never alerts (the owner, Oct 26, 2026). The page's own confirmation must not promise entries (the owner's Oct 30 screenshot still said "entries, sells").
  const m = /kalshiPushSay\('Phone alerts are on for this device: ([^']+)'\)/.exec(html);
  assert.ok(m, 'the confirmation line is found');
  assert.ok(!/entr/i.test(m[1]) && /closes/.test(m[1]), 'the confirmation says closes, not entries');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
