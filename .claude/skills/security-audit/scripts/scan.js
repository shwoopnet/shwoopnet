#!/usr/bin/env node
'use strict';
// The security scan (Oct 22, 2026). Deterministic checks the security agent runs first, so a review always starts from the same facts. It reads the repo only: it prints no secret value (a finding names a file
// and a pattern, never the text matched), changes nothing, and exits 1 if any check FAILs. WARN means "a human or the agent should look", FAIL means "do not ship".
//
// Usage: node .claude/skills/security-audit/scripts/scan.js [--offline] [--history]
//   --offline  skip the dependency audit (it needs the network)
//   --history  also scan every commit on every branch for secret shapes (slower)
//   --root DIR scan another repo (used by the test with a deliberately bad fake one)
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const argv = process.argv.slice(2);
const rootArg = argv.indexOf('--root');   // lets a test point the scan at a deliberately bad fake repo
const root = rootArg >= 0 ? path.resolve(argv[rootArg + 1]) : path.join(__dirname, '..', '..', '..', '..');
const args = new Set(argv);
const out = [];
const add = (level, id, msg) => out.push({ level, id, msg });
const read = (f) => fs.readFileSync(path.join(root, f), 'utf8');
const sh = (cmd, a, opts) => execFileSync(cmd, a, Object.assign({ cwd: root, encoding: 'utf8', maxBuffer: 1 << 28, stdio: ['ignore', 'pipe', 'ignore'] }, opts || {}));
const tracked = sh('git', ['ls-files']).split('\n').filter(Boolean).filter((f) => !/node_modules|package-lock\.json|\.(png|webp|woff2|jpg|ico|gz|pdf)$/.test(f));
const SECRET_SHAPES = [
  ['a private key block', /-----BEGIN (RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----/], ['an AWS access key id', /AKIA[0-9A-Z]{16}/], ['a live payment key', /sk_live_[0-9A-Za-z]{16,}/],
  ['a Slack token', /xox[baprs]-[0-9A-Za-z-]{10,}/], ['a GitHub token', /gh[pousr]_[0-9A-Za-z]{30,}/], ['a service account key', /"private_key_id"\s*:/], ['a Google API key', /AIza[0-9A-Za-z_-]{35}/],
];

// 1. Secrets: no key file or .env tracked, no secret shape in any tracked file (the Firebase web key in index.html is public by design and the only allowed Google key).
{
  const names = tracked.filter((f) => /\.(pem|key|p12|pfx)$/i.test(f) || /(^|\/)\.env($|\.)/.test(f) || /serviceAccount|service-account/i.test(f));
  names.forEach((f) => add('FAIL', 'secrets', 'a key or env file is tracked: ' + f));
  tracked.forEach((f) => {
    if (/securityHardeningGates|security-audit\/scripts\/scan\.js/.test(f)) return;
    const text = read(f);
    SECRET_SHAPES.forEach(([what, re]) => { if (re.test(text) && !(f === 'index.html' && what === 'a Google API key')) add('FAIL', 'secrets', f + ' contains ' + what + ' (value not shown: rotate it, then remove it)'); });
  });
  const keys = (read('index.html').match(/AIza[0-9A-Za-z_-]{35}/g) || []).length;
  add(keys === 1 ? 'PASS' : 'FAIL', 'secrets', 'index.html carries ' + keys + ' Google key (expected exactly 1: the public Firebase web key)');
  const ign = fs.existsSync(path.join(root, 'functions', '.gitignore')) ? read('functions/.gitignore') : '';
  add(/^\.env$/m.test(ign) && /^\.env\.\*$/m.test(ign) ? 'PASS' : 'FAIL', 'secrets', 'functions/.gitignore ignores .env and .env.*');
  if (args.has('--history')) {
    let hits = 0;
    try {
      const log = sh('git', ['log', '--all', '-p', '--no-color']);
      SECRET_SHAPES.slice(0, 6).forEach(([what, re]) => { const g = new RegExp('^\\+.*' + re.source, 'm'); if (g.test(log)) { hits++; add('FAIL', 'history', 'a commit on some branch added ' + what + ' (value not shown: rotate it)'); } });
    } catch (e) { add('WARN', 'history', 'could not read the full history'); }
    if (!hits) add('PASS', 'history', 'no secret shape was ever added on any branch');
  }
}

// 2. Workflows: every action pinned to a commit, token permissions stated, no pull_request_target, no secret but the built-in token.
{
  const dir = path.join(root, '.github', 'workflows');
  (fs.existsSync(dir) ? fs.readdirSync(dir) : []).filter((f) => /\.ya?ml$/.test(f)).forEach((f) => {
    const wf = fs.readFileSync(path.join(dir, f), 'utf8');
    [...wf.matchAll(/uses:\s*([^\s#]+)/g)].forEach((m) => { if (!/@[0-9a-f]{40}$/.test(m[1])) add('FAIL', 'workflows', f + ': ' + m[1] + ' is not pinned to a full commit'); });
    if (!/^permissions:/m.test(wf)) add('FAIL', 'workflows', f + ' does not state its token permissions');
    if (/permissions:\s*write-all/.test(wf)) add('FAIL', 'workflows', f + ' asks for write-all');
    if (/pull_request_target/.test(wf)) add('FAIL', 'workflows', f + ' runs on pull_request_target');
    if (/secrets\.(?!GITHUB_TOKEN)/.test(wf)) add('WARN', 'workflows', f + ' uses a secret other than the built-in token: check it is needed');
    if (/\$\{\{\s*github\.event\.(issue|pull_request|comment|head_commit)/.test(wf)) add('WARN', 'workflows', f + ' puts attacker-controlled text into a script: use an env variable instead');
  });
  if (!out.some((o) => o.id === 'workflows')) add('PASS', 'workflows', 'every workflow is pinned, scoped and uses only the built-in token');
}

// 3. Database rules: nothing is open, and the rules for money-related collections are server-write-only. The match list is printed for a human to read.
{
  const rules = read('firestore.rules').replace(/\/\/[^\n]*/g, '');
  if (/allow\s+[a-z, ]+:\s*if\s+true/.test(rules)) add('FAIL', 'rules', 'a rule allows everything (if true)');
  // One chunk per `match` statement (the first chunk is the database wrapper and the helper functions, so it is skipped).
  const blocks = rules.split(/\bmatch\s+/).slice(2).map((c) => ({ path: c.split(/\s/)[0], body: c }));
  blocks.forEach((b) => {
    if (!/kalshi/i.test(b.path)) return;
    const w = /allow\s+(?:write|create|update|delete)[^;]*;/.exec(b.body), r = /allow\s+(?:read|get|list)[^;]*;/.exec(b.body);
    if (w && !/if false/.test(w[0]) && !/isAdmin\(\)/.test(w[0])) add('FAIL', 'rules', b.path + ' lets a non-admin write');
    if (!r || !/isAdmin\(\)/.test(r[0])) add('WARN', 'rules', b.path + ' is readable without the admin check: confirm that is intended');
  });
  add('INFO', 'rules', 'collections with a rule: ' + blocks.map((b) => b.path).join(', ') + ' (everything else is denied by default)');
  if (!out.some((o) => o.id === 'rules' && o.level !== 'INFO')) add('PASS', 'rules', 'no open rule, and every kalshi collection is admin-read and server-write');
}

// 4. Server functions: every callable checks the caller, no open HTTP endpoint, secrets only through the secret store, no secret printed.
{
  const src = read('functions/index.js'), lines = src.split('\n');
  lines.forEach((l, i) => {
    if (/exports\.\w+\s*=\s*onCall\(/.test(l)) {
      const body = lines.slice(i, i + 14).join('\n');
      if (!/assertKalshiAdmin|assertSignedIn/.test(body)) add('FAIL', 'functions', 'functions/index.js:' + (i + 1) + ' a callable does not check who is calling in its first lines');
    }
    if (/onRequest\(/.test(l) && /exports\.\w+\s*=\s*onRequest\(/.test(l)) {
      // The ONE reviewed exception (Oct 28, 2026, the nightly order report): an HTTP endpoint is allowed only when it is the report handler, which is closed without a long secret token (test/kalshiReportGates.test.js R3). Anything else stays a FAIL.
      const body = lines.slice(i, i + 8).join('\n');
      if (!(/KALSHI_REPORT_TOKEN/.test(body) && /makeReportHandler\(/.test(body))) add('FAIL', 'functions', 'functions/index.js:' + (i + 1) + ' an open HTTP endpoint: it needs its own authentication, review it');
    } else if (/onRequest\(/.test(l) && !/require\(/.test(l)) add('FAIL', 'functions', 'functions/index.js:' + (i + 1) + ' an open HTTP endpoint: it needs its own authentication, review it');
    if (/console\.(log|error|warn|info)\([^)]*\.value\(\)/.test(l)) add('FAIL', 'functions', 'functions/index.js:' + (i + 1) + ' prints a secret value');
    if (/process\.env\.[A-Z_]*(KEY|SECRET|TOKEN|PRIVATE)/.test(l)) add('WARN', 'functions', 'functions/index.js:' + (i + 1) + ' reads a secret from process.env: use defineSecret');
  });
  const sec = [...src.matchAll(/defineSecret\("([A-Z_]+)"\)/g)].map((m) => m[1]);
  add('INFO', 'functions', 'secrets held in the secret store: ' + sec.join(', '));
  if (!out.some((o) => o.id === 'functions' && o.level !== 'INFO')) add('PASS', 'functions', 'every callable checks its caller, no open endpoint, no secret printed');
}

// 5. The page: no eval or document.write, no insecure link, a frame guard, only expected hosts, and values reaching HTML are escaped.
{
  const html = read('index.html'), lines = html.split('\n');
  const script = html.replace(/<!--[\s\S]*?-->/g, '');
  if (/\beval\s*\(|document\.write\s*\(/.test(script)) add('FAIL', 'page', 'index.html uses eval or document.write');
  if (/new Function\(/.test(script)) add('WARN', 'page', 'index.html builds code with new Function');
  (html.match(/<a\b[^>]*target="_blank"[^>]*>/g) || []).forEach((a) => { if (!/rel="[^"]*noopener/.test(a)) add('WARN', 'page', 'a _blank link has no rel=noopener: ' + a.slice(0, 80)); });
  [...new Set((script.match(/['"]http:\/\/(?!www\.w3\.org)[^'"\s]+/g) || []))].forEach((u) => add('WARN', 'page', 'a plain http address: ' + u.slice(0, 60)));
  add(/window\.top !== window\.self/.test(html) ? 'PASS' : 'FAIL', 'page', 'the frame guard is present');
  const hosts = [...new Set((script.match(/https?:\/\/[a-z0-9.-]+/gi) || []).map((h) => h.replace(/^https?:\/\//i, '').toLowerCase()))].filter((h) => h !== 'www.w3.org');
  add('INFO', 'page', 'hosts the page can reach: ' + hosts.join(', '));
  let unescaped = 0;
  lines.forEach((l, i) => {
    if (!/innerHTML\s*\+?=|insertAdjacentHTML/.test(l) || /=\s*part\(/.test(l)) return;   // part() escapes its error argument
    const parts = [...l.matchAll(/'\s*\+\s*([A-Za-z_][\w.\[\]()]*)/g)].map((m) => m[1]).filter((p) => !/esc|Escape|money|Money|toFixed|String\(|Math\.|\.length|signed|pct|fmt|Number|round|Text\(|px|cls|class|stakeRow|foot\.join|\.status|^n$/.test(p));
    if (parts.length) { unescaped++; add('WARN', 'page', 'index.html:' + (i + 1) + ' puts ' + parts.slice(0, 3).join(', ') + ' into HTML without an escape call: check it is not external text'); }
  });
  if (!unescaped) add('PASS', 'page', 'every value concatenated into HTML is escaped or numeric');
  if (/localStorage\.setItem\([^)]*(token|password|secret|apikey)/i.test(script)) add('FAIL', 'page', 'a secret-looking value is saved in localStorage');
  if (/<meta name="robots" content="noindex/.test(html)) add('PASS', 'page', 'search engines are asked not to index the page');
}

// 6. Dependencies: the server's own packages (skipped with --offline). High or critical is a FAIL, moderate a WARN.
if (!args.has('--offline')) {
  try {
    const raw = execFileSync('npm', ['audit', '--omit=dev', '--json'], { cwd: path.join(root, 'functions'), encoding: 'utf8', timeout: 90000, stdio: ['ignore', 'pipe', 'ignore'] });
    report(raw);
  } catch (e) { if (e.stdout) report(e.stdout); else add('WARN', 'deps', 'could not run the dependency audit (offline?)'); }
}
function report(raw) {
  try {
    const v = (JSON.parse(raw).metadata || {}).vulnerabilities || {};
    const line = ['critical', 'high', 'moderate', 'low'].map((k) => k + ' ' + (v[k] || 0)).join(', ');
    add((v.critical || 0) + (v.high || 0) ? 'FAIL' : ((v.moderate || 0) ? 'WARN' : 'PASS'), 'deps', 'server dependencies: ' + line + ' (npm audit --omit=dev in functions/)');
  } catch (e) { add('WARN', 'deps', 'the dependency audit gave no readable answer'); }
}

const order = { FAIL: 0, WARN: 1, INFO: 2, PASS: 3 };
out.sort((a, b) => order[a.level] - order[b.level]);
out.forEach((o) => console.log(o.level.padEnd(4) + '  [' + o.id + '] ' + o.msg));
const fails = out.filter((o) => o.level === 'FAIL').length, warns = out.filter((o) => o.level === 'WARN').length;
console.log('\nSECURITY SCAN: ' + (fails ? fails + ' FAIL' : 'no FAIL') + ', ' + warns + ' WARN.');
process.exit(fails ? 1 : 0);
