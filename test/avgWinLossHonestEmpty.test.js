// "AVG WIN +$0" over 13 real closed trades, 0 wins.
//
// avgWinDollar fell back to 0 when winCount was 0 -- winCount ? sum/winCount
// : 0 -- and the card rendered that unconditionally as "+$0". That reads as
// a MEASURED average win of zero dollars, which cannot happen: a winning
// trade is by definition > $0. The real fact was "there is nothing to
// average", the same distinction profitFactorText already draws for a
// profit factor with no losing trade -- and this card did not draw it.
//
// A losing streak that empties one side of the ledger is a real result a
// trader needs to see plainly, not a number dressed up to look like data.

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

const computeAggregatePL = lift('computeAggregatePL', {
  computePL: lift('computePL', {}),
  isWinningReturn: lift('isWinningReturn', {}),
});

// computePL derives pct/dollar from entry/exit/direction/qty -- not from a
// pre-computed field -- so the fixture has to hand it real prices.
const losingTrade = (i) => ({ status: 'closed', direction: 'Long', entry: 100, exit: 100 - (1 + i), qty: 1 });
const winningTrade = (i) => ({ status: 'closed', direction: 'Long', entry: 100, exit: 100 + (1 + i), qty: 1 });

const gates = {};

// The exact shape from the screenshot: 13 closed trades, all losers.
gates.G1 = () => {
  const entries = Array.from({ length: 13 }, (_, i) => losingTrade(i));
  const agg = computeAggregatePL(entries);
  assert.strictEqual(agg.winCount, 0, 'fixture precondition: no winners');
  assert.strictEqual(agg.avgWinDollar, null,
    'a zero-winner set must report avgWinDollar as null, not a fabricated $0');
  assert.notStrictEqual(agg.avgLossDollar, null, 'the loss side has real data and must not be nulled');
  console.log('G1 PASS an all-losing set reports no average win, not a fabricated $0');
};

// The mirror case, for the same reason in the other direction.
gates.G2 = () => {
  const entries = Array.from({ length: 5 }, (_, i) => winningTrade(i));
  const agg = computeAggregatePL(entries);
  assert.strictEqual(agg.lossCount, 0, 'fixture precondition: no losers');
  assert.strictEqual(agg.avgLossDollar, null,
    'a zero-loser set must report avgLossDollar as null, not a fabricated $0');
  console.log('G2 PASS an all-winning set reports no average loss, not a fabricated $0');
};

// The rendering contract: null must reach the page as an em dash, never as
// a dollar figure -- checked against the source, since the render function
// is deep inside a DOM-heavy block this file does not lift wholesale.
gates.G3 = () => {
  const code = src.replace(/\/\/[^\n]*/g, '');
  assert.ok(/avgWinDollar === null \? '—'/.test(code),
    'avgWinEl must render an em dash when avgWinDollar is null');
  assert.ok(/avgLossDollar === null \? '—'/.test(code),
    'avgLossEl must render an em dash when avgLossDollar is null');
  // The false-branch of the ternary legitimately still contains
  // ".avgWinDollar.toFixed" -- what must be gone is the OLD unconditional
  // assignment that called it with no null guard at all.
  assert.ok(!/textContent = '\+\$' \+ filtered\.avgWinDollar\.toFixed/.test(code),
    'avgWinEl must never call .toFixed on a value that can be null');
  assert.ok(!/textContent = '−\$' \+ Math\.abs\(filtered\.avgLossDollar\)\.toFixed/.test(code),
    'avgLossEl must never call .toFixed on a value that can be null');
  console.log('G3 PASS null never reaches .toFixed and always renders as an em dash');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
