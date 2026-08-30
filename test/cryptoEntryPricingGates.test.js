const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

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

function constant(name) {
  const m = new RegExp('var ' + name + ' = ([\\d.]+);').exec(src);
  if (!m) throw new Error(name + ' not found');
  return Number(m[1]);
}

const REWARD = constant('CRYPTO_BT_REWARD_MULTIPLE');
const bar = (o, h, l, c) => ({ o, h, l, c, t: new Date(), vol: 1000 });

const gates = {};

gates.G1 = () => {
  const fill = lift('fillCryptoSignalAtNextBar', { CRYPTO_BT_REWARD_MULTIPLE: REWARD });
  // Signal bar broke through rangeHigh=100 and ran to close 103.
  // The next bar opens at 102.5 -- that is the earliest price a market
  // order sent after the signal bar closed could realistically touch.
  const bars = [bar(99, 103, 98, 103), bar(102.5, 104, 102, 103.5)];
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 };
  const out = fill(bars, 0, signal);
  assert.ok(out, 'a fillable signal must not be dropped');
  assert.strictEqual(out.entry, 102.5, 'entry must be the NEXT bar open, not the breakout level');
  assert.notStrictEqual(out.entry, signal.entry, 'entry must never be the breakout level the bar ran through');
  assert.strictEqual(out.entryIdx, 1, 'the fill bar is the bar after the signal');
  // Positive control: the old behaviour must be something this rejects.
  assert.ok(signal.entry < out.entry, 'control: the old entry was cheaper, which is exactly the free money being removed');
  console.log('G1 PASS entry is priced at the next bar\'s open');
};

gates.G2 = () => {
  const sim = lift('simulateCryptoForward', {
    CRYPTO_BT_TRAIL_TRIGGER_RR: constant('CRYPTO_BT_TRAIL_TRIGGER_RR'),
    CRYPTO_BT_TREND_LOOKBACK_BARS: constant('CRYPTO_BT_TREND_LOOKBACK_BARS'),
    CRYPTO_BT_EARLY_BREAKEVEN_RR: constant('CRYPTO_BT_EARLY_BREAKEVEN_RR'),
  });
  // Filled at 102.5 on bar index 1, whose own low is 94 -- below the 95
  // stop. That trade is stopped out on the bar it entered on.
  const bars = [bar(99, 103, 98, 103), bar(102.5, 103, 94, 96), bar(96, 99, 95.5, 98)];
  const filled = { direction: 'Long', entry: 102.5, stop: 95, t1: 125 };
  const out = sim(bars, 1, filled, false);
  assert.strictEqual(out.result, 'stopped', 'a same-bar stop-out must be recorded, not skipped');
  assert.strictEqual(out.bars, 0, 'resolving on the entry bar is zero bars held');
  assert.strictEqual(out.price, 95);
  // Positive control: a bar that does NOT reach the stop must survive it,
  // or this gate would pass by stopping everything out immediately.
  const safe = [bar(99, 103, 98, 103), bar(102.5, 104, 101, 103.5), bar(103, 104, 94, 95)];
  const out2 = sim(safe, 1, filled, false);
  assert.strictEqual(out2.result, 'stopped');
  assert.strictEqual(out2.bars, 1, 'control: a trade surviving its entry bar stops out on a later one');
  console.log('G2 PASS entry bar can resolve the trade');
};

gates.G3 = () => {
  const fill = lift('fillCryptoSignalAtNextBar', { CRYPTO_BT_REWARD_MULTIPLE: REWARD });
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 };
  // A signal on the LAST bar has no bar to fill on.
  assert.strictEqual(fill([bar(99, 103, 98, 103)], 0, signal), null, 'a signal on the final bar must be dropped');
  // A gap straight through the stop leaves no trade to model.
  assert.strictEqual(fill([bar(99, 103, 98, 103), bar(94, 95, 90, 91)], 0, signal), null, 'a fill at or below the stop must be dropped');
  assert.strictEqual(fill([bar(99, 103, 98, 103), bar(0, 1, 0, 1)], 0, signal), null, 'a nonsense open must be dropped');
  // Levels must be re-anchored to the REAL fill, not left at the signal's.
  const out = fill([bar(99, 103, 98, 103), bar(102.5, 104, 102, 103.5)], 0, signal);
  assert.strictEqual(out.stop, 95, 'the stop stays where the signal put it');
  const risk = out.entry - out.stop;
  assert.ok(Math.abs(out.t1 - (out.entry + REWARD * risk)) < 1e-9, 'target must be recomputed from the real fill');
  assert.notStrictEqual(out.t1, signal.t1, 'target must not be left at the signal-bar value');
  // Risk really did grow, which is the honest consequence of a worse fill.
  assert.ok(risk > (signal.entry - signal.stop), 'a worse fill means more risk per unit, and that must be reflected');
  console.log('G3 PASS unfillable signals dropped and levels re-anchored');
};

gates.G5 = () => {
  const out = execFileSync(process.execPath,
    [path.join(root, '.claude/skills/pre-ship/scripts/check-frontend.js'), path.join(root, 'index.html')],
    { encoding: 'utf8' });
  assert.ok(/FRONTEND: clean/.test(out), 'pre-ship not clean:\n' + out);
  // Zero orphans, not "only the known one". intradayToggle was cleared,
  // so this is now a strictly stronger assertion than it was.
  const m = /no matching element: (.+)/.exec(out);
  assert.strictEqual(m, null, m ? `orphaned lookup(s): ${m[1]}` : '');
  console.log('G5 PASS pre-ship clean');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
