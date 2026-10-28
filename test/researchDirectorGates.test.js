'use strict';
// The research director (the owner, Oct 28, 2026): it watches the research session, keeps the search broad and drafts briefs. It must never be able to change code, send a brief, deploy or promote a strategy,
// and its scoreboard must say what it is built to say. Gate names R1 to R7 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const agent = fs.readFileSync(path.join(root, '.claude', 'agents', 'research-director.md'), 'utf8');
const skill = fs.readFileSync(path.join(root, '.claude', 'skills', 'research-director', 'SKILL.md'), 'utf8');
const sb = require('../.claude/skills/research-director/scripts/scoreboard.js');
const gates = {};

gates.R1 = () => {
  // It can read and run read-only commands and nothing else: no Edit, no Write, no notebook edit, no messaging tool.
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  assert.deepStrictEqual(tools.sort(), ['Bash', 'Glob', 'Grep', 'Read']);
};
gates.R2 = () => {
  // The rules that stop it becoming an overfitting machine are written down in both files.
  for (const [name, text] of [['agent', agent], ['skill', skill]]) {
    assert.ok(/never (send|sends)|DRAFT/i.test(text) && /FALSIFIED/.test(text) && /NOT_YET_FALSIFIED is not a pass/.test(text), name + ': drafts only, the verdict words, and NOT_YET_FALSIFIED is not a pass');
    assert.ok(/variant of L1 is not a new strategy/i.test(text), name + ': an L1 variant is not new');
    assert.ok(!/(^|[^a-z])em dash(es)?[^.]*use/i.test(text) || /never use em dashes/i.test(text));
  }
  assert.ok(!/—/.test(agent) && !/—/.test(skill), 'no em dashes');
};
gates.R3 = () => {
  // The success bar is fixed in the file, before any result: profit factor 1.5 in three windows, after the fee and after deflating for the number tried.
  assert.ok(/profit factor at or above \*\*1\.5 in each of three windows\*\*/.test(skill));
  assert.ok(/AFTER deflating/.test(skill) && /counterparty/.test(skill) && /numeric prediction/.test(skill));
  assert.ok(/hope, not a test/.test(skill), 'it does not promise positive weeks');
};
gates.R4 = () => {
  // It never touches trading code or deploys.
  assert.ok(/Edit anything under `functions\/`/.test(skill) && /Send a brief to the research session itself/.test(skill));
  assert.ok(!/firebase deploy|deploy-sizing|deploy-push/.test(agent), 'the agent file holds no deploy command');
};
gates.R5 = () => {
  // The scoreboard counts L1 variants the way the ledger writes them, including scalps and opening-window tests on the same contracts.
  const regs = sb.registrations([
    '## Pre-registration: B4, L1 one band lower, 84c to 88c (the owner\'s idea; fixed 2026-10-10, before any code)',
    '## Pre-registration: T5, the cheap side scalped at tick level in minutes 5 to 8 (fixed 2026-10-10)',
    '## Pre-registration: W1, daily highs against public forecasts (fixed 2026-10-11, before any code)',
    '## Results: B4, one run, read once (2026-10-10)',   // a result reports an earlier registration: not new work
    '## A heading with no date',
  ].join('\n'));
  assert.strictEqual(regs.length, 3, 'a Results heading is not new work');
  assert.deepStrictEqual(regs.map((r) => r.l1), [true, true, false]);
};
gates.R6 = () => {
  // Drift is reported when more than half of the recent registrations are L1 variants, and the families that were never mentioned are named.
  const dir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'rd-'));
  const readme = path.join(dir, 'README.md');
  fs.writeFileSync(readme, ['## Pre-registration: B1, L1 band (fixed 2026-10-20)', '## Pre-registration: X1, L1 exits (fixed 2026-10-21)', '## Pre-registration: S1, L1 sizing (fixed 2026-10-22)', '## Pre-registration: W1, weather highs (fixed 2026-10-22)'].join('\n'));
  const s = sb.build({ readme, mechanisms: null, ledger: null, events: null, days: 14, now: '2026-10-28' });
  assert.deepStrictEqual([s.registrations.recent, s.registrations.recentL1], [4, 3]);
  const out = sb.render(s);
  assert.ok(/DRIFT: more than half/.test(out));
  assert.ok(/Never mentioned anywhere:[^\n]*sports/.test(out) && !/Never mentioned anywhere:[^\n]*weather/.test(out));
  // Messages from the research session are measured too.
  const evf = path.join(dir, 'ev.json');
  fs.writeFileSync(evf, JSON.stringify(Array.from({ length: 10 }, () => 'tuning the L1 band again')));
  const s2 = sb.build({ readme, mechanisms: null, ledger: null, events: evf, days: 14, now: '2026-10-28' });
  assert.ok(/most of the research session's recent messages/.test(sb.render(s2)));
};
gates.R7 = () => {
  // The checklist covers families that are NOT the live strategy: weather, economic releases, sports, events, calibration and cross-market, so there is somewhere new to look.
  const keys = sb.FAMILIES.filter((f) => !f.live).map((f) => f.key);
  for (const k of ['weather', 'econ', 'sports', 'events', 'longshot', 'cross']) assert.ok(keys.indexOf(k) > -1, k);
  // And it runs on the real ledger without error, read only.
  const out = require('child_process').execFileSync('node', [path.join(root, '.claude', 'skills', 'research-director', 'scripts', 'scoreboard.js'), '--days', '30', '--now', '2026-10-13'], { encoding: 'utf8' });
  assert.ok(/RESEARCH SCOREBOARD/.test(out) && /There is no promote verb/.test(out));
};

let failed = 0;
for (const k of Object.keys(gates)) { try { gates[k](); console.log(k + ' PASS'); } catch (e) { failed++; console.log(k + ' FAIL ' + e.message); } }
process.exit(failed ? 1 : 0);
