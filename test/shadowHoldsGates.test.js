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

// SHD1 (hand case, invented rows): a ticker inside an OPEN row is refused with that row named; a ticker in no row below the deny line is allowed, at or after it refused; an S1 clearance clears only the rows it overrides, only for a spec that names the series, only from its own start.
gates.SHD1 = () => {
  const r = py(`
rows = [
 {"id": "H02", "tickers": ["KXA15M*"], "from": 500, "to": 800, "card": "c1", "status": "OPEN"},
 {"id": "H09", "tickers": ["KXA15M*"], "from": 1100, "to": 1200, "card": "c9", "status": "OPEN"},
 {"id": "H20", "tickers": ["KXB*"], "from": 900, "to": None, "card": "c2", "status": "FROZEN"},
 {"id": "H30", "tickers": ["KXC*"], "from": 0, "to": None, "card": "c3", "status": "CLOSED"},
 {"id": "H01", "tickers": ["*"], "from": 0, "to": None, "card": "arch", "status": "FROZEN", "scope": "archive_binary"}]
S1 = {"id": "S1", "kind": "clearance", "status": "APPROVED", "tickers": [], "from": "x", "to": None, "overrides": ["H02", "H20", "H22 and the forward_default_deny for these cells, for the shadow runner only"]}
t0 = {"forward_default_deny_from": 1000, "rows": rows}
t1 = {"forward_default_deny_from": 1000, "rows": rows + [S1]}
d = h.decide
sp = {"sha256": "a" * 64, "series": ["KXA15M", "KXB15M", "KXD15M"], "start_utc": 1000}
a = [d(t0, None, "KXA15M-1", 600)[0], d(t0, None, "KXA15M-1", 850)[0], d(t0, None, "KXB15M-1", 950)[0], d(t0, None, "KXD15M-1", 950)[0], d(t0, None, "KXD15M-1", 1000)[0], d(t0, None, "KXC15M-1", 100)[0]]
b = [d(t1, sp, "KXB15M-1", 1500)[0], d(t1, sp, "KXD15M-1", 1500)[0], d(t1, sp, "KXA15M-1", 1150)[0], d(t1, sp, "KXB15M-1", 999)[0], d(t1, dict(sp, start_utc=2000), "KXB15M-1", 1500)[0], d(t1, dict(sp, series=["KXZ15M"]), "KXB15M-1", 1500)[0], d(t1, dict(sp, sha256="short"), "KXB15M-1", 1500)[0], d(t1, None, "KXB15M-1", 1500)[0], d(t0, sp, "KXB15M-1", 1500)[0]]
print(json.dumps({"a": a, "b": b, "why": d(t0, None, "KXA15M-1", 600)[1]}))`);
  assert.deepStrictEqual(r.a, [false, true, false, true, false, true], 'inside OPEN refused, outside every row allowed below the line, the deny line refuses, a CLOSED row and an archive-only row do not apply');
  assert.deepStrictEqual(r.b, [true, true, false, false, false, false, false, false, false], 'S1 clears H20 and the default deny for a spec that names the series from its start; it does not clear H09 (not overridden), a close before the spec start, a series the spec does not name, a spec without a full sha256, another reader, or a table with no S1 row');
  assert.ok(/H02/.test(r.why), 'the refusal names the row');
};
// SHD2: a time that is not an integer is refused (a missing close never reads as clear), and a table of the wrong shape stops the run.
gates.SHD2 = () => {
  assert.deepStrictEqual(py(`t = {"forward_default_deny_from": 1000, "rows": []}; print(json.dumps([h.decide(t, None, "K", None)[0], h.decide(t, None, "K", "5")[0], h.decide(t, None, "K", True)[0], h.decide(t, None, "K", 5)[0]]))`), [false, false, false, true]);
  assert.throws(() => execFileSync('python3', ['-I', '-c', `
import importlib.util, tempfile, os
spec = importlib.util.spec_from_file_location('h', ${JSON.stringify(path.join(root, 'scripts', 'shadow_holds.py'))}); h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
p = os.path.join(tempfile.mkdtemp(), 'x.json'); open(p, 'w').write('{"rows": []}'); h.load(p)`], { stdio: 'pipe' }));
};
// SHD3: the committed table: the S1 row is there; a Bitcoin 15 minute close in the CFRTI sitting window (H09, Nov 17 to Nov 20) is refused even for a listed spec; one after it is read, as is a Bitcoin close before the deny line by no row.
gates.SHD3 = () => {
  const r = py(`
t = h.load(os.path.join(${JSON.stringify(root)}, "kalshi-scalper", "workers", "HOLDS.json"))
sp = {"sha256": "b" * 64, "series": ["KXBTC15M", "KXHYPE15M"], "start_utc": 1794873600}
print(json.dumps({"deny": t["forward_default_deny_from"], "ids": [x["id"] for x in t["rows"]], "version": t["version"],
 "btc_in_sitting": h.decide(t, sp, "KXBTC15M-26NOV180100-00", 1794880000), "btc_after": h.decide(t, sp, "KXBTC15M-26NOV211200-00", 1795219200 + 3600), "hype": h.decide(t, sp, "KXHYPE15M-26NOV180100-00", 1794880000), "other_reader": h.decide(t, None, "KXHYPE15M-26NOV180100-00", 1794880000)}))`);
  assert.strictEqual(r.deny, 1794787200);
  assert.ok(['H02', 'H09', 'H20', 'H22', 'H23', 'S1', 'S2'].every((i) => r.ids.includes(i)) && /\+8$/.test(r.version));
  assert.strictEqual(r.btc_in_sitting[0], false, 'H09 is not overridden by S1: ' + r.btc_in_sitting[1]);
  assert.strictEqual(r.btc_after[0], true, r.btc_after[1]);
  assert.strictEqual(r.hype[0], true, 'a listed spec reads its own series after its start (H22 and the default deny are overridden): ' + r.hype[1]);
  assert.strictEqual(r.other_reader[0], false, 'any other reader is refused');
};
let failed = 0;
for (const [name, fn] of Object.entries(gates)) { try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); } }
process.exit(failed ? 1 : 0);
