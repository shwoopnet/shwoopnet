const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  return new Function('return (' + src.slice(start, end) + ')')();
}
function objConst(name) {
  const m = new RegExp('var ' + name + ' = (\\{[\\s\\S]*?\\});').exec(src);
  if (!m) throw new Error(name + ' not found');
  return new Function('return ' + m[1])();
}

const gates = {};

gates.G1 = () => {
  const day = lift('sipProbeTradingDay');
  const dow = (iso) => new Date(iso + 'T12:00:00Z').getUTCDay();
  for (let back = 0; back <= 40; back++) {
    const d = day(back);
    assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(d), `daysBack=${back} produced ${d}`);
    assert.ok(dow(d) >= 1 && dow(d) <= 5, `daysBack=${back} landed on a weekend (${d})`);
    assert.ok(new Date(d) <= new Date(), `daysBack=${back} produced a future date ${d}`);
  }
  // Control: a helper that always returned the same day would satisfy the
  // weekend check trivially.
  assert.notStrictEqual(day(0), day(30), 'the walk must depend on its input');
  // And the deep probes must reach genuinely old data, or the depth
  // question is not being asked.
  assert.ok(new Date(day(2190)) < new Date(Date.now() - 5 * 365 * 86400000),
    'the deepest probe must reach ~6 years back');
  console.log('G1 PASS probe dates are always weekdays');
};

gates.G2 = () => {
  const describe = lift('describeProbeResult');
  // These mean different things and the report must not blur them: 403 is
  // the plan, 401 is the key, a network error is neither.
  assert.ok(/403/.test(describe({ ok: false, status: 403 })));
  assert.ok(/plan/i.test(describe({ ok: false, status: 403 })), 'a 403 must name the plan as the cause');
  assert.ok(/401/.test(describe({ ok: false, status: 401 })));
  assert.ok(/credential/i.test(describe({ ok: false, status: 401 })), 'a 401 must name credentials, not the plan');
  assert.ok(/network/i.test(describe({ ok: false, status: 0, networkError: 'boom' })));
  assert.ok(/500/.test(describe({ ok: false, status: 500 })));
  // Success must be null, so the caller can tell "no problem" from "a
  // problem described as a string".
  assert.strictEqual(describe({ ok: true, status: 200 }), null);
  console.log('G2 PASS failures are told apart');
};

gates.G3 = () => {
  const front = objConst('AUCTION_CONDITIONS');
  // M is the official close: without it the probe cannot answer its own
  // question, whatever else it finds.
  assert.ok(front.M && /close/i.test(front.M), 'M must map to the official close');
  assert.ok(Object.keys(front).length >= 2, 'the condition map must be populated');

  // It must agree with the backend script it mirrors. Two probes that
  // answer the same question differently are worse than one.
  const backendPath = path.join(root, '..', 'shwoop-server', 'research', 'probes', 'sipAndAuction.js');
  assert.ok(fs.existsSync(backendPath),
    'the backend probe must exist — this card mirrors it and the two must not drift');
  const { AUCTION_CONDITIONS: back } = require(backendPath);
  assert.deepStrictEqual(Object.keys(front).sort(), Object.keys(back).sort(),
    'frontend and backend auction condition codes must match exactly');
  console.log('G3 PASS auction codes match the backend probe');
};

gates.G4 = () => {
  const out = execFileSync(process.execPath,
    [path.join(root, '.claude/skills/pre-ship/scripts/check-frontend.js'), path.join(root, 'index.html')],
    { encoding: 'utf8' });
  assert.ok(/FRONTEND: clean/.test(out), 'pre-ship not clean:\n' + out);
  const m = /no matching element: (.+)/.exec(out);
  assert.strictEqual(m, null, m ? `orphaned lookup(s): ${m[1]}` : '');
  console.log('G4 PASS pre-ship clean');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
