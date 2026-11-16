'use strict';
// The held-out guard of the forward shadow runner (Nov 16, 2026). Each gate states the consequence. Hand cases use invented rows.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const gates = {};
const py = (src) => JSON.parse(execFileSync('python3', ['-I', '-c', `
import importlib.util, json, os
spec = importlib.util.spec_from_file_location('h', ${JSON.stringify(path.join(root, 'scripts', 'shadow_holds.py'))}); h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
${src}`], { encoding: 'utf8' }));

// SHD1 (hand case): a ticker inside an OPEN row is refused with that row named; a ticker outside every row but before the deny line is allowed; at or after the deny line it is refused unless a signed clause for that spec and window clears it; the clause clears the OPEN row too, only for its spec.
gates.SHD1 = () => {
  const r = py(`
t = {"forward_default_deny_from": 1000, "rows": [
 {"id": "R1", "tickers": ["KXA15M*"], "from": 500, "to": 800, "card": "c1", "status": "OPEN"},
 {"id": "R2", "tickers": ["KXB*"], "from": 900, "to": None, "card": "c2", "status": "FROZEN"},
 {"id": "R3", "tickers": ["KXC*"], "from": 0, "to": None, "card": "c3", "status": "CLOSED"},
 {"id": "R4", "tickers": ["*"], "from": 0, "to": None, "card": "arch", "status": "FROZEN", "scope": "archive_binary"}]}
d = h.decide
a = d(t, "S1", "KXA15M-1", 600)[0], d(t, "S1", "KXA15M-1", 850)[0], d(t, "S1", "KXB15M-1", 950)[0], d(t, "S1", "KXD15M-1", 950)[0], d(t, "S1", "KXD15M-1", 1000)[0], d(t, "S1", "KXC15M-1", 100)[0]
t["clauses"] = [{"spec_ids": ["S1"], "tickers": ["KXA15M*", "KXD15M*"], "from": 500, "to": 2000}]
b = d(t, "S1", "KXA15M-1", 600)[0], d(t, "S2", "KXA15M-1", 600)[0], d(t, "S1", "KXD15M-1", 1500)[0], d(t, "S1", "KXD15M-1", 2000)[0], d(t, "S1", "KXB15M-1", 950)[0]
print(json.dumps({"a": a, "b": b, "why": d({"forward_default_deny_from": 1000, "rows": t["rows"]}, "S1", "KXA15M-1", 600)[1]}))`);
  assert.deepStrictEqual(r.a, [false, true, false, true, false, true], 'inside OPEN refused, outside every row allowed below the line, the deny line refuses, a CLOSED row and an archive-only row do not apply');
  assert.deepStrictEqual(r.b, [true, false, true, false, false], 'a signed clause clears its own spec and window only (the window end is exclusive), and not a row its tickers do not cover');
  assert.ok(/R1/.test(r.why), 'the refusal names the row');
};
// SHD2: a time that is not an integer is refused (a missing close never reads as clear), and a table of the wrong shape stops the run.
gates.SHD2 = () => {
  assert.deepStrictEqual(py(`t = {"forward_default_deny_from": 1000, "rows": []}; print(json.dumps([h.decide(t, "S", "K", None)[0], h.decide(t, "S", "K", "5")[0], h.decide(t, "S", "K", True)[0], h.decide(t, "S", "K", 5)[0]]))`), [false, false, false, true]);
  assert.throws(() => execFileSync('python3', ['-I', '-c', `
import importlib.util, tempfile, os
spec = importlib.util.spec_from_file_location('h', ${JSON.stringify(path.join(root, 'scripts', 'shadow_holds.py'))}); h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
p = os.path.join(tempfile.mkdtemp(), 'x.json'); open(p, 'w').write('{"rows": []}'); h.load(p)`], { stdio: 'pipe' }));
};
// SHD3: the committed table loads, and the rows the runner depends on are there: the Bitcoin forward rows, the R6 series row and the default deny line at 2026-11-17T00:00Z.
gates.SHD3 = () => {
  const r = py(`
t = h.load(os.path.join(${JSON.stringify(root)}, "kalshi-scalper", "workers", "HOLDS.json"))
ids = [x["id"] for x in t["rows"]]
print(json.dumps({"deny": t["forward_default_deny_from"], "ids": ids, "btc": h.decide(t, "ANY", "KXBTC15M-26NOV170100-00", 1794880000)}))`);
  assert.strictEqual(r.deny, 1794787200);
  assert.ok(['H02', 'H20', 'H22'].every((i) => r.ids.includes(i)));
  assert.strictEqual(r.btc[0], false, 'a Bitcoin 15 minute close after the forward start is refused until a signed clause clears it: ' + r.btc[1]);
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
