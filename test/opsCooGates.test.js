'use strict';
// The operations officer (the owner, Nov 6, 2026: "someone monitor (think COO or workforce management) guiding and directing, as well as cutting down on pointless caches or tasks that are circling or just dead-ending"). The owner (Nov 7, 2026) then gave it the calls on saving credits and guiding research, within written limits: it may slow, merge or retire (disable) routines and send guidance, and nothing else.
// Gate names OC1 to OC4 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const agent = fs.readFileSync(path.join(__dirname, '..', '.claude', 'agents', 'ops-coo.md'), 'utf8');
const gates = {};

gates.OC1 = () => {
  // It may slow, merge or retire a routine and guide a chat, and nothing more: no code, no session life, no creating, firing or deleting routines.
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  for (const t of tools) assert.ok(!/Edit|Write|NotebookEdit|send_later|create_trigger|delete_trigger|fire_trigger|interrupt|archive|create_session|set_session|add_repo/.test(t), 'no tool outside its limits: ' + t);
  for (const t of ['Read', 'mcp__claude-code-remote__get_session', 'mcp__claude-code-remote__list_triggers', 'mcp__claude-code-remote__update_trigger', 'mcp__claude-code-remote__send_message']) assert.ok(tools.includes(t), 'has: ' + t);
};
gates.OC2 = () => {
  assert.ok(/KEEP/.test(agent) && /SLOW DOWN/.test(agent) && /MERGE/.test(agent) && /RETIRE/.test(agent), 'the four routine verdicts');
  assert.ok(/Limits on your calls/.test(agent) && /only spend LESS or point work at something better under the Charter/.test(agent) && /At most five calls per run/.test(agent), 'the call limits are written down');
  assert.ok(/Research direction \(Charter level 1\)/.test(agent) && /brief checklist/.test(agent) && /at most two/.test(agent), 'research direction is bounded by the Charter checklist');
  assert.ok(/never delete/.test(agent) && /reversible/.test(agent), 'retire means disable, and every call is reversible');
};
gates.OC3 = () => {
  assert.ok(/credit guard/.test(agent) && /exit watch and loss stop alarms/.test(agent) && /nightly order report/.test(agent), 'safety routines are protected');
  assert.ok(/Never promise a dollar saving you cannot compute/.test(agent), 'no invented savings');
  assert.ok(/Never interrupt, archive or unarchive a session/.test(agent) && /never a command to change trading code/.test(agent), 'no session life, no trading commands');
};
gates.OC4 = () => {
  assert.ok(/Print a secret or ask for one/.test(agent) && !/KALSHI_REPORT_TOKEN/.test(agent), 'no secret handling');
  assert.ok(!/firebase deploy|deploy-sizing|deploy-push|deploy-report/.test(agent), 'no deploy command');
  assert.ok(!/—/.test(agent), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
