'use strict';
// The read-only account view. Each gate states a consequence: it can never place or change anything, one failing
// read hides nothing else, and an unfamiliar response shape is shown instead of guessed at.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const acct = require('../functions/kalshiAccountLib');

const root = path.join(__dirname, '..');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const NOW = Date.parse('2026-10-07T17:00:00Z');
const gates = {};

function world(over = {}) {
  const calls = [];
  const reply = (status, body) => ({ status, text: async () => (typeof body === 'string' ? body : JSON.stringify(body)) });
  const fetchFn = async (url, o) => {
    const u = new URL(url);
    calls.push({ host: u.hostname, path: u.pathname, method: o.method, headers: o.headers, body: o.body });
    if (u.pathname.endsWith('/portfolio/balance')) return over.balance || reply(200, { balance: 9810, balance_breakdown: [{ balance: '98.1000', exchange_index: 0 }, { balance: '0.1000', exchange_index: 2 }] });
    if (u.pathname.endsWith('/portfolio/positions')) return over.positions || reply(200, { market_positions: [{ ticker: 'KXBTC15M-26OCT071200-00', position: 1, realized_pnl: 0 }, { ticker: 'FLAT', position: 0 }] });
    if (u.pathname.endsWith('/portfolio/fills')) return over.fills || reply(200, { fills: [{ ticker: 'KXBTC15M-26OCT071200-00', side: 'yes', action: 'buy', count: 1, yes_price: 41, is_taker: true, created_time: '2026-10-07T16:50:00Z' }] });
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  return { calls, fetchFn, reply };
}
const read = (w) => acct.readAccount({ fetchFn: w.fetchFn, keyId: 'live-key-id', pem, now: NOW });

gates.R1 = async () => {
  // Only GETs, only the production host, signed, and only the three read endpoints. Nothing can be placed.
  const w = world(); const d = await read(w);
  assert.strictEqual(w.calls.length, 3);
  assert.ok(w.calls.every((c) => c.method === 'GET' && c.host === 'external-api.kalshi.com' && c.body === undefined), JSON.stringify(w.calls.map((c) => [c.method, c.host])));
  assert.deepStrictEqual(w.calls.map((c) => c.path.replace('/trade-api/v2', '')).sort(), ['/portfolio/balance', '/portfolio/fills', '/portfolio/positions']);
  const c = w.calls[0];
  assert.ok(crypto.verify(null, Buffer.from(c.headers['KALSHI-ACCESS-TIMESTAMP'] + 'GET' + c.path), ed.publicKey, Buffer.from(c.headers['KALSHI-ACCESS-SIGNATURE'], 'base64')), 'signed over the path, query left out');
  assert.ok(!JSON.stringify(d).includes('PRIVATE') && !JSON.stringify(d).includes('live-key-id'), 'no key material in the result');
};

gates.R2 = async () => {
  // Per-shard dollars are shown as they are, with the total summed from them, and a flat position is not listed.
  const d = await read(world());
  assert.deepStrictEqual(d.balance.shards, [{ shard: 0, dollars: 98.1 }, { shard: 2, dollars: 0.1 }]);
  assert.ok(Math.abs(d.balance.totalDollars - 98.2) < 1e-9 && d.balance.totalFrom === 'sum of the shards');
  assert.deepStrictEqual(d.positions.positions.map((p) => [p.ticker, p.position]), [['KXBTC15M-26OCT071200-00', 1]]);
  assert.strictEqual(d.fills.fills[0].count, 1); assert.strictEqual(d.fills.fills[0].taker, true); assert.strictEqual(d.fills.fills[0].price, '41');
  // With no breakdown only the top-level balance exists, documented in cents, and the page is told which was used.
  const w = world({ balance: world().reply(200, { balance: 9810 }) });
  const b = (await read(w)).balance;
  assert.ok(b.shards.length === 0 && Math.abs(b.totalDollars - 98.1) < 1e-9 && /cents/.test(b.totalFrom));
};

gates.R3 = async () => {
  // One failing read hides nothing else, and a failure says what Kalshi answered.
  const w = world(); const ok = await read(w);
  const w2 = world(); const base = world();
  const bad = world({ positions: base.reply(500, { error: 'down' }) });
  const d = await read(bad);
  assert.ok(d.balance.ok && d.fills.ok && !d.positions.ok && d.positions.status === 500 && /down/.test(d.positions.error));
  const auth = await read(world({ balance: base.reply(401, { error: { code: 'authentication_error' } }) }));
  assert.ok(!auth.balance.ok && auth.balance.status === 401 && auth.positions.ok);
  assert.ok(ok.balance.ok && w2);
};

gates.R4 = async () => {
  // An unfamiliar shape is shown as its field names instead of guessed at, and nothing throws.
  const base = world();
  const odd = await read(world({
    balance: base.reply(200, { cash: '98.10', something_new: 1 }),
    positions: base.reply(200, { market_positions: 'oops' }),
    fills: base.reply(200, 'not json at all'),
  }));
  assert.ok(odd.balance.ok && odd.balance.shards.length === 0 && odd.balance.totalDollars === null && odd.balance.keys.includes('cash'));
  assert.ok(odd.positions.ok && odd.positions.positions.length === 0);
  assert.ok(!odd.fills.ok && odd.fills.status === 200);
};

const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiAccountLib.js'), 'utf8');

gates.R8 = async () => {
  // The line: fills before it are hidden (and counted), the balance becomes a change from the starting balance, and
  // nothing is erased. Without a line everything shows, flagged as having none.
  const since = Date.parse('2026-10-07T16:55:00Z');
  const base = world({ fills: world().reply(200, { fills: [
    { ticker: 'OLD', side: 'yes', action: 'sell', count: 6, yes_price: 26, is_taker: true, created_time: '2026-10-07T15:10:14Z' },
    { ticker: 'AT', side: 'yes', action: 'buy', count: 1, yes_price: 48, created_time: '2026-10-07T16:55:00Z' },
    { ticker: 'NEW', side: 'yes', action: 'buy', count: 1, yes_price: 41, created_time: '2026-10-07T16:56:00Z' },
    { ticker: 'NOTIME', side: 'yes', count: 1 },
  ] }) });
  const d = await acct.readAccount({ fetchFn: base.fetchFn, keyId: 'k', pem, now: NOW, baseline: { since, startingDollars: 97.48 } });
  assert.deepStrictEqual(d.fills.fills.map((f) => f.ticker), ['AT', 'NEW'], 'the line is inclusive, earlier and undated fills are hidden');
  assert.strictEqual(d.fills.hiddenBeforeBaseline, 2);
  assert.strictEqual(d.changeSinceStart, 0.72, '98.2 now against 97.48 at the start');
  assert.deepStrictEqual(d.baseline, { since, startingDollars: 97.48 });
  const none = await acct.readAccount({ fetchFn: world().fetchFn, keyId: 'k', pem, now: NOW });
  assert.strictEqual(none.baseline, null); assert.strictEqual(none.changeSinceStart, undefined);
  assert.strictEqual(none.fills.fills.length, 1, 'with no line nothing is hidden');
  // A malformed stored line must not hide every fill: it is ignored, and the view says it has no line.
  for (const junk of [{}, { since: 'yesterday' }, { since: null, startingDollars: 5 }]) {
    const j = await acct.readAccount({ fetchFn: world().fetchFn, keyId: 'k', pem, now: NOW, baseline: junk });
    assert.ok(j.baseline === null && j.fills.fills.length === 1, JSON.stringify(junk));
  }
  // A failed fills read or balance read does not break the baseline view.
  const bad = world({ fills: world().reply(500, 'x'), balance: world().reply(401, 'x') });
  const e = await acct.readAccount({ fetchFn: bad.fetchFn, keyId: 'k', pem, now: NOW, baseline: { since, startingDollars: 97.48 } });
  assert.ok(!e.fills.ok && !e.balance.ok && e.changeSinceStart === null);
};

gates.R9 = () => {
  // The baseline function: admin first, takes nothing from the caller, can be set exactly once, refuses without a
  // readable balance, never touches order code, and defined before the paper bot.
  const m = /exports\.kalshiLiveBaseline = onCall\(([\s\S]*?)\n\);/.exec(fnSrc);
  assert.ok(m, 'kalshiLiveBaseline not found');
  const b = m[1];
  assert.ok(b.indexOf('assertKalshiAdmin(request.auth)') > -1 && b.indexOf('assertKalshiAdmin') < b.indexOf('.create('), 'admin first');
  assert.ok(!/request\.data/.test(b), 'takes nothing from the caller: the time and balance are the server\'s own');
  assert.ok(/\.create\(doc\)/.test(b) && !/\.set\(|\.update\(|\.delete\(/.test(b), 'written with create() only, so it can never be overwritten');
  assert.ok(/existing\.exists\) return \{ set: false, alreadySet: true/.test(b), 'a second press reports the existing line');
  assert.ok(/total === null\) throw new HttpsError\("failed-precondition"/.test(b), 'no readable balance, no line');
  assert.ok(!/runLiveTest|runArmedTick|KALSHI_LIVE_ENABLED/.test(b), 'no order code, and independent of the order switch');
  assert.ok(fnSrc.indexOf('exports.kalshiLiveBaseline') < fnSrc.indexOf('exports.kalshiBot ='), 'defined before the paper bot');
  const acc = /exports\.kalshiLiveAccount = onCall\(([\s\S]*?)\n\);/.exec(fnSrc)[1];
  assert.ok(/doc\("baseline"\)\.get\(\)/.test(acc) && /baseline: snap\.exists \? snap\.data\(\) : null/.test(acc), 'the account view applies the stored line');
  // The page: first click only asks, only the confirm click sets it, admin only, and nothing but one call site.
  const i = html.indexOf("var go = document.getElementById('kalAcctStart')");
  assert.ok(i > -1, 'baseline wiring not found');
  const iife = html.slice(i, html.indexOf('})();', i));
  const first = /go\.addEventListener\('click', function\(\)\{([\s\S]*?)\}\);/.exec(iife);
  assert.ok(first && !/kalshiLiveBaseline\(/.test(first[1]) && /ask\(true\)/.test(first[1]), 'the first click only asks');
  assert.ok(/yes\.addEventListener\('click'[\s\S]*currentUserIsAdmin[\s\S]*api\.kalshiLiveBaseline\(\)/.test(iife), 'the confirm click sets it, for the admin only');
  assert.strictEqual((html.match(/api\.kalshiLiveBaseline\(\)/g) || []).length, 1, 'one call site');
  assert.ok(/kalshiLiveBaselineFn\(\{\}\)/.test(html), 'the callable is sent no arguments');
  const code = libSrc.replace(/\/\/[^\n]*/g, '');
  assert.ok(!/firebase|firestore|getFirestore|\.create\(|\.set\(/.test(code), 'the account module itself writes nothing anywhere');
};


gates.R5 = () => {
  // The module cannot place or change anything: no order path, no write method, no use of the order function.
  const code = libSrc.replace(/\/\/[^\n]*/g, '');
  assert.ok(!/events\/orders|runLiveTest|runArmedTick|liveOrderBody|"POST"|"DELETE"|"PUT"|"PATCH"|transfer/i.test(code), 'no order, write or transfer path in the account module');
  assert.deepStrictEqual([...code.matchAll(/method: "(\w+)"/g)].map((m) => m[1]), ['GET'], 'the only method named is GET');
};

gates.R6 = () => {
  // The function: admin first, takes nothing from the caller, live secrets only, and does not need the live switch.
  const m = /exports\.kalshiLiveAccount = onCall\(([\s\S]*?)\n\);/.exec(fnSrc);
  assert.ok(m, 'kalshiLiveAccount not found');
  const body = m[1];
  assert.ok(body.indexOf('assertKalshiAdmin(request.auth)') > -1 && body.indexOf('assertKalshiAdmin') < body.indexOf('readAccount'), 'admin check first');
  assert.ok(!/request\.data/.test(body), 'takes nothing from the caller');
  assert.ok(/secrets: \[KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(body), 'the live secrets');
  assert.ok(!/KALSHI_LIVE_ENABLED|runLiveTest|runArmedTick/.test(body), 'reading is independent of the order switch and never goes near order code');
  assert.ok(fnSrc.indexOf('exports.kalshiLiveAccount') < fnSrc.indexOf('exports.kalshiBot ='), 'defined before the paper bot');
  assert.ok(!/KALSHI_LIVE|kalshiAccountLib/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiBot ='))), 'the paper bot never sees the live key or the account module');
};

gates.R7 = () => {
  // The page: one button, admin only, one call per press, and nothing it renders can write.
  const i = html.indexOf("var btn = document.getElementById('kalAcctRefresh')");
  assert.ok(i > -1, 'account wiring not found');
  const iife = html.slice(i, html.indexOf("var kalshiTab = 'bot';", i));   // the whole account block, including the baseline control inside it
  assert.ok(/currentUserIsAdmin/.test(iife) && /btn\.disabled = true/.test(iife) && /api\.kalshiLiveAccount\(\)/.test(iife), 'admin only, disabled while reading');
  // Two call sites, both reads: the Refresh button, and the refresh right after the starting line is set.
  assert.strictEqual((html.match(/kalshiLiveAccount\(\)/g) || []).length, 2, 'exactly two calls in the page');
  assert.ok(!/kalshiLiveTrade|kalshiLiveArm/.test(iife), 'the account panel never calls an order or arm function');
  assert.ok(/kalshiLiveAccountFn\(\{\}\)/.test(html), 'the callable is sent no arguments');
  assert.ok(/escapeHtml\(String\(s\.shard\)\)/.test(iife) && /escapeHtml\(x\.ticker\)/.test(iife), 'values from Kalshi are escaped before they reach the page');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
