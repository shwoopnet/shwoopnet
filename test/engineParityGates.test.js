const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
// The live engine, required directly. This is the whole point: the thing
// the backtest claims to simulate is a module in the repo that places the
// orders, so parity can be asserted rather than reviewed.
// Sibling checkout, not an absolute path -- this is a hard requirement,
// not a skippable one. A parity test that silently passes when it cannot
// find the thing it is comparing against is worse than no parity test.
const LIVE_ENGINE = path.join(root, '..', 'shwoop-server', 'src', 'lib', 'technicalAnalysisCrypto.js');
if (!fs.existsSync(LIVE_ENGINE)) {
  console.error('Cannot find the live engine at ' + LIVE_ENGINE +
    '\nThis test compares the backtest against the code that actually places orders.' +
    '\nClone shwoop-server as a sibling of this repo and re-run.');
  process.exit(1);
}
const { createTA } = require(LIVE_ENGINE);

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
function num(name) {
  const m = new RegExp('var ' + name + ' = ([\\d.]+);').exec(src);
  if (!m) throw new Error(name + ' not found in index.html');
  return Number(m[1]);
}
const bar = (o, h, l, c) => ({ o, h, l, c, t: new Date(), vol: 1000 });

function sim(deps) {
  return lift('simulateCryptoForward', Object.assign({
    CRYPTO_BT_TRAIL_TRIGGER_RR: num('CRYPTO_BT_TRAIL_TRIGGER_RR'),
    CRYPTO_BT_EARLY_BREAKEVEN_RR: num('CRYPTO_BT_EARLY_BREAKEVEN_RR'),
    CRYPTO_BT_TREND_LOOKBACK_BARS: num('CRYPTO_BT_TREND_LOOKBACK_BARS'),
  }, deps || {}));
}

const gates = {};

gates.G1 = () => {
  const ta = createTA({});
  // Every live parameter that describes the STRATEGY (not the plumbing)
  // must have a backtest twin with the same value.
  const pairs = [
    ['RANGE_LOOKBACK_BARS', 'CRYPTO_BT_RANGE_LOOKBACK_BARS'],
    ['VOLUME_LOOKBACK', 'CRYPTO_BT_VOLUME_LOOKBACK'],
    ['VOLUME_CONFIRM_MULTIPLE', 'CRYPTO_BT_VOLUME_CONFIRM_MULTIPLE'],
    ['REWARD_MULTIPLE', 'CRYPTO_BT_REWARD_MULTIPLE'],
    ['TRAIL_TRIGGER_RR', 'CRYPTO_BT_TRAIL_TRIGGER_RR'],
    ['EARLY_BREAKEVEN_RR', 'CRYPTO_BT_EARLY_BREAKEVEN_RR'],
    ['TREND_LOOKBACK_BARS', 'CRYPTO_BT_TREND_LOOKBACK_BARS'],
    ['TREND_MARGIN_PCT', 'CRYPTO_BT_TREND_MARGIN_PCT'],
  ];
  for (const [liveName, btName] of pairs) {
    const liveVal = ta.params[liveName];
    assert.ok(liveVal !== undefined, `live is missing ${liveName}`);
    let btVal;
    try { btVal = num(btName); } catch (e) { assert.fail(`backtest has no counterpart for live ${liveName} (expected ${btName})`); }
    assert.strictEqual(btVal, liveVal, `${btName} is ${btVal} but live ${liveName} is ${liveVal}`);
  }
  // Positive control: the check must actually be capable of failing.
  assert.throws(() => num('CRYPTO_BT_DEFINITELY_NOT_A_REAL_CONSTANT'),
    'control: a missing constant must throw, or G1 could pass vacuously');
  console.log('G1 PASS constants match live');
};

gates.G2 = () => {
  const f = sim();
  const EB = num('CRYPTO_BT_EARLY_BREAKEVEN_RR');
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 }; // risk 5
  // Reaches 0.2R (101.0) on its close, never reaches the 0.5R trail
  // trigger (102.5), then collapses through the original stop.
  const bars = [bar(100, 101.4, 99.8, 101.2), bar(101, 101.2, 90, 91)];
  const out = f(bars, 0, signal, false);
  assert.strictEqual(out.price, 100, `expected a breakeven exit at 100, got ${out.price}`);
  assert.ok(EB > 0 && EB < num('CRYPTO_BT_TRAIL_TRIGGER_RR'),
    'early breakeven must engage BEFORE the trail trigger, or it changes nothing');
  // POSITIVE CONTROL: a trade that never reaches 0.2R must still exit at
  // the ORIGINAL stop, or this gate would pass by flooring everything.
  const never = [bar(100, 100.5, 99.8, 100.2), bar(100, 100.2, 90, 91)];
  const out2 = f(never, 0, signal, false);
  assert.strictEqual(out2.price, 95, `a trade that never reached ${EB}R must exit at 95, got ${out2.price}`);
  console.log('G2 PASS early breakeven protects the trade');
};

gates.G3 = () => {
  const f = sim();
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 };
  // A long upper wick to 108 that CLOSES back at 100.5. Live sees only
  // the close, so trailing must not activate and must not trail from 108.
  const bars = [bar(100, 108, 99.9, 100.5), bar(100, 100.6, 94, 94.5)];
  const out = f(bars, 0, signal, false);
  assert.notStrictEqual(out.result, 'trailing_stopped',
    'an intrabar wick must not activate trailing -- live never saw that price at a close');
  assert.ok(out.price <= 100, `trailing from the 108 wick would have exited near 103; got ${out.price}`);
  // POSITIVE CONTROL: the same peak reached at a CLOSE must activate it,
  // or this gate would pass by never trailing at all.
  const closed = [bar(100, 108, 99.9, 108), bar(108, 108.2, 100, 100.5)];
  const out2 = f(closed, 0, signal, false);
  assert.strictEqual(out2.result, 'trailing_stopped', 'a close at 108 must activate trailing');
  assert.strictEqual(out2.price, 103, `should trail to 108 - risk(5) = 103, got ${out2.price}`);
  console.log('G3 PASS trailing follows closes');
};

gates.G4 = () => {
  const f = sim();
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 };
  // Dips to 94 intrabar and closes back at 99. A resting stop-limit at
  // the broker really does fill on that dip -- this must NOT become a
  // close-only rule just because the trail updates did.
  const bars = [bar(100, 100.5, 94, 99)];
  const out = f(bars, 0, signal, false);
  assert.strictEqual(out.result, 'stopped', 'a resting stop must fill on the intrabar low');
  assert.strictEqual(out.price, 95);
  console.log('G4 PASS stops still fill intrabar');
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

gates.G6 = () => {
  // THE BOUNDARIES THEMSELVES. G2-G4 each clear their threshold by a
  // comfortable margin, so every comparison in the walk could be shifted
  // by one tick -- >= to >, <= to < -- and no gate noticed. A backtest
  // that resolves the exact-touch case differently from live is producing
  // a number for a strategy nobody runs, which is how the last figure in
  // CLAUDE.md was withdrawn.
  const f = sim();
  const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 }; // risk 5
  const risk = 5;

  // (1) A low that touches the stop EXACTLY is a fill. A resting order at
  // 95 fills at 95; treating it as a miss keeps losers alive for free.
  const touch = f([bar(100, 100.5, 95, 99), bar(99, 99.5, 98, 98.5)], 0, signal);
  assert.strictEqual(touch.result, 'stopped', 'a low exactly at the stop must fill, not survive');
  assert.strictEqual(touch.price, 95);

  // (2) A close exactly AT the trail trigger arms trailing. One tick short
  // and the trade rides the original stop, reporting a bigger loss than
  // the live engine would have taken.
  const trig = 100 + num('CRYPTO_BT_TRAIL_TRIGGER_RR') * risk;
  const armed = f([bar(100, trig, 99.9, trig), bar(trig, trig, trig - risk, trig - risk)], 0, signal);
  assert.strictEqual(armed.result, 'trailing_stopped',
    'a close exactly at the trail trigger must arm trailing, not merely reach it');

  // (3) A close exactly AT the early-breakeven level moves the stop to
  // entry. One tick short and the same trade exits at 95 instead of 100 --
  // a full R of invented loss on every trade that just touches the level.
  const eb = 100 + num('CRYPTO_BT_EARLY_BREAKEVEN_RR') * risk;
  const be = f([bar(100, eb + 0.2, 99.8, eb), bar(eb, eb, 90, 91)], 0, signal);
  assert.strictEqual(be.price, 100,
    `a close exactly at the ${num('CRYPTO_BT_EARLY_BREAKEVEN_RR')}R level must move the stop to entry, got ${be.price}`);
  console.log('G6 PASS the exact-touch case resolves the way live resolves it');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
