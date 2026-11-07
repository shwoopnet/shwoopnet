'use strict';
// The release manager (the owner, Nov 7, 2026: "chief of staff that reads and reviews all PRs and ships prior to handing off to me", option 1 with a two week trial). It reviews; it never merges, pushes, comments or deploys.
// Gate names RM1 to RM4 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const agent = fs.readFileSync(path.join(root, '.claude', 'agents', 'release-manager.md'), 'utf8');
const charter = fs.readFileSync(path.join(root, 'docs', 'CHARTER.md'), 'utf8');
const gates = {};

gates.RM1 = () => {
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  for (const t of tools) assert.ok(!/merge|create_pull_request|update_pull_request|add_issue_comment|add_comment|pull_request_review_write|request_copilot|create_or_update_file|push_files|delete_file|create_branch|Write|Edit|send_message|update_trigger|enable_pr_auto_merge/.test(t), 'no write tool: ' + t);
  for (const t of ['Read', 'Bash', 'mcp__github__pull_request_read']) assert.ok(tools.includes(t), 'has: ' + t);
};
gates.RM2 = () => {
  assert.ok(/READY/.test(agent) && /NEEDS CHANGES/.test(agent) && /NEEDS YOU/.test(agent), 'the three answers');
  assert.ok(/Merge, close or update a pull request, push to its branch, post a comment or review/.test(agent) && /Deploy, run a deploy script/.test(agent), 'it never merges, comments or deploys');
  assert.ok(/pre-ship/.test(agent) && /siteFreshnessGates/.test(agent) && /security-audit/.test(agent) && /for f in test\/\*\.test\.js/.test(agent), 'it runs the gates');
};
gates.RM3 = () => {
  // The trial rule: Charter and agent files always come to the owner.
  assert.ok(/docs\/CHARTER\.md/.test(agent) && /\.claude\/agents\//.test(agent) && /always NEEDS YOU/.test(agent), 'Charter and agent-file changes are the owner\'s');
  assert.ok(/Release trial \(Nov 7 to Nov 21, 2026\)/.test(charter) && /merges nothing/.test(charter) && /Whether a pull request is ready \| \*\*Release Manager\*\* reviews; \*\*Owner\*\* merges/.test(charter), 'the Charter records the trial and who merges');
};
gates.RM4 = () => {
  assert.ok(/PUBLIC/.test(agent) && /personal finance figure/.test(agent), 'public repo rules');
  assert.ok(!/firebase deploy|deploy-sizing\.sh --yes|KALSHI_REPORT_TOKEN/.test(agent), 'no deploy command run, no token');
  assert.ok(!/—/.test(agent), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
