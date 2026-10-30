'use strict';
// The owner's phone alerts stopped after a redeploy from a fresh clone (Oct 30, 2026). deploy-push.sh made a NEW phone alert key whenever it failed to READ the old one for any reason, and a new key orphans every subscribed phone. A new key may only be made when the secret is truly missing.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');
const sh = fs.readFileSync(path.join(__dirname, '..', 'functions', 'deploy-push.sh'), 'utf8');
const gates = {};

// Run only the key block of the real script against a fake firebase CLI and a fake node, so no network and no real key is touched.
function runKeyBlock(accessBehaviour) {
  const start = sh.indexOf('# The phone alert key: made once.'), end = sh.indexOf('# The bot buys about 6 minutes');
  assert.ok(start > 0 && end > start, 'the key block is found');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pushkey-'));
  const log = path.join(dir, 'calls.log');
  fs.writeFileSync(path.join(dir, 'fakefb'), '#!/bin/bash\necho "$@" >> "' + log + '"\nif [[ "$1" == "functions:secrets:access" ]]; then\n' + accessBehaviour + '\nfi\nexit 0\n', { mode: 0o755 });
  fs.writeFileSync(path.join(dir, 'node'), '#!/bin/bash\nprintf "fakekey"\n', { mode: 0o755 });
  const script = 'set -euo pipefail\nPROJECT=shwoopnet\nFB=("' + path.join(dir, 'fakefb') + '")\n' + sh.slice(start, end) + '\necho KEYBLOCK_DONE\n';
  const r = spawnSync('bash', ['-c', script], { env: Object.assign({}, process.env, { PATH: dir + ':' + process.env.PATH, DRY_RUN: '' }), encoding: 'utf8' });
  const calls = fs.existsSync(log) ? fs.readFileSync(log, 'utf8') : '';
  return { status: r.status, out: r.stdout + r.stderr, madeKey: /functions:secrets:set/.test(calls) };
}
gates.K1 = () => {
  const r = runKeyBlock('echo "secretvalue"; exit 0');
  assert.strictEqual(r.status, 0, 'an existing key is kept without error');
  assert.ok(!r.madeKey && /keeping it/.test(r.out), 'no new key is made when the old one can be read');
  assert.ok(!/secretvalue/.test(r.out), 'the key value is never printed');
};
gates.K2 = () => {
  const r = runKeyBlock('echo "Error: Secret [KALSHI_PUSH_VAPID_PRIVATE] not found" >&2; exit 1');
  assert.strictEqual(r.status, 0, 'a truly missing key is created');
  assert.ok(r.madeKey && /was created/.test(r.out), 'the new key is stored only when the secret does not exist');
};
gates.K3 = () => {
  const r = runKeyBlock('echo "Error: getaddrinfo ECONNRESET network error" >&2; exit 1');
  assert.notStrictEqual(r.status, 0, 'a failed read that is not "missing" stops the deploy');
  assert.ok(!r.madeKey, 'it must NOT make a new key: that would orphan every subscribed phone');
  assert.ok(/STOP: could not read the phone alert key/.test(r.out), 'it says why it stopped');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
