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
  assert.ok(live.PAUSED_SERIES.includes('KXDOGE15M') && live.FIXED_CONTRACTS.KXDOGE15M === 5, 'Dogecoin is paused in code (its fixed 5 waits for a reviewed resume)');
  assert.ok(/Gold grows with the account/.test(t) && /except gold, whose size scales with the account/.test(t) && !/Dogecoin[^.]*(contracts|grow)/.test(t), 'the page says gold scales and does not give Dogecoin a size while it is paused');
  assert.ok(!/Ethereum 1\b/.test(t) && live.PAUSED_SERIES.includes('KXETH15M'), 'Ethereum is paused and no longer listed with a size');
  assert.ok(new RegExp('at most a quarter of the base size').test(t) && live.ADDON_MAX_FRACTION === 0.25, 'the add-on cap is a quarter of the base');
  assert.deepStrictEqual(live.QUIET_HOURS_CT, {}, 'no quiet hours are set in code (lifted Oct 30, 2026), so the page must not promise a pause');
  assert.ok(!/place no new orders from 8 PM/.test(t) && /around the clock/.test(t), 'the page says gold and Dogecoin trade around the clock');
};
gates.SF3 = () => {
  // The one deliberate exception: the sentence about the second strategy, which trades Bitcoin through the slot (not through L1, where Bitcoin stays paused). It must name only the registered strategy's market.
  const slotSpan = (menu.match(/<span id="kalRulesSlot">[\s\S]*?<\/span>/) || [''])[0];
  assert.ok(/Bitcoin only/.test(slotSpan) && !/Ethereum|gold|Dogecoin|XRP|AUD|CAD|natural gas/i.test(slotSpan), 'the slot sentence names Bitcoin and nothing else');
  const flowSpan = (menu.match(/<span id="kalRulesSlotFlow">[\s\S]*?<\/span>/) || [''])[0];
  assert.ok(!flowSpan || (/Bitcoin only/.test(flowSpan) && !/Ethereum|gold|Dogecoin|XRP|AUD|CAD|natural gas/i.test(flowSpan)), 'the FLOW1 sentence names Bitcoin and nothing else (Nov 4, 2026)');
  const rest = text(menu.replace(/<span id="kalRulesPaused">[\s\S]*?<\/span>/, '').replace(/<span id="kalRulesSlot">[\s\S]*?<\/span>/, '').replace(/<span id="kalRulesSlotFlow">[\s\S]*?<\/span>/, '').replace(/<span id="kalRulesSlotXrp">[\s\S]*?<\/span>/, ''));
  const xrpSpan = (menu.match(/<span id="kalRulesSlotXrp">[\s\S]*?<\/span>/) || [''])[0];
  assert.ok(/XRPYES10/.test(xrpSpan) && /trades only XRP/.test(xrpSpan) && !/Ethereum|gold|Dogecoin|Bitcoin|AUD|CAD|natural gas/i.test(xrpSpan), 'the XRPYES10 sentence names XRP and nothing else (Nov 10, 2026)');
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(rest), 'the Account card and its rules never name ' + n + ' as anything but paused'));
  const open = text((html.match(/id="kalL1Confirm"[\s\S]*?<\/span>/) || [''])[0]);
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(open), 'the Start confirmation does not mention paused ' + n));
};
gates.SF4 = () => {
  // The next look names the markets each strategy looks at (the Bot status card covers every strategy, the owner, Oct 31, 2026): the Closing buy names the live L1 markets, the open interest jump names Bitcoin, and no paused market is named.
  const looks = /var KAL_LOOKS = \[[\s\S]*?\n  \];\n/.exec(html);
  assert.ok(looks, 'the next look table is found');
  const l1 = /name: 'Closing buy', what: function\(goldClosed\)\{ return ([^;]+); \}/.exec(looks[0]);
  assert.ok(l1, 'the Closing buy look is found');
  liveNames.filter((n) => n !== 'Bitcoin').forEach((n) => assert.ok(new RegExp(n, 'i').test(l1[1]), 'the Closing buy look names ' + n));
  pausedNames.forEach((n) => assert.ok(!new RegExp(n.replace('/', '\\/'), 'i').test(looks[0].replace(/Bitcoin/g, '')) || n === 'Bitcoin', 'the next look does not name paused ' + n));
  assert.ok(/name: 'Open interest jump', what: function\(\)\{ return 'Bitcoin,/.test(looks[0]), 'the open interest jump names Bitcoin (the second strategy trades it through the slot)');
  assert.ok(!/10 minute look/.test(looks[0]) || live.EARLY_PROBE_SERIES.some((s) => !live.PAUSED_SERIES.includes(s)), 'no 10 minute look unless a market with one can trade');
};
gates.SF9 = () => {
  // Nov 4, 2026: the Bot status card's copy of EVENT830's release calendar must equal the bot's (SLOT_CALENDARS.EVENT830), so the countdown never names a window the bot will not trade, or misses one it will.
  const slot = require('../functions/kalshiSlotLib.js');
  const looks = /var KAL_LOOKS = \[[\s\S]*?\n  \];\n/.exec(html)[0];
  const closes = [...(/closes: \[([^\]]+)\]/.exec(looks) || assert.fail('the release look has its dates'))[1].matchAll(/'([^']+)'/g)].map((m) => m[1]);
  assert.deepStrictEqual(closes, slot.SLOT_CALENDARS.EVENT830.map((r) => r.closeUtc), 'the page lists exactly the release windows in the bot\'s code');
  const kinds = [...(/kinds: \[([^\]]+)\]/.exec(looks) || assert.fail('the release look has its kinds'))[1].matchAll(/'([^']+)'/g)];
  assert.strictEqual(kinds.length, closes.length, 'one release name per date');
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
  // The Rules text names the cheap-side floor, which is the bot's own skip line (SLOT_SKIP_BELOW, Nov 8, 2026): it said 5c for a day after the 8c skip went live.
  const skipBelow = slot.SLOT_SKIP_BELOW && slot.SLOT_SKIP_BELOW.OICORE;
  if (skipBelow) assert.ok(new RegExp(Math.round(skipBelow * 100) + 'c to ' + Math.round(strat.entry.priceMax * 100) + 'c').test(span), 'the Rules text names the ' + Math.round(skipBelow * 100) + 'c floor of OICORE\'s skip, not the registry band edge');
  // The Start box confirms real money, so it must name the ladder's start and its top step (SLOT_LADDERS), not a fixed size.
  const steps = (slot.SLOT_LADDERS && slot.SLOT_LADDERS.OICORE && slot.SLOT_LADDERS.OICORE.steps) || [strat.contractsPerOrder];
  const confirm = text((html.match(/<span id="kalL1Confirm"[\s\S]*?<\/span><\/span>/) || [''])[0]);
  assert.ok(new RegExp('OICORE \\(' + steps[0] + ' contracts to start, up to ' + steps[steps.length - 1] + ' ').test(confirm), 'the Start box names OICORE start ' + steps[0] + ' and top step ' + steps[steps.length - 1]);
  const live1 = live.L1_SERIES.filter((s) => !live.PAUSED_SERIES.includes(s));
  if (!live1.some((s) => live.CAPPED_SERIES.includes(s))) assert.ok(!/At most one crypto order per 15 minute window/.test(text(menu)), 'no live market is under the one-crypto-order rule, so the page must not state it');
};

gates.SF7 = () => {
  // Phone alerts are closes, stops and issues; a buy never alerts (the owner, Oct 26, 2026). The page's own confirmation must not promise entries (the owner's Oct 30 screenshot still said "entries, sells").
  const m = /kalshiPushSay\('Phone alerts are on for this device: ([^']+)'\)/.exec(html);
  assert.ok(m, 'the confirmation line is found');
  assert.ok(!/entr/i.test(m[1]) && /closes/.test(m[1]), 'the confirmation says closes, not entries');
};

gates.SF8 = () => {
  // Nov 3, 2026: the Settings changelog had Nov 1 to Nov 3 entries under an "Oct 30" heading. The top heading must be the newest date among CLAUDE.md's dated sections, so a change noted there cannot sit under an old day on the site.
  const notes = fs.readFileSync(path.join(__dirname, '..', 'CLAUDE.md'), 'utf8');
  const MON = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6, Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };
  const dates = [...notes.matchAll(/^## .*\((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2}), 2026/gm)].map((m) => MON[m[1]] * 100 + Number(m[2]));
  assert.ok(dates.length > 5, 'dated sections found in CLAUDE.md');
  const newest = Math.max(...dates);
  const top = /<div class="changelog-day">(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})<\/div>/.exec(html);
  assert.ok(top, 'the changelog has day headings');
  assert.strictEqual(MON[top[1]] * 100 + Number(top[2]), newest, 'the top changelog heading (' + top[0] + ') is the newest dated section in CLAUDE.md');
  // headings run newest first
  const heads = [...html.matchAll(/<div class="changelog-day">(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{1,2})<\/div>/g)].map((m) => MON[m[1]] * 100 + Number(m[2]));
  for (let i = 1; i < heads.length; i++) assert.ok(heads[i] <= heads[i - 1], 'changelog days run newest first');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
