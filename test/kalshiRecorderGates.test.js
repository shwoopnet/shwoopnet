// The recorder runs once a minute and can overlap itself: Cloud Scheduler can
// deliver twice, and a redeploy briefly runs two instances. A doubled snapshot
// would quietly corrupt every spread and cost statistic computed from this
// data, and nothing downstream would notice. These gates state the consequences.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/kalshiLib');
const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');

const gates = {};

// Two invocations a few hundred ms apart, inside the same minute, must write
// the SAME document id. Keying on "now" instead of the minute bucket is what
// would double every snapshot.
gates.G1 = () => {
  const t = Date.parse('2026-10-02T14:45:07.100Z');
  assert.strictEqual(lib.snapshotId('KXBTC15M-X', t), lib.snapshotId('KXBTC15M-X', t + 450));
  assert.notStrictEqual(lib.snapshotId('KXBTC15M-X', t), lib.snapshotId('KXBTC15M-X', t + 60000));
  assert.notStrictEqual(lib.snapshotId('KXBTC15M-X', t), lib.snapshotId('KXGOLD15M-X', t));
};

// The recorder must write by deterministic id (set), never by auto id (add).
gates.G2 = () => {
  const m = /exports\.kalshiRecorder = onSchedule\(([\s\S]*)$/.exec(fnSrc);
  assert.ok(m, 'kalshiRecorder not found');
  assert.ok(/\.doc\(kalshi\.snapshotId\(/.test(m[1]), 'snapshots must use snapshotId');
  assert.ok(!/\.add\(/.test(m[1]), 'add() would create a new doc per invocation');
};

// Retention: every snapshot carries an expiry 30 days out so storage stays bounded.
gates.G3 = () => {
  const t = Date.parse('2026-10-02T14:45:07Z');
  const d = lib.snapshotDoc({ ticker: 'T', yesBid: 0.5, yesAsk: 0.52 }, t);
  assert.strictEqual(d.expireAtMs - d.bucket, 30 * 24 * 3600 * 1000);
  assert.strictEqual(d.yesBid, 0.5);
};

// Kalshi sends dollar strings; a missing or empty price must become null,
// never 0, or an unquoted market would read as a free contract.
gates.G4 = () => {
  const m = lib.trimMarket('KXBTC15M', { ticker: 'T', close_time: 'c', floor_strike: 86140.06,
    yes_bid_dollars: '0.0950', yes_ask_dollars: '', yes_bid_size_fp: '29.77' });
  assert.strictEqual(m.yesBid, 0.095);
  assert.strictEqual(m.yesAsk, null);
  assert.strictEqual(m.yesBidSz, 29.77);
};

// Still read-only and keyless: the recorder may write only its own two
// collections and must not touch orders, users, or any credential.
gates.G5 = () => {
  const m = /exports\.kalshiRecorder = onSchedule\(([\s\S]*)$/.exec(fnSrc)[1];
  const cols = [...m.matchAll(/collection\("([^"]+)"\)/g)].map((x) => x[1]);
  assert.ok(cols.length > 0 && cols.every((c) => c === 'kalshiSnapshots' || c === 'kalshiResults'), 'unexpected collections: ' + cols);
  assert.ok(!/\/orders|Authorization|KALSHI_(API_)?KEY|method\s*:/i.test(m));
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
