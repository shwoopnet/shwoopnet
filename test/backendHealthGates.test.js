'use strict';
// Gates for the Backend Status card's reconcile-health row.
//
// WHY THIS EXISTS. The heartbeat used to be the whole story, so a backend
// whose reconcile pass had been throwing for hours -- the only thing that
// verifies protective orders, submits them, and runs the end-of-day
// flatten -- still rendered as "Backend online". These assert the
// consequence of getting that wrong, not the mechanism:
//   1. a Firestore Timestamp must not be read as Invalid Date (the exact
//      shape that silently disabled trailing stops in shwoop-server), and
//   2. a long-dead reconcile pass must not render as healthy, while
//   3. an account whose backend predates the fields must not render as
//      failing.
//
// The functions are lifted out of index.html with new Function, per
// CLAUDE.md, because there is no build step to import from.

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  // Brace-match from the opening brace of the declaration.
  let i = html.indexOf('{', start);
  let depth = 0;
  for (let j = i; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

// Constants the state machine reads, taken from the file itself so the
// test cannot drift from the thresholds actually shipped.
function liftConst(name) {
  const m = new RegExp('var ' + name + ' = ([^;]+);').exec(html);
  assert.ok(m, 'could not find ' + name);
  return m[1];
}

const harness = `
  var RECONCILE_DEGRADED_AFTER_MS = ${liftConst('RECONCILE_DEGRADED_AFTER_MS')};
  var RECONCILE_FAILING_AFTER_MS = ${liftConst('RECONCILE_FAILING_AFTER_MS')};
  var RECONCILE_FAILING_STREAK_MS = ${liftConst('RECONCILE_FAILING_STREAK_MS')};
  var backendReconcileLastSuccessAt = null;
  var backendReconcileFailingSince = null;
  var backendReconcileLastError = null;
  function escapeHtml(s){ return String(s); }
  ${lift('formatAgo')}
  ${lift('firestoreMillis')}
  ${lift('reconcileHealthState')}
  return {
    firestoreMillis: firestoreMillis,
    state: function(fields, nowMs){
      backendReconcileLastSuccessAt = fields.lastSuccess === undefined ? null : fields.lastSuccess;
      backendReconcileFailingSince = fields.failingSince === undefined ? null : fields.failingSince;
      backendReconcileLastError = fields.lastError === undefined ? null : fields.lastError;
      return reconcileHealthState(nowMs);
    }
  };
`;
const api = new Function(harness)();

const NOW = Date.UTC(2026, 8, 2, 15, 0, 0);
const MIN = 60 * 1000;

// ---- 1. Firestore Timestamp shapes ----------------------------------
// The consequence: if any of these reads as NaN, a healthy backend and a
// dead one produce the same render, which is the bug this card exists to
// end.
const target = NOW - 3 * MIN;
assert.strictEqual(api.firestoreMillis(target), target, 'epoch number');
assert.strictEqual(api.firestoreMillis(new Date(target)), target, 'Date');
assert.strictEqual(api.firestoreMillis(new Date(target).toISOString()), target, 'ISO string');
assert.strictEqual(
  api.firestoreMillis({ _seconds: Math.floor(target / 1000), _nanoseconds: 0 }),
  target, 'JSON-shaped Admin SDK Timestamp'
);
assert.strictEqual(
  api.firestoreMillis({ seconds: Math.floor(target / 1000), nanoseconds: 0 }),
  target, 'JSON-shaped web SDK Timestamp'
);
assert.strictEqual(
  api.firestoreMillis({ toMillis: function(){ return target; } }),
  target, 'real Timestamp instance'
);
assert.ok(Number.isNaN(api.firestoreMillis(null)), 'null is not datable');
assert.ok(Number.isNaN(api.firestoreMillis({})), 'an empty object is not datable');
assert.ok(Number.isNaN(api.firestoreMillis('not a date')), 'garbage is not datable');

// A Timestamp must produce the SAME verdict as the equivalent number.
// This is the assertion that fails if anyone re-introduces new Date(obj).
const tsFailing = { _seconds: Math.floor((NOW - 47 * MIN) / 1000), _nanoseconds: 0 };
assert.strictEqual(api.state({ lastSuccess: tsFailing }, NOW).level, 'failing',
  'a 47-minute-old Timestamp must read as failing, not as unknown/healthy');

// ---- 2. Absent fields are UNKNOWN, never failing ---------------------
assert.strictEqual(api.state({}, NOW).level, 'unknown',
  'a backend that has not deployed the new fields must not render as failing');
assert.strictEqual(api.state({ lastSuccess: undefined, failingSince: undefined }, NOW).level, 'unknown');

// ---- 3. The healthy / degraded / failing bands -----------------------
assert.strictEqual(api.state({ lastSuccess: NOW - 40 * 1000 }, NOW).level, 'ok');
// One slow minute is NOT degraded -- alerting on that is how a signal
// gets ignored.
assert.strictEqual(api.state({ lastSuccess: NOW - 90 * 1000 }, NOW).level, 'ok',
  'a single missed minute must stay healthy');
assert.strictEqual(api.state({ lastSuccess: NOW - 8 * MIN }, NOW).level, 'degraded');
assert.strictEqual(api.state({ lastSuccess: NOW - 47 * MIN }, NOW).level, 'failing');
assert.ok(/47 minutes/.test(api.state({ lastSuccess: NOW - 47 * MIN }, NOW).label),
  'the failing label must carry the duration, not just say "failing"');

// ---- 4. The backend's own failing flag beats a stale-ish success -----
// A fresh success stamp plus an active failure run must still escalate:
// the flag is the fresher fact.
assert.strictEqual(
  api.state({ lastSuccess: NOW - 30 * 1000, failingSince: NOW - 2 * MIN }, NOW).level,
  'degraded', 'a short failure run is degraded even with a recent success');
assert.strictEqual(
  api.state({ lastSuccess: NOW - 12 * MIN, failingSince: NOW - 12 * MIN }, NOW).level,
  'failing', 'a failure run past the server alert threshold is failing');
// Matches shwoop-server FAILURE_ALERT_AFTER_MS: the app must not say
// "fine" while the owner is holding the SMS that says otherwise.
assert.strictEqual(api.state({ failingSince: NOW - 10 * MIN }, NOW).level, 'failing');
assert.strictEqual(api.state({ failingSince: NOW - 9 * MIN }, NOW).level, 'degraded');

// ---- 5. Recovery ----------------------------------------------------
// The backend clears reconcileFailingSince on success; once cleared the
// card must go green again, or a single blip would look permanent.
assert.strictEqual(api.state({ lastSuccess: NOW - 20 * 1000, failingSince: null }, NOW).level, 'ok');

// ---- 6. The error text is escaped -----------------------------------
assert.ok(/Last error/.test(api.state({ failingSince: NOW - 20 * MIN, lastError: 'boom' }, NOW).sub));

// ---- 7. The row is actually WIRED INTO the card ----------------------
// Everything above tests the state machine in isolation, and a state
// machine nobody renders is exactly as useless as no state machine: the
// card would go back to saying "Backend online" while nothing reconciles.
// Mutation-testing found this gap -- deleting the row from
// renderBackendStatus passed every other check in the repo -- so it is
// asserted at the source level, which is the only level available
// without a build step.
const renderSrc = lift('renderBackendStatus');
assert.ok(/reconcileHealthState\(/.test(renderSrc),
  'renderBackendStatus must call reconcileHealthState -- the reconcile row is gone from the card');
assert.ok(/backend-pulse-label[^]*rec\.label/.test(renderSrc),
  'the reconcile row must render its label into the card body');
assert.ok(/headMeta[^]*Not reconciling/.test(renderSrc),
  'a failing reconcile pass must also change the card header, or the collapsed card still lies');

console.log('backendHealthGates: all assertions passed');
