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

gates.G5 = () => {
  // THE defect this gate exists for. The first run of this probe asked
  // for a 15-minute window with limit=10000, got back exactly 10,000
  // trades, found no auction print, and reported that as evidence. It was
  // not evidence -- Alpaca returns trades ASCENDING FROM start, so the cap
  // truncated the response about a minute in and never reached 20:00.
  //
  // Third time this project has hit that trap (crypto charts, options
  // probe, this). CLAUDE.md records it in as many words, which evidently
  // is not enough, so it is asserted here instead.
  const fetchFn = src.slice(src.indexOf('function fetchSipClosingTrades('),
                            src.indexOf('function runSipAuctionProbe('));
  assert.ok(/page_token/.test(fetchFn), 'the closing-trade fetch must paginate, not cap');
  assert.ok(/next_page_token/.test(fetchFn), 'it must follow next_page_token');
  assert.ok(/truncated/.test(fetchFn), 'it must report when it ran out of page budget');

  // The window must be tight around the 20:00Z close. A wide one is what
  // made the cap bite in the first place.
  // Timestamps extracted rather than pattern-matched against the whole
  // URL: it is built across two lines, and a regex that assumes one line
  // fails for a reason that has nothing to do with the window.
  const stamps = fetchFn.match(/T(\d\d):(\d\d):\d\dZ/g) || [];
  assert.ok(stamps.length >= 2, `the trade window must have an explicit start and end; found ${stamps.length}`);
  const toMin = (t) => Number(t.slice(1, 3)) * 60 + Number(t.slice(4, 6));
  const startMin = toMin(stamps[0]);
  const endMin = toMin(stamps[1]);
  const closeMin = 20 * 60; // 16:00 ET during EDT
  assert.ok(startMin < closeMin && endMin > closeMin, 'the window must SPAN 20:00Z, or it cannot contain the print');
  assert.ok(endMin - startMin <= 15, `the window is ${endMin - startMin} minutes; too wide invites the cap that caused this`);

  // And a truncated scan must NOT be reported as an absence -- that is
  // the whole distinction, and reporting them the same way is what made
  // the first run misleading.
  // Checks the substance, not a literal phrase in a fixed word order --
  // an earlier version of this assertion failed only because the message
  // said "Not an absence, a truncation" rather than the reverse.
  const truncatedBranch = /scanTruncated\)\{[\s\S]{0,600}?statusEl\.className/.exec(src);
  assert.ok(truncatedBranch, 'there must be a distinct branch for a truncated scan');
  assert.ok(/truncat/i.test(truncatedBranch[0]) && /absence/i.test(truncatedBranch[0]),
    'the truncated branch must name it as a truncation AND say it is not an absence');
  assert.ok(/proves nothing/i.test(truncatedBranch[0]),
    'a truncated scan must state it is not evidence either way');
  console.log('G5 PASS the trade scan paginates and reports truncation');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
