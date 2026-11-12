'use strict';
// Nov 11, 2026 (owner direction: collect only from sources whose terms allow automated reads). Hosts blocked here, and why:
//   - Rotten Tomatoes (rottentomatoes.com, fandango.com): Fandango's Terms of Use (last updated Jan 6, 2026) section 10 bars collecting data by "robots, scripts, spiders, data extractors or other automated means" without express written authorization, and section 6 bars systematic retrieval to compile a database. FORBIDDEN.
//   - Metacritic (metacritic.com), Billboard (billboard.com), kworb (kworb.net): terms UNCHECKED (Metacritic's and Billboard's generally bar scraping). PARKED until the terms are read and allow automated reads; the owner or counsel can lift one host by a reviewed edit of this regex after reading its terms.
//   - Sports score sites and Polymarket: see below.
// Earlier the same day: no automated collection from sports score sites, and none from Polymarket. Polymarket's terms (effective Aug 11, 2026, section 4.2) bar data mining tools, robots, crawlers and similar tools that scrape or remove data from the Site, any Interface or Features, and bar non-retail professional entities from accessing Data directly or through an API without written agreement; the terms are read as for business use. The owner parked cross-venue Polymarket work (popup, Nov 11, 2026) and the xtracker adapter of the REF recorder was removed. V2's source probe found that ESPN/Disney's terms (May 24, 2024) forbid accessing or extracting content with "a robot, spider, script, or other automated means", and the terms are read as for business use. The SPORTS-PRE recorder (record-sportspre.yml) read ESPN's site API on a schedule and was stopped. This gate keeps it, or anything like it, from coming back unnoticed.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const gates = {};
const BLOCKED = /(^|[^a-z0-9])(espn\.com|espncdn\.com|nhle\.com|nhl\.com|statsapi\.mlb\.com|mlb\.com|nba\.com|cdn\.nba\.com|stats\.nba\.com|[a-z0-9.-]*polymarket\.com|[a-z0-9.-]*rottentomatoes\.com|[a-z0-9.-]*fandango\.com|[a-z0-9.-]*metacritic\.com|[a-z0-9.-]*billboard\.com|[a-z0-9.-]*kworb\.net)(?![a-z0-9])/i;
const strip = (s) => s;
const list = (dir, re) => fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => re.test(f)).map((f) => path.join(dir, f)) : [];

// NS1: no workflow, script or function requests an ESPN, NHL, MLB or NBA.com host. Comments are scanned too on purpose: a host named in a comment next to code is how it started.
gates.NS1 = () => {
  const files = [
    ...list(path.join(root, '.github', 'workflows'), /\.ya?ml$/),
    ...list(path.join(root, 'scripts'), /\.(py|js|sh)$/),
    ...list(path.join(root, 'functions'), /\.(js|sh)$/),
  ];
  assert.ok(files.length > 15, 'the recorder workflows and scripts are found');
  const hits = [];
  for (const f of files) {
    const txt = strip(fs.readFileSync(f, 'utf8'));
    txt.split('\n').forEach((line, i) => { if (BLOCKED.test(line)) hits.push(path.relative(root, f) + ':' + (i + 1)); });
  }
  assert.deepStrictEqual(hits, [], 'no sports score site host anywhere a job could read it: ' + hits.join(', '));
};

// NS2: the retired recorder's files stay gone.
gates.NS2 = () => {
  assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', 'record-sportspre.yml')), 'the schedule is gone');
  assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_sportspre.py')), 'the script is gone');
};

// NS4: the REF recorder's watchlist and adapters name none of the blocked hosts or sources.
gates.NS4 = () => {
  const w = fs.readFileSync(path.join(root, 'kalshi-scalper', 'workers', 'RECREF_WATCHLIST.json'), 'utf8').split('\n').filter((l) => !/"_parked"/.test(l)).join('\n');
  assert.ok(!BLOCKED.test(w), 'the watchlist names no blocked host');
  assert.ok(!BLOCKED.test(fs.readFileSync(path.join(root, 'scripts', 'ref_adapters.py'), 'utf8')), 'the adapters name no blocked host');
};

// NS3: record_signals.py's allowlist (the one place a new host could be added by a registry entry) holds none of them either.
gates.NS3 = () => {
  const src = fs.readFileSync(path.join(root, 'scripts', 'record_signals.py'), 'utf8');
  const m = /ALLOWLIST\s*=\s*frozenset\(\{([\s\S]*?)\}\)/.exec(src);
  assert.ok(m, 'the allowlist is found');
  const hosts = [...m[1].matchAll(/"([^"]+)"/g)].map((x) => x[1]);
  assert.ok(hosts.length >= 5, 'hosts parsed');
  for (const h of hosts) assert.ok(!BLOCKED.test(h), h + ' is a blocked site (sports score, Polymarket, Rotten Tomatoes, or a parked unchecked-terms host)');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
