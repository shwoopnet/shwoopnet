// Nov 11, 2026 (the owner): Yahoo's terms forbid automated reads, so nothing the site's functions run may contact a Yahoo host, and the market tape may contact exactly the hosts whose terms were read.
// Consequence: a future edit that brings Yahoo (or a news feed whose terms nobody read) back into the tape fails here. NOTE: PR 779 may add its own no-Yahoo gate for the research reads; the two cover
// different folders (this one: functions/, the page and the tape's host list) and should be reconciled into one file once both are on main.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const gates = {};
const strip = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:"'`\\])\/\/.*$/gm, '$1');

const fnFiles = fs.readdirSync(path.join(root, 'functions')).filter((f) => f.endsWith('.js'));

gates.Y1 = () => {
  assert.ok(fnFiles.includes('marketTapeLib.js') && fnFiles.includes('index.js'));
  for (const f of fnFiles) {
    const code = strip(fs.readFileSync(path.join(root, 'functions', f), 'utf8'));
    assert.ok(!/yahoo|query1\.finance|query2\.finance|finance\.yahoo/i.test(code), f + ' (comments stripped) names no Yahoo host');
  }
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(!/query[12]\.finance|finance\.yahoo/i.test(html), 'the page names no Yahoo host');
};

// The tape's hosts are exactly these two, in the library's list and in every URL the library builds.
gates.Y2 = () => {
  const lib = require('../functions/marketTapeLib.js');
  assert.deepStrictEqual(lib.ALLOWED_HOSTS.slice().sort(), ['api.alternative.me', 'home.treasury.gov'], 'the exact allowlist; adding a source is a deliberate edit here too');
  const code = strip(fs.readFileSync(path.join(root, 'functions', 'marketTapeLib.js'), 'utf8'));
  const hosts = new Set([...code.matchAll(/https?:\/\/([a-z0-9.-]+)/gi)].map((m) => m[1].toLowerCase()));
  assert.deepStrictEqual([...hosts].sort(), [], 'no literal URL host in the code: every host comes from the pinned constants');
  const consts = [...code.matchAll(/const (\w+_HOST) = "([^"]+)"/g)].map((m) => m[2]).sort();
  assert.deepStrictEqual(consts, ['api.alternative.me', 'home.treasury.gov'], 'the host constants are the allowlist');
  for (const banned of ['cnbc', 'dowjones', 'marketwatch', 'wsj', 'coindesk', 'cointelegraph', 'cnn.io', 'cnn.com', 'coinbase', 'kraken', 'gold-api']) assert.ok(!code.toLowerCase().includes(banned), banned + ' is not read by the tape (terms unread or barred)');
};

// Every URL the tape builds goes to an allowlisted host over https, and a symbol with no source triggers no request at all.
gates.Y3 = async () => {
  const lib = require('../functions/marketTapeLib.js');
  const urls = [];
  await lib.readTape({ fetchFn: async (u) => { urls.push(u); return { ok: true, status: 200, text: async () => '' }; }, now: Date.UTC(2026, 10, 11) });
  assert.ok(urls.length >= 2 && urls.every((u) => { const x = new URL(u); return x.protocol === 'https:' && lib.ALLOWED_HOSTS.includes(x.hostname); }), 'only allowlisted https hosts: ' + urls.join(' '));
  const unsourced = lib.SYMBOLS.filter((s) => !s.source).map((s) => encodeURIComponent(s.sym));
  assert.ok(!urls.some((u) => unsourced.some((s) => u.includes(s))), 'no request names a symbol that has no permitted source');
};

// No key value in the tape or the page: the library has no secret at all.
gates.Y4 = () => {
  const code = fs.readFileSync(path.join(root, 'functions', 'marketTapeLib.js'), 'utf8');
  assert.ok(!/defineSecret|apikey|api_key|[?&]key=|Bearer /i.test(code), 'no key, no secret binding');
  assert.ok(!/[A-Za-z0-9_-]{32,}/.test(strip(code).replace(/"[^"]*"/g, '""')), 'no long token-like string in the code');
};

// The sources doc records the Nov 11 confirmation, so the next reader knows what was and was not confirmed.
gates.Y5 = () => {
  const doc = fs.readFileSync(path.join(root, 'docs', 'MARKET_TAPE_SOURCES.md'), 'utf8');
  assert.ok(/## Nov 11 confirmation/.test(doc) && /daily_treasury_yield_curve/.test(doc), 'the confirmation section names the endpoint');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
