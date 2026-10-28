// The nightly order report: read only, behind one secret token, and it never carries an order id or a credential.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const lib = require('../functions/kalshiReportLib');
const gates = {};

const NOW = Date.parse('2026-10-29T00:00:00Z');
const ord = (o) => Object.assign({ ticker: 'KXGOLD15M-26OCT28-T1', side: 'yes', fillCount: 1, avgFill: 0.93, status: 'filled', settled: true, result: 'yes', settledPnl: 0.05, ts: NOW - 3600000, entryLead: '6m', orderId: 'SECRET-ORDER-ID', clientOrderId: 'L1-SECRET' }, o);
const call = async (handler, req) => {
  const out = { code: null, body: null, headers: {} };
  const res = { set: (k, v) => { out.headers[k] = v; }, status: (c) => { out.code = c; return res; }, json: (b) => { out.body = b; } };
  await handler(Object.assign({ method: 'GET', headers: {}, query: {} }, req), res);
  return out;
};
const TOKEN = 'a'.repeat(32);
const handler = (orders, token) => lib.makeReportHandler({ getToken: () => (token === undefined ? TOKEN : token), now: () => NOW, readOrders: async () => orders });

// R1: the report counts wins, losses, net and profit factor the way the page does, and open orders have no result.
gates.R1 = () => {
  const r = lib.buildReport([
    ord({ settledPnl: 0.05 }), ord({ settledPnl: 0.05 }), ord({ settledPnl: -0.9, result: 'no' }),
    ord({ settled: false, settledPnl: null, result: null }), ord({ status: 'no fill', fillCount: 0 }),
    ord({ ts: NOW - 99 * 3600000, settledPnl: -5 }),   // outside the window
  ], NOW, 24, false);
  assert.deepStrictEqual([r.total.filled, r.total.settled, r.total.won, r.total.lost, r.total.open, r.total.noFill], [4, 3, 2, 1, 1, 1]);
  assert.strictEqual(r.total.net, -0.8);
  assert.strictEqual(r.total.profitFactor, 0.11, 'gross win 0.10 over gross loss 0.90');
  assert.strictEqual(lib.buildReport([ord({})], NOW, 24, false).total.profitFactor, null, 'no loss means no profit factor, never infinity');
  assert.deepStrictEqual(Object.keys(r.byMarket), ['KXGOLD15M'], 'split by market');
  assert.ok(r.byEntryLead['6m'], 'and by entry lead');
};

// R2: nothing that identifies an order or the account ever leaves, even in the per-order rows.
gates.R2 = () => {
  const r = lib.buildReport([ord({})], NOW, 24, true);
  const text = JSON.stringify(r);
  assert.ok(!/SECRET-ORDER-ID|L1-SECRET|orderId|clientOrderId/.test(text), 'no order id or client order id');
  assert.strictEqual(r.orders.length, 1);
  assert.deepStrictEqual(Object.keys(r.orders[0]).sort(), ['avgFill', 'count', 'entryLead', 'result', 'settledPnl', 'side', 'status', 'ticker', 'ts']);
  assert.ok(!('orders' in lib.buildReport([ord({})], NOW, 24, false)), 'rows only on request');
};

// R3: closed without the right token, and closed when no token is configured.
gates.R3 = async () => {
  assert.strictEqual((await call(handler([ord({})]), {})).code, 401, 'no header');
  assert.strictEqual((await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + 'b'.repeat(32) } })).code, 401, 'wrong token');
  assert.strictEqual((await call(handler([ord({})], ''), { headers: { authorization: 'Bearer ' } })).code, 401, 'no token configured: closed, never open');
  assert.strictEqual((await call(handler([ord({})], 'short'), { headers: { authorization: 'Bearer short' } })).code, 401, 'a short token is refused');
  const ok = await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + TOKEN } });
  assert.strictEqual(ok.code, 200);
  assert.strictEqual(ok.headers['Cache-Control'], 'no-store');
  const bad = await call(handler([ord({})]), { headers: { authorization: 'Bearer ' + 'b'.repeat(32) } });
  assert.ok(!JSON.stringify(bad.body).includes(TOKEN), 'the secret is never echoed');
};

// R4: GET only; a read failure says nothing about why; the window is bounded.
gates.R4 = async () => {
  assert.strictEqual((await call(handler([]), { method: 'POST', headers: { authorization: 'Bearer ' + TOKEN } })).code, 405);
  const boom = lib.makeReportHandler({ getToken: () => TOKEN, now: () => NOW, readOrders: async () => { throw new Error('Firestore says SECRET internals'); } });
  const r = await call(boom, { headers: { authorization: 'Bearer ' + TOKEN } });
  assert.strictEqual(r.code, 500);
  assert.ok(!/SECRET|Firestore/.test(JSON.stringify(r.body)), 'the error text is not echoed');
  const big = await call(handler([]), { headers: { authorization: 'Bearer ' + TOKEN }, query: { hours: '99999999' } });
  assert.strictEqual(big.body.hours, lib.MAX_HOURS, 'the window is capped');
};

// R5: the function holds no Kalshi key, sends nothing to Kalshi, writes nothing, and the deploy script keeps an existing token.
gates.R5 = () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiReportLib.js'), 'utf8');
  assert.ok(!/KALSHI_LIVE|liveRequest|fetch\(|https?:\/\/|\.set\(\{|\.add\(|\.delete\(|setDoc|runTransaction|firestore|getFirestore/i.test(src.replace(/res\.set\(/g, '').replace(/createHash\("sha256"\)\.update\(/g, '')), 'no key, no network call, no write, and no database access of its own (the order read is passed in)');
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  const fn = idx.slice(idx.indexOf('exports.kalshiNightlyReport'));
  assert.ok(/secrets: \[KALSHI_REPORT_TOKEN\]/.test(fn) && !/KALSHI_LIVE/.test(fn), 'only the report token');
  assert.ok(/\.collection\("kalshiLiveOrders"\)\.where\("ts", ">=", sinceMs\)\.get\(\)/.test(fn) && !/\.(set|update|add|delete)\(/.test(fn), 'one read of the bot orders');
  assert.ok(idx.indexOf('exports.kalshiBookRecorder') < idx.indexOf('exports.kalshiNightlyReport'), 'after the recorder, so the no-order-code slices still cover everything before it');
  const sh = fs.readFileSync(path.join(root, 'functions', 'deploy-report.sh'), 'utf8');
  assert.ok(/functions:secrets:get KALSHI_REPORT_TOKEN/.test(sh) && /keeping it/.test(sh), 'an existing token is kept');
  assert.ok(/ONLY=functions:kalshiNightlyReport\b/.test(sh), 'deploys only this function');
};

(async () => {
  for (const [name, fn] of Object.entries(gates)) { await fn(); console.log('ok   ' + name); }
})().catch((e) => { console.error(e); process.exit(1); });
