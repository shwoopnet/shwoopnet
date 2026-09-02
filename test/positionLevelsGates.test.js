// What the Equities Setups card says about a position you actually hold.
//
// The card merges live screener signals with real open positions. It already
// let the journal entry override strategy and status, on the reasoning that
// the entry records what HAPPENED while the live row only says what is
// signalling now -- and then left the prices behind.
//
// The stop is the one that matters. safety/trailingStop.js ratchets it as a
// trade goes the right way, so a row rendering the signal's original stop
// shows protection that is no longer where it says: a stop read as further
// away than it really is, on the card people check to see where they stand.
//
// These state the consequences.

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

const gates = {};

// The signal said enter at 3.10 with a 3.02 stop. The account filled at 3.11
// and the stop has since trailed up to 3.06. The row must say 3.11 / 3.06.
gates.G1 = () => {
  const position = {
    sym: 'OPEN', direction: 'Long', status: 'open', source: 'alpaca',
    screenerType: 'intraday', strategy: 'orb',
    entry: 3.11, stop: 3.06, t1: 3.25,
  };
  const merge = lift('withOpenPositionsMergedIn', {
    journalEntries: [position],
    isOpenAlpacaPositionForCurrentAccount: () => true,
  });
  const signal = { sym: 'OPEN', direction: 'Long', status: 'active', strategy: 'orb',
    entry: 3.10, stop: 3.02, t1: 3.24, stopPctFromEntry: -0.0258, t1PctFromEntry: 0.045 };
  const [row] = merge([signal]);

  assert.strictEqual(row.entry, 3.11, 'the row must show the price the account actually filled at');
  assert.strictEqual(row.stop, 3.06, 'the row must show the CURRENT stop, which trailing has moved');
  assert.strictEqual(row.t1, 3.25, 'the row must show the target re-anchored to the real fill');
  // The bar under the numbers is drawn from the percentages, so they cannot
  // be allowed to describe a different trade from the prices above them.
  assert.ok(Math.abs(row.stopPctFromEntry - ((3.06 - 3.11) / 3.11)) < 1e-9,
    'stop % must be recomputed from the real prices, or the bar contradicts the numbers');
  assert.ok(Math.abs(row.t1PctFromEntry - ((3.25 - 3.11) / 3.11)) < 1e-9,
    'target % must be recomputed from the real prices');
  console.log('G1 PASS a held position\'s own entry, trailed stop and target win');
};

// A symbol with no position must be untouched -- the signal's own plan is
// the only thing that exists for it.
gates.G2 = () => {
  const merge = lift('withOpenPositionsMergedIn', {
    journalEntries: [],
    isOpenAlpacaPositionForCurrentAccount: () => false,
  });
  const signal = { sym: 'HOOD', direction: 'Long', status: 'watching', entry: 40, stop: 39, t1: 43 };
  const [row] = merge([signal]);
  assert.strictEqual(row.entry, 40, 'an untraded setup keeps its own planned entry');
  assert.strictEqual(row.stop, 39, 'an untraded setup keeps its own stop');
  console.log('G2 PASS an untraded setup is left alone');
};

// Fails closed: an entry missing a usable price must not blank the row.
gates.G3 = () => {
  const position = {
    sym: 'OPEN', direction: 'Long', status: 'open', source: 'alpaca',
    screenerType: 'intraday', entry: null, stop: null, t1: null,
  };
  const merge = lift('withOpenPositionsMergedIn', {
    journalEntries: [position],
    isOpenAlpacaPositionForCurrentAccount: () => true,
  });
  const signal = { sym: 'OPEN', direction: 'Long', status: 'active', entry: 3.10, stop: 3.02, t1: 3.24 };
  const [row] = merge([signal]);
  assert.strictEqual(row.entry, 3.10, 'an unreadable position price must leave the signal\'s own showing, not undefined');
  assert.strictEqual(row.stop, 3.02, 'same for the stop');
  console.log('G3 PASS an unusable position price does not blank the row');
};

// The chart draws three levels. A fourth "P" line existed to show the gap
// between plan and fill; that gap is now bounded by the chase gate and the
// real-fill re-anchor, and its axis tag sat on top of the fill's anyway.
gates.G4 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(!/planEntry/.test(code), 'no planEntry line, lookup or level should remain in the code');
  assert.ok(/levelLine\(lv\.target/.test(code) && /levelLine\(lv\.entry/.test(code) && /levelLine\(lv\.stop/.test(code),
    'entry, stop and target lines must all still be drawn');
  console.log('G4 PASS the chart draws entry, stop and target and nothing else');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
