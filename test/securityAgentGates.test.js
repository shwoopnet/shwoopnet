'use strict';
// The security agent and its scan (Oct 22, 2026). Consequence: the agent that guards a repo placing real orders cannot quietly lose its rules, and the scan it relies on really fails on a bad repo, not only passes on a good one.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync, execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const scan = path.join(root, '.claude', 'skills', 'security-audit', 'scripts', 'scan.js');
const gates = {};
const front = (text) => { const m = text.match(/^---\n([\s\S]*?)\n---\n/); assert.ok(m, 'has frontmatter'); const o = {}; m[1].split('\n').forEach((l) => { const i = l.indexOf(':'); if (i > 0) o[l.slice(0, i).trim()] = l.slice(i + 1).trim(); }); return o; };

// The agent is defined, can read and fix but cannot reach the web or spawn others, and its rules are written down.
gates.SA1 = () => {
  const text = fs.readFileSync(path.join(root, '.claude', 'agents', 'security.md'), 'utf8');
  const f = front(text);
  assert.strictEqual(f.name, 'security');
  assert.ok(f.description.length > 80 && /never merges, never deploys/.test(f.description), 'a description that says when to use it and what it never does');
  assert.deepStrictEqual(f.tools.split(',').map((t) => t.trim()).sort(), ['Bash', 'Edit', 'Glob', 'Grep', 'Read', 'Write'], 'exactly these tools: no web fetch, no spawning other agents');
  [/Never print, copy or ask for a secret/, /repository is public/i, /Never merge, never deploy/, /Never loosen or delete a gate/, /Never touch trading behaviour/, /email_verified/, /after `git add`/, /owner actions?/i, /scan\.js/]
    .forEach((re) => assert.ok(re.test(text), 'the agent states: ' + re));
  assert.ok(!/—/.test(text), 'no em dashes');
  assert.ok(!/heiszcam|@gmail\.com/.test(text), 'no personal address in a public file');
};

gates.SA2 = () => {
  const text = fs.readFileSync(path.join(root, '.claude', 'skills', 'security-audit', 'SKILL.md'), 'utf8');
  const f = front(text);
  assert.strictEqual(f.name, 'security-audit');
  assert.ok(/security agent/.test(text) && /never print or ask for a secret/i.test(text) && !/—/.test(text));
};

// The scan is clean on this repo (a regression here fails the build, so a weakness cannot slip in unseen).
gates.SA3 = () => {
  const r = spawnSync('node', [scan, '--offline'], { cwd: root, encoding: 'utf8' });
  assert.strictEqual(r.status, 0, 'the scan passes on the repo:\n' + r.stdout.split('\n').filter((l) => /^FAIL/.test(l)).join('\n'));
  assert.ok(/SECURITY SCAN: no FAIL/.test(r.stdout));
};

// The scan really catches problems: a fake repo with a key file, an unpinned workflow, an open rule, a callable that never checks its caller and an open HTTP endpoint must FAIL on each.
gates.SA4 = () => {
  const d = fs.mkdtempSync(path.join(os.tmpdir(), 'badrepo-'));
  const w = (f, t) => { fs.mkdirSync(path.dirname(path.join(d, f)), { recursive: true }); fs.writeFileSync(path.join(d, f), t); };
  w('index.html', '<html><body><script>eval("1")</script></body></html>');
  w('functions/.gitignore', 'node_modules/\n');
  w('functions/index.js', 'exports.doIt = onCall(async (request) => {\n  return 1;\n});\nexports.hook = onRequest((req, res) => res.send(1));\n');
  w('firestore.rules', "rules_version = '2';\nservice cloud.firestore { match /databases/{database}/documents {\n match /kalshiLiveOrders/{id} { allow read, write: if true; }\n } }\n");
  w('.github/workflows/x.yml', 'name: x\non: pull_request_target\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n');
  w('config/server.key', 'not really a key');
  w('notes.txt', '-----BEGIN ' + 'PRIVATE KEY-----\nabc\n');
  const git = (a) => execFileSync('git', a, { cwd: d, stdio: 'ignore' });
  git(['init', '-q']); git(['add', '-A']); git(['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x']);
  const r = spawnSync('node', [scan, '--offline', '--root', d], { encoding: 'utf8' });
  assert.strictEqual(r.status, 1, 'a bad repo fails the scan');
  [/FAIL\s+\[secrets\] a key or env file is tracked: config\/server\.key/, /FAIL\s+\[secrets\] notes\.txt contains a private key block/, /FAIL\s+\[secrets\] functions\/\.gitignore ignores/, /FAIL\s+\[workflows\].*not pinned/, /FAIL\s+\[workflows\].*pull_request_target/,
    /FAIL\s+\[rules\] a rule allows everything/, /FAIL\s+\[functions\].*callable does not check/, /FAIL\s+\[functions\].*open HTTP endpoint/, /FAIL\s+\[page\] index\.html uses eval/, /FAIL\s+\[page\] the frame guard is present/]
    .forEach((re) => assert.ok(re.test(r.stdout), 'the scan reports: ' + re + '\n' + r.stdout));
  assert.ok(!/notes\.txt contains[^\n]*abc/.test(r.stdout), 'it never prints a secret value');
  fs.rmSync(d, { recursive: true, force: true });
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
