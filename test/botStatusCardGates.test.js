'use strict';
// SC1 to SC8: the redone Bot status card (the owner, Oct 31, 2026: style B with a countdown ring and a tall health line; "bot status should cover all strategies"; "no repeat information on the page, all unique and helpful"; "avoid collapsables").
// Consequence (price and depth tiles removed Nov 11, 2026, see SC10): the card is the ring, the health line and "Needs a look"; never a fold; it covers both strategies (the Closing buy and the open interest jump); the tick ids exist; and it repeats nothing the Strategies table shows.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const gates = {};
const fn = (name) => { const m = new RegExp('  function ' + name + '\\([^)]*\\)\\{[\\s\\S]*?\\n  \\}\\n').exec(html); assert.ok(m, name + ' is in the page'); return m[0]; };
const block = (re) => { const m = re.exec(html); assert.ok(m, 'block ' + re + ' is in the page'); return m[0]; };
const RealDate = Date;
const DateStub = (nowMs) => Object.assign(function (...a) { return new RealDate(...a); }, { now: () => nowMs, parse: (x) => RealDate.parse(x) });
const FRI_EVE = RealDate.parse('2026-10-31T01:30:00Z'), TUE = RealDate.parse('2026-10-27T18:00:00Z');   // Friday 8:30 PM Central, Tuesday 1 PM Central
const lib = (nowMs) => new Function('Date', 'Intl', 'Math', 'Number', 'Array', 'Object', 'String', 'escapeHtml', 'kalTime', 'kalshiAgeText', 'kalshiBooksLast',
  fn('kalshiCtWeekMinute') + fn('kalshiGoldClosed') + block(/  var KAL_LOOKS = \[[\s\S]*?\n  \];\n/) + fn('kalshiNextEntry') +
  '; return { kalshiNextEntry, kalshiGoldClosed };')(DateStub(nowMs), Intl, Math, Number, Array, Object, String, (x) => String(x), () => '9:45 PM', (s) => s + ' seconds ago', null);

gates.SC1 = () => {
  // the card's markup: the ring, the health line; no fold; the ids the one second tick writes to
  const src = fn('renderKalshiStatus');
  assert.ok(!/<details|<summary|collaps/i.test(src), 'no fold of any kind on the card');
  for (const id of ['kalRing', 'kalNextIn', 'kalNextName', 'kalNextWhat', 'kalNextThen', 'kalEcg', 'kalHb', 'kalHbText']) assert.ok(new RegExp('id="' + id + '"').test(src), id + ' is on the card');
  assert.ok(!/Last order|Orders today|Win rate|Best market|Worst market|Fill rate/.test(src), 'nothing the Strategies table shows is repeated on this card');
  assert.ok(!/kal-more|kalMoreBody/.test(html), 'the More numbers fold is gone from the page');
};
gates.SC2 = () => {
  // every strategy's next look: the Closing buy at 9:00 into each 15 minutes, the open interest jump at 12:00
  const Q = 900000, base = Math.floor(TUE / Q) * Q;
  const at = (offsetMs) => lib(base + offsetMs).kalshiNextEntry(base + offsetMs);
  let n = at(60000); assert.strictEqual(n.name, 'Closing buy'); assert.strictEqual(n.inMs, 480000); assert.ok(/^Gold, /.test(n.what) && /then Open interest jump \(Bitcoin\)/.test(n.then));
  n = at(600000); assert.strictEqual(n.name, 'Open interest jump', 'after the 9 minute look the next one is the Bitcoin strategy'); assert.strictEqual(n.inMs, 120000); assert.ok(/Bitcoin/.test(n.what) && /then Closing buy/.test(n.then));
  n = at(800000); assert.strictEqual(n.name, 'Closing buy', 'after the 12 minute look it wraps to the next quarter hour'); assert.strictEqual(n.inMs, 640000);
  assert.ok(n.frac > 0 && n.frac < 1, 'the ring fills between the previous look and the next');
  assert.ok(!/10 minute look/.test(JSON.stringify(n)), 'no 10 minute look unless a market with one can trade');
};
gates.SC3 = () => {
  const l = lib(FRI_EVE);
  assert.ok(/^No market is open, /.test(l.kalshiNextEntry(FRI_EVE).what) || l.kalshiNextEntry(FRI_EVE).name === 'Open interest jump', 'with gold closed (Dogecoin is paused since Nov 3, 2026) the Closing buy says no market is open');
  assert.strictEqual(lib(TUE).kalshiGoldClosed(TUE), false); assert.strictEqual(l.kalshiGoldClosed(FRI_EVE), true, 'gold closed from Friday 5 PM Central');
  assert.strictEqual(l.kalshiGoldClosed(RealDate.parse('2026-11-02T00:30:00Z')), false, 'gold open again from Sunday 6 PM Central');
};
// SC9 (Nov 4, 2026, the owner: "check to see if the bot status page includes other strategies outside of L1 & OICORE ... our dashboard is as an overall"): the ring covers EVENT830.
// Consequence: on a release day the countdown names the release window (with the open interest jump, which looks at the same moment); on any other day it never claims one; SF9 ties the ring's list to the bot's calendar.
gates.SC9 = () => {
  const Q = 900000, rel = RealDate.parse('2026-11-05T13:30:00Z'), plain = RealDate.parse('2026-11-04T13:30:00Z');
  const onDay = lib(rel - 6 * 60000).kalshiNextEntry(rel - 6 * 60000);
  assert.strictEqual(onDay.at, rel - 180000, 'on a release day the next look is 3 minutes before the 7:30 AM Central close');
  assert.ok(/Open interest jump and Release day longshot/.test(onDay.name) && /Bitcoin/.test(onDay.what) && /Silver, copper, oil/.test(onDay.what), 'both strategies looking at that moment are named, as one look');
  const offDay = lib(plain - 6 * 60000).kalshiNextEntry(plain - 6 * 60000);
  assert.strictEqual(offDay.name, 'Open interest jump', 'on a day with no listed release the countdown never names the release window');
  let seen = 0; for (let t = RealDate.parse('2026-11-04T00:00:00Z'); t < RealDate.parse('2026-11-05T00:00:00Z'); t += 60000) { if (/Release day/.test(lib(t).kalshiNextEntry(t).name + lib(t).kalshiNextEntry(t).then)) seen++; } assert.strictEqual(seen, 0, 'Nov 4 has no release window at any minute');
};
gates.SC7 = () => {
  assert.ok(/\.kal-st-top\{[^}]*grid-template-columns/.test(html) && /@container \(max-width:520px\)\{ \.kal-st-top\{ grid-template-columns:1fr; \} \}/.test(html) && /@media \(max-width:520px\)\{ \.kal-st-top\{ grid-template-columns:1fr; \}/.test(html), 'the two tiles stack on a narrow card');
  assert.ok(/#kalStatusBody\{ container-type:inline-size; \}/.test(html), 'the card measures its own width, not the window (it sits in a rail)');
};
// SC10 (Nov 11, 2026, the owner: "this can probably go too, not sure of much use for this anymore"): the prices and depth tiles are gone.
// Consequence: nothing of the two tiles is left on the page, and the page asks Firestore or the network for nothing new.
gates.SC10 = () => {
  for (const name of ['kalPrices', 'kalDepth', 'kalshiPriceWatch', 'KAL_PRICE_WATCH', 'kalshiRenderPrices', 'kalshiEventNext', 'kalshiEscapedEventCell', 'kalshiEscapedPriceCell', 'kalshiLastOrderSizes', 'kalshiEscapedDepthRow', 'kalshiEscapedDepthRows', 'kal-st-bottom', 'kal-st-prices', 'kal-st-depth', 'kal-st-pgrid', 'kal-st-pcell', 'kal-st-drow'])
    assert.ok(!html.includes(name), name + ' is gone from the page');
  assert.ok(!/Prices right now, against what each strategy buys|Depth at the touch, against our order size/.test(html), 'neither tile title is on the page');
  const status = fn('renderKalshiStatus');
  assert.ok(/id="kalWork"/.test(status), 'the Needs a look block still has its place');
  assert.deepStrictEqual(html.match(/fetch\([^,)]*/g), ['fetch(location.pathname'], 'the only fetch is the page freshness HEAD check: removing tiles added no request');
};
// What stays: the ring and the health line, and the relay read that Open positions still needs.
gates.SC11 = () => {
  const status = fn('renderKalshiStatus');
  for (const id of ['kalRing', 'kalEcg', 'kalHbText']) assert.ok(new RegExp('id="' + id + '"').test(status), id + ' is still on the card');
  assert.ok(/Needs a look/.test(status), 'the Needs a look block stays');
  assert.ok(/kalshiBooksLast = data \|\| null;\n    renderKalshiPositions\(\);/.test(html), 'the relay read still feeds Open positions (time left, price and chart)');
  assert.ok(/function kalshiNextEntry\(/.test(html) && /var KAL_LOOKS = \[/.test(html), 'the countdown ring keeps its looks');
};
(async () => { let failed = 0; for (const [name, g] of Object.entries(gates)) { try { await g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } } process.exit(failed ? 1 : 0); })();
