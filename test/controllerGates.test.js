'use strict';
// The Controller (the owner, Nov 7, 2026: "do we have someone for accounting? managing bills, subscriptions, cutting costs"). It keeps a PRIVATE ledger and drafts cuts; it must never touch accounts, money, secrets, code or git.
// Gate names CT1 to CT4 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const agent = fs.readFileSync(path.join(__dirname, '..', '.claude', 'agents', 'controller.md'), 'utf8');
const gates = {};

gates.CT1 = () => {
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  for (const t of tools) assert.ok(!/Write|NotebookEdit|send_message|send_later|create_trigger|update_trigger|delete_trigger|fire_trigger|interrupt|archive|set_session|publish_files|publish_version|pin_artifact/.test(t), 'no tool outside its limits: ' + t);
  for (const t of ['Read', 'mcp__claude-artifacts__read_artifact', 'mcp__claude-artifacts__edit_version', 'mcp__claude-code-remote__get_session']) assert.ok(tools.includes(t), 'has: ' + t);
};
gates.CT2 = () => {
  // The repo is public, so the ledger must live outside it.
  assert.ok(/PUBLIC repository/.test(agent) && /never in git and never in a pull request/.test(agent), 'the ledger stays out of the public repo');
  assert.ok(/KEEP, REVIEW, CUT/.test(agent), 'verdict words');
};
gates.CT3 = () => {
  assert.ok(/Log in anywhere/.test(agent) && /pay, cancel, subscribe, change a plan or move money/.test(agent), 'no accounts, no money');
  assert.ok(/card number, account number, password, key, token or address/.test(agent) && /Never print a secret/.test(agent), 'no secrets held');
  assert.ok(/Never present a list-price usage value as a bill/.test(agent), 'usage is not a bill');
};
gates.CT4 = () => {
  assert.ok(!/firebase deploy|deploy-sizing|deploy-push|deploy-report/.test(agent), 'no deploy command');
  assert.ok(!/KALSHI_REPORT_TOKEN/.test(agent), 'no token');
  assert.ok(!/—/.test(agent), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
