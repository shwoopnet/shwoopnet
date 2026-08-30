const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// Lifts a top-level function out of index.html by name, per CLAUDE.md's
// documented approach for a file with no build step.
function lift(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let depth = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
  }
  return new Function('return (' + src.slice(start, end) + ')')();
}

function liftUniverse() {
  const m = /var CRYPTO_UNIVERSE = (\[[\s\S]*?\]);/.exec(src);
  if (!m) throw new Error('CRYPTO_UNIVERSE not found');
  return new Function('return ' + m[1])();
}

function liftDays() {
  const m = /var CRYPTO_PREV_CLOSE_DAYS = (\d+);/.exec(src);
  if (!m) throw new Error('CRYPTO_PREV_CLOSE_DAYS not found');
  return Number(m[1]);
}

const gates = {};

gates.G1 = () => {
  const cryptoBarsUrl = lift('cryptoBarsUrl');
  const universe = liftUniverse();
  const days = liftDays();
  assert.ok(universe.length >= 12, `expected the full universe, got ${universe.length}`);

  const url = new URL(cryptoBarsUrl('https://data.alpaca.markets/v1beta3/crypto/us', universe, days));
  const limit = Number(url.searchParams.get('limit'));

  // The defect: limit caps the WHOLE response on this endpoint, so a
  // limit below the universe size cannot return a bar for every pair.
  assert.ok(
    limit >= universe.length * 2,
    `limit ${limit} cannot cover 2 bars for each of ${universe.length} pairs`,
  );
  // Positive control: the shipped value must actually reject the old one.
  assert.ok(!(2 >= universe.length * 2), 'control: the old limit=2 must fail this same predicate');

  // The window must be pinned, not left to the endpoint default.
  const start = url.searchParams.get('start');
  assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(start || ''), `start must be an explicit date, got ${start}`);
  const ageDays = (Date.now() - new Date(start + 'T00:00:00Z').getTime()) / 86400000;
  assert.ok(ageDays >= 2, `start ${start} is only ${ageDays.toFixed(1)} days back; too short for a previous daily close`);
  assert.ok(ageDays <= 30, `start ${start} is ${ageDays.toFixed(1)} days back; wider than needed`);

  assert.strictEqual(url.searchParams.get('timeframe'), '1Day');
  // Every pair must be named in the request.
  const asked = (url.searchParams.get('symbols') || '').split(',');
  assert.deepStrictEqual(asked.sort(), universe.slice().sort(), 'every pair must be requested');
  console.log('G1 PASS bars request is sized for the whole universe');
};

gates.G2 = () => {
  const prevCloseFromBars = lift('prevCloseFromBars');
  // The exact shape that produced the fabricated 0.00% moves: one bar.
  assert.strictEqual(prevCloseFromBars([{ c: 7.40 }]), null, 'a single bar must not become its own previous close');
  assert.strictEqual(prevCloseFromBars([]), null);
  assert.strictEqual(prevCloseFromBars(undefined), null);
  // Positive control: two bars must still yield the EARLIER one.
  assert.strictEqual(prevCloseFromBars([{ c: 100 }, { c: 105 }]), 100, 'two bars must yield the previous close, not the latest');
  // More than two: still the one immediately before the latest.
  assert.strictEqual(prevCloseFromBars([{ c: 90 }, { c: 100 }, { c: 105 }]), 100);
  console.log('G2 PASS a single bar yields no previous close');
};

gates.G3 = () => {
  const prevCloseFromBars = lift('prevCloseFromBars');
  const universe = liftUniverse();
  // A well-formed response: every pair carries several daily bars, which
  // is what the corrected limit and start actually make possible.
  const bars = {};
  universe.forEach((sym, i) => {
    bars[sym] = [{ c: 100 + i }, { c: 101 + i }, { c: 102 + i }];
  });
  const priced = universe.filter((sym) => prevCloseFromBars(bars[sym]) !== null);
  assert.strictEqual(
    priced.length, universe.length,
    `only ${priced.length} of ${universe.length} pairs got a previous close`,
  );
  // And the resulting change must be a real move, not 0.00%.
  universe.forEach((sym) => {
    const last = bars[sym][bars[sym].length - 1].c;
    const prev = prevCloseFromBars(bars[sym]);
    assert.notStrictEqual(last, prev, `${sym}: previous close must not equal the current close`);
  });
  console.log('G3 PASS all 12 pairs priced');
};

gates.G4 = () => {
  const out = execFileSync(
    process.execPath,
    [path.join(root, '.claude/skills/pre-ship/scripts/check-frontend.js'), path.join(root, 'index.html')],
    { encoding: 'utf8' },
  );
  assert.ok(/FRONTEND: clean/.test(out), 'pre-ship did not report clean:\n' + out);
  // The known, long-standing note is allowed; a SECOND orphan is not.
  // Zero orphans, not "only the known one". intradayToggle was cleared,
  // so this is now a strictly stronger assertion than it was.
  const orphans = /no matching element: (.+)/.exec(out);
  assert.strictEqual(orphans, null, orphans ? `orphaned lookup(s): ${orphans[1]}` : '');
  console.log('G4 PASS pre-ship clean');
};

gates.G5 = () => {
  const shouldHide = lift('shouldHideTodayPL');
  // The reported case: a fresh account, nothing open, equities closed on
  // a Sunday while crypto traded 24/7 beside it. The delta is exactly
  // zero and there is nothing stale about it.
  assert.strictEqual(shouldHide(false, false, 0), false, 'a zero delta must be shown, not hidden');
  assert.strictEqual(shouldHide(false, false, 0.004), false, 'sub-cent dust renders as $0.00 and must be shown');
  // Positive control: the protection this flag exists for must survive.
  // A real non-zero weekend delta can span two sessions and must stay
  // hidden, or this gate has simply deleted the feature.
  assert.strictEqual(shouldHide(false, false, 12.5), true, 'control: a real stale weekend gain must stay hidden');
  assert.strictEqual(shouldHide(false, false, -30), true, 'control: a real stale weekend loss must stay hidden');
  // The existing overrides must still work.
  assert.strictEqual(shouldHide(false, true, 12.5), false, 'an open crypto position means equity really is moving now');
  assert.strictEqual(shouldHide(true, false, 12.5), false, 'a normal trading day is never hidden');
  assert.strictEqual(shouldHide(null, false, 12.5), false, 'an older server build (null) must fall through, not hide');
  assert.strictEqual(shouldHide(undefined, false, 12.5), false);
  console.log('G5 PASS zero P&L is shown, stale delta still hidden');
};

function main() {
  const arg = process.argv[2];
  const names = arg ? [arg] : Object.keys(gates);
  for (const name of names) {
    if (!gates[name]) throw new Error('unknown gate: ' + name);
    gates[name]();
  }
}

try { main(); } catch (err) { console.error(err.message); process.exit(1); }
