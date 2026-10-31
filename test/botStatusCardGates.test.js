'use strict';
// SC1 to SC4: the redone Bot status card (the owner, Oct 31, 2026: template C with the health line, "too much to read", "avoid collapsables").
// Consequence: the card is two tiles (next look, health line) and short rows, never a fold; the ids the one second tick and the ECG draw into still exist; gold is shown closed over the weekend and open on a weekday; "Needs a look" shows only when something is wrong.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const fn = (name) => { const m = new RegExp('  function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const render = (over) => {
  over = over || {};
  const els = {}; let sHtml = '';
  const mk = (id) => (els[id] = els[id] || { id, textContent: '', innerHTML: '', insertAdjacentHTML(_w, h) { this.innerHTML += h; }, classList: { add() {}, remove() {} } });
  const status = mk('kalStatusBody'); mk('kalRiskBody');
  Object.defineProperty(status, 'innerHTML', { get: () => sHtml, set: (v) => { sHtml = v; }, configurable: true });
  status.insertAdjacentHTML = (_w, h) => { sHtml += h; };
  const document = { getElementById: (id) => (['kalStatusBody', 'kalRiskBody'].includes(id) ? els[id] : (sHtml.includes('id="' + id + '"') || id === 'kalEcg' ? mk(id) : null)) };
  const ctx = {
    document, escapeHtml: (x) => String(x), Date: Object.assign(function (...a) { return new Date(...a); }, { now: () => over.now }), Intl, Number, Math, Array, Object, String,
    kalshiLiveCtl: { session: { active: true, lastTickAt: over.now - 20000, lastNote: '' } }, kalshiBotState: { control: {} },
    kalshiHeartbeat: () => ({ state: 'ok', ageSec: 20 }), kalshiSkipNote: () => '', kalshiBeats: [], kalshiBeatNote() {}, kalshiAgeText: (s) => s + 's',
    kalshiOrdersLoaded: true, kalshiAllOrders: () => [], kalshiTodayWork: () => ({ sent: 3, filled: 2, noFill: 1, problem: over.problem || 0, lastTs: over.now - 120000 }),
    kalshiHeartbeatSvg: () => '<svg></svg>', kalshiReads: [], kalshiOrderTimes: () => [], kalshiLiveAcct: null, kalshiLiveOrders: [], kalshiResolveOrders: () => [], kalshiGroupFills() { return []; },
    kalshiSilentMarkets: () => over.silent || [], kalshiRiskMeter: () => ({ fraction: 0.1 }), kalshiStatusTick() {}, kalshiMoney: (x) => '$' + x,
  };
  const src = fn('kalshiCtWeekMinute') + fn('kalshiMarketsText') + fn('renderKalshiStatus') + '; return renderKalshiStatus;';
  const f = new Function(...Object.keys(ctx), src)(...Object.values(ctx));
  f();
  return sHtml;
};
const SAT = Date.parse('2026-10-31T01:30:00Z'), TUE = Date.parse('2026-10-27T18:00:00Z');   // Friday 8:30 PM Central, and Tuesday 1 PM Central
gates.SC1 = () => {
  const h = render({ now: TUE });
  assert.ok(!/<details|<summary|collaps/i.test(h), 'no fold of any kind on the card');
  assert.ok(/Next look/.test(h) && /id="kalNextIn"/.test(h) && /id="kalNextWhat"/.test(h), 'the next look tile keeps the ids the one second tick writes to');
  assert.ok(/Health/.test(h) && /id="kalEcg"/.test(h) && /id="kalHbText"/.test(h) && /id="kalHb"/.test(h), 'the health tile keeps the ECG and the text the tick updates');
  assert.ok(/Last order/.test(h) && /Orders today/.test(h) && /Markets/.test(h), 'the three short rows');
};
gates.SC2 = () => {
  assert.ok(/Gold and Dogecoin open/.test(render({ now: TUE })), 'gold and Dogecoin are shown open on a weekday');
  const closed = render({ now: SAT });
  assert.ok(/Gold closed, back Sun 6 PM/.test(closed) && !/Gold and Dogecoin open/.test(closed), 'gold is shown closed from Friday 5 PM Central until Sunday 6 PM');
};
gates.SC3 = () => {
  const ok = render({ now: TUE });
  assert.ok(!/kal-warn|Needs a look/.test(ok), 'a healthy day shows no warning');
  const bad = render({ now: TUE, silent: ['Dogecoin has sent no order for 4 hours.'], problem: 1 });
  assert.ok(/kal-warn/.test(bad) && /Dogecoin has sent no order for 4 hours/.test(bad) && /Needs a look/.test(bad), 'a silent market and a lost order answer both show');
};
gates.SC4 = () => {
  assert.ok(!/kal-more|kalMoreBody/.test(html), 'the More numbers fold is gone from the page');
  assert.ok(/\.kal-st-tiles\{[^}]*grid-template-columns/.test(html) && /@media \(max-width:520px\)\{ \.kal-st-tiles\{ grid-template-columns:1fr; \} \}/.test(html), 'two tiles on a desktop rail, one column on a phone');
};
let failed = 0;
for (const [name, g] of Object.entries(gates)) { try { g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
