const assert = require('assert');
const fs = require('fs');
const path = require('path');

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

function liftNum(name) {
  const m = new RegExp('var ' + name + ' = (\\d+);').exec(src);
  if (!m) throw new Error(name + ' not found');
  return Number(m[1]);
}

const STREAK = liftNum('QUOTE_FAIL_STREAK_LIMIT');
const STALE = liftNum('QUOTE_STALE_MS');

// Replays a sequence of batch outcomes through the SAME streak bookkeeping
// the page runs (noteQuoteBatchResult), then asks what the header would
// say. `outcomes` is a list of booleans, one per completed batch, spaced
// `stepMs` apart.
function replay(quoteFeedStatus, outcomes, opts) {
  const o = opts || {};
  const stepMs = o.stepMs === undefined ? 45000 : o.stepMs;
  let now = 1000000;
  let streak = 0;
  let lastGoodAt = o.lastGoodAt === undefined ? null : o.lastGoodAt;
  let last = false;
  for (const ok of outcomes) {
    now += stepMs;
    if (ok) { streak = 0; lastGoodAt = now; } else { streak++; }
    last = ok;
  }
  return quoteFeedStatus({
    equitiesOk: last, cryptoOk: false,
    failStreak: streak, lastGoodAt, now,
    streakLimit: o.streakLimit === undefined ? STREAK : o.streakLimit,
    staleMs: o.staleMs === undefined ? STALE : o.staleMs,
    sources: o.sources || ['alpaca', 'alpaca'],
  });
}

const gates = {};

gates.G1 = () => {
  const quoteFeedStatus = lift('quoteFeedStatus');
  // The reported symptom: one rate-limited burst among healthy batches.
  // The feed is fine, the prices on screen are seconds old, and the
  // header must not claim the feed is down.
  const s = replay(quoteFeedStatus, [true, true, false]);
  assert.notStrictEqual(s.cls, 'fail', 'one failed batch must not report the feed as down: ' + s.text);
  // And recovery on the very next batch must read green again.
  assert.strictEqual(replay(quoteFeedStatus, [true, true, false, true]).cls, 'ok');
  // Alternating fail/succeed -- exactly the flapping pattern -- must
  // never once render red.
  const flap = [true, false, true, false, true, false, true, false];
  for (let i = 1; i <= flap.length; i++) {
    const st = replay(quoteFeedStatus, flap.slice(0, i));
    assert.notStrictEqual(st.cls, 'fail', `flapping batch ${i} reported the feed down: ${st.text}`);
  }
  console.log('G1 PASS one failed batch among healthy ones does not report the feed down');
};

gates.G2 = () => {
  const quoteFeedStatus = lift('quoteFeedStatus');
  // The protection must not have deleted the feature: a feed that is
  // genuinely dead -- every batch failing, long past the staleness
  // window -- must still be reported, or the indicator is decoration.
  const dead = replay(quoteFeedStatus, [true, false, false, false, false, false, false]);
  assert.strictEqual(dead.cls, 'fail', 'a genuinely dead feed must still be reported: ' + dead.text);
  // A feed that never came up at all (no good data since load) also
  // reports failure once the streak is reached.
  const neverUp = replay(quoteFeedStatus, [false, false, false, false, false]);
  assert.strictEqual(neverUp.cls, 'fail', 'a feed that never came up must be reported');
  console.log('G2 PASS a genuinely dead feed is still reported');
};

gates.G3 = () => {
  const quoteFeedStatus = lift('quoteFeedStatus');
  // Mutation test on the streak threshold. With the shipped limit, a
  // single failure is not a failure. Remove the hysteresis (limit 1) and
  // the SAME sequence goes red -- which is the shipped bug, and proves
  // the gate above is actually testing the threshold and not something
  // incidental.
  const seq = [true, true, false];
  assert.notStrictEqual(replay(quoteFeedStatus, seq).cls, 'fail');
  assert.strictEqual(
    replay(quoteFeedStatus, seq, { streakLimit: 1, staleMs: 0 }).cls, 'fail',
    'control: with the threshold removed this sequence MUST go red, or G1 proves nothing',
  );
  // Mutation test on the staleness half: a long fail streak whose data
  // is still fresh (batches arriving fast) is not a down feed either,
  // but with staleMs removed it would be.
  const fast = [true, false, false, false, false];
  assert.notStrictEqual(replay(quoteFeedStatus, fast, { stepMs: 2000 }).cls, 'fail',
    'a fail streak over a few seconds is not stale data');
  assert.strictEqual(replay(quoteFeedStatus, fast, { stepMs: 2000, staleMs: 0 }).cls, 'fail',
    'control: with the staleness threshold removed this MUST go red');
  console.log('G3 PASS hysteresis is load-bearing on both the streak and the staleness half');
};

gates.G4 = () => {
  const quoteFeedStatus = lift('quoteFeedStatus');
  // The middle state must not lie in either direction. It is neither
  // "Live via" (the last batch failed) nor "Sync failed" (the prices are
  // recent), and it must say what it is actually showing.
  const mid = replay(quoteFeedStatus, [true, false]);
  assert.strictEqual(mid.cls, 'warn');
  assert.ok(!/^Live via/.test(mid.text), 'a failed batch must not claim to be live: ' + mid.text);
  assert.ok(/Retrying/.test(mid.text), 'the degraded state must say it is retrying: ' + mid.text);
  // Crypto alone being up is still live, since crypto trades 24/7 --
  // the pre-existing behaviour this change must not regress.
  const cryptoOnly = quoteFeedStatus({
    equitiesOk: false, cryptoOk: true, failStreak: 9, lastGoodAt: null,
    now: 1e9, streakLimit: STREAK, staleMs: STALE, sources: [],
  });
  assert.strictEqual(cryptoOnly.cls, 'ok');
  assert.ok(/crypto/.test(cryptoOnly.text), 'must name the side that is live: ' + cryptoOnly.text);
  // And the source label must still distinguish Alpaca from a silent
  // Finnhub fallback.
  assert.ok(/Alpaca \(IEX\)/.test(replay(quoteFeedStatus, [true]).text));
  assert.ok(/Finnhub/.test(replay(quoteFeedStatus, [true], { sources: ['alpaca', 'finnhub'] }).text));
  console.log('G4 PASS the degraded state names what it is showing');
};

gates.G5 = () => {
  // Request volume must not go up. Two guards make that structural: an
  // in-flight batch is reused rather than duplicated, and a new batch is
  // refused inside a minimum interval -- so the journal listener, which
  // fires on every write to the shared account doc, can no longer start
  // an unbounded number of bursts per minute.
  const floor = liftNum('QUOTE_BATCH_MIN_INTERVAL_MS');
  assert.ok(floor > 0, 'there must be a floor between batches');
  // The loop's interval is now a named constant rather than a literal, so
  // read it by name and assert the loop really uses it -- a regex that
  // silently matched nothing would make this gate vacuous.
  const loopMs = liftNum('QUOTE_POLL_INTERVAL_MS');
  const loopSrc = src.slice(src.indexOf('function startRealQuoteLoop()'));
  assert.ok(/}, QUOTE_POLL_INTERVAL_MS\);/.test(loopSrc.slice(0, 2000)),
    'the quote loop must use the named poll interval, not a bare literal');
  assert.ok(
    floor <= loopMs,
    `the floor (${floor}ms) must not throttle the poll loop itself (${loopMs}ms)`,
  );
  const body = src.slice(src.indexOf('function fetchAllQuotes()'), src.indexOf('function runQuoteBatch()'));
  assert.ok(/quoteBatchInflight/.test(body), 'concurrent callers must reuse the in-flight batch');
  assert.ok(/lastQuoteBatchStartedAt/.test(body), 'a second batch inside the floor must be refused');
  console.log('G5 PASS duplicate quote bursts are collapsed, poll cadence unchanged');
};

// The SHIPPED constants, not just the parameters.
//
// G3 proves the hysteresis is load-bearing when quoteFeedStatus is CALLED
// with a weak threshold. It cannot see the values renderHeaderLiveStatus
// actually passes, because it supplies its own. So the shipped configuration
// -- the only one a user ever sees -- was unprotected: setting
// QUOTE_FAIL_STREAK_LIMIT back to 1 broke nothing and no test noticed.
//
// This pins the shipped numbers to the reasoning behind them. The streak must
// span more than one poll, and the staleness window must outlast several poll
// ticks, or a single unlucky burst is once again enough to call a live feed
// dead. Change these deliberately, with the argument updated -- not by
// accident.
gates.G6 = () => {
  const constant = (name) => {
    const m = new RegExp('var ' + name + ' = (\\d+);').exec(src);
    if (!m) throw new Error('shipped constant not found: ' + name);
    return Number(m[1]);
  };
  const quoteFeedStatus = lift('quoteFeedStatus');
  const streak = constant('QUOTE_FAIL_STREAK_LIMIT');
  const stale = constant('QUOTE_STALE_MS');
  const poll = constant('QUOTE_POLL_INTERVAL_MS');
  const floor = constant('QUOTE_BATCH_MIN_INTERVAL_MS');

  assert.ok(streak >= 2, 'a single failed batch must never be enough to call the feed down (got ' + streak + ')');
  assert.ok(stale > poll * 2, 'the staleness window must outlast more than two poll ticks, or fresh prices get called stale (stale ' + stale + ' vs poll ' + poll + ')');
  assert.ok(floor < poll, 'the dedupe floor must be shorter than the poll interval, or it would slow the loop it is meant to leave alone');
  assert.ok(floor > 0, 'a zero floor collapses no duplicate bursts at all');

  // And the shipped values, fed through the real function, must actually
  // survive a flap. This is the consequence, not the constants themselves.
  const flap = [false, true, false, true, false, false, true, false];
  const out = replay(quoteFeedStatus, flap, { streakLimit: streak, staleMs: stale });
  assert.notStrictEqual(out.cls, 'fail',
    'with the SHIPPED thresholds, an alternating flap must never report the feed down');
  console.log('G6 PASS the shipped thresholds, not just the parameters, survive a flap');
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
