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

// Run the real admin check against a scripted Firestore. It must let in only the
// owner whose user document says isAdmin, deny everyone else with the SAME generic
// message, and when Firestore itself fails it must deny AND say why, because an
// unnamed error here is what the page showed as "INTERNAL".
function liftAdminCheck(firestore, calls) {
  const start = fnSrc.indexOf('async function assertKalshiAdmin(');
  let d = 0, end = -1;
  for (let i = fnSrc.indexOf('{', start); i < fnSrc.length; i++) {
    if (fnSrc[i] === '{') d++;
    else if (fnSrc[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const assertSignedIn = (a) => { if (!a) throw new FakeHttpsError('permission-denied', 'Sign in required.'); };
  // The default app already exists, so a correct check initialises nothing.
  return new Function('assertSignedIn', 'HttpsError', 'KALSHI_OWNER_EMAIL', 'ensureDefaultAdminApp', 'getFirestore', 'console',
    'return (' + fnSrc.slice(start, end) + ')')(assertSignedIn, FakeHttpsError, 'heiszcam@gmail.com', () => {},
    () => { calls.push('firestore'); return firestore; }, { error: () => {} });
}

// The function that decides whether the default admin app must be created, run for
// real against a scripted app list.
function liftEnsureApp(apps, inits) {
  const start = fnSrc.indexOf('function ensureDefaultAdminApp(');
  let d = 0, end = -1;
  for (let i = fnSrc.indexOf('{', start); i < fnSrc.length; i++) {
    if (fnSrc[i] === '{') d++;
    else if (fnSrc[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  return new Function('getApps', 'initializeApp', 'return (' + fnSrc.slice(start, end) + ')')(
    () => apps, () => { inits.push('init'); apps.push({ name: '[DEFAULT]' }); });
}
const userDoc = (exists, data) => ({ collection: () => ({ doc: () => ({ get: async () => ({ exists, data: () => data }) }) }) });
const owner = { uid: 'u1', token: { email: 'heiszcam@gmail.com' } };
const attempt = async (auth, fs) => { const calls = []; try { await liftAdminCheck(fs, calls)(auth); return { ok: true, calls }; } catch (e) { return { e, calls }; } };

gates.G11 = async () => {
  assert.ok((await attempt(owner, userDoc(true, { isAdmin: true }))).ok, 'the owner with isAdmin must pass');
  // Wrong email: denied before Firestore is even asked.
  const other = await attempt({ uid: 'u2', token: { email: 'someone@else.com' } }, userDoc(true, { isAdmin: true }));
  assert.ok(other.e && other.e.code === 'permission-denied' && other.calls.length === 0);
  // Right email, flag false or missing document: denied with the same generic message.
  for (const fs of [userDoc(true, { isAdmin: false }), userDoc(true, {}), userDoc(false, undefined)]) {
    const r = await attempt(owner, fs);
    assert.ok(r.e && r.e.code === 'permission-denied' && r.e.message === other.e.message, 'denial must not reveal which check failed');
  }
  assert.ok((await attempt(null, userDoc(true, { isAdmin: true }))).e, 'no sign-in must be denied');
};

gates.G12 = async () => {
  const broken = { collection: () => ({ doc: () => ({ get: async () => { throw new Error('7 PERMISSION_DENIED: Missing or insufficient permissions'); } }) }) };
  const r = await attempt(owner, broken);
  assert.ok(r.e instanceof FakeHttpsError && r.e.code === 'unavailable', 'a Firestore failure must be a named error, never INTERNAL');
  assert.ok(/Admin check failed: .*PERMISSION_DENIED/.test(r.e.message), r.e.message);
  const boom = await attempt(owner, { collection: () => { throw new TypeError('getFirestore is not a function'); } });
  assert.ok(boom.e instanceof FakeHttpsError, 'even a synchronous failure must be named');
};

// The production failure, reproduced. The functions runtime already holds ANOTHER
// app, so "is any app initialised?" said yes, nothing was initialised, and
// getFirestore() threw "The default Firebase app does not exist". The default app
// must be created whenever it is missing, whatever else exists, and never twice.
gates.G13 = () => {
  const inits = [];
  const apps = [{ name: 'firebase-functions-internal' }];
  liftEnsureApp(apps, inits)();
  assert.strictEqual(inits.length, 1, 'with only a non-default app present, the default app must be created');
  liftEnsureApp(apps, inits)();
  assert.strictEqual(inits.length, 1, 'once the default app exists it must not be initialised again');
  const none = [];
  liftEnsureApp([], none)();
  assert.strictEqual(none.length, 1, 'with no apps at all it must be created');
  assert.ok(/getApps\(\)\.some\(\(a\) => a\.name === "\[DEFAULT\]"\)/.test(fnSrc), 'the check must be by app name');
  assert.ok(!/if \(!getApps\(\)\.length\)/.test(fnSrc), 'the "any app" check that caused this must not come back');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
