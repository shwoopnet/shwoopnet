'use strict';
// Nov 12, 2026 (owner direction): the Deribit recorder is stopped. Deribit's terms forbid use beyond personal use, and the account holder is an LLC. W-DERIBIT1 is retired.
// The data already recorded on the data branch stays there as history and is not read further. This gate keeps a Deribit host from coming back unnoticed in a workflow, script or function.
// Comments are scanned too on purpose. This file, CLAUDE.md and the docs are the only places the name may appear.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const gates = {};
const BLOCKED = /deribit/i;
const list = (dir, re) => fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => re.test(f)).map((f) => path.join(dir, f)) : [];

// DB1: the recorder workflow and script are gone.
gates.DB1 = () => {
  assert.ok(!fs.existsSync(path.join(root, '.github', 'workflows', 'record-deribit.yml')), 'the Deribit workflow is deleted');
  assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_deribit.py')), 'the Deribit script is deleted');
};

// DB2: no workflow, script or function names Deribit, and the signal logger allowlist does not hold the host.
gates.DB2 = () => {
  const files = [
    ...list(path.join(root, '.github', 'workflows'), /\.ya?ml$/),
    ...list(path.join(root, 'scripts'), /\.(py|js|sh)$/),
    ...list(path.join(root, 'functions'), /\.(js|sh)$/),
  ];
  assert.ok(files.length > 15, 'the recorder workflows and scripts are found');
  const hits = [];
  for (const f of files) fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => { if (BLOCKED.test(line)) hits.push(path.relative(root, f) + ':' + (i + 1)); });
  assert.deepStrictEqual(hits, [], 'no Deribit host anywhere a job could read it: ' + hits.join(', '));
};

// DB3: the signal registry does not point a signal at it.
gates.DB3 = () => {
  const reg = path.join(root, 'kalshi-scalper', 'signals', 'REGISTRY.json');
  if (fs.existsSync(reg)) assert.ok(!BLOCKED.test(fs.readFileSync(reg, 'utf8')), 'REGISTRY.json names no Deribit URL');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
