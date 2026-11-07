'use strict';
// The fact checker (the owner, Nov 6, 2026: "do we have an agent fact checking both research and refinement chats"): it re-derives claims and answers CONFIRMED, WRONG or CANNOT_CHECK. It must stay read only, must check "live" against the code, and must not handle secrets.
// Gate names FC1 to FC4 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const agent = fs.readFileSync(path.join(__dirname, '..', '.claude', 'agents', 'fact-checker.md'), 'utf8');
const gates = {};

gates.FC1 = () => {
  const tools = /^tools:\s*(.+)$/m.exec(agent)[1].split(',').map((t) => t.trim());
  assert.deepStrictEqual(tools.sort(), ['Bash', 'Glob', 'Grep', 'Read'], 'read only: no Edit, Write or messaging tool');
};
gates.FC2 = () => {
  assert.ok(/CONFIRMED/.test(agent) && /WRONG/.test(agent) && /CANNOT_CHECK/.test(agent), 'the three verdict words');
  assert.ok(!/\bpromote\b[^.]*\b(yes|ok|approve)/i.test(agent), 'no promote verb');
};
gates.FC3 = () => {
  assert.ok(/functions\/kalshiLiveLib\.js/.test(agent) && /origin\/main/.test(agent), 'live is checked against the code on main');
  assert.ok(/A merge date is not a deploy date/.test(agent), 'merge versus deploy');
  assert.ok(/limit plus fee/.test(agent) && /avgFill/.test(agent), 'limit-booked versus fill-booked');
};
gates.FC4 = () => {
  assert.ok(/Never print a secret/.test(agent) && /KALSHI_REPORT_TOKEN/.test(agent), 'no secret handling');
  assert.ok(!/firebase deploy|deploy-sizing|deploy-push|deploy-report/.test(agent), 'no deploy command');
  assert.ok(!/—/.test(agent), 'no em dashes');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
