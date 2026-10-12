'use strict';
// WHAT THE PAGE SAYS WHEN IT DOES NOT KNOW.
//
// Every fault this file gates has the same shape: the frontend had a
// confident-looking answer ready for a case where it had no answer at all.
// A price cell that says "NaN", a P&L of exactly $0.00 on something nobody
// could price, the literal word "undefined" where a sentence belongs. None
// of these look broken, which is precisely what makes them worse than a
// blank card.
//
// These gates state the CONSEQUENCE of each one, not the mechanism. The
// ones about the removed trading pages went with those pages; what is left
// is the price formatter the Brief's movers still use.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

// Lifted out of index.html with new Function, per CLAUDE.md -- there is no
// build step to import from.
function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  assert.notStrictEqual(start, -1, 'not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}

const gates = {};

// ---------------------------------------------------------------------
// A price cell must never print a non-number as if it were a price.
// ---------------------------------------------------------------------
gates.G1_fmt_never_prints_a_fake_price = () => {
  const fmt = lift('fmt');
  // A price that never arrived. "NaN" in a price cell is read as a price.
  assert.strictEqual(fmt(NaN), '—', 'NaN must render as a gap, never as the string "NaN"');
  assert.strictEqual(fmt(undefined), '—', 'a missing level must render as a gap');
  assert.strictEqual(fmt(null), '—', 'a null level must render as a gap, not as $0.00');
  assert.strictEqual(fmt(Infinity), '—', 'an infinite price is not a price');
  // ...and must not throw. A TypeError raised inside a .map() building a
  // table's innerHTML takes the whole card down.
  assert.doesNotThrow(() => fmt(undefined), 'a missing level must not blank the card it appears in');
  // Real prices are untouched, including the sub-dollar scaling
  // this function exists for.
  assert.strictEqual(fmt(12.345), '12.35');
  assert.strictEqual(fmt(0.12345678), '0.1235');
  assert.strictEqual(fmt(0.000012345678), '0.00001235');
  assert.strictEqual(fmt(0), '0.00000000', 'zero is a real number and must still print');
};

let failures = 0;
const only = process.argv[2];
Promise.all(Object.keys(gates).filter((k) => !only || k.includes(only)).map((name) => {
  return Promise.resolve().then(gates[name]).then(
    () => console.log('PASS ' + name),
    (e) => { failures++; console.error('FAIL ' + name + ': ' + e.message); }
  );
})).then(() => {
  if (failures) { console.error(failures + ' gate(s) failed'); process.exit(1); }
  console.log('failureModeGates: all gates passed');
});
