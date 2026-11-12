// Fast research reads (Nov 12, 2026): a read-only endpoint that runs a job of PUBLIC market-data GETs through the owner's own key. Each gate states the consequence. Synthetic data only.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.join(__dirname, '..');
const lib = require('../functions/kalshiFastReadLib');
const live = require('../functions/kalshiLiveLib');
const src = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const code = (s) => s.replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const { privateKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const PEM = privateKey.export({ type: 'pkcs8', format: 'pem' });
const TOKEN = 'f'.repeat(40);
const gates = {};

// A UTC time in a quarter-hour minute that is allowed (minute 0) and one that is not (minute 8: the bot buys).
const T_OK = Date.parse('2026-11-12T14:00:20Z');
const T_BAD = Date.parse('2026-11-12T14:08:20Z');
const mkWorld = (o = {}) => {
  const w = { calls: [], sleeps: [], t: o.t === undefined ? T_OK : o.t };
  w.now = () => w.t;
  w.sleep = async (ms) => { w.sleeps.push(ms); w.t += ms; };
  w.fetchFn = async (url, init) => {
    w.calls.push({ url: String(url), method: (init && init.method) || 'GET', body: init && init.body, headers: init && init.headers, at: w.t });
    w.t += 5;
    const st = typeof o.status === 'function' ? o.status(w.calls.length) : (o.status || 200);
    const body = typeof o.body === 'function' ? o.body(w.calls.length, String(url)) : (o.body || { markets: [] });
    return { status: st, text: async () => JSON.stringify(body) };
  };
  w.run = (job) => lib.runFastRead({ job, fetchFn: w.fetchFn, keyId: 'KEYID-SECRET', pem: PEM, now: w.now, sleep: w.sleep });
  return w;
};
const cand = (n) => ({ ep: 'candles', series: 'KXBTC15M', ticker: 'KXBTC15M-26NOV1210-T' + n, start_ts: 1790000000, end_ts: 1790003600, period: 60 });

gates.FR1 = async () => {   // only GET ever leaves, and only to the market-data paths
  const w = mkWorld();
  const r = await w.run({ requests: [cand(1), { ep: 'market', ticker: 'KXBTC15M-26NOV1210-T1' }, { ep: 'markets_list', series: 'KXBTC15M', status: 'settled', limit: 100 }, { ep: 'trades', ticker: 'KXBTC15M-26NOV1210-T1' }, { ep: 'hist_markets_list', series: 'KXBTC15M' }, { ep: 'hist_market', ticker: 'X-1' }, { ep: 'hist_candles', ticker: 'X-1', start_ts: 1790000000, end_ts: 1790003600, period: 1440 }, { ep: 'hist_trades', ticker: 'X-1' }] });
  assert.strictEqual(r.status, 'done'); assert.strictEqual(w.calls.length, 8);
  for (const c of w.calls) { assert.strictEqual(c.method, 'GET'); assert.ok(!c.body); assert.ok(/^https:\/\/external-api\.kalshi\.com\/trade-api\/v2\/(markets|series\/[A-Z0-9]+\/markets|historical\/)/.test(c.url), c.url); }
  const l = code(src('functions/kalshiFastReadLib.js'));
  assert.ok(!/method: "(POST|PUT|DELETE|PATCH)"|placeOrder|sellOrder|createOrder|\/orders|kalshiLiveOrders|getFirestore|writeFile|collection\(|\.doc\(/.test(l), 'no write verb, order code or storage in the library');
  assert.ok(/method: "GET"/.test(l));
};
gates.FR2 = async () => {   // a job cannot reach portfolio, orders, fills, positions, balance or account, by any spelling
  const bad = [
    { ep: '/portfolio/balance' }, { ep: 'portfolio' }, { ep: 'balance' }, { ep: 'orders' }, { ep: 'fills' }, { ep: 'positions' }, { ep: 'account' }, { ep: '../portfolio/orders' },
    { ep: 'market', ticker: '../portfolio/balance' }, { ep: 'market', ticker: 'X/../../portfolio/orders' }, { ep: 'market', ticker: 'X?cursor=1' }, { ep: 'market', ticker: 'x-lower' },
    { ep: 'trades', ticker: 'X-1', path: '/portfolio/fills' }, { ep: 'trades', ticker: 'X-1', url: 'https://evil.example/' }, { ep: 'markets_list', series: 'portfolio/orders' },
    { ep: 'markets_list', series: 'KXBTC15M', status: 'orders' }, { ep: 'market', ticker: 'PORTFOLIO-BALANCE' + '%2F' }, { ep: 'candles', series: 'A/B', ticker: 'X-1', start_ts: 1790000000, end_ts: 1790003600, period: 60 },
  ];
  for (const b of bad) { const w = mkWorld(); const r = await w.run({ requests: [b] }); assert.strictEqual(r.status, 'refused', JSON.stringify(b)); assert.strictEqual(w.calls.length, 0); }
  // Even a legal ticker that contains a forbidden word is refused as a path (defence in depth).
  const w = mkWorld(); const r = await w.run({ requests: [{ ep: 'market', ticker: 'KXPOSITION-1' }] });
  assert.strictEqual(r.status, 'refused'); assert.strictEqual(w.calls.length, 0);
  assert.ok(/portfolio\|order\|fill\|position\|balance\|account/.test(lib.FORBIDDEN_PATH.source));
  assert.deepStrictEqual(Object.keys(lib.ENDPOINTS).sort(), ['candles', 'hist_candles', 'hist_market', 'hist_markets_list', 'hist_trades', 'market', 'markets_list', 'trades']);
  for (const k of Object.keys(lib.ENDPOINTS)) assert.ok(!lib.FORBIDDEN_PATH.test(k) && !lib.FORBIDDEN_PATH.test(lib.ENDPOINTS[k].path({ ticker: 'T', series: 'S' })), k);
  // The job carries no free-form path or url field at all.
  for (const k of ['path', 'url', 'host', 'method']) assert.strictEqual(lib.planEntry({ ep: 'market', ticker: 'X-1', [k]: 'x' }).ok, false);
};
gates.FR3 = async () => {   // rate: never above 5 a second, in practice under 3; one request starts at a time
  assert.ok(lib.MIN_GAP_MS >= 200, 'never above 5 requests a second');
  assert.ok(1000 / lib.MIN_GAP_MS < 3 + 1e-9, 'at most about 3 a second');
  const w = mkWorld();
  await w.run({ requests: [cand(1), cand(2), cand(3), cand(4), cand(5), cand(6)] });
  assert.strictEqual(w.calls.length, 6);
  for (let i = 1; i < w.calls.length; i++) assert.ok(w.calls[i].at - w.calls[i - 1].at >= lib.MIN_GAP_MS - 1, 'spaced by the minimum gap');
};
gates.FR4 = async () => {   // the hard request cap: 300 per call, pages included; a bigger job is refused outright
  assert.strictEqual(lib.MAX_REQUESTS, 300);
  const w = mkWorld(); const big = { requests: Array.from({ length: 301 }, (_, i) => cand(i)) };
  assert.strictEqual((await w.run(big)).status, 'refused'); assert.strictEqual(w.calls.length, 0);
  assert.strictEqual((await w.run({ max_requests: 301, requests: [cand(1)] })).status, 'refused');
  // pages count against the cap: one list asking 50 pages with a cursor on every answer, cap 7
  const p = mkWorld({ body: { markets: [], cursor: 'next' } });
  const r = await p.run({ max_requests: 7, requests: [{ ep: 'markets_list', series: 'KXBTC15M', max_pages: 50 }] });
  assert.strictEqual(r.status, 'stopped_at_cap'); assert.strictEqual(p.calls.length, 7);
  assert.ok(p.calls[1].url.includes('cursor=next'), 'the cursor goes back through the encoder');
  const long = mkWorld({ body: { cursor: 'x'.repeat(600) } });
  await long.run({ requests: [{ ep: 'markets_list', max_pages: 5 }] }); assert.strictEqual(long.calls.length, 1, 'a cursor over 512 characters is not followed');
};
gates.FR5 = async () => {   // the exit watch's minutes: refuse to start, and stop mid-job when the clock enters them
  for (let m = 0; m < 15; m++) {
    const t = Date.parse('2026-11-12T14:00:30Z') + m * 60000;
    const inWindow = live.EXIT_BUY_MINUTES.includes(m);
    if (inWindow) assert.strictEqual(lib.inBlockedWindow(t), true, 'minute ' + m);
  }
  for (const m of live.EXIT_BUY_MINUTES) { assert.strictEqual(lib.inBlockedWindow(Date.parse('2026-11-12T14:00:00Z') + (m - 1) * 60000), true); assert.strictEqual(lib.inBlockedWindow(Date.parse('2026-11-12T14:00:00Z') + (m + 1) * 60000), true, 'a minute of padding either side'); }
  assert.strictEqual(lib.inBlockedWindow(Date.parse('2026-11-12T14:00:20Z')), false); assert.strictEqual(lib.inBlockedWindow(Date.parse('2026-11-12T14:13:20Z')), false);
  const w = mkWorld({ t: T_BAD }); const r = await w.run({ requests: [cand(1)] });
  assert.strictEqual(r.status, 'refused'); assert.strictEqual(r.reason, 'exit_watch_window'); assert.strictEqual(w.calls.length, 0, 'not one request in the bot\'s buying minutes');
  // Same in the other quarters of the hour and under Central time (every quarter hour aligns in UTC and Central).
  for (const hm of ['15:08', '16:23', '17:38', '03:53']) { const x = mkWorld({ t: Date.parse('2026-11-12T' + hm + ':10Z') }); assert.strictEqual((await x.run({ requests: [cand(1)] })).status, 'refused', hm); }
  // Mid-job: starts at minute 1 (allowed), the clock runs into minute 2 (padding): it stops, keeps what it read.
  const m = mkWorld({ t: Date.parse('2026-11-12T14:01:50Z') });
  m.fetchFn = ((orig) => async (u, i) => { const r2 = await orig(u, i); m.t += 8000; return r2; })(m.fetchFn);
  const r2 = await m.run({ requests: Array.from({ length: 10 }, (_, i) => cand(i)) });
  assert.strictEqual(r2.status, 'stopped_exit_watch_window'); assert.ok(r2.results.length >= 1 && r2.results.length < 10);
  const l = code(src('functions/kalshiFastReadLib.js'));
  assert.ok(/live\.EXIT_BUY_MINUTES/.test(l), 'the window follows the code constant, not a copy');
};
gates.FR6 = async () => {   // three 429s in a row stop the job; a refused read is never asked twice by this module's own retry
  const w = mkWorld({ status: 429 });
  const r = await w.run({ requests: Array.from({ length: 20 }, (_, i) => cand(i)) });
  assert.strictEqual(r.status, 'stopped_429'); assert.strictEqual(w.calls.length, 3, 'exactly three tries, then stop'); assert.strictEqual(lib.MAX_429_IN_A_ROW, 3);
  const mix = mkWorld({ status: (n) => (n === 1 || n === 2 ? 429 : 200) });
  const r2 = await mix.run({ requests: [cand(1), cand(2)] });
  assert.strictEqual(r2.status, 'done', 'a success resets the count'); assert.strictEqual(r2.results.length, 2);
  assert.ok(mix.sleeps.some((s) => s >= 1000), 'it waits after a 429');
  assert.ok(/noRetry: true/.test(code(src('functions/kalshiFastReadLib.js'))), 'liveRequest\'s own single retry is switched off here');
  const err = mkWorld({ status: 500 }); assert.strictEqual((await err.run({ requests: [cand(1)] })).status, 'done', 'other errors are reported per request, never thrown');
};
gates.FR7 = async () => {   // token: constant time, closed with none, GET refused, wrong token refused, nothing is run without it
  const idx = code(src('functions/index.js'));
  const fn = idx.slice(idx.indexOf('exports.kalshiFastRead = onRequest('), idx.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/secrets: \[KALSHI_FASTREAD_TOKEN, KALSHI_LIVE_KEY_ID, KALSHI_LIVE_PRIVATE_KEY\]/.test(fn) && /cors: false/.test(fn) && /maxInstances: 1/.test(fn) && /concurrency: 1/.test(fn), 'its own token, the two existing key secrets, no CORS, one instance, one request at a time so two calls cannot double the rate on the trading key');
  assert.ok(!/KALSHI_REPORT_TOKEN|VAPID/.test(fn) && !/kalshiLiveOrders|kalshiLiveControl|getFirestore|runL1Tick|runExitWatch/.test(fn), 'it touches no order, session, control or storage');
  assert.ok(/timingSafeEqual/.test(code(src('functions/kalshiFastReadLib.js'))));
  const call = async (token, req) => {
    const w = mkWorld(); const out = { code: null, body: null }; const res = { set() {}, status: (c) => { out.code = c; return res; }, json: (b) => { out.body = b; } };
    await lib.makeFastReadHandler({ getToken: () => token, getKeyId: () => 'KEYID-SECRET', getPem: () => PEM, fetchFn: w.fetchFn, now: w.now, sleep: w.sleep })(Object.assign({ method: 'POST', headers: { authorization: 'Bearer ' + TOKEN }, body: { job: { requests: [cand(1)] } } }, req), res);
    out.calls = w.calls.length; return out;
  };
  assert.strictEqual((await call(TOKEN, {})).code, 200);
  assert.strictEqual((await call('', {})).code, 401, 'no token configured means closed');
  assert.strictEqual((await call('short', { headers: { authorization: 'Bearer short' } })).code, 401, 'a short token is no token');
  const bad = await call(TOKEN, { headers: { authorization: 'Bearer ' + 'e'.repeat(40) } }); assert.strictEqual(bad.code, 401); assert.strictEqual(bad.calls, 0);
  assert.strictEqual((await call(TOKEN, { headers: {} })).code, 401);
  assert.strictEqual((await call(TOKEN, { method: 'GET' })).code, 405);
  assert.strictEqual((await call(TOKEN, { method: 'DELETE' })).code, 405);
  assert.ok(lib.sameToken('a', 'a') && !lib.sameToken('a', 'b') && !lib.sameToken('a', 'aa'));
};
gates.FR8 = async () => {   // nothing secret in any output, including on errors and refusals; the key is only in the signed headers
  const secretish = ['KEYID-SECRET', 'BEGIN', 'PRIVATE', TOKEN];
  const w = mkWorld({ body: (n, url) => ({ markets: [{ ticker: 'X-1' }], echoed: 'ok' }) });
  const outs = [await w.run({ requests: [cand(1), { ep: 'markets_list', series: 'KXBTC15M' }] }), await mkWorld({ status: 429 }).run({ requests: [cand(1)] }), await mkWorld({ t: T_BAD }).run({ requests: [cand(1)] }), await mkWorld().run({ requests: [{ ep: 'portfolio', secretsLeak: 'KEYID-SECRET' }] })];
  for (const o of outs) for (const s of secretish) assert.ok(!JSON.stringify(o).includes(s), 'no ' + s + ' in ' + o.status);
  assert.ok(w.calls[0].headers['KALSHI-ACCESS-KEY'] === 'KEYID-SECRET', 'the key is sent to Kalshi only, in its header');
  // The handler's error path says nothing about the cause.
  const res = { set() {}, status(c) { this.c = c; return this; }, json(b) { this.b = b; } };
  await lib.makeFastReadHandler({ getToken: () => TOKEN, getKeyId: () => { throw new Error('KEYID-SECRET leaked'); }, getPem: () => PEM, fetchFn: async () => ({}), now: () => T_OK, sleep: async () => {} })({ method: 'POST', headers: { authorization: 'Bearer ' + TOKEN }, body: { job: { requests: [cand(1)] } } }, res);
  assert.strictEqual(res.c, 500); assert.ok(!JSON.stringify(res.b).includes('KEYID')); assert.deepStrictEqual(res.b, { error: 'could not run' });
  const idx = code(src('functions/index.js')); const fn = idx.slice(idx.indexOf('exports.kalshiFastRead = onRequest('), idx.indexOf('exports.kalshiBookRecorder'));
  assert.ok(/console\.error\("kalshiFastRead: " \+ String\(\(e && e\.name\) \|\| "Error"\)\)/.test(fn), 'the log line is the error name only');
  assert.ok(!/console\.log/.test(code(src('functions/kalshiFastReadLib.js'))), 'the library logs nothing');
};
gates.FR9 = async () => {   // the response is bounded and public data only; rows carry endpoint, status and the body, never request headers
  const w = mkWorld({ body: () => ({ markets: ['x'.repeat(3 * 1024 * 1024)] }) });
  const r = await w.run({ requests: [cand(1), cand(2), cand(3), cand(4)] });
  assert.strictEqual(r.truncated, true); assert.strictEqual(r.status, 'stopped_response_size'); assert.ok(JSON.stringify(r).length <= lib.MAX_RESPONSE_BYTES + 1024);
  const ok = mkWorld(); const o = await ok.run({ requests: [cand(1)] });
  assert.deepStrictEqual(Object.keys(o.results[0]).sort(), ['body', 'ep', 'i', 'page', 'status']);
  const rules = src('firestore.rules'); assert.ok(!/kalshiFastRead/i.test(rules), 'nothing is stored, so no collection or rule exists');
};
gates.FR10 = () => {   // deploy and notes: its own script with its own token, no switch needed, CLAUDE.md and the changelog say so
  const sh = src('functions/deploy-fastread.sh');
  assert.ok(/ONLY=functions:kalshiFastRead/.test(sh) && /KALSHI_FASTREAD_TOKEN/.test(sh) && !/KALSHI_REPORT_TOKEN|KALSHI_LIVE_ENABLED/.test(sh));
  assert.ok(!/functions:kalshiFastRead/.test(src('functions/deploy-sizing.sh')) && !/functions:kalshiFastRead/.test(src('functions/deploy-report.sh')), 'the other deploys never carry it');
  require('child_process').execFileSync('bash', ['-n', path.join(root, 'functions', 'deploy-fastread.sh')]);
  assert.ok(/## Fast research reads .*\(Nov 12, 2026/.test(src('CLAUDE.md')));
  assert.ok(/fast research reads/i.test(src('index.html')));
  assert.ok(!(src('functions/kalshiFastReadLib.js') + src('functions/deploy-fastread.sh') + src('test/kalshiFastReadGates.test.js')).includes(String.fromCharCode(8212)), 'no em dashes');
};
(async () => { for (const [n, f] of Object.entries(gates)) { await f(); console.log('ok   ' + n); } })().catch((e) => { console.error(e); process.exit(1); });
