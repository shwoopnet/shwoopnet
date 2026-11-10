'use strict';
// The notification center (Oct 25, 2026, the owner: a bell with a red bubble for unread, a Mark all as read, and a loud banner for the worst cases). Consequences: the bubble counts only what matters, the banner is for the bot stopping or an order
// needing a check and stays for as long as that is true, dollars are masked in Privacy view, and none of it can write or change anything.
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
const f = new Function("var KAL_TZ = 'America/Chicago';\n" + ['kalshiMarketName', 'kalshiOrderPnl', 'kalshiCloseFromTicker', 'kalshiNotifFeed', 'kalshiNotifUnread', 'kalshiCriticalNow'].map(fnSource).join('\n') +
  '\nreturn { kalshiCloseFromTicker, kalshiNotifFeed, kalshiNotifUnread, kalshiCriticalNow };')();
const at = (iso) => Date.parse(iso);
const NOW = at('2026-10-24T20:00:00Z');
const money = (v) => '$' + v.toFixed(2);
const mask = () => '****';

gates.N1 = () => {
  const events = [
    { ts: at('2026-10-24T19:00:00Z'), kind: 'order', detail: 'yes 11 at 93.0c on KXGOLD15M-26OCT241500-00: filled' },
    { ts: at('2026-10-24T18:50:00Z'), kind: 'order', detail: 'no 3 at 90.0c on KXXRP15M-26OCT241445-45: no fill' },
    { ts: at('2026-10-24T18:00:00Z'), kind: 'exit', detail: 'KXGOLD15M-26OCT241400-00: YES bid at 22c, sold' },
    { ts: at('2026-10-24T17:00:00Z'), kind: 'exit', detail: 'KXBTC15M-26OCT241300-00: Kalshi refused the exit sell: HTTP 400' },
    { ts: at('2026-10-24T16:00:00Z'), kind: 'session ended', detail: 'the bot is down $11.00 settled' },
    { ts: at('2026-10-24T15:00:00Z'), kind: 'session ended', detail: 'switched off by you' },
    { ts: at('2026-10-24T14:00:00Z'), kind: 'probe dropped', detail: 'KXUSDCAD15M is dropped' },
    { ts: at('2026-10-10T14:00:00Z'), kind: 'order', detail: 'yes 1 at 90.0c on KXGOLD15M-26OCT101000-00: filled' },
  ];
  const orders = [
    { strategy: 'L1', ts: at('2026-10-24T18:40:00Z'), ticker: 'KXGOLD15M-26OCT241500-00', series: 'KXGOLD15M', side: 'yes', fillCount: '4.00', settled: true, result: 'yes', settledPnl: 0.25, clientOrderId: 'a' },
    { strategy: 'L1', ts: at('2026-10-24T17:40:00Z'), ticker: 'KXGOLD15M-26OCT241330-30', series: 'KXGOLD15M', side: 'yes', fillCount: '4.00', settled: true, result: 'no', settledPnl: -3.8, clientOrderId: 'b' },
    { strategy: 'L1', ts: at('2026-10-24T13:00:00Z'), ticker: 'KXETH15M-26OCT240900-00', series: 'KXETH15M', side: 'no', fillCount: '1.00', status: 'unknown', error: 'HTTP 502', clientOrderId: 'c' },
  ];
  const feed = f.kalshiNotifFeed(events, orders, NOW, money);
  const titles = feed.map((x) => x.level + ': ' + x.title);
  assert.ok(feed.every((x, i) => i === 0 || feed[i - 1].ts >= x.ts), 'newest first');
  assert.ok(titles.some((t) => t === 'info: Bought Gold: 11 YES at 93.0c'), 'a filled buy is an info line: ' + titles.join(' | '));
  assert.ok(!titles.some((t) => /XRP/.test(t) && /Bought/.test(t)), 'a no fill is not a notification');
  assert.ok(titles.some((t) => t === 'warning: Sold Gold early'), 'an early sell is a warning');
  assert.ok(titles.some((t) => /^critical: Check the bot: an early sell had a problem/.test(t)), 'a refused exit is critical');
  assert.ok(titles.some((t) => t === 'critical: The bot stopped by itself'), 'the bot stopping by itself is critical');
  assert.ok(titles.some((t) => t === 'info: Bot stopped by you'), "the owner's own stop is only info");
  assert.ok(titles.some((t) => t === 'warning: A test market was dropped'), 'a dropped probe is a warning');
  assert.ok(titles.some((t) => t === 'info: Won Gold +$0.25') && titles.some((t) => t === 'warning: Lost Gold -$3.80'), 'a win is info, a loss is a warning');
  assert.ok(titles.some((t) => /^critical: Check the bot: Ethereum order needs a look/.test(t)), 'an order with an unknown answer is critical');
  assert.ok(!feed.some((x) => x.ts < NOW - 7 * 86400000), 'only the last 7 days');
  const win = feed.find((x) => /^Won Gold/.test(x.title));
  assert.strictEqual(win.ts, at('2026-10-24T19:00:00Z'), 'a settlement is stamped at the market close (15:00 Eastern is 19:00 UTC), not when the order was placed');
  const masked = f.kalshiNotifFeed(events, orders, NOW, mask).map((x) => x.title).join(' | ');
  assert.ok(/Lost Gold -\*\*\*\*/.test(masked) && !/\$\d/.test(masked), 'in Privacy view the dollars are masked and the sign stays');
  const dup = f.kalshiNotifFeed(events.concat(events), orders.concat(orders), NOW, money);
  assert.strictEqual(dup.length, feed.length, 'the same event twice is one notification');
};
gates.N2 = () => {
  const items = [{ ts: 100, level: 'info' }, { ts: 200, level: 'warning' }, { ts: 300, level: 'critical' }, { ts: 50, level: 'critical' }];
  assert.strictEqual(f.kalshiNotifUnread(items, 0), 3, 'the bubble counts unread warnings and critical items, never info');
  assert.strictEqual(f.kalshiNotifUnread(items, 250), 1, 'only what is newer than the last mark all as read');
  assert.strictEqual(f.kalshiNotifUnread(items, 300), 0, 'and zero once everything is read (the bubble hides)');
  assert.strictEqual(f.kalshiNotifUnread([], 0), 0);
};
gates.N3 = () => {
  assert.strictEqual(f.kalshiCloseFromTicker('KXGOLD15M-26OCT231200-00'), at('2026-10-23T16:00:00Z'), 'the ticker time is Eastern: 12:00 in October is 16:00 UTC');
  assert.strictEqual(f.kalshiCloseFromTicker('KXGOLD15M-26DEC011200-00'), at('2026-12-01T17:00:00Z'), 'and 17:00 UTC in December');
  assert.strictEqual(f.kalshiCloseFromTicker('KXGOLD15M-26NOV010100-00'), at('2026-11-01T05:00:00Z'), 'on the day daylight saving ends, 01:00 is still the first one (EDT)');
  assert.strictEqual(f.kalshiCloseFromTicker('nonsense'), null);
};
gates.N4 = () => {
  const stopped = { active: false, endedAt: NOW - 3600000, endedBecause: 'loss stop' };
  const a = f.kalshiCriticalNow(stopped, [], 'off', NOW, 'Stopped by the loss stop. It stays off until you press Start bot.');
  assert.ok(a && a.title === 'The bot is stopped' && /loss stop/.test(a.text), 'a bot that stopped itself is a banner, with the reason');
  assert.strictEqual(f.kalshiCriticalNow({ active: false, endedAt: NOW - 3600000, endedBecause: 'switched off by the owner' }, [], 'off', NOW, ''), null, 'a stop you did yourself is not an alarm');
  assert.strictEqual(f.kalshiCriticalNow({ active: true }, [], 'ok', NOW, ''), null, 'a healthy running bot: no banner');
  const bad = [{ strategy: 'L1', ts: NOW - 600000, ticker: 'KXETH15M-26OCT241600-00', series: 'KXETH15M', status: 'unknown', error: 'HTTP 502' }];
  const b = f.kalshiCriticalNow({ active: true }, bad, 'ok', NOW, '');
  assert.ok(b && b.title === 'An order needs checking' && /Ethereum/.test(b.text), 'an order with an unknown answer is a banner');
  assert.strictEqual(f.kalshiCriticalNow({ active: true }, [Object.assign({}, bad[0], { ts: NOW - 2 * 86400000 })], 'ok', NOW, ''), null, 'an old one no longer is');
  const c = f.kalshiCriticalNow({ active: true }, [], 'down', NOW, '');
  assert.ok(c && /not checked in/.test(c.title), 'no check for several minutes is a banner');
  assert.strictEqual(f.kalshiCriticalNow({ active: false }, [], 'off', NOW, ''), null, 'never started: not an alarm');
};
gates.N5 = () => {
  const page = html.slice(html.indexOf('<main class="page" id="page-kalshi"'), html.indexOf('<main class="page" id="page-settings"'));
  // Oct 25, 2026 (the owner: "notification bell needs to be up here to the left of brief", "not down by layout/privacy in bot"): the bell sits in the top navigation, first, left of Brief, and not in the Bot page header.
  const nav = html.slice(html.indexOf('<nav class="side-nav"'), html.indexOf('</nav>', html.indexOf('<nav class="side-nav"')));
  assert.ok(/id="kalNotifBtn"/.test(nav) && /id="kalNotifBadge"/.test(nav) && /id="kalNotifReadAll">Mark all as read</.test(nav), 'a bell with a bubble and a Mark all as read, in the navigation');
  assert.ok(nav.indexOf('id="kalNotif"') < nav.indexOf('data-page="brief"'), 'to the left of Brief');
  assert.ok(!/kalNotif/.test(page.replace(/id="kalNotifList"/g, '')), 'not in the Bot page header');
  assert.ok(/kalBell\.hidden = !currentUserIsAdmin/.test(html), 'only the admin sees it');
  assert.ok(/<div class="kal-alert" id="kalAlert" role="alert" hidden>/.test(page), 'the banner is an alert and hidden until needed');
  assert.ok(page.indexOf('id="kalAlert"') < page.indexOf('id="kalTabBot"'), 'across the top of the Bot page, above every card');
  assert.ok(/\.kal-notif-badge\{[^}]*background:var\(--loss\)/.test(html) && /\.kal-alert\{[^}]*background:var\(--loss\)/.test(html), 'red bubble, red banner');
  const code = html.slice(html.indexOf('  function kalshiCloseFromTicker'), html.indexOf("  var kalshiTradeFilter = 'bot';"));
  assert.ok(!/fetch\(|setDoc|updateDoc|addDoc|callable|Fn\(|api\./.test(code), 'it reads what the page holds and writes nothing to the account');
  assert.ok(/shwoopnet:notifRead/.test(code) && /localStorage/.test(code), 'what has been read is kept in this browser only');
  assert.ok(/renderKalshiNotifications\(\);\n    kalshiSoundCheck\(\);/.test(html), 'it redraws with every bot update, so Privacy view masks it too');
};
// The bell fills on every page (the owner, Oct 25, 2026: "constantly filling up, regardless of whether I have the bot panel open"): the listeners start for the admin from sign-in, not when the Bot page is shown.
gates.N6 = () => {
  const admin = html.slice(html.indexOf('function applyAdminUI'), html.indexOf('function applyAdminUI') + 900);
  assert.ok(/if\(currentUserIsAdmin\)\{ startKalshiFeed\(\); \} else \{ stopKalshiFeed\(\); \}/.test(admin), 'the feed starts with the admin account and stops on sign-out');
  assert.ok(/function kalshiOnShow\(\)\{ startKalshiBot\(\); startKalshiPoll\(\); \}/.test(html) && !/function stopKalshiBot\(\)\{[^}]*kalshiLiveUnsub/.test(html), 'leaving the Bot page no longer stops the listeners');
  assert.ok(/function kalshiFeedRender\(\)\{[\s\S]*?renderKalshiNotifications\(\)/.test(html), 'with the Bot page hidden an update still redraws the bell and the banner');
  assert.ok(!/Open the Bot page once/.test(html), 'no more asking the owner to open the Bot page');
};
// Clear (the owner, Oct 25, 2026): hides what is listed so far, in this browser only, and never the banner.
gates.N7 = () => {
  assert.ok(/id="kalNotifClear">Clear</.test(html), 'the panel has a Clear button beside Mark all as read');
  assert.ok(/shwoopnet:notifCleared/.test(html) && /\.filter\(function\(x\)\{ return x\.ts > clearedAt; \}\)/.test(html), 'lines up to the click are hidden, newer ones still show');
  const code = html.slice(html.indexOf('function kalshiNotifLoadCleared'), html.indexOf("var kalshiTradeFilter = 'bot';"));
  assert.ok(!/fetch\(|setDoc|updateDoc|addDoc|callable/.test(code), 'clearing writes nothing to the account');
  const render = html.slice(html.indexOf('function renderKalshiNotifications'), html.indexOf('function renderKalshiNotifications') + 2200);
  assert.ok(/bannerEl\.hidden = !crit/.test(render) && !/clearedAt[^;]*crit/.test(render), 'the red banner does not depend on Clear');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
