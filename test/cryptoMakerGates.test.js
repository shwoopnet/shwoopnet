const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name, deps) {
  const start = src.indexOf('function ' + name + '(');
  if (start < 0) throw new Error('not found in index.html: ' + name);
  let d = 0, end = -1;
  for (let i = src.indexOf('{', start); i < src.length; i++) {
    if (src[i] === '{') d++;
    else if (src[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const names = Object.keys(deps || {});
  return new Function(...names, 'return (' + src.slice(start, end) + ')')(...names.map((n) => deps[n]));
}
function num(name) {
  const m = new RegExp('var ' + name + ' = ([\\d.]+);').exec(src);
  if (!m) throw new Error(name + ' not found');
  return Number(m[1]);
}
function objConst(name) {
  const m = new RegExp('var ' + name + ' = (\\{[^}]*\\});').exec(src);
  if (!m) throw new Error(name + ' not found');
  return new Function('return ' + m[1])();
}

const REWARD = num('CRYPTO_BT_REWARD_MULTIPLE');
const MAKER_FEE = num('CRYPTO_MAKER_FEE_BPS');
const TAKER_FEE = num('CRYPTO_SLIPPAGE_BPS');
const WAIT = num('CRYPTO_MAKER_WAIT_BARS');
const LEGS = objConst('CRYPTO_BT_MARKET_LEGS_BY_OUTCOME');
const bar = (o, h, l, c) => ({ o, h, l, c, t: new Date(), vol: 1000 });
const signal = { direction: 'Long', entry: 100, stop: 95, t1: 115 };

const gates = {};

gates.G1 = () => {
  const fill = lift('fillCryptoSignalAsMakerLimit', { CRYPTO_BT_REWARD_MULTIPLE: REWARD });
  // Bar 0 is the breakout. Bar 1 stays above the 100 level; bar 2 dips to 99.
  const bars = [bar(99, 104, 98, 103), bar(103, 105, 101, 104), bar(104, 105, 99, 102)];
  const out = fill(bars, 0, signal, WAIT);
  assert.ok(out, 'a bar trading back to the level must fill');
  assert.strictEqual(out.entry, 100, 'a limit fills at its price, not at the bar low or open');
  assert.strictEqual(out.entryIdx, 2, 'the fill happens on the bar that came back, not earlier');
  // Levels re-anchor to the limit price.
  assert.strictEqual(out.stop, 95);
  assert.ok(Math.abs(out.t1 - (100 + REWARD * 5)) < 1e-9, 'target is computed from the limit price');
  // Positive control: the SAME bars under the market-order model fill at
  // a worse price, which is the entire point of the experiment.
  const takerFill = lift('fillCryptoSignalAtNextBar', { CRYPTO_BT_REWARD_MULTIPLE: REWARD })(bars, 0, signal);
  assert.ok(takerFill.entry > out.entry, 'control: the market order pays more than the resting limit');
  console.log('G1 PASS limit fills only when price returns');
};

gates.G2 = () => {
  const fill = lift('fillCryptoSignalAsMakerLimit', { CRYPTO_BT_REWARD_MULTIPLE: REWARD });
  // The predicted failure mode: it broke out and never looked back.
  const runaway = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT + 3; i++) runaway.push(bar(103 + i, 106 + i, 102 + i, 105 + i));
  assert.strictEqual(fill(runaway, 0, signal, WAIT), null, 'a runaway breakout must be missed, not filled');
  // Just outside the wait window is still a miss -- the order would have
  // been pulled by then.
  const late = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT; i++) late.push(bar(103, 105, 101, 104));
  late.push(bar(103, 105, 99, 102)); // comes back one bar too late
  assert.strictEqual(fill(late, 0, signal, WAIT), null, 'a return after the wait window must not fill');
  // Positive control: one bar earlier and it DOES fill, so the window
  // boundary is real rather than the check always returning null.
  const justInTime = late.slice(0, WAIT).concat([bar(103, 105, 99, 102)]);
  assert.ok(fill(justInTime, 0, signal, WAIT), 'control: inside the window it must fill');
  console.log('G2 PASS runaway breakouts are missed');
};

gates.G3 = () => {
  const maker = lift('applyCryptoMakerSlippage', {
    CRYPTO_MAKER_FEE_BPS: MAKER_FEE, CRYPTO_SLIPPAGE_BPS: TAKER_FEE,
    CRYPTO_BT_MARKET_LEGS_BY_OUTCOME: LEGS,
  });
  const taker = lift('applyCryptoBacktestSlippage', {
    CRYPTO_SLIPPAGE_BPS: TAKER_FEE, CRYPTO_BT_MARKET_LEGS_BY_OUTCOME: LEGS,
  });
  // A two-leg outcome: maker on the entry, taker on the exit.
  const expectedMakerCost = (MAKER_FEE / 100) + (TAKER_FEE / 100);
  assert.ok(Math.abs(maker(0, 'stopped') - -expectedMakerCost) < 1e-9,
    `maker cost should be ${expectedMakerCost}%, got ${-maker(0, 'stopped')}%`);
  assert.ok(Math.abs(taker(0, 'stopped') - -(2 * TAKER_FEE / 100)) < 1e-9, 'market model unchanged');
  // Cheaper, and by exactly the fee difference on ONE leg -- not two.
  // Assuming maker on both legs is how the first draft of the CLAUDE.md
  // note overstated this, so it is asserted rather than trusted.
  const saving = maker(0, 'stopped') - taker(0, 'stopped');
  assert.ok(Math.abs(saving - ((TAKER_FEE - MAKER_FEE) / 100)) < 1e-9,
    `maker should save exactly one leg's fee difference, saved ${saving}`);
  assert.ok(saving > 0, 'the maker model must be cheaper, or there is no experiment');
  // An unresolved trade has only one leg paid; the entry is that leg.
  assert.ok(Math.abs(maker(0, 'unresolved') - -(MAKER_FEE / 100)) < 1e-9,
    'an unresolved trade pays only the maker entry');
  console.log('G3 PASS maker costs entry-maker exit-taker');
};

gates.G4 = () => {
  const describe = lift('describeMakerFills');
  // The trap this gate exists for: a great-looking result on 2 of 10
  // signals, where the 8 skipped ones were the winners.
  const trades = [{}, {}];
  trades.makerEntries = true;
  trades.missedTrades = Array.from({ length: 8 }, () => ({ pctReturn: 2.5, outcome: 'trailing_stopped' }));
  const out = describe(trades);
  assert.ok(/2 of 10/.test(out), `fill count must be stated: ${out}`);
  assert.ok(/20%/.test(out), `fill RATE must be stated: ${out}`);
  assert.ok(/8 missed/.test(out), `the missed count must be stated: ${out}`);
  assert.ok(/\+2\.50%/.test(out), `what the missed signals would have made must be stated: ${out}`);
  assert.ok(/predicted failure mode/.test(out), 'skipping winners must be named as the predicted failure, not left implicit');
  // Negative control: a market-order run must produce NO maker note, or
  // this text would appear on runs it does not describe.
  const plain = [{}, {}];
  assert.strictEqual(describe(plain), '', 'a market-order run must not claim a fill rate');
  // Missed losers must NOT be framed as the failure mode -- the warning
  // has to be earned, or it is noise that gets ignored when it matters.
  const goodSkip = [{}, {}];
  goodSkip.makerEntries = true;
  goodSkip.missedTrades = [{ pctReturn: -1.5, outcome: 'stopped' }];
  assert.ok(!/predicted failure mode/.test(describe(goodSkip)), 'skipping losers is not the failure mode');
  console.log('G4 PASS fill rate and missed signals reported');
};

gates.G5 = () => {
  const out = execFileSync(process.execPath,
    [path.join(root, '.claude/skills/pre-ship/scripts/check-frontend.js'), path.join(root, 'index.html')],
    { encoding: 'utf8' });
  assert.ok(/FRONTEND: clean/.test(out), 'pre-ship not clean:\n' + out);
  const m = /no matching element: (.+)/.exec(out);
  if (m) {
    const names = m[1].split(',').map((x) => x.trim()).filter(Boolean);
    assert.deepStrictEqual(names, ['intradayToggle'], `new orphaned lookup(s): ${names.join(', ')}`);
  }
  console.log('G5 PASS pre-ship clean');
};

gates.G6 = () => {
  // The universe run is where the real experiment is actually run, and
  // its first version carried only a COUNT of missed signals -- which
  // made the one question this experiment exists to answer unanswerable
  // from the run that matters. This gate exists so that cannot recur.
  const src2 = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  const start = src2.indexOf('function renderCryptoUniverseBacktestResults(');
  assert.ok(start > 0, 'universe renderer not found');
  let d = 0, end = -1;
  for (let i = src2.indexOf('{', start); i < src2.length; i++) {
    if (src2[i] === '{') d++;
    else if (src2[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const body = src2.slice(start, end);
  assert.ok(/missedTrades/.test(body), 'the universe run must receive the missed RETURNS, not just a count');
  assert.ok(/missedAvg/.test(body), 'the universe run must compute what the missed signals would have made');
  assert.ok(/selection rather than better execution/.test(body),
    'a positive missed average must be named as selection, not left for the reader to notice');
  // And the aggregation must actually carry them through.
  assert.ok(/universeMissedTrades = universeMissedTrades\.concat/.test(src2),
    'missed trades must be accumulated across pairs, not tallied');
  assert.ok(!/new Array\(universeMissed\)/.test(src2),
    'the synthetic zero-return placeholder must be gone -- it made every missed average read as 0.00%');
  console.log('G6 PASS universe run reports what the misses would have made');
};

gates.G7 = () => {
  const hybrid = lift('fillCryptoSignalHybrid', {
    CRYPTO_BT_REWARD_MULTIPLE: REWARD,
    CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION: num('CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION'),
    fillCryptoSignalAsMakerLimit: lift('fillCryptoSignalAsMakerLimit', { CRYPTO_BT_REWARD_MULTIPLE: REWARD }),
  });
  // A runaway: breaks out at bar 0 and never comes back within the window.
  const bars = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT + 4; i++) bars.push(bar(110 + i, 112 + i, 109 + i, 111 + i));
  const out = hybrid(bars, 0, signal, WAIT);
  assert.ok(out, 'a runaway must still be priced, whether or not it is taken');
  // This particular runaway is now REFUSED by live's chase gate (see G9).
  // The claim THIS gate makes is about WHEN the fallback is priced, which
  // holds either way -- a refused signal still carries the honest entry
  // so the gate's cost can be measured.
  assert.strictEqual(out.entryIdx, 1 + WAIT,
    `the fallback must be priced at signalIdx + waitBars + 1 (${1 + WAIT}), got ${out.entryIdx}`);
  assert.strictEqual(out.entry, bars[1 + WAIT].o, 'the fallback fills at that bar open');
  // THE DEFECT THIS GATE EXISTS FOR: pricing it at the next bar would be
  // lookahead, and on a runaway it is also a far better price -- which is
  // exactly why it would flatter the result.
  assert.notStrictEqual(out.entryIdx, 1, 'the fallback must NOT be priced at the bar after the signal');
  assert.ok(out.entry > bars[1].o,
    'control: on a runaway the honest fallback is WORSE than the next-bar price, which is the whole point');
  // A chase INSIDE live's gate is taken, and is still priced after the
  // window -- so the pricing rule is not an artifact of refusal.
  const near = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT; i++) near.push(bar(101, 101.4, 100.6, 101.2));
  near.push(bar(101, 102, 100.5, 101.5));
  const legal = hybrid(near, 0, signal, WAIT);
  assert.strictEqual(legal.filledAs, 'taker', 'a legal chase fills as a taker');
  assert.strictEqual(legal.entryIdx, 1 + WAIT, 'and is still priced after the window');

  // A limit that does fill still fills as maker, at the limit price.
  const comesBack = [bar(99, 104, 98, 103), bar(103, 105, 99, 102)];
  const m = hybrid(comesBack, 0, signal, WAIT);
  assert.strictEqual(m.filledAs, 'maker');
  assert.strictEqual(m.entry, 100, 'a resting fill is at the limit price');
  // No bar left to fall back on -> dropped, not invented.
  assert.strictEqual(hybrid([bar(99, 104, 98, 103), bar(110, 112, 109, 111)], 0, signal, WAIT), null,
    'with no bar after the window the signal must be dropped');
  console.log('G7 PASS hybrid fallback is priced after the window');
};

gates.G8 = () => {
  const hybrid = lift('fillCryptoSignalHybrid', {
    CRYPTO_BT_REWARD_MULTIPLE: REWARD,
    CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION: num('CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION'),
    fillCryptoSignalAsMakerLimit: lift('fillCryptoSignalAsMakerLimit', { CRYPTO_BT_REWARD_MULTIPLE: REWARD }),
  });
  const src2 = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  // Cost must follow the ACTUAL fill, not the run mode.
  assert.ok(/filled\.filledAs === 'maker' \|\| entryMode === 'maker'/.test(src2),
    'a chased fallback must be charged the taker cost, not the maker cost');
  // The chase distance is measured against the setup's own risk width,
  // and against LIVE's number -- 0.3, not a laxer one.
  const chaseConst = new RegExp('CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION = ([\\d.]+);').exec(src2);
  assert.ok(chaseConst, 'the chase gate constant must exist');
  assert.strictEqual(Number(chaseConst[1]), 0.3,
    'must mirror shwoop-server autoTrade.js CHASE_LIMIT_RISK_FRACTION exactly, or the backtest counts trades live refuses');
  // A runaway fallback must actually record how far it chased.
  const bars = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT + 4; i++) bars.push(bar(110 + i, 112 + i, 109 + i, 111 + i));
  const out = hybrid(bars, 0, signal, WAIT);
  const expected = (out.entry - signal.entry) / Math.abs(signal.entry - signal.stop);
  assert.ok(Math.abs(out.chaseRiskFraction - expected) < 1e-9, 'chase distance must be in risk-width units');
  assert.ok(out.chaseRiskFraction > 0.3, 'control: this fixture must actually breach live\'s gate, or the check proves nothing');
  // And the run must SAY so rather than quietly counting it.
  assert.ok(/were REFUSED by the same chase gate live/.test(src2),
    'chases live would refuse must be reported, not silently included');
  assert.ok(/chased at market after the limit expired/.test(src2), 'the maker/chase split must be in the headline');
  console.log('G8 PASS hybrid costs and split are honest');
};

gates.G9 = () => {
  const hybrid = lift('fillCryptoSignalHybrid', {
    CRYPTO_BT_REWARD_MULTIPLE: REWARD,
    CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION: num('CRYPTO_BT_CHASE_LIMIT_RISK_FRACTION'),
    fillCryptoSignalAsMakerLimit: lift('fillCryptoSignalAsMakerLimit', { CRYPTO_BT_REWARD_MULTIPLE: REWARD }),
  });
  // A runaway that blows past live's gate: entry 100, stop 95 (risk 5),
  // so 30% of risk width is 1.5 -- anything filling above 101.5 is refused.
  const far = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT + 4; i++) far.push(bar(110 + i, 112 + i, 109 + i, 111 + i));
  const refused = hybrid(far, 0, signal, WAIT);
  assert.ok(refused, 'a refused signal must be RETURNED, not dropped -- the gate cost has to be measurable');
  assert.strictEqual(refused.refusedByChaseGate, true, 'a chase past live\'s gate must be marked refused');
  assert.ok(refused.chaseRiskFraction > 0.3);
  // It must still carry a priceable entry so the counterfactual is honest.
  assert.strictEqual(refused.entry, far[1 + WAIT].o);
  assert.ok(refused.stop === signal.stop && refused.t1 > refused.entry, 'a refused signal must still be simulable');

  // POSITIVE CONTROL: a chase INSIDE the gate must still be taken, or the
  // gate would simply be refusing every fallback and this proves nothing.
  const near = [bar(99, 104, 98, 103)];
  for (let i = 0; i < WAIT; i++) near.push(bar(101, 101.4, 100.6, 101.2));
  near.push(bar(101, 102, 100.5, 101.5)); // fallback bar opens at 101 -> 0.2 of risk width
  const taken = hybrid(near, 0, signal, WAIT);
  assert.ok(taken, 'a legal chase must fill');
  assert.ok(!taken.refusedByChaseGate, 'a chase inside the gate must NOT be refused');
  assert.strictEqual(taken.filledAs, 'taker');

  // The runner must exclude refused trades from the results and report
  // what they would have made.
  const src2 = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(/filled\.refusedByChaseGate/.test(src2), 'the runner must act on the refusal flag');
  assert.ok(/chaseRefusedTrades\.push/.test(src2), 'refused trades must be recorded, not discarded');
  assert.ok(/filled = null;/.test(src2), 'a refused trade must not enter the results');
  assert.ok(/NOT in the numbers above/.test(src2), 'the report must say refused trades are excluded');
  assert.ok(/NOT worth loosening because it would improve this number/.test(src2),
    'a positive refused average must warn against loosening the gate to chase the number');
  console.log('G9 PASS the chase gate is enforced and its cost measured');
};

function main() {
  const arg = process.argv[2];
  for (const n of (arg ? [arg] : Object.keys(gates))) {
    if (!gates[n]) throw new Error('unknown gate: ' + n);
    gates[n]();
  }
}
try { main(); } catch (e) { console.error(e.message); process.exit(1); }
