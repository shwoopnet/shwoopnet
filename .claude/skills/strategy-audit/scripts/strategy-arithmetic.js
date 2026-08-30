#!/usr/bin/env node
// Derives the numbers a backtest summary does NOT show you, from the ones
// it does -- then flags the combinations that have turned out to be bugs.
//
// This exists because the same three calculations settled three separate
// questions in one weekend, and each time they were done by hand:
//
//   1. Equities reported +0.09% expectancy against a 0.10% modeled cost.
//      The edge was smaller than the cost already subtracted from it --
//      i.e. entirely inside the error bar of a single assumption.
//   2. Crypto reported profit factor 4.08 at a 55% win rate, which implies
//      a 3.4:1 average win to average loss. For a stop-based strategy that
//      is not a good result, it is a symptom. The cause was the crypto
//      backtest charging equities' trading costs.
//   3. After fixing that, expectancy fell by EXACTLY the amount the cost
//      change predicted (0.40pp). That exactness is what established the
//      fix changed one thing and only that thing.
//
// Usage:
//   node strategy-arithmetic.js --pf 1.93 --wins 125 --losses 155 \
//        --expectancy 0.44 --cost 0.50
//
//   node strategy-arithmetic.js --compare \
//        --before-pf 4.08 --before-expectancy 0.84 --before-wins 153 --before-losses 127 \
//        --after-pf 1.93  --after-expectancy 0.44  --after-wins 125 --after-losses 155 \
//        --cost-change 0.40
//
// --cost is the ROUND-TRIP cost already deducted, in percentage points.

function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return fallback;
  const v = process.argv[i + 1];
  return v === undefined || v.startsWith('--') ? true : parseFloat(v);
}
const has = (n) => process.argv.includes('--' + n);

// Recovers gross gains and losses from the summary stats. profit factor is
// gains/losses and expectancy is (gains - losses)/n, which is two equations
// in two unknowns -- so the per-trade averages a summary omits are always
// recoverable from the ones it prints.
function derive({ pf, wins, losses, expectancy }) {
  const n = wins + losses;
  const net = n * expectancy;
  if (Math.abs(pf - 1) < 1e-9) return { n, net, indeterminate: true };
  const grossLosses = net / (pf - 1);
  const grossGains = pf * grossLosses;
  return {
    n, net, grossGains, grossLosses,
    avgWin: wins ? grossGains / wins : 0,
    avgLoss: losses ? grossLosses / losses : 0,
    winRate: n ? (wins / n) * 100 : 0,
  };
}

function report(label, d, cost) {
  console.log(`\n${label}`);
  if (d.indeterminate) {
    console.log('  profit factor is exactly 1.00 -- gains and losses cannot be separated.');
    return;
  }
  console.log(`  trades ${d.n} | win rate ${d.winRate.toFixed(0)}%`);
  console.log(`  avg win  ${d.avgWin.toFixed(2)}%`);
  console.log(`  avg loss ${d.avgLoss.toFixed(2)}%`);
  console.log(`  win:loss ratio ${(d.avgWin / d.avgLoss).toFixed(1)}:1`);

  const flags = [];

  // The one that mattered most. A strategy whose per-trade edge is smaller
  // than the cost it already subtracted is not weakly profitable -- it is
  // indistinguishable from break-even, because being slightly wrong about
  // fills erases it entirely.
  if (isFinite(cost) && cost > 0) {
    const ratio = (d.net / d.n) / cost;
    console.log(`  edge / modeled cost  ${ratio.toFixed(2)}x`);
    if (ratio < 1) {
      flags.push(`the per-trade edge is SMALLER than the ${cost}% cost already deducted. ` +
        'Being modestly wrong about fills takes this negative. Not tradeable on this evidence.');
    } else if (ratio < 2) {
      flags.push(`the per-trade edge is only ${ratio.toFixed(1)}x the cost assumption. ` +
        'Re-run with the cost raised 50% -- if the edge does not survive, it was the assumption, not the strategy.');
    }
  }

  // Not a law of nature, but in this codebase both times a win:loss ratio
  // this lopsided appeared alongside a healthy win rate, it was a defect in
  // the cost model or the fill price, not an edge.
  const wl = d.avgWin / d.avgLoss;
  if (wl > 3 && d.winRate > 50) {
    flags.push(`${wl.toFixed(1)}:1 average win to loss AND a ${d.winRate.toFixed(0)}% win rate. ` +
      'A stop-based strategy rarely gets both. Check the fill price and the cost model before believing it.');
  }
  if (d.avgLoss < cost * 1.5 && isFinite(cost)) {
    flags.push(`average loss (${d.avgLoss.toFixed(2)}%) is barely above the round-trip cost. ` +
      'Losses that small usually mean stops are not actually being hit in the simulation -- ' +
      'check whether a breakeven floor is engaging before the stop can.');
  }
  flags.forEach((f) => console.log(`  FLAG  ${f}`));
  if (!flags.length) console.log('  no arithmetic flags.');
}

if (has('compare')) {
  // Verifying a fix: a change to a per-trade cost should move expectancy by
  // exactly that amount and nothing else. If it moves by more or less, the
  // change did something beyond what was intended -- which is far easier to
  // see here than by reading the diff.
  const before = derive({ pf: arg('before-pf'), wins: arg('before-wins'), losses: arg('before-losses'), expectancy: arg('before-expectancy') });
  const after = derive({ pf: arg('after-pf'), wins: arg('after-wins'), losses: arg('after-losses'), expectancy: arg('after-expectancy') });
  const cost = arg('cost', NaN);
  report('BEFORE', before, cost);
  report('AFTER', after, cost);

  const expectedDelta = arg('cost-change', NaN);
  const actualDelta = (before.net / before.n) - (after.net / after.n);
  console.log('\nCHANGE');
  console.log(`  expectancy moved  ${actualDelta.toFixed(2)}pp`);
  if (isFinite(expectedDelta)) {
    console.log(`  cost change predicted  ${expectedDelta.toFixed(2)}pp`);
    const off = Math.abs(actualDelta - expectedDelta);
    if (off < 0.011) {
      console.log('  MATCH -- expectancy moved by exactly the predicted amount, so the change did one thing and only that.');
    } else {
      console.log(`  MISMATCH by ${off.toFixed(2)}pp -- the change did something beyond the cost adjustment. Find out what before trusting either number.`);
    }
  }
  const flipped = before.n === after.n ? (after.losses !== undefined ? null : null) : null;
  const wins = arg('before-wins') - arg('after-wins');
  if (wins > 0) {
    console.log(`  ${wins} trades flipped from win to loss -- a fixed per-trade cost lands hardest on marginal wins, `
      + 'which is why profit factor falls further than expectancy does.');
  }
} else {
  const d = derive({ pf: arg('pf'), wins: arg('wins'), losses: arg('losses'), expectancy: arg('expectancy') });
  report('MEASURED', d, arg('cost', NaN));
  console.log('\nThis is arithmetic, not evidence. It cannot tell you whether the sample is');
  console.log('independent, whether the window is one regime, or whether the fill price was real.');
}
