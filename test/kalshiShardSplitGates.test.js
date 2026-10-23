'use strict';
// The automatic shard split (Oct 23, 2026, the owner, after losing money moving funds between shards by hand). Consequences: the money split is set ONCE to a fixed target in code, nothing from the caller can change it, it is
// admin only, it moves no money itself and places no order, and a refusal is reported, never retried.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const gates = {};

const stub = (opts = {}) => {
  const calls = [];
  let stored = opts.initial || [];
  const fetchFn = async (url, o) => {
    calls.push({ url, method: o.method, body: o.body ? JSON.parse(o.body) : null });
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (!url.endsWith('/portfolio/target_balance_allocation')) throw new Error('unexpected ' + url);
    if (o.method === 'POST') { if (opts.refuse) return reply(opts.refuse, { error: 'no' }); stored = JSON.parse(o.body).allocations; return reply(200, {}); }
    if (opts.readStatus) return reply(opts.readStatus, {});
    return reply(200, { allocations: stored, resting_margin_reservation: {} });
  };
  return { fetchFn, calls };
};

gates.SP1 = async () => {
  assert.deepStrictEqual(live.SHARD_SPLIT, [{ exchange_index: 0, percent: 20 }, { exchange_index: 2, percent: 80 }], 'a fixed split: 20% on shard 0 (gold and the forex probes), 80% on shard 2 (crypto and natural gas)');
  assert.strictEqual(live.SHARD_SPLIT.reduce((a, x) => a + x.percent, 0), 100, 'percentages total 100, as Kalshi requires');
  const w = stub();
  const r = await live.applyShardSplit({ fetchFn: w.fetchFn, keyId: 'k', pem, nowMs: 1700000000000 });
  const posts = w.calls.filter((c) => c.method === 'POST');
  assert.ok(r.ok && posts.length === 1, 'sent once, never retried');
  assert.deepStrictEqual(posts[0].body, { allocations: live.SHARD_SPLIT }, 'the body is the fixed split and nothing else');
  assert.deepStrictEqual(r.allocations, live.SHARD_SPLIT, 'and the answer is read back from Kalshi');
  const read = await live.readShardSplit({ fetchFn: stub({ initial: [] }).fetchFn, keyId: 'k', pem, nowMs: 1700000000000 });
  assert.ok(read.ok && read.allocations.length === 0, 'no split set reads as an empty list');
};
gates.SP2 = async () => {
  const w = stub({ refuse: 403 });
  const r = await live.applyShardSplit({ fetchFn: w.fetchFn, keyId: 'k', pem, nowMs: 1700000000000 });
  assert.ok(r.ok === false && r.status === 403 && /did not accept/.test(r.reason), 'a refusal is reported plainly: ' + JSON.stringify(r));
  assert.strictEqual(w.calls.filter((c) => c.method === 'POST').length, 1, 'a refused POST is not retried');
  const bad = await live.readShardSplit({ fetchFn: stub({ readStatus: 500 }).fetchFn, keyId: 'k', pem, nowMs: 1700000000000 });
  assert.ok(bad.ok === false, 'an unreadable split is a failure, not an empty one');
};
gates.SP3 = () => {
  const f = fnSrc.slice(fnSrc.indexOf('exports.kalshiShardSplit'), fnSrc.indexOf('exports.kalshiFlattenAll'));
  assert.ok(/assertKalshiAdmin\(request\.auth\)/.test(f), 'admin only');
  assert.ok(/request\.data && request\.data\.action === "apply"/.test(f) && !/request\.data\.(percent|allocations|shard|amount)/.test(f), 'the only thing taken from the caller is read or apply: never a percentage or an amount');
  assert.ok(/live\.applyShardSplit\(args\)/.test(f) && !/transfer|orders|flatten/i.test(f.replace(/\/\/.*$/gm, '')), 'it sets the target and nothing else: no transfer, no order');
  const lib = libSrc.slice(libSrc.indexOf('const SHARD_SPLIT'), libSrc.indexOf('module.exports'));
  assert.ok(!/portfolio\/orders|intra_exchange_instance_transfer/.test(lib), 'the library part moves no money itself and places no order');
  const page = html.slice(html.indexOf("var msg = document.getElementById('kalShardMsg')"), html.indexOf("document.getElementById('kalOrdersCopy')"));
  assert.ok(/kalshiShardSplit\(action\)/.test(page) && /kalshiShardSplitFn\(\{ action: action === 'apply' \? 'apply' : 'read' \}\)/.test(html), 'the page sends only read or apply: the call carries nothing else');
  assert.ok(/Tap again to set 20% \/ 80%/.test(page), 'setting it takes two taps');
};

gates.SP4 = () => {
  const f = fnSrc.slice(fnSrc.indexOf('exports.kalshiShardSplit'), fnSrc.indexOf('exports.kalshiFlattenAll'));
  assert.ok(/try \{\s*ensureDefaultAdminApp\(\);[\s\S]*?KALSHI_LIVE_PRIVATE_KEY\.value\(\)[\s\S]*?out = apply \? await live\.applyShardSplit\(args\)/.test(f) && /catch \(e\)/.test(f), 'a throw inside the split call is caught and reported with its own reason, not the page\'s blank "internal"');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
