// The Activity Log's filters said one thing and did another.
//
// The dropdown listed a "Scan" row reading "Shown" while scans were in fact
// hidden -- isRoutineScan drops an ordinary scan independently of the group
// filters, so the toggle claimed to control something it did not. And when
// every entry was filtered out, the card said "Nothing logged yet" over a
// header reading "130 hidden": two statements about the same log that could
// not both be true.
//
// Both are the same failure -- a control or a message that describes a state
// the app is not in. These gates state the consequences.

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

// No control may claim to govern the routine-scan collapse, because none
// does. Listing one is what produced "Shown" over a card with no scans in it.
gates.G1 = () => {
  const m = /var ACTIVITY_FILTER_GROUPS = \[([\s\S]*?)\];/.exec(src);
  assert.ok(m, 'ACTIVITY_FILTER_GROUPS not found');
  assert.ok(!/cycle_summary/.test(m[1]),
    'the Scan row must not be offered: isRoutineScan hides scans regardless of it');
  // The groups that DO control something must survive -- removing the lie
  // must not quietly remove the working filters with it.
  ['sent', 'skipped', 'error', 'position_drift'].forEach((k) => {
    assert.ok(new RegExp("key:'" + k + "'").test(m[1]), 'filter group must remain: ' + k);
  });
  console.log('G1 PASS no filter row claims to control the scan collapse');
};

// Only an abnormal scan is worth a row. This is the behaviour the removed
// control was contradicting, so it has to be pinned or the fix is unmoored.
gates.G2 = () => {
  const isRoutineScan = lift('isRoutineScan');
  const scan = (text) => ({ type: 'cycle_summary', text });
  assert.strictEqual(isRoutineScan(scan('Scanned 16 symbols (16 fetched), no setups.')), true,
    'an ordinary complete scan is routine and must not take a row');
  assert.strictEqual(isRoutineScan(scan('Scanned 16 symbols (12 fetched), no setups.')), false,
    'a scan that fetched fewer symbols than it meant to is worth reading');
  assert.strictEqual(isRoutineScan(scan('Cycle failed: Alpaca 500')), false,
    'a scan naming a failure is worth reading');
  assert.strictEqual(isRoutineScan({ type: 'sent', text: 'Scanned 16 symbols (16 fetched)' }), false,
    'only a cycle_summary can be a routine scan, whatever its text says');
  console.log('G2 PASS only abnormal scans survive the collapse');
};

// A stale persisted hide must not strand abnormal scans invisible with no
// control left to undo it.
gates.G3 = () => {
  const stored = { cycle_summary: true, skipped: true };
  const store = {
    getItem: () => JSON.stringify(stored),
    setItem: () => {},
  };
  // loadActivityLogFilterPrefs assigns to a closed-over name rather than
  // returning, so it is rebuilt inside a wrapper that hands the result back.
  const fn = new Function('window', 'saveActivityLogFilterPrefs',
    'var activityLogHiddenGroups = {};' +
    src.slice(src.indexOf('function loadActivityLogFilterPrefs()'),
      src.indexOf('function saveActivityLogFilterPrefs()')) +
    'loadActivityLogFilterPrefs(); return activityLogHiddenGroups;');
  const out = fn({ localStorage: store }, () => {});
  assert.strictEqual(out.cycle_summary, undefined,
    'a stored Scan hide must be dropped, or abnormal scans stay hidden with no control to restore them');
  assert.strictEqual(out.skipped, true,
    'every OTHER stored preference must survive the migration');
  console.log('G3 PASS a stale Scan hide is dropped, other preferences are kept');
};

// "Nothing logged yet" over N filtered entries is the reassuring reading of
// an ambiguous state, and it is the wrong one.
gates.G4 = () => {
  const body = src.slice(src.indexOf('function renderActivityLog()'),
    src.indexOf('function renderActivityLog()') + 4000);
  assert.ok(/currentAccountLog\.length > 0/.test(body),
    'the empty branch must distinguish an empty log from a filtered one');
  assert.ok(/are hidden by the filters above/.test(body),
    'a fully-filtered log must say so rather than claiming nothing was logged');
  // The genuinely-empty case must still reach the original message.
  assert.ok(/emptyEl\.removeAttribute\('hidden'\)/.test(body),
    'a genuinely empty log must still show the "nothing logged yet" state');
  console.log('G4 PASS a filtered-empty log is not reported as an empty one');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
