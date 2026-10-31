'use strict';
// SC1 to SC7: the redone Bot status card (the owner, Oct 31, 2026: style B with a countdown ring and a tall health line; "bot status should cover all strategies"; "no repeat information on the page, all unique and helpful"; "avoid collapsables").
// Consequence: the card is the ring, the health line and one price tile; never a fold; it covers both strategies (the Closing buy and the open interest jump); the tick ids exist; it repeats nothing the Strategies table shows; and it says plainly when a market is out of its buying band.
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
  fn('kalshiCtWeekMinute') + fn('kalshiGoldClosed') + block(/  var KAL_LOOKS = \[[\s\S]*?\n  \];\n/) + fn('kalshiNextEntry') + block(/  var KAL_PRICE_WATCH = \[[\s\S]*?\n  \];\n/) + fn('kalshiPriceWatch') +
  '; return { kalshiNextEntry, kalshiPriceWatch, kalshiGoldClosed };')(DateStub(nowMs), Intl, Math, Number, Array, Object, String, (x) => String(x), () => '9:45 PM', (s) => s + 's', null);

gates.SC1 = () => {
  // the card's markup: the ring, the health line, the price tile; no fold; the ids the one second tick writes to
  const src = fn('renderKalshiStatus');
  assert.ok(!/<details|<summary|collaps/i.test(src), 'no fold of any kind on the card');
  for (const id of ['kalRing', 'kalNextIn', 'kalNextName', 'kalNextWhat', 'kalNextThen', 'kalEcg', 'kalHb', 'kalHbText', 'kalPrices']) assert.ok(new RegExp('id="' + id + '"').test(src), id + ' is on the card');
  assert.ok(!/Last order|Orders today|Win rate|Best market|Worst market|Fill rate/.test(src), 'nothing the Strategies table shows is repeated on this card');
  assert.ok(!/kal-more|kalMoreBody/.test(html), 'the More numbers fold is gone from the page');
};
gates.SC2 = () => {
  // every strategy's next look: the Closing buy at 9:00 into each 15 minutes, the open interest jump at 12:00
  const Q = 900000, base = Math.floor(TUE / Q) * Q;
  const at = (offsetMs) => lib(base + offsetMs).kalshiNextEntry(base + offsetMs);
  let n = at(60000); assert.strictEqual(n.name, 'Closing buy'); assert.strictEqual(n.inMs, 480000); assert.ok(/gold and Dogecoin/.test(n.what) && /then Open interest jump \(Bitcoin\)/.test(n.then));
  n = at(600000); assert.strictEqual(n.name, 'Open interest jump', 'after the 9 minute look the next one is the Bitcoin strategy'); assert.strictEqual(n.inMs, 120000); assert.ok(/Bitcoin/.test(n.what) && /then Closing buy/.test(n.then));
  n = at(800000); assert.strictEqual(n.name, 'Closing buy', 'after the 12 minute look it wraps to the next quarter hour'); assert.strictEqual(n.inMs, 640000);
  assert.ok(n.frac > 0 && n.frac < 1, 'the ring fills between the previous look and the next');
  assert.ok(!/10 minute look/.test(JSON.stringify(n)), 'no 10 minute look unless a market with one can trade');
};
gates.SC3 = () => {
  const l = lib(FRI_EVE);
  assert.ok(/^Dogecoin, /.test(l.kalshiNextEntry(FRI_EVE).what) || l.kalshiNextEntry(FRI_EVE).name === 'Open interest jump', 'with gold closed the Closing buy names only Dogecoin');
  assert.strictEqual(lib(TUE).kalshiGoldClosed(TUE), false); assert.strictEqual(l.kalshiGoldClosed(FRI_EVE), true, 'gold closed from Friday 5 PM Central');
  assert.strictEqual(l.kalshiGoldClosed(RealDate.parse('2026-11-02T00:30:00Z')), false, 'gold open again from Sunday 6 PM Central');
};
const mk = (series, bid, ask, close) => ({ series, ticker: series + '-X', closeTime: close || '2026-10-27T18:15:00Z', yesBid: bid, yesAsk: ask });
gates.SC4 = () => {
  const l = lib(TUE);
  const rows = l.kalshiPriceWatch([mk('KXGOLD15M', 0.91, 0.92), mk('KXDOGE15M', 0.05, 0.07), mk('KXBTC15M', 0.88, 0.90)], TUE), by = (n) => rows.find((r) => r.name === n);
  assert.strictEqual(by('Gold').state, 'in', 'gold favourite side (yes at 92c) is inside 88c to 97c'); assert.ok(Math.abs(by('Gold').price - 0.92) < 1e-9);
  assert.strictEqual(by('Dogecoin').state, 'in', 'a market at 5c yes has a 95c no side: the favourite is the no side, inside the band'); assert.ok(Math.abs(by('Dogecoin').price - 0.95) < 1e-9);
  assert.strictEqual(by('Bitcoin').state, 'in', 'the Bitcoin strategy buys the cheaper side: no at 12c is inside 5c to 50c'); assert.ok(Math.abs(by('Bitcoin').price - 0.12) < 1e-9, 'the cheaper side is 1 minus the yes bid');
  const out = l.kalshiPriceWatch([mk('KXGOLD15M', 0.83, 0.84), mk('KXDOGE15M', 0.985, 0.99), mk('KXBTC15M', 0.01, 0.02)], TUE);
  assert.strictEqual(out[0].state, 'below', 'gold at 84c is below the band: this is why nothing is trading'); assert.strictEqual(out[1].state, 'above'); assert.strictEqual(out[2].state, 'below', 'a cheaper side under 5c is below the Bitcoin range');
  assert.ok(out[0].pos >= 0 && out[0].pos <= 1 && out[0].bandWidth > 0, 'the marker and band are fractions of the scale');
};
gates.SC5 = () => {
  const r = lib(FRI_EVE).kalshiPriceWatch([mk('KXGOLD15M', 0.91, 0.92, '2026-10-31T01:45:00Z'), mk('KXDOGE15M', 0.5, 0.52, '2026-10-31T01:45:00Z')], FRI_EVE);
  assert.strictEqual(r[0].state, 'closed', 'gold is shown closed on a Friday evening whatever the relay says'); assert.strictEqual(r[1].state, 'in' === r[1].state ? 'in' : r[1].state);
  const none = lib(TUE).kalshiPriceWatch([], TUE); assert.ok(none.every((x) => x.state === 'none'), 'no relay data: no quote, never a made-up price');
  const stale = lib(TUE).kalshiPriceWatch([mk('KXDOGE15M', 0.9, 0.91, '2026-10-27T17:00:00Z')], TUE).find((x) => x.name === 'Dogecoin'); assert.strictEqual(stale.state, 'none', 'a market that already closed is not shown');
  const zero = lib(TUE).kalshiPriceWatch([mk('KXDOGE15M', 0, 0, '2026-10-27T18:15:00Z')], TUE).find((x) => x.name === 'Dogecoin'); assert.strictEqual(zero.state, 'none', 'an empty book is no quote');
};
gates.SC6 = () => {
  // the redraw reads only the relay data and never throws on empty data; the rendered tile names the verdict in words
  const el = { innerHTML: '' }; const data = { fetchedAt: TUE - 14000, markets: [mk('KXGOLD15M', 0.83, 0.84), mk('KXDOGE15M', 0.91, 0.92), mk('KXBTC15M', 0.88, 0.90)] };
  const src = block(/  var KAL_PRICE_WATCH = \[[\s\S]*?\n  \];\n/) + fn('kalshiCtWeekMinute') + fn('kalshiGoldClosed') + fn('kalshiPriceWatch') + fn('kalshiEscapedPriceCell') + fn('kalshiRenderPrices') + '; return kalshiRenderPrices;';
  const f = new Function('document', 'Date', 'Intl', 'Math', 'Number', 'Array', 'Object', 'String', 'escapeHtml', 'kalTime', 'kalshiAgeText', 'kalshiBooksLast', src)({ getElementById: (id) => (id === 'kalPrices' ? el : null) }, DateStub(TUE), Intl, Math, Number, Array, Object, String, (x) => String(x), () => '9:45 PM', (s) => s + 's', data);
  f();
  assert.ok(/Below the 88c to 97c band/.test(el.innerHTML) && /Inside the 88c to 97c band/.test(el.innerHTML) && /Inside the 5c to 50c band/.test(el.innerHTML), 'each market gets a verdict in words');
  assert.ok(/Read 14s ago/.test(el.innerHTML) && /open interest jump/i.test(el.innerHTML), 'the age of the read and the open interest caveat are shown');
  const empty = { innerHTML: '' }; new Function('document', 'Date', 'Intl', 'Math', 'Number', 'Array', 'Object', 'String', 'escapeHtml', 'kalTime', 'kalshiAgeText', 'kalshiBooksLast', src)({ getElementById: () => empty }, DateStub(TUE), Intl, Math, Number, Array, Object, String, (x) => String(x), () => '', (s) => s, null)();
  assert.ok(/No quote yet/.test(empty.innerHTML) && /Reading the markets/.test(empty.innerHTML), 'no data yet: says so');
};
gates.SC7 = () => {
  assert.ok(/\.kal-st-top\{[^}]*grid-template-columns/.test(html) && /@container \(max-width:520px\)\{ \.kal-st-top\{ grid-template-columns:1fr; \} \}/.test(html) && /@media \(max-width:520px\)\{ \.kal-st-top\{ grid-template-columns:1fr; \} \}/.test(html), 'ring and health side by side, stacked when the card or the screen is narrow');
  assert.ok(/#kalStatusBody\{ container-type:inline-size; \}/.test(html), 'the card measures its own width, not the window (it sits in a rail)');
  assert.ok(/relay on every read|kalshiRenderPrices\(\);/.test(html) && /kalshiBooksLast = data \|\| null;\n    renderKalshiPositions\(\);\n    kalshiRenderPrices\(\);/.test(html), 'the price tile is redrawn on every relay read');
};
(async () => { let failed = 0; for (const [name, g] of Object.entries(gates)) { try { await g(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } } process.exit(failed ? 1 : 0); })();
