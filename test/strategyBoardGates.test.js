'use strict';
// SB1 to SB13: the Strategy pipeline card (Nov 9, 2026; on its own Strategies page since Nov 10, 2026, the owner: "an entirely new page"; the card is gone from the Bot page, the owner: a one glance, phone readable board of every strategy, profit factor first, always on the cash basis).
// Consequence: a profit factor shown on the board is the one the bot's own cash arithmetic gives; a kill line or a shadow rule that drifts from the bot's code fails here; an unreadable shadow log never breaks the page; and no dollar figure escapes Privacy view.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const live = require('../functions/kalshiLiveLib.js');
const slot = require('../functions/kalshiSlotLib.js');
const shadow = require('../functions/kalshiShadowLib.js');
const gates = {};

// Lift a top level page function by matching braces from its "  function name(".
function fn(name) {
  const at = html.indexOf('  function ' + name + '(');
  assert.ok(at >= 0, name + ' is in the page');
  let i = html.indexOf('{', at), depth = 0, q = null;
  for (; i < html.length; i++) {
    const c = html[i];
    if (q) { if (c === '\\') i++; else if (c === q) q = null; continue; }
    if (c === "'" || c === '"') { q = c; continue; }
    if (c === '/' && html[i + 1] === '/') { i = html.indexOf('\n', i); continue; }
    if (c === '{') depth++;
    if (c === '}') { depth--; if (depth === 0) break; }
  }
  return html.slice(at, i + 1);
}
const varLine = (name) => { const m = new RegExp('  var ' + name + ' = .*\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const varBlock = (name) => { const m = new RegExp('  var ' + name + ' = [\\[{][\\s\\S]*?\\n  [\\] }]+;\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const names = ['kalshiBoardFillCost', 'kalshiBoardCash', 'kalshiBoardRows', 'kalshiBoardPf', 'kalshiBoardWindows', 'kalshiBoardPfText', 'kalshiBoardKill', 'kalshiBoardShadow', 'kalshiBoardDate', 'kalshiStratPfOf', 'kalshiStratPfAttr', 'kalshiStratSpark', 'kalshiStratGauge', 'kalshiStratLifecycle', 'kalshiStratBadge', 'kalshiStratRing', 'kalshiStratRingText', 'kalshiStratOneLine', 'kalshiStratTwinFirst', 'kalshiBoardHtml'];
const src = varLine('KAL_BOARD_TRIPWIRE') + varLine('KAL_BOARD_KILL') + varBlock('KAL_BOARD_LIVE') + varLine('KAL_BOARD_SHADOW_RULES') + varBlock('KAL_BOARD_SHADOW') + varBlock('KAL_BOARD_RETIRED') + varLine('KAL_BOARD_DAY') + varLine('KAL_BOARD_LADDER') + names.map(fn).join('\n');
const P = new Function('Intl', 'Math', 'Date', 'Number', 'Array', 'Object', 'String', 'isFinite', src + '; return { ' + names.join(', ') + ', KAL_BOARD_TRIPWIRE, KAL_BOARD_KILL, KAL_BOARD_LIVE, KAL_BOARD_SHADOW, KAL_BOARD_RETIRED };')(Intl, Math, Date, Number, Array, Object, String, isFinite);
const money = (x) => (x < 0 ? '-' : '') + '$' + Math.abs(x).toFixed(2);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => '&#' + c.charCodeAt(0) + ';');

const ord = (o) => Object.assign({ settled: true, fillCount: 5, count: 5, side: 'yes', result: 'yes', maxCost: 4.6, averageFillPrice: 0.9, averageFeePaid: 0.02, settledPnl: 0.4, ts: 1 }, o);
const FIX = [
  ord({}), ord({ result: 'no' }), ord({ side: 'no', result: 'no', averageFillPrice: 0.12, averageFeePaid: 0.01 }), ord({ side: 'no', result: 'yes', averageFillPrice: 0.12 }),
  ord({ averageFillPrice: null }), ord({ averageFeePaid: '' }), ord({ averageFillPrice: 1.5 }), ord({ averageFillPrice: 0.99, averageFeePaid: 0.5 }), ord({ fillCount: 2 }), ord({ fillCount: 9, count: 5 }),
  ord({ count: 0, fillCount: 1, maxCost: 0.95 }), ord({ side: 'maybe' }), ord({ maxCost: undefined, averageFillPrice: undefined }),
];

gates.SB1 = () => {
  // the cash result of a settled, held order is the bot's own fillCost arithmetic: the page's number can never differ from what the bot books
  for (const o of FIX) {
    const want = Number(o.count) > 0 ? Number(o.count) : 1, got = Math.min(Number(o.fillCount), want);
    const a = P.kalshiBoardFillCost(o, got, want), b = live.fillCost(o, got, want);
    assert.ok((Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-12, 'fillCost port matches on ' + JSON.stringify(o));
    const cash = P.kalshiBoardCash(o);
    if (Number.isFinite(b)) assert.ok(Math.abs(cash - ((o.result === o.side ? got : 0) - b)) < 1e-4, 'cash result on ' + JSON.stringify(o));
  }
  const slotFc = slot.fillCost;
  for (const o of FIX) { const a = P.kalshiBoardFillCost(o, 5, 5), b = slotFc(o, 5, 5); assert.ok((Number.isNaN(a) && Number.isNaN(b)) || Math.abs(a - b) < 1e-12, 'slot copy agrees too'); }
};
gates.SB2 = () => {
  // an order sold early keeps its stored result; open, unfilled and hand-closed orders count for nothing
  assert.strictEqual(P.kalshiBoardCash(ord({ result: 'exit', settledPnl: -2.5 })), -2.5);
  assert.strictEqual(P.kalshiBoardCash(ord({ result: 'yes', exitCount: 2, settledPnl: 0.77 })), 0.77);
  assert.strictEqual(P.kalshiBoardCash(ord({ result: 'exit', settledPnl: null })), null);
  assert.strictEqual(P.kalshiBoardCash(ord({ settled: false })), null);
  assert.strictEqual(P.kalshiBoardCash(ord({ fillCount: 0 })), null);
  assert.strictEqual(P.kalshiBoardCash(ord({ result: 'hand' })), null);
  assert.strictEqual(P.kalshiBoardCash(ord({ result: undefined })), null);
};
gates.SB3 = () => {
  // profit factor windows: wins over losses on the cash basis, 7 and 30 days and since start; no losses is said, not shown as infinity
  const now = Date.UTC(2026, 10, 9, 18, 0), D = 86400000;
  const mk = (daysAgo, p) => ord({ ts: now - daysAgo * D, result: p > 0 ? 'yes' : 'exit', settledPnl: p, averageFillPrice: null, maxCost: 1 });   // averageFillPrice null with result yes would use maxCost; use exits for exact figures
  const orders = [{ ...mk(1, 2), result: 'exit' }, { ...mk(2, -1), result: 'exit' }, { ...mk(10, 3), result: 'exit' }, { ...mk(40, -3), result: 'exit' }];
  const w = P.kalshiBoardWindows(orders, now);
  assert.strictEqual(w.d7.pf, 2); assert.strictEqual(w.d7.n, 2); assert.strictEqual(w.d30.pf, 5 / 1); assert.strictEqual(w.d30.net, 4); assert.strictEqual(w.all.n, 4); assert.strictEqual(w.all.pf, 1.25);
  assert.strictEqual(P.kalshiBoardPfText(P.kalshiBoardWindows([orders[0]], now).d7), 'no losses');
  assert.strictEqual(P.kalshiBoardPfText(P.kalshiBoardWindows([], now).d7), 'n/a');
  assert.strictEqual(P.kalshiBoardPfText(w.d30), '5.00');
};
const exits = (pnls, t0 = Date.UTC(2026, 10, 9, 17, 0)) => pnls.map((p, i) => ord({ ts: t0 + i * 900000, result: 'exit', settledPnl: p }));
gates.SB4 = () => {
  // L1 gold tripwire: counts only trades from Nov 9 10:22 AM Central (16:22 UTC), and the rolling 60 only once 60 trades exist
  assert.strictEqual(P.KAL_BOARD_TRIPWIRE.from, Date.parse('2026-11-09T16:22:00Z'));
  const before = exits([1, 1, 1], Date.parse('2026-11-09T15:00:00Z')), after = exits([2, -1, 1], Date.parse('2026-11-09T16:30:00Z'));
  const k = P.kalshiBoardKill('L1', before.concat(after), 0, money);
  assert.strictEqual(k.count, 3, 'only trades from the tripwire time count'); assert.strictEqual(k.pf, 3); assert.strictEqual(k.rolling, null);
  assert.ok(/^Tripwire 3 of 100 trades, PF 3\.00 \(cut under 1\.0\) · rolling 60 PF n\/a \(alert under 0\.7\)$/.test(k.lines[0]), k.lines[0]); assert.strictEqual(k.lines.length, 1, 'one short status line');
  const many = exits(Array.from({ length: 60 }, (_, i) => (i % 3 === 2 ? -1 : 1)), Date.parse('2026-11-09T17:00:00Z'));
  assert.strictEqual(P.kalshiBoardKill('L1', many, 0, money).rolling, 2, 'rolling 60 PF: 40 wins over 20 losses');
};
gates.SB5 = () => {
  // OICORE: the current loss streak and net since its review date, in the bot's own words; every dollar figure goes through money
  const from = Date.UTC(2026, 9, 31);
  const o = exits([1, -1, -1], from).concat(exits([5], Date.UTC(2026, 9, 1)));
  let seen = 0; const m = (x) => { seen++; return money(x); };
  const k = P.kalshiBoardKill('OICORE', o, 0, m);
  assert.strictEqual(k.streak, 2); assert.strictEqual(k.fills, 3, 'orders before the review date do not count'); assert.strictEqual(k.drawdown, 2, 'peak +1 down to -1 is a drawdown of 2'); assert.strictEqual(k.room, 48);
  assert.ok(/^Drawdown room \$48\.00 of \$50\.00 · streak 2 of 24$/.test(k.lines[0]), k.lines[0]); assert.ok(seen >= 2, 'money used for the room and the stop'); assert.strictEqual(k.lines.length, 1);
  const e = P.kalshiBoardKill('EVENT830', exits([-0.5, -0.5, -0.5, -0.5, -0.5]), 0, money);
  assert.ok(/^5 trades, 0 won · losing streak 5 of 20$/.test(e.lines[0]), e.lines[0]); assert.strictEqual(e.wins, 0);
};
gates.SB6 = () => {
  // the copied kill constants equal the bot's code: a change to the bot's kill rule that the board does not follow fails here
  const reg = Object.fromEntries(slot.SLOT_STRATEGIES.map((s) => [s.id, s]));
  assert.strictEqual(P.KAL_BOARD_KILL.OICORE.streak, reg.OICORE.killRules.maxConsecutiveLosses);
  assert.strictEqual(P.KAL_BOARD_KILL.OICORE.afterFills, reg.OICORE.killRules.minNet.afterFills);
  assert.strictEqual(P.KAL_BOARD_KILL.OICORE.net, reg.OICORE.killRules.minNet.net);
  assert.strictEqual(P.KAL_BOARD_KILL.OICORE.from, Date.parse(reg.OICORE.reviewedAt + 'T00:00:00Z'));
  assert.deepStrictEqual(P.KAL_BOARD_LIVE.map((s) => s.id), ['L1'].concat(slot.SLOT_STRATEGIES.map((s) => s.id)), 'the live strategies are L1 and every registered slot strategy');
  assert.strictEqual(P.KAL_BOARD_KILL.EVENT830.streak, reg.EVENT830.killRules.maxConsecutiveLosses, 'the EVENT830 streak kill is the bot\'s');
  const L = slot.SLOT_LADDERS.OICORE; assert.strictEqual(P.KAL_BOARD_KILL.OICORE.ddStop, L.stopPerContract * L.steps[0], 'the drawdown stop is the bot\'s at the bottom step (5 x 10 contracts)');
};
const SH = (rule, atMs, o) => Object.assign({ rule, atMs, closeMs: atMs + 360000, side: 'yes', price: 0.9, size: 1, wouldFill: true, settled: true, pnl: 0.07 }, o);
const shFixture = (now) => {
  const D = 86400000, rows = [];
  for (let i = 0; i < 160; i++) rows.push(SH('ETHL1', now - (20 - i * 0.125) * D, { pnl: i % 9 === 0 ? -0.9 : 0.08, wouldFill: i % 5 !== 0 }));
  for (let i = 0; i < 30; i++) rows.push(SH('GOLDALL', now - (5 - i * 0.1) * D, { pnl: i % 4 === 0 ? -0.9 : 0.06, settled: i < 25 }));
  for (let i = 0; i < 4; i++) rows.push(SH('BTCHI6', now - (1 - i * 0.1) * D));
  for (let i = 0; i < 60; i++) rows.push(SH('XRPYES10', now - (31 - i * 0.2) * D, { pnl: -0.5 }));
  return rows;
};
gates.SB7 = () => {
  // the page's shadow scoring is the bot's shadowReport: the same fixture through both gives the same numbers, so the board never reads a different PF or status than the nightly report
  const now = Date.UTC(2026, 10, 20, 12, 0), rows = shFixture(now), ids = shadow.SHADOW_RULES;
  const a = shadow.shadowReport(ids, rows, now), b = P.kalshiBoardShadow(ids.map((r) => ({ id: r.id })), rows, now);
  assert.strictEqual(a.length, b.length);
  a.forEach((x, i) => { for (const k of Object.keys(x)) assert.deepStrictEqual(b[i][k], x[k], x.rule + '.' + k); });
  assert.ok(a.some((x) => x.status.startsWith('kill')) && a.some((x) => x.status === 'collecting'), 'the fixture exercises more than one status');
};
gates.SB8 = () => {
  // the ON DECK ids are the bot's registry, in order: a rule added or removed in the bot without the board fails here
  assert.deepStrictEqual(P.KAL_BOARD_SHADOW.map((r) => r.id), shadow.SHADOW_RULES.map((r) => r.id));
  P.KAL_BOARD_SHADOW.forEach((r) => assert.ok(r.rule && r.rule.length < 80, 'one line of rule text for ' + r.id));
};
gates.SB9 = () => {
  // earliest next stage: nothing is guessed before 10 signals; after that it is the later of 14 days and 150 signals at the rate so far
  const now = Date.UTC(2026, 10, 20, 12, 0), D = 86400000;
  const few = P.kalshiBoardShadow([{ id: 'BTCHI6' }], shFixture(now), now)[0];
  assert.strictEqual(few.etaMs, null, '4 signals: not enough rows yet');
  const one = P.kalshiBoardShadow([{ id: 'GOLDALL' }], shFixture(now), now)[0];
  assert.ok(one.etaMs >= one.firstAtMs + 14 * D - 1 && one.etaMs > now, 'never before 14 days from the first signal, never in the past for an unfinished rule');
  const done = P.kalshiBoardShadow([{ id: 'ETHL1' }], shFixture(now), now)[0];
  assert.ok(done.fillable >= 100 && done.etaMs >= now - 1);
};
gates.SB10 = () => {
  // Nov 10, 2026: the card became a page. It is NOT on the Bot page any more (no card, no layout entry, no render call), and a saved layout that still lists it is cleaned by complete().
  assert.ok(!/data-card="board"/.test(html) && !/id="kalBoard"/.test(html) && !/renderKalshiBoard/.test(html), 'the Bot page has no Strategy pipeline card any more');
  assert.ok(!/\['board', 'Strategy pipeline'\]/.test(html) && /var CARDS = \['account', 'status', 'pnl', 'positions', 'trades'\];/.test(html), 'and the Bot layout lists five cards');
  assert.ok(/id="page-strategies"/.test(html) && /id="stratBody"/.test(html), 'the page and its container exist');
  const comp = new Function(fn('complete').replace('function complete', 'return function complete'))();
  assert.deepStrictEqual(comp(['account', 'board', 'status', 'pnl', 'positions', 'trades'], ['account', 'status', 'pnl', 'positions', 'trades']), ['account', 'status', 'pnl', 'positions', 'trades'], 'a layout saved while the card existed drops it');
  assert.ok(/renderStrategiesPage\(\);/.test(fn('showPage')) && /renderStrategiesPage\(\); \}/.test(fn('kalshiFeedRender')), 'drawn when the page is shown and on each feed change, no timer of its own');
};
gates.SB11 = () => {
  // every dollar goes through money, every value is escaped, and an unreadable shadow log shows the fallback instead of breaking the page
  const now = Date.UTC(2026, 10, 9, 18, 0);
  const lv = P.KAL_BOARD_LIVE.map((s) => ({ id: s.id, name: s.name, rule: s.rule, w: P.kalshiBoardWindows(exits([1, -1, 2]), now), kill: P.kalshiBoardKill(s.id, exits([1, -1, 2]), now, (x) => 'MASK') }));
  const model = (state) => ({ live: lv, deck: { state, rows: P.KAL_BOARD_SHADOW.map((r) => ({ id: r.id, rule: r.rule, rep: P.kalshiBoardShadow([r], [], now)[0] })) }, retired: P.KAL_BOARD_RETIRED });
  const masked = P.kalshiBoardHtml(model('unreadable'), esc, (x) => (x < 0 ? '-' : '') + '****');
  assert.ok(!/\$\d/.test(masked), 'no dollar figure appears when money masks them');
  assert.strictEqual((masked.match(/Shadow log not readable yet/g) || []).length, 4, 'every ON DECK rule says the log is not readable');
  assert.ok(/Comes back when: a 14 day cool off/.test(masked) && /class="sp-bar"/.test(P.kalshiBoardHtml(model('ok'), esc, money)) && !/class="sp-bar"/.test(masked), 'retired rows say when they come back; ON DECK rows with a log carry a progress bar');
  assert.ok(/XRP/.test(masked) && /Natural gas/.test(masked), 'the other groups still draw');
  assert.ok(/Reading the shadow log/.test(P.kalshiBoardHtml(model('loading'), esc, money)));
  const evil = P.kalshiBoardHtml({ live: [{ id: 'X', name: '<img src=x onerror=1>', rule: '"><script>', w: P.kalshiBoardWindows([], now), kill: { lines: ['<b>'] } }], deck: { state: 'unreadable', rows: [] }, retired: { asOf: '<i>', back: '<u>', rows: [{ name: 'n', pf: 1, n: 1 }] } }, esc, money);
  assert.ok(!/<img|<script/.test(evil) && evil.includes('&#60;b&#62;') && evil.includes('&#60;i&#62;') && evil.includes('&#60;u&#62;'), 'every value is escaped');
  const body = fn('renderStrategiesPage');
  assert.ok(/kalshiMoney/.test(body) && !/toFixed\(2\)[^;]*\$|'\$'/.test(fn('kalshiBoardHtml') + fn('kalshiBoardKill')), 'no dollar sign typed into the board text');
  assert.ok(/kalshiShadowCache\.error \? 'unreadable'/.test(body), 'a failed read is a state, not an exception');
};
gates.SB13 = () => {
  // the owner's standing rule (Nov 10, 2026): every strategy shows IMPLEMENT, KILL and RETURN; a strategy without a written one says so instead of hiding the gap
  assert.ok(P.KAL_BOARD_LIVE.every((s) => Array.isArray(s.rules) && s.rules.length === 3), 'every live strategy carries three rules');
  assert.ok(/Never automatic/.test(P.KAL_BOARD_LIVE.find((s) => s.id === 'OICORE').rules[2]), 'OICORE return is the owner choice A');
  assert.ok(/Not written yet/.test(P.KAL_BOARD_LIVE.find((s) => s.id === 'EVENT830').rules[2]), 'the missing EVENT830 return rule is shown as a gap');
  const now = Date.UTC(2026, 10, 10, 18, 0);
  const lv = P.KAL_BOARD_LIVE.map((s) => ({ id: s.id, name: s.name, rule: s.rule, rules: s.rules, w: P.kalshiBoardWindows([], now), kill: { lines: ['x'] } }));
  const h = P.kalshiBoardHtml({ live: lv, deck: { state: 'unreadable', rows: P.KAL_BOARD_SHADOW.map((r) => ({ id: r.id, rule: r.rule })) }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.strictEqual((h.match(/class="kal-bd-rules"/g) || []).length, 4, 'four live strategies have Implement, Kill and Return');
  const ok = P.kalshiBoardHtml({ live: [], deck: { state: 'ok', rows: P.KAL_BOARD_SHADOW.map((r) => ({ id: r.id, rule: r.rule, rep: P.kalshiBoardShadow([r], [], now)[0] })) }, retired: P.KAL_BOARD_RETIRED }, esc, money);
  assert.strictEqual((ok.match(/class="kal-bd-rules"/g) || []).length, 5, 'every shadow rule has a Rules line');
  assert.ok(/<b>Implement<\/b>/.test(ok) && /<b>Kill<\/b>/.test(ok) && /<b>Return<\/b>/.test(ok));
};
gates.SB12 = () => {
  // no timer, no write, no storage: the board only reads, and the shadow read is cached for ten minutes without a retry loop
  const code = [fn('renderStrategiesPage'), fn('kalshiShadowEnsure'), fn('kalshiBoardHtml'), fn('kalshiBoardShadow')].join('\n');
  assert.ok(!/setInterval|setTimeout|localStorage|setDoc|updateDoc|addDoc|syncUserSetting/.test(code), 'no timer, storage or write in the board code');
  assert.ok(/KAL_SHADOW_TTL = 600000/.test(html) && /kalshiShadowCache\.at = Date\.now\(\)/.test(fn('kalshiShadowEnsure')), 'the attempt time is stamped before the read, so a refusal is not retried until the cache expires');
  const mod = html.slice(html.indexOf('readKalshiShadowRows'), html.indexOf('readKalshiShadowRows') + 1500);
  assert.ok(/collection\(db, 'kalshiShadowRows'\)/.test(mod) && !/setDoc|updateDoc|addDoc/.test(mod), 'a plain read of the shadow log');
  assert.ok(/match \/kalshiShadowRows\/\{id\} \{\s*allow read: if isAdmin\(\);\s*allow write: if false;/.test(fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8')), 'admin read, no client write');
  assert.ok(/\.sp-board\{[^}]*display:grid; grid-template-columns:minmax\(0,1fr\)/.test(html) && /\.sp-cards\{ display:grid; grid-template-columns:minmax\(0,1fr\)/.test(html) && /\.sp-top\{ display:flex; align-items:center/.test(html), 'the lanes are a shrinking grid: one column on a phone, so a phone never scrolls sideways');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); } }
if (failed) process.exit(1);
