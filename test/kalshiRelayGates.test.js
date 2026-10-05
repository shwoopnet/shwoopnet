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

// The documented host comes first and the old one stays as a fallback. A single
// refused host must not take the page down, and an error must name which host
// said no and never carry a whole HTML page.
gates.G6 = () => {
  const hosts = /const KALSHI_HOSTS = \[([\s\S]*?)\];/.exec(fnSrc);
  assert.ok(hosts, 'KALSHI_HOSTS not found');
  const list = [...hosts[1].matchAll(/"https:\/\/([^/"]+)/g)].map((x) => x[1]);
  assert.deepStrictEqual(list, ['external-api.kalshi.com', 'api.elections.kalshi.com']);
  const m = /async function kalshiFetchSeries\(([\s\S]*?)\n\}\n/.exec(fnSrc)[1];
  assert.ok(/for \(const base of KALSHI_HOSTS\)/.test(m) && /continue;/.test(m), 'must try each host in turn');
  const thrown = /throw new HttpsError\("unavailable", "Kalshi " \+ series[^;]*;/.exec(m);
  assert.ok(thrown && !/body/.test(thrown[0]), 'the thrown message must not include the response body');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); }
  catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
