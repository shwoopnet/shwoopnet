// Notifications were not populating, and the app said nothing about it.
//
// Two separate copies of the same browser-notification code existed (the
// trading-paused alert and the position-closed alert), identical apart from
// the strings they built. Both asked for permission LAZILY, at the moment an
// alert fired, from inside a Firestore snapshot callback -- which is not a
// user gesture, so Safari refuses the request outright and a prompt raised
// while nobody is looking at the tab gets dismissed. Permission therefore
// stayed at 'default' forever. And when it was not granted, both copies
// simply returned: nothing in the app ever said notifications were switched
// off, so "your browser is blocking these" and "nothing has happened worth
// telling you about" were the same screen.
//
// These gates state the consequences: one implementation, permission asked
// only from a real click, and an off channel that says it is off.

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

// One implementation. Two copies is how the last drift happened -- the
// paused alert grew a fix (naming WHICH strategy paused) that the
// position-closed copy never received, and nobody noticed because the two
// looked interchangeable.
gates.G1 = () => {
  const constructions = src.match(/new Notification\(/g) || [];
  assert.strictEqual(constructions.length, 1,
    'exactly one place may construct a Notification; found ' + constructions.length +
    ' -- a second copy is a fix that will land on only one of them');
  assert.ok(/function showBrowserNotification\(/.test(src),
    'the one implementation must be the shared helper');
  // Both callers must actually go through it, or "one implementation" is
  // true only because the other caller stopped notifying at all.
  ['notifyTradingPausedViaBrowser', 'notifyPositionClosedViaBrowser'].forEach((fn) => {
    const body = src.slice(src.indexOf('function ' + fn + '('), src.indexOf('function ' + fn + '(') + 700);
    assert.ok(/showBrowserNotification\(/.test(body), fn + ' must route through showBrowserNotification');
  });
  console.log('G1 PASS one notification implementation, both alerts routed through it');
};

// Permission is asked for from a click, and from nowhere else. Asking from
// a snapshot callback is what made the answer permanently 'default'.
gates.G2 = () => {
  // Counts real call sites, not the prose explaining why there is only one.
  const asks = src.match(/Notification\.requestPermission\(/g) || [];
  assert.strictEqual(asks.length, 1,
    'permission may be requested from exactly one place; found ' + asks.length);
  const at = src.indexOf('Notification.requestPermission(');
  // The one call site must sit inside the Settings button's click handler.
  const before = src.slice(Math.max(0, at - 1600), at);
  assert.ok(/browserNotifyBtn\.addEventListener\('click'/.test(before),
    'the permission request must be inside the Settings button click handler -- a request without a user gesture is refused outright by Safari and dismissed everywhere else');
  const helper = src.slice(src.indexOf('function showBrowserNotification('),
    src.indexOf('function showBrowserNotification(') + 500);
  assert.ok(!/Notification\.requestPermission\(/.test(helper),
    'the send path must never prompt: it fires from a Firestore snapshot callback');
  console.log('G2 PASS permission is requested from a real click and nowhere else');
};

// The send path must not claim delivery it did not achieve, and must not
// throw into the render that triggered it.
gates.G3 = () => {
  const calls = [];
  function FakeNotification(title, opts) { calls.push({ title, body: opts && opts.body }); }
  const run = (perm) => {
    const showBrowserNotification = lift('showBrowserNotification', {
      refreshBrowserNotifyState: () => perm,
      Notification: FakeNotification,
      console,
    });
    return showBrowserNotification('T', 'B');
  };
  assert.strictEqual(run('granted'), true, 'a granted permission must actually deliver');
  assert.strictEqual(calls.length, 1, 'exactly one notification for one granted send');
  assert.strictEqual(run('denied'), false, 'a denied permission must report NOT delivered, not silently "done"');
  assert.strictEqual(run('default'), false, 'an unanswered permission must report NOT delivered');
  assert.strictEqual(run('unsupported'), false, 'a browser without Notification must report NOT delivered');
  assert.strictEqual(calls.length, 1, 'nothing may be delivered while permission is not granted');

  // A browser that throws on construction (some do, for a page in a state
  // it dislikes) must not take down the caller.
  const throwing = lift('showBrowserNotification', {
    refreshBrowserNotifyState: () => 'granted',
    Notification: function () { throw new Error('nope'); },
    console: { error: () => {} },
  });
  assert.strictEqual(throwing('T', 'B'), false, 'a failed construction reports false rather than throwing');
  console.log('G3 PASS the send path reports delivery honestly and never throws');
};

// An off channel says it is OFF. This is the whole bug as experienced: no
// notifications and no explanation are indistinguishable from nothing
// having happened.
gates.G4 = () => {
  const m = /var BROWSER_NOTIFY_TEXT = \{([\s\S]*?)\n  \};/.exec(src);
  assert.ok(m, 'BROWSER_NOTIFY_TEXT not found');
  const table = m[1];
  ['unsupported', 'granted', 'denied', "'default'"].forEach((k) => {
    assert.ok(table.indexOf(k + ':') > -1, 'every permission state must have wording: ' + k);
  });
  const denied = /denied: \{([\s\S]*?)\},/.exec(table)[1];
  assert.ok(/Off/.test(denied), 'a blocked permission must be described as off, not left blank');
  assert.ok(/site settings/i.test(denied),
    'a blocked permission cannot be re-prompted from script, so the wording must say where to fix it');
  const dflt = /'default': \{([\s\S]*?)\}/.exec(table)[1];
  assert.ok(/Off/.test(dflt), 'a never-enabled permission must be described as off');
  assert.ok(/renderBrowserNotifySetting/.test(src) && /browserNotifyDesc\.textContent/.test(src),
    'the wording must actually be written into the Settings row');
  assert.ok(/id="browserNotifyDesc"/.test(src) && /id="browserNotifyBtn"/.test(src),
    'the Settings row the renderer targets must exist in the markup');
  console.log('G4 PASS every not-granted state is stated in words, not left silent');
};

// State is re-read at every send. Permission can be revoked from the
// address bar with no event fired, so a value cached at page load would let
// the Settings row keep claiming "On" over a channel that is dead.
gates.G5 = () => {
  const helper = src.slice(src.indexOf('function showBrowserNotification('),
    src.indexOf('function showBrowserNotification(') + 500);
  assert.ok(/refreshBrowserNotifyState\(\)/.test(helper),
    'every send must re-read the live permission rather than trust a cached one');
  const refresh = src.slice(src.indexOf('function refreshBrowserNotifyState('),
    src.indexOf('function refreshBrowserNotifyState(') + 400);
  assert.ok(/renderBrowserNotifySetting/.test(refresh),
    'a re-read must update what the Settings row says, or the row goes stale exactly when it matters');
  console.log('G5 PASS permission state is re-read per send and re-rendered');
};

// The priority lane's acknowledgement lives in localStorage forever, so an
// over-broad key would suppress the "Needs You" lane permanently and look
// exactly like the reported symptom. It must be keyed per entry id and
// nothing else, and nothing may bulk-acknowledge.
gates.G7 = () => {
  const render = src.slice(src.indexOf('function renderPriorityLog()'),
    src.indexOf('function renderPriorityLog()') + 2500);
  assert.ok(/!acknowledgedPriorityIds\[entry\.id\]/.test(render),
    'the lane must suppress only the exact entry id that was acknowledged');
  const writes = src.match(/acknowledgedPriorityIds\[[^\]]*\] *=/g) || [];
  assert.deepStrictEqual(writes, ['acknowledgedPriorityIds[btn.dataset.ackId] ='],
    'only the per-row "Mark done" button may acknowledge; a bulk write would empty the lane for good');
  console.log('G7 PASS acknowledgement is per entry id and cannot suppress the lane wholesale');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
