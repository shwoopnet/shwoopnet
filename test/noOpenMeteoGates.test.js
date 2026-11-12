'use strict';
// Nov 11, 2026 (owner direction): no Open-Meteo reads. Open-Meteo's hosted API is free for NON-COMMERCIAL use only, and the terms are read as for business use. Weather research data
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

// OM2: the signal logger's allowlist (where a registry entry could add a host) does not hold it, and the weather recorder has no ensemble table or member parser left.
gates.OM2 = () => {
  const sig = fs.readFileSync(path.join(root, 'scripts', 'record_signals.py'), 'utf8');
  const m = /ALLOWLIST\s*=\s*frozenset\(\{([\s\S]*?)\}\)/.exec(sig);
  assert.ok(m, 'the allowlist is found');
  assert.ok(!BLOCKED.test(m[1]));
  assert.ok(/"api\.weather\.gov"/.test(m[1]), 'NWS stays allowed');
  const wx = fs.readFileSync(path.join(root, 'scripts', 'record_wxens.py'), 'utf8');
  assert.ok(!/parse_ensemble|temperature_2m/.test(wx), 'no ensemble parser or Open-Meteo variable name');
};

// OM3: the signal registry does not point a signal at it.
gates.OM3 = () => {
  const reg = path.join(root, 'kalshi-scalper', 'signals', 'REGISTRY.json');
  if (fs.existsSync(reg)) assert.ok(!BLOCKED.test(fs.readFileSync(reg, 'utf8')), 'REGISTRY.json names no Open-Meteo URL');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
