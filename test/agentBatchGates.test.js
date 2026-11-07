'use strict';
// The batch from the owner's 1:1 review of the agents (Nov 7, 2026): the director folds into the COO, the Auditor merges into the Verification Analyst, the release team coordinates, freshness runs weekly.
// Gate names AB1 to AB6 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const coo = read('.claude/agents/ops-coo.md'), fc = read('.claude/agents/fact-checker.md'), rm = read('.claude/agents/release-manager.md'), sec = read('.claude/agents/security.md'), fresh = read('.claude/agents/freshness.md'), dir = read('.claude/agents/research-director.md'), charter = read('docs/CHARTER.md');
const gates = {};

gates.AB1 = () => {
  // The COO runs the census itself but cannot approve its own draft alone, and slows itself when idle.
  assert.ok(/Breadth census/.test(coo) && /may not approve your own draft on your say alone/.test(coo) && /marks CONFIRMED/.test(coo), 'census with an independent feasibility check');
  assert.ok(/If three runs in a row ended with nothing to decide, slow it to every other day/.test(coo) && /every 6 hours, not every 2/.test(coo), 'self-slowing and the idle research chat cadence');
  assert.ok(/Now run by the COO/.test(dir), 'the director file points at the COO');
};
gates.AB2 = () => {
  // One verification role with two modes; the only push it may make is its audit log.
  assert.ok(/Verification Analyst/.test(fc) && /Audit mode/.test(fc) && /claude\/research-audit/.test(fc), 'audit mode merged in');
  assert.ok(/push anything except your audit log on branch `claude\/research-audit`/.test(fc), 'its only push is the audit log');
  const tools = /^tools:\s*(.+)$/m.exec(fc)[1].split(',').map((t) => t.trim());
  assert.deepStrictEqual(tools.sort(), ['Bash', 'Glob', 'Grep', 'Read'], 'still read only');
};
gates.AB3 = () => {
  // The Release Manager keeps the trial log, calls verification, and hands sensitive changes to security.
  assert.ok(/ops\/RELEASE_LOG\.md/.test(rm) && /claude\/release-log/.test(rm) && /never main/.test(rm), 'the trial log');
  assert.ok(/Ask the Verification Analyst/.test(rm) && /security review requested/.test(rm), 'verification and security hand-offs');
  const tools = /^tools:\s*(.+)$/m.exec(rm)[1].split(',').map((t) => t.trim());
  for (const t of tools) assert.ok(!/merge|create_pull_request|update_pull_request|add_issue_comment|Write|Edit/.test(t), 'the Release Manager still has no write tool: ' + t);
};
gates.AB4 = () => {
  assert.ok(/security review requested/.test(sec) && /never in the public repo/.test(sec) && /weekly deep sweep is proposed separately/.test(sec), 'security coordinates, keeps findings private and does not start a weekly sweep unasked');
};
gates.AB5 = () => {
  assert.ok(/weekly \(Sundays\), in a fresh session/.test(fresh) && /Release Manager/.test(fresh), 'freshness is weekly and reports to the Release Manager');
};
gates.AB6 = () => {
  assert.ok(/Research method: backtest first/.test(charter) && /data inventory/.test(charter) && /hold up on data the scan never saw/.test(charter) && /At most three analysts run at once/.test(charter), 'the backtest-first mandate is in the Charter');
  assert.ok(/The release team/.test(charter) && /The owner merges/.test(charter), 'the release team and who merges');
  assert.ok(!/—/.test(coo + fc + rm + sec + fresh + dir + charter), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
