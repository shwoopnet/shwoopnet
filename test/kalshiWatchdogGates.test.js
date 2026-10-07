// The outside watchdog for the live arm: a dead-man's switch. Silence is the alarm.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { pingsFor, sendAll } = require('../functions/kalshiWatchdogLib');

const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const URL_ = 'https://hc-ping.com/abc';
const gates = {};

// Not configured means not sent: the arm check must behave exactly as before.
gates.W1 = () => {
  assert.deepStrictEqual(pingsFor({ base: '', ok: true }), []);
  assert.deepStrictEqual(pingsFor({ base: undefined, ok: false }), []);
};

// A healthy run keeps the switch alive; a failed run must NOT, or a broken function would look healthy.
gates.W2 = () => {
  assert.deepStrictEqual(pingsFor({ base: URL_ + '///', ok: true }).map((x) => x.url), [URL_], 'trailing slashes are trimmed');
  const bad = pingsFor({ base: URL_, ok: false, reason: 'markets down' });
  assert.deepStrictEqual(bad.map((x) => x.url), [URL_ + '/fail'], 'a failure sends only the failure ping, never the success one');
};

// A broken watchdog must never break the arm check: a rejected or refused ping is only logged.
gates.W3 = async () => {
  const logs = [];
  await sendAll(async () => { throw new Error('network down'); }, [{ url: URL_, body: 'x' }], (m) => logs.push(m));
  await sendAll(async () => ({ ok: false, status: 500 }), [{ url: URL_, body: 'x' }], (m) => logs.push(m));
  assert.strictEqual(logs.length, 2, JSON.stringify(logs));
};

// Wired into the live arm, after the check runs (so a failed run sends nothing good), and the failure still surfaces.
gates.W4 = () => {
  const arm = fnSrc.slice(fnSrc.indexOf('exports.kalshiLiveArmed = onSchedule('), fnSrc.indexOf('exports.kalshiBookRecorder'));
  assert.ok(arm.indexOf('runArmedTick(') > -1 && arm.indexOf('runArmedTick(') < arm.indexOf('watchdog.sendAll('), 'ping only after the check completes');
  assert.ok(/ok: !failure/.test(arm) && /if \(failure\) throw failure;/.test(arm), 'a failed run reports failure and is still thrown to the scheduler');
  assert.ok(/defineString\("KALSHI_WATCHDOG_URL", \{ default: "" \}\)/.test(fnSrc), 'optional, empty by default');
  assert.deepStrictEqual([...fnSrc.matchAll(/exports\.(\w+) = onSchedule\(/g)].map((x) => x[1]), ['kalshiLiveArmed', 'kalshiBookRecorder']);
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
