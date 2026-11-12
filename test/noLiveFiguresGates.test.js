'use strict';
// Standing rule (the owner, Nov 12, 2026, "rule and accept history"): no live trading figures from our
// own account in the public repo. A result, balance or sizing figure of the real account is not
// a design constant: kill lines, caps and thresholds are fine, "what the account made" is not.
//
// This gate is deliberately NARROW. It cannot tell a threshold from a result in general ("net under -$15"
// is a rule, "net +$14" is a result), so it only fails on the phrasings a RESULT takes: a profit factor
// "over N fills", "live PF 1.3", "N settled, N won", "net +$N", a market name followed by a signed dollar
// figure, "N fills, N losses". It will not catch every leak; the standing rule in CLAUDE.md is what binds.
// A line that is a research or design figure can carry [research] or [design] to opt out on purpose.
// History is accepted and not rewritten, so only the tracked files as they are now are scanned.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.join(__dirname, '..');

const PATTERNS = [
  ['profit factor over N fills', /\b(profit factor|PF)\s+[0-9.]+\s+(over|on)\s+\d+\s+(fills|orders|trades|settled)/i],
  ['live profit factor figure', /\blive\s+(cash\s+)?(profit factor|PF)\s+[0-9]/i],
  ['N settled, N won', /\b\d+\s+settled,\s+\d+\s+won/i],
  ['net with a signed dollar amount', /\bnet\s+[-+]\$\d/i],
  ['market followed by a signed dollar amount', /\b(gold|bitcoin|ethereum|xrp|dogecoin|oicore|event830)\s+[-+]\$\d/i],
  ['N fills, N losses', /\b\d+\s+(fills|orders|trades),\s+\d+\s+(losses|wins|won|lost)\b/i],
  ['N of N lost', /\b\d+\s+of\s+\d+\s+(fills|settled|orders)\s+(lost|won)/i],
];
const OPT_OUT = /\[(design|research)\]/;

function scanText(text, name) {
  const hits = [];
  text.split('\n').forEach((line, i) => {
    if (OPT_OUT.test(line)) return;
    for (const [what, re] of PATTERNS) if (re.test(line)) { hits.push(name + ':' + (i + 1) + ' (' + what + '): ' + line.match(re)[0]); break; }
  });
  return hits;
}

function trackedFiles() {
  const out = [];
  const add = (rel) => { if (fs.existsSync(path.join(root, rel))) out.push(rel); };
  add('CLAUDE.md'); add('index.html'); add('kalshi-scalper/README.md'); add('functions/DEPLOY.md');
  for (const f of fs.readdirSync(path.join(root, 'docs'))) {
    // docs/CHARTER.md is owner-only and not edited by agents.
    if (f.endsWith('.md') && f !== 'CHARTER.md') add('docs/' + f);
  }
  for (const f of fs.readdirSync(path.join(root, 'docs', 'reviews'))) if (f.endsWith('.md')) add('docs/reviews/' + f);
  for (const f of fs.readdirSync(path.join(root, 'functions'))) if (f.endsWith('.js')) add('functions/' + f);
  for (const d of ['.claude/agents']) for (const f of fs.readdirSync(path.join(root, d))) if (f.endsWith('.md')) add(d + '/' + f);
  for (const s of fs.readdirSync(path.join(root, '.claude', 'skills'))) if (s !== 'unlazy') add('.claude/skills/' + s + '/SKILL.md');
  return out;
}

const gates = {};

gates.NL1 = () => {
  // Consequence: a live result of the real account must not be committed to the public repo.
  const hits = [];
  for (const f of trackedFiles()) hits.push(...scanText(fs.readFileSync(path.join(root, f), 'utf8'), f));
  assert.deepStrictEqual(hits, [], 'live-looking figures found (move them to a message, or tag a research/design line [research] or [design]):\n' + hits.join('\n'));
};

gates.NL2 = () => {
  // The gate must fail on a deliberately bad fixture, so a passing run means something.
  const bad = [
    'XRP is profit factor 0.49 over 65 fills',
    'Dogecoin live PF 1.77 so far',
    'since Oct 20: 131 settled, 125 won',
    'the account is at net +$14.46',
    'gold +$28.35 in the first trades',
    'it had 7 fills, 3 losses',
  ];
  for (const s of bad) assert.ok(scanText(s, 'fixture').length === 1, 'should flag: ' + s);
  // A temp file goes through the same path as the real scan.
  const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'nolive-'));
  fs.writeFileSync(path.join(dir, 'x.md'), 'ok line\nBitcoin is profit factor 0.72 over 155 orders\n');
  assert.strictEqual(scanText(fs.readFileSync(path.join(dir, 'x.md'), 'utf8'), 'x.md').length, 1);
  fs.rmSync(dir, { recursive: true, force: true });
};

gates.NL3 = () => {
  // Thresholds, caps and research figures are design, not results, and must not be flagged.
  const ok = [
    'kill: net under -$15 from 20 settled fills',
    'drawdown from gold\'s own cash peak of $58.75',
    'research: held profit factor 1.85 on validation',
    'a shadow gate of 150 fills passes 12% of zero edge ideas',
    'XRP is profit factor 0.49 over 65 fills [research]',
  ];
  for (const s of ok) assert.strictEqual(scanText(s, 'fixture').length, 0, 'should not flag: ' + s);
};

gates.NL4 = () => {
  // The rule is written down where agents and testers will read it.
  const claude = fs.readFileSync(path.join(root, 'CLAUDE.md'), 'utf8');
  assert.ok(/^## No live trading figures in the repo \(Nov 12, 2026/m.test(claude), 'CLAUDE.md has the dated rule section');
  const rnd = fs.readFileSync(path.join(root, 'docs', 'RND_CHARTER.md'), 'utf8');
  assert.ok(/live trading figures/i.test(rnd), 'the R&D charter lists committing live figures as out of bounds');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
