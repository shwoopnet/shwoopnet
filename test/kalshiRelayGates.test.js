// The Kalshi relay reads Kalshi from Firebase for the Live books tab. Kalshi's
// CDN refuses Google Cloud addresses (HTTP 403), so the relay is best effort and
// the journal never depends on it. These gates state what must stay true.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/kalshiLib');
const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');

const gates = {};

// Kalshi sends dollar strings; a missing or empty price must become null,
// never 0, or an unquoted market would read as a free contract.
gates.G1 = () => {
  const m = lib.trimMarket('KXBTC15M', { ticker: 'T', close_time: 'c', floor_strike: 86140.06,
    yes_bid_dollars: '0.0950', yes_ask_dollars: '', yes_bid_size_fp: '29.77' });
  assert.strictEqual(m.yesBid, 0.095);
  assert.strictEqual(m.yesAsk, null);
  assert.strictEqual(m.yesBidSz, 29.77);
};

// Only Bitcoin and gold, never more.
gates.G2 = () => {
  assert.deepStrictEqual(lib.KALSHI_SERIES, ['KXBTC15M', 'KXGOLD15M']);
};

// When Kalshi refuses a request the error must say what it said, and requests
// must identify themselves. A bare "HTTP 403" cannot tell a bug in our code
// from a network path Kalshi's CDN refuses, and the two have different fixes.
gates.G3 = () => {
  const m = /async function kalshiFetchSeries\(([\s\S]*?)\n\}/.exec(fnSrc);
  assert.ok(m, 'kalshiFetchSeries not found');
  assert.ok(/"User-Agent"/.test(m[1]), 'requests must send a User-Agent');
  assert.ok(/res\.text\(\)/.test(m[1]) && /console\.error\(/.test(m[1]), 'a refusal must log and surface what Kalshi said');
};

// A scheduled recorder on Firebase can only fail every minute against Kalshi's
// CDN, so it must not come back. Recording is done by the local recorder and by
// scalper.backfill, which read Kalshi from a connection it accepts.
gates.G4 = () => {
  assert.ok(!/kalshiRecorder|onSchedule/.test(fnSrc), 'the Firebase recorder must stay removed');
};

// The relay stays read-only and keyless: GET only, nothing to place an order with.
gates.G5 = () => {
  assert.ok(!/\/orders|Authorization|KALSHI_(API_)?KEY|method\s*:/i.test(fnSrc.slice(fnSrc.indexOf('KALSHI_HOSTS'))));
};

// Run the real kalshiFetchSeries against a scripted fetch. This is the code that
// answered "INTERNAL" in production, so it is exercised, not just read.
class FakeHttpsError extends Error { constructor(code, msg) { super(msg); this.code = code; } }
function liftFetchSeries(scripted, log) {
  const start = fnSrc.indexOf('async function kalshiFetchSeries(');
  let d = 0, end = -1;
  for (let i = fnSrc.indexOf('{', start); i < fnSrc.length; i++) {
    if (fnSrc[i] === '{') d++;
    else if (fnSrc[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const hosts = ['https://external-api.kalshi.com/trade-api/v2', 'https://api.elections.kalshi.com/trade-api/v2'];
  const fetch = async (url) => { log.push(url.split('/')[2]); return scripted.shift()(); };
  return new Function('KALSHI_HOSTS', 'HttpsError', 'fetch', 'AbortSignal', 'console',
    'return (' + fnSrc.slice(start, end) + ')')(hosts, FakeHttpsError, fetch, { timeout: () => undefined }, { error: () => {} });
}
const okJson = (markets) => () => ({ ok: true, json: async () => ({ markets }), headers: { get: () => '' } });
const refused = () => ({ ok: false, status: 403, text: async () => '<!DOCTYPE HTML>', headers: { get: (k) => (k === 'x-cache' ? 'Error from cloudfront' : '') } });
const run = (scripted) => { const log = []; return liftFetchSeries(scripted.slice(), log)('KXBTC15M', 'open', 5).then((r) => ({ r, log }), (e) => ({ e, log })); };

// The documented host comes first and the old one stays as a fallback.
gates.G6 = async () => {
  const hosts = /const KALSHI_HOSTS = \[([\s\S]*?)\];/.exec(fnSrc);
  const list = [...hosts[1].matchAll(/"https:\/\/([^/"]+)/g)].map((x) => x[1]);
  assert.deepStrictEqual(list, ['external-api.kalshi.com', 'api.elections.kalshi.com']);
  const a = await run([okJson([{ ticker: 'A' }])]);
  assert.deepStrictEqual(a.log, ['external-api.kalshi.com'], 'a working first host must be the only one asked');
  assert.strictEqual(a.r.length, 1);
};

// One refused host must not take the page down: fall back and succeed.
gates.G7 = async () => {
  const a = await run([refused, okJson([{ ticker: 'B' }])]);
  assert.deepStrictEqual(a.log, ['external-api.kalshi.com', 'api.elections.kalshi.com']);
  assert.strictEqual(a.r[0].ticker, 'B');
};

// Any other way a host can fail (timeout, dropped connection, a 200 whose body
// is not JSON) is also just that host failing. Escaping as a raw error is what
// produced "INTERNAL" on the page.
gates.G8 = async () => {
  const timeout = () => { const e = new Error('The operation was aborted'); e.name = 'TimeoutError'; throw e; };
  const notJson = () => ({ ok: true, json: async () => { throw new SyntaxError('Unexpected token <'); }, headers: { get: () => '' } });
  const dropped = () => { throw new TypeError('fetch failed'); };
  for (const bad of [timeout, notJson, dropped]) {
    const a = await run([bad, okJson([{ ticker: 'C' }])]);
    assert.ok(!a.e && a.r[0].ticker === 'C', 'a failing first host must fall back, not crash');
  }
};

// When every host fails the error is a clean HttpsError naming each host and
// status, and never carries the response body (a whole HTML page).
gates.G9 = async () => {
  const a = await run([refused, refused]);
  assert.ok(a.e instanceof FakeHttpsError && a.e.code === 'unavailable');
  assert.ok(/external-api\.kalshi\.com HTTP 403/.test(a.e.message) && /api\.elections\.kalshi\.com HTTP 403/.test(a.e.message), a.e.message);
  assert.ok(!/DOCTYPE|<HTML/i.test(a.e.message), 'the message must not include the response body');
  const b = await run([() => { throw new TypeError('fetch failed'); }, () => { throw new TypeError('fetch failed'); }]);
  assert.ok(b.e instanceof FakeHttpsError, 'two dropped connections must still be an HttpsError');
};

// The handler never lets an unexpected error reach the page as "INTERNAL".
gates.G10 = () => {
  const m = /exports\.kalshiBooks = onCall\(async \(request\) => \{([\s\S]*?)\n\}\);/.exec(fnSrc)[1];
  assert.ok(/catch \(e\)/.test(m) && /instanceof HttpsError/.test(m) && /Relay error: /.test(m), 'unexpected errors must become a named HttpsError');
  assert.ok(m.indexOf('assertKalshiAdmin') < m.indexOf('try {'), 'the admin check must stay outside the catch so it can never be swallowed');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
