'use strict';
// Nov 11, 2026 (owner direction): no Open-Meteo reads. Open-Meteo's hosted API is free for NON-COMMERCIAL use only, and the account holder is an LLC trading real money. Weather research data
// now comes from the NWS API (api.weather.gov, US government, public domain). This gate keeps an Open-Meteo host from coming back unnoticed, in a workflow, a script, a function or the signal logger allowlist.
// Comments are scanned too on purpose: a host named in a comment next to code is how it started. This file and the notes are the only places the name may appear.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const gates = {};
const BLOCKED = /open-meteo\.com|openmeteo|ensemble-api\.open-meteo/i;
const list = (dir, re) => fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => re.test(f)).map((f) => path.join(dir, f)) : [];

// OM1: no workflow, script or function names an Open-Meteo host.
gates.OM1 = () => {
  const files = [
    ...list(path.join(root, '.github', 'workflows'), /\.ya?ml$/),
    ...list(path.join(root, 'scripts'), /\.(py|js|sh)$/),
    ...list(path.join(root, 'functions'), /\.(js|sh)$/),
  ];
  assert.ok(files.length > 15, 'the recorder workflows and scripts are found');
  const hits = [];
  for (const f of files) fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => { if (BLOCKED.test(line)) hits.push(path.relative(root, f) + ':' + (i + 1)); });
  assert.deepStrictEqual(hits, [], 'no Open-Meteo host anywhere a job could read it: ' + hits.join(', '));
};

// OM2: the signal logger and the weather recorder (the two files that could name an Open-Meteo host or variable) were deleted Nov 16, 2026 and stay gone.
gates.OM2 = () => {
  assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_signals.py')), 'record_signals.py is gone');
  assert.ok(!fs.existsSync(path.join(root, 'scripts', 'record_wxens.py')), 'record_wxens.py is gone');
  assert.ok(!fs.existsSync(path.join(root, 'kalshi-scalper', 'signals', 'REGISTRY.json')), 'the signal registry is gone');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
