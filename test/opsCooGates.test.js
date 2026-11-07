'use strict';
// The operations officer (the owner, Nov 6, 2026: "someone monitor (think COO or workforce management) guiding and directing, as well as cutting down on pointless caches or tasks that are circling or just dead-ending"). It drafts; it must not be able to change routines, message chats, edit or deploy.
// Gate names OC1 to OC4 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const agent = fs.readFileSync(path.join(__dirname, '..', '.claude', 'agents', 'ops-coo.md'), 'utf8');
const gates = {};

gates.OC1 = () => {
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  for (const t of tools) assert.ok(!/Edit|Write|NotebookEdit|send_message|send_later|create_trigger|update_trigger|delete_trigger|fire_trigger|interrupt|archive|create_session|set_session/.test(t), 'no write or control tool: ' + t);
  for (const t of ['Read', 'mcp__claude-code-remote__get_session', 'mcp__claude-code-remote__list_triggers']) assert.ok(tools.includes(t), 'reads: ' + t);
};
gates.OC2 = () => {
  assert.ok(/KEEP/.test(agent) && /SLOW DOWN/.test(agent) && /MERGE/.test(agent) && /RETIRE/.test(agent), 'the four routine verdicts');
  assert.ok(/for the owner to approve/.test(agent) && /relays an approved directive/.test(agent), 'drafts only, the main session relays');
};
gates.OC3 = () => {
  assert.ok(/credit guard/.test(agent) && /loss stop and exit watch alarms/.test(agent) && /nightly order report/.test(agent), 'safety routines are protected');
  assert.ok(/Never promise a dollar saving you cannot compute/.test(agent), 'no invented savings');
};
gates.OC4 = () => {
  assert.ok(/Never print a secret|Print a secret or ask for one/.test(agent) && !/KALSHI_REPORT_TOKEN/.test(agent), 'no secret handling');
  assert.ok(!/firebase deploy|deploy-sizing|deploy-push|deploy-report/.test(agent), 'no deploy command');
  assert.ok(!/—/.test(agent), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
