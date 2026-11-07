'use strict';
// The Charter (the owner, Nov 7, 2026: "I'd like our COO or our agents to actually perform and make sound decisions based on our end goal so I don't have to sit here constantly"). Autonomy for research direction and cost; money, live changes, deploys and merges stay with the owner.
// The repo is PUBLIC: no personal figures. Gate names CH1 to CH5 are local to this file.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const charter = fs.readFileSync(path.join(root, 'docs', 'CHARTER.md'), 'utf8');
const coo = fs.readFileSync(path.join(root, '.claude', 'agents', 'ops-coo.md'), 'utf8');
const gates = {};

gates.CH1 = () => {
  // Money and anything live stay with the owner.
  assert.ok(/Anything goes live, changes a live rule, size, stop or market \| \*\*Owner\*\*/.test(charter), 'going live is the owner\'s');
  assert.ok(/Merge a pull request, run a deploy command \| \*\*Owner\*\*/.test(charter) && /Spend money, change a plan, pay, cancel \| \*\*Owner\*\*/.test(charter), 'merge, deploy and money are the owner\'s');
  assert.ok(/Change this Charter, the research bar or the bans \| \*\*Owner\*\*/.test(charter), 'the Charter is the owner\'s');
  assert.ok(/no level where an agent changes a live rule, a size, a stop or a market, spends money or deploys by itself/i.test(charter), 'no level lets an agent do these');
};
gates.CH2 = () => {
  // The bar and the brief checklist are written before any result.
  assert.ok(/profit factor 1\.5 or better in each of three history windows after fees and after deflating/.test(charter) && /held out and read once/.test(charter), 'the bar');
  assert.ok(/The brief checklist/i.test(charter) && /named counterparty/.test(charter) && /numeric prediction/.test(charter) && /cheap side only/i.test(charter), 'the brief checklist');
};
gates.CH3 = () => {
  // The owner is interrupted only by the written tripwires, and a packet exists for going live.
  for (const w of ['A result clears the bar', 'A loss stop trips', 'Any request to spend money', 'Two agents disagree', 'credit guard']) assert.ok(charter.includes(w), 'tripwire: ' + w);
  assert.ok(/promotion packet/i.test(charter) && /never goes live by itself/.test(charter) && /fact checker/i.test(charter), 'the packet');
};
gates.CH4 = () => {
  // The COO's authority points at the Charter and stays inside its checklist.
  assert.ok(/docs\/CHARTER\.md/.test(coo) && /Research direction \(Charter level 1\)/.test(coo), 'the COO reads the Charter');
  assert.ok(/send a chat to a family that has not passed the Charter's brief checklist/.test(coo), 'no unapproved family');
  assert.ok(/Never\*\* approve a brief that needs money/.test(coo), 'money briefs go to the owner');
};
gates.CH6 = () => {
  // The credit watch: a ladder driven by what the platform shows, no invented percentage, budget kept out of the public file.
  assert.ok(/Credit watch and the throttle ladder/.test(charter) && /It does not show a percentage used/.test(charter), 'the ladder is built on visible figures');
  assert.ok(/Normal/.test(charter) && /Warning/.test(charter) && /Stop/.test(charter) && /No new workers/.test(charter), 'three steps');
  assert.ok(/Burn and the throttle ladder/.test(coo) && /no percentage of the session limit used; say so rather than guess/.test(coo), 'the COO logs burn and does not guess a percentage');
};
gates.CH7 = () => {
  // Tokens are a cost too: written efficiency rules, owned by the COO, measured per verdict.
  assert.ok(/Efficiency across the board \(tokens and credits\)/.test(charter) && /Read once\./.test(charter) && /Fresh and short beats big and warm/.test(charter) && /No agent for a three-call job/.test(charter), 'the efficiency rules');
  assert.ok(/tokens per verdict/i.test(charter) && /Token efficiency \(Charter/.test(coo) && /get_trigger/.test(coo), 'the COO measures tokens per verdict');
};
gates.CH5 = () => {
  // Public repo: no personal finance figures, no secrets, no em dashes.
  assert.ok(!/—/.test(charter), 'no em dashes');
  assert.ok(!/income gap|VA income|\bVA\b|tax set-aside|\$\d{2,}/i.test(charter), 'no personal finance figures in a public file');
  assert.ok(!/KALSHI_REPORT_TOKEN|api key|password/i.test(charter), 'no secrets');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
