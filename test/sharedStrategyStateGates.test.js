'use strict';
// Nov 12, 2026, the owner: the Bot status "isnt updated to reflect all strategies, and it should communicate with the other pages because itll display irrelevant information as we rotate".
// Consequence: a killed strategy never appears as the next look and is never called silent; every armed strategy appears in the next look; an unreadable kill state claims nothing; a rotation (registry row) reaches every consumer with no code edit.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
function fnSource(name) {
  const start = html.indexOf('function ' + name + '(');
  assert.ok(start >= 0, name + ' exists');
  let i = html.indexOf('{', html.indexOf(')', start)), depth = 0;
  for (; i < html.length; i++) { if (html[i] === '{') depth++; else if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1); }
  throw new Error('unbalanced ' + name);
}
const looks = /  var KAL_LOOKS = \[[\s\S]*?\n  \];\n/.exec(html)[0];
const watch = /var KAL_WATCH = [^\n]*\n/.exec(html)[0];
const f = new Function(looks + watch + ['kalshiStrategyState', 'kalshiCtWeekMinute', 'kalshiGoldClosed', 'kalshiNextEntry', 'kalshiMarketName', 'kalshiDurationText', 'kalshiSilentMarkets'].map(fnSource).join('\n') +
  '; return { kalshiStrategyState, kalshiNextEntry, kalshiSilentMarkets };')();
const TUE = Date.parse('2026-11-03T15:00:00Z'), Q = 900000, base = Math.floor(TUE / Q) * Q;
const SLOTS = ['OICORE', 'EVENT830', 'CFRTIK', 'SPXOI1', 'HYPEOI1', 'BNBOI1'];
const state = (gold, extra) => f.kalshiStrategyState(Object.assign({ gold: { state: gold }, slotIds: SLOTS, registry: [], shadowIds: ['SHADOWX'] }, extra || {}));
// every look (minute offset in the quarter) the card can name, across a whole quarter
const names = (st, from) => { const out = new Set(); for (let t = from; t < from + Q; t += 30000) { const n = f.kalshiNextEntry(t, st); if (n) out.add(n.name); } return [...out]; };

gates.SS1 = () => {
  const st = state('killed');
  assert.deepStrictEqual([st.L1, st.OICORE, st.EVENT830, st.CFRTIK, st.SHADOWX], ['off', 'armed', 'armed', 'armed', 'shadow']);
  const n = f.kalshiNextEntry(base + 60000, st);
  assert.notStrictEqual(n.name, 'Closing buy', 'killed gold is not the next look');
  assert.ok(!/Gold/.test(n.what + n.then), 'killed gold is not named in the look or the one after');
  assert.deepStrictEqual(n.off, ['Gold'], 'it is named as off instead');
  assert.ok(!names(st, base).includes('Closing buy'), 'at no minute of the quarter does the ring show the Closing buy');
};
gates.SS2 = () => {
  const all = names(state('armed'), base);
  ['Closing buy', 'Open interest jump', 'Perp-model longshot'].forEach((x) => assert.ok(all.includes(x), x + ' is a next look while armed'));
  const n = f.kalshiNextEntry(base + 730000, state('armed'));
  assert.strictEqual(n.name, 'Perp-model longshot'); assert.strictEqual(n.at, base + 780000, 'CFRTIK looks 2 minutes before the close');
  const rel = Date.parse('2026-11-05T13:30:00Z');
  assert.ok(/Release day longshot/.test(f.kalshiNextEntry(rel - 6 * 60000, state('armed')).name), 'EVENT830 appears on a listed release window');
  assert.deepStrictEqual(f.kalshiNextEntry(base + 60000, state('armed')).off, [], 'nothing is off when gold is armed');
};
gates.SS3 = () => {
  ['loading', 'unknown', undefined].forEach((g) => {
    const st = state(g);
    assert.strictEqual(st.L1, 'unknown');
    assert.ok(!names(st, base).includes('Closing buy'), 'an unreadable latch must not claim gold is about to trade (' + g + ')');
    assert.deepStrictEqual(f.kalshiNextEntry(base + 60000, st).off, [], 'and must not claim it is off either');
  });
  const none = f.kalshiNextEntry(base + 60000, f.kalshiStrategyState({ gold: { state: 'killed' }, slotIds: [], registry: [] }));
  assert.strictEqual(none, null, 'with nothing armed there is no next look (the card says so)');
};
gates.SS4 = () => {
  // the silent-market alert: a killed or unknown gold is never "silent"; an armed gold still is
  const H = 3600000, MIN = 60000, o = [];
  for (let t = TUE - 5 * H; t > TUE - 3 * 86400000; t -= 20 * MIN) o.push({ strategy: 'L1', series: 'KXGOLD15M', ts: t });
  const live = { active: true };
  assert.strictEqual(f.kalshiSilentMarkets(o, live, TUE, state('armed')).length, 1, 'armed gold with no order for hours is called silent');
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE, state('killed')), [], 'killed gold is off, not silent');
  assert.deepStrictEqual(f.kalshiSilentMarkets(o, live, TUE, state('unknown')), [], 'unknown state claims no silence');
  assert.strictEqual(f.kalshiSilentMarkets(o, live, TUE).length, 1, 'without a state the pure rule is unchanged');
};
gates.SS5 = () => {
  // rotation with no code edit: registry rows decide, and a Retired verdict wins
  const st = f.kalshiStrategyState({ gold: { state: 'armed' }, slotIds: ['OICORE'], registry: [
    { id: 'NEWPROBE', stage: 'Probe', code: { live: true } }, { id: 'IDEA1', stage: 'Idea' }, { id: 'SHAD1', stage: 'Shadow' }, { id: 'OICORE', stage: 'Retired' }] });
  assert.deepStrictEqual([st.NEWPROBE, st.IDEA1, st.SHAD1, st.OICORE], ['armed', undefined, 'shadow', 'retired']);
  assert.ok(!names(f.kalshiStrategyState({ gold: { state: 'armed' }, slotIds: ['OICORE'], registry: [{ id: 'OICORE', stage: 'Retired' }] }), base).includes('Open interest jump'), 'a retired strategy leaves the ring');
};
gates.SS6 = () => {
  // wiring: every consumer reads the one function
  const status = fnSource('renderKalshiStatus'), tick = fnSource('kalshiStatusTick'), table = fnSource('renderKalshiStrategies'), page = fnSource('renderStrategiesPage');
  assert.ok(/kalshiSilentMarkets\(orders, s, now, liveState\)/.test(status) && /kalshiGoldEnsure\(\)/.test(status), 'Needs a look reads the shared state and the Bot page starts the reads');
  assert.ok(/kalshiNextEntry\(now, stNow\)/.test(tick) && /kalNextOff/.test(tick), 'the ring reads it and says what is off');
  assert.ok(/kalshiLiveStateNow\(now\)/.test(table) && /Off, cooling down/.test(table), 'the Strategies table reads it');
  assert.ok(/liveState\[s\.id\] === 'off'/.test(page), 'the Strategies page lanes read the same state');
  assert.ok(/function kalshiStateChanged\(\)\{ renderStrategiesPage\(\); if\(typeof renderKalshiStatus/.test(html), 'both pages redraw when the latch or registry answers');
  // every KAL_LOOKS entry belongs to a strategy the state can name
  assert.ok([...looks.matchAll(/sid: '([A-Z0-9]+)'/g)].length === 4, 'four looks, each tied to a strategy id');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok ' + name); } catch (e) { failed++; console.error('FAIL ' + name + ': ' + (e && e.stack || e)); } }
if (failed) process.exit(1);
