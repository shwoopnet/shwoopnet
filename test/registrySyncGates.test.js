'use strict';
// Nov 13, 2026: the registry sync (scripts/sync_registry.py, .github/workflows/sync-registry.yml).
// Consequence: a sync can only ever refresh the generated wheel and closure rows; it cannot touch a live strategy, loosen a gate, push to main or merge.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const gates = {};
const script = fs.readFileSync(path.join(root, 'scripts/sync_registry.py'), 'utf8');
const wf = fs.readFileSync(path.join(root, '.github/workflows/sync-registry.yml'), 'utf8');
const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
const HAND = ['L1', 'OICORE', 'EVENT830', 'GOLDOFF', 'W-SPOTLEAD1', 'CFRTIK', 'S3', 'NC15DEPTH1', 'MMSIM1'];

// A scratch git repo with a fake rnd-queue branch, so the gate needs no network and never the real branch.
function scratch(admitExtra) {
  const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'regsync-'));
  const sh = (...a) => execFileSync('git', a, { cwd: dir, stdio: 'pipe' });
  sh('init', '-q'); sh('config', 'user.email', 'a@b.c'); sh('config', 'user.name', 'x');
  const admit = 'CFRTI-K on Bitcoin. silver, copper, WTI, HYPE, BNB, USD/CAD. five further CFRTI-K places. INPLAYJUMP ESOCTIE. EUR/USD 13, GBP/USD 0. WITHDRAWN Nov 13 00:48Z REMATCH closed at stage 1\n**ADMITTED, BATCH 2, dated 2026-11-13T00:23:49Z (recorded 00:24Z).**\n' + (admitExtra || '');
  fs.writeFileSync(path.join(dir, 'WHEEL_ADMIT_LIST.md'), admit);
  fs.writeFileSync(path.join(dir, 'RND_QUEUE.md'), 'PERPBIN1: FALSIFIED on development\nS2 long leg (stocks)\nPOL-i2: CLOSED on cost\nPROPUNDER\nPREMOVE WITHDRAWN UNREAD\nPREDRIFT\n');
  sh('add', '.'); sh('commit', '-q', '-m', 'q'); sh('branch', '-M', 'rnd-queue');
  const regPath = path.join(dir, 'registry.json');
  return { dir, regPath, run: (...extra) => execFileSync('python3', ['-I', path.join(root, 'scripts/sync_registry.py'), '--ref', 'rnd-queue', '--registry', regPath, ...extra], { cwd: dir, encoding: 'utf8', stdio: 'pipe' }) };
}

gates.RS1 = () => {
  // Consequence: the generated registry still passes the registry gates (schema, UNPROVEN labels, causes, no result figures).
  const out = execFileSync('node', [path.join(__dirname, 'strategyRegistryGates.test.js')], { encoding: 'utf8' });
  assert.ok(!/FAIL/.test(out));
  const wh = reg.strategies.filter((x) => x.id.startsWith('WH-'));
  assert.strictEqual(wh.filter((x) => x.stage === 'Shadow').length, 19 - 0, 'the 19 admitted wheel places are Shadow rows');
  assert.ok(wh.filter((x) => x.stage === 'Retired').length === 4, 'the four withdrawn forex places are Retired');
  for (const id of ['CL-MAPBREAK', 'CL-REMATCH', 'CL-TIE3', 'CL-WXDAYEND']) { const x = reg.strategies.find((y) => y.id === id); assert.ok(x && x.stage === 'Retired' && x.cause === 'failed the bar', id + ' is Retired (failed the bar)'); }
  assert.ok(!/PENDING RECOUNT/i.test(JSON.stringify(reg)), 'MAPBREAK is closed, never pending');
};

gates.RS2 = () => {
  // Consequence: running the sync twice changes nothing, and a hand-written row (live strategies, hand notes) is never overwritten.
  const s = scratch();
  fs.writeFileSync(s.regPath, JSON.stringify({ asOf: 'x', note: 'n', stages: reg.stages, strategies: reg.strategies.filter((x) => HAND.includes(x.id)).map((x) => (x.id === 'L1' ? { ...x, notes: ['HAND NOTE'] } : x)) }, null, 1) + '\n');
  s.run();
  const first = fs.readFileSync(s.regPath, 'utf8');
  assert.ok(/registry unchanged/.test(s.run()), 'second run reports unchanged');
  assert.strictEqual(fs.readFileSync(s.regPath, 'utf8'), first, 'idempotent');
  const out = JSON.parse(first);
  assert.deepStrictEqual(out.strategies.find((x) => x.id === 'L1').notes, ['HAND NOTE'], 'a hand note survives');
  assert.deepStrictEqual(out.strategies.filter((x) => HAND.includes(x.id)).map((x) => x.id), HAND.filter((i) => out.strategies.some((x) => x.id === i)), 'hand rows keep their order and content');
  assert.ok(out.strategies.every((x) => HAND.includes(x.id) || /^(WH|CL)-/.test(x.id)), 'only WH- and CL- rows are generated');
  assert.ok(/6:23 PM CT/.test(out.strategies.find((x) => x.id === 'WH-NC15-WTI').nextReadText), 'the counting start comes from the list, in Central time');
};

gates.RS3 = () => {
  // Consequence: a reworded ledger fails closed: no write when a source line a row rests on is gone.
  const s = scratch();
  fs.writeFileSync(s.regPath, JSON.stringify({ asOf: 'x', note: 'n', stages: reg.stages, strategies: [] }) + '\n');
  fs.writeFileSync(path.join(s.dir, 'RND_QUEUE.md'), 'nothing relevant');
  execFileSync('git', ['commit', '-qam', 'q2'], { cwd: s.dir });
  const before = fs.readFileSync(s.regPath, 'utf8');
  assert.throws(() => s.run(), /fail closed|no longer found/i);
  assert.strictEqual(fs.readFileSync(s.regPath, 'utf8'), before, 'nothing written');
};

gates.RS4 = () => {
  // Consequence: the workflow cannot reach main or merge anything. It opens or updates a PR from registry-sync/auto and refuses a file failing the gates.
  assert.ok(/workflow_dispatch/.test(wf) && /cron: "17 /.test(wf) && !/cron: "0 /.test(wf), 'scheduled at a minute offset, and by hand');
  assert.ok(!/git push[^\n]*\bmain\b/.test(wf) && !/HEAD:main|:refs\/heads\/main/.test(wf), 'never pushes to main');
  const pushes = wf.match(/git push[^\n]*/g) || [];
  assert.ok(pushes.length === 1 && /origin registry-sync\/auto$/.test(pushes[0]), 'the only push is the bot branch');
  assert.ok(!/gh pr merge|--auto|merge_pull_request|enable-auto-merge/.test(wf), 'never merges');
  assert.ok(/permissions:\s*\n\s+contents: write\s*\n\s+pull-requests: write/.test(wf) && !/secrets\./.test(wf), 'only the built-in token, contents and pull-requests');
  assert.ok(/git diff --quiet/.test(wf) && /strategyRegistryGates/.test(wf) && /noLiveFiguresGates/.test(wf), 'skips when unchanged and runs the gates before pushing');
  assert.ok(/ref: main/.test(wf) && /@[0-9a-f]{40}/.test(wf), 'checks out main with a pinned action');
  assert.ok(!/https?:\/\//.test(script.replace(/"""[\s\S]*?"""/, '')), 'the script names no host');
  assert.ok(!/urllib|requests|socket|os\.environ/.test(script), 'the script has no network or environment access');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
