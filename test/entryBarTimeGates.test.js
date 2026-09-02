// The Firestore Timestamp round trip, on the frontend side.
//
// entryBarTime is written by the backend as a JS Date, stored by the Admin
// SDK as a Timestamp, and read back by this tab as an OBJECT -- never as a
// Date or a string. `new Date(thatObject)` is Invalid Date, and every
// comparison against the resulting NaN is false, so the failure mode is not
// an error or a blank screen: it is a feature that silently does not run.
//
// These gates state the consequence. The chart's entry zone must actually be
// drawn for a position loaded from Firestore, and the coercion must reject a
// value it cannot date rather than substituting a plausible one -- an
// anchor at "now" would tint the chart from a bar the position was never
// opened at, which reads as real information.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}

const entryBarMillis = lift('entryBarMillis');

// 2026-09-02T13:45:00Z
const MS = 1788356700000;

const gates = {};

// Every shape this field genuinely arrives in must date to the same instant.
// The two object shapes are the ones the old code got wrong; they are also
// the only two that production actually stores.
gates.G1 = () => {
  const shapes = {
    'Date (a signal computed in this tab)': new Date(MS),
    'ISO string': new Date(MS).toISOString(),
    'epoch number': MS,
    'web SDK Timestamp object': { seconds: MS / 1000, nanoseconds: 0 },
    'Admin SDK Timestamp through JSON': { _seconds: MS / 1000, _nanoseconds: 0 },
    'live Timestamp instance': { toMillis: () => MS },
    'live Timestamp instance, toDate only': { toDate: () => new Date(MS) },
  };
  Object.keys(shapes).forEach((label) => {
    assert.strictEqual(entryBarMillis(shapes[label]), MS, label + ' must date to the stored instant');
  });
  // Positive control: the code this replaced failed on exactly the two
  // object shapes above and on nothing else, which is why it survived.
  assert.ok(isNaN(new Date(shapes['web SDK Timestamp object']).getTime()),
    'control: a raw new Date() on the stored shape really is Invalid Date');
  console.log('G1 PASS every stored shape of entryBarTime dates to the same instant');
};

// An undatable value must be NaN, never a substituted instant. A caller that
// silently anchored to "now" or to the first visible bar would draw a zone
// the position was never opened at -- a wrong answer wearing the face of a
// right one, which is worse than drawing nothing.
gates.G2 = () => {
  [null, undefined, '', 'not a date', {}, { seconds: 'x' }, { _seconds: null }, NaN, []].forEach((v) => {
    assert.ok(isNaN(entryBarMillis(v)), 'undatable input must be NaN: ' + JSON.stringify(v));
  });
  console.log('G2 PASS undatable values are NaN, not a plausible substitute');
};

// The consequence gate: the chart's entry-zone anchor must be computed
// through the coercion, so a position loaded from Firestore actually gets
// its zone drawn. Asserted against the source because the anchor lives
// inside a large drawing function that cannot be lifted on its own.
gates.G3 = () => {
  // Comments stripped first: the helper's own comment names the broken
  // expression on purpose, so a future change cannot reintroduce it
  // without noticing, and a check that reads comments would flag that
  // documentation as the bug it prevents.
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(/var entryTime0 = lv0\.entryBarTime \? entryBarMillis\(lv0\.entryBarTime\) : NaN;/.test(src),
    'the chart entry-zone anchor must go through entryBarMillis');
  assert.ok(!/new Date\(lv0\.entryBarTime\)/.test(code),
    'the chart must never build the anchor with a raw new Date(entryBarTime)');
  assert.ok(!/new Date\(j\.entryBarTime\)/.test(code),
    'the stale-entry session date must never use a raw new Date(entryBarTime)');
  console.log('G3 PASS no raw new Date() survives on any entryBarTime reader');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
