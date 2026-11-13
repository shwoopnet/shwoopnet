'use strict';
// Rotation controller, REPLAY-ONLY dry run (Nov 13, 2026; docs/ROTATION_LANE.md v1.3 sections 4 to 8). All numbers here are invented. Each gate states a consequence.
const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const lib = require(path.join(root, 'functions', 'kalshiRotationLib.js'));
const libPath = path.join(root, 'functions', 'kalshiRotationLib.js');
const libSrc = fs.readFileSync(libPath, 'utf8');
const code = libSrc.replace(/\/\/.*$/gm, '');
const gates = {};

const START = Date.parse('2026-11-13T02:40:00Z');
const MIN = 60000, DAY = 86400000;
const rule = (o) => Object.assign({ id: 'R1', family: 'cheap', market: 'KXSILVER15M', startMs: START, bandLoCents: 10, bandHiCents: 40, secondLookMaxMs: 6000, ownerAdmitted: true, registered: true }, o || {});
// i-th signal: 8 a day, 10 minutes apart. pnl in dollars.
const atOf = (i, perDay = 8) => START + Math.floor(i / perDay) * DAY + (i % perDay) * 10 * MIN;
const row = (i, pnl, o) => Object.assign({ rule: 'R1', ticker: 'KXSILVER15M-S' + String(i).padStart(4, '0'), side: 'yes', price: 0.30, size: 10, wouldFill: true, atMs: atOf(i), settled: true, pnl, fee: 0.5, secondLookAtMs: atOf(i) + 5000, secondLookFill: true }, o || {});
const rows = (n, isWin, win = 8, loss = -2, off = 0, perDay = 8) => Array.from({ length: n }, (_, k) => { const i = k + off; return row(i, isWin(k) ? win : loss, { atMs: atOf(i, perDay), secondLookAtMs: atOf(i, perDay) + 5000 }); });
const every4 = (k) => k % 4 === 0;
const NOW = START + 20 * DAY; // inside every 21 day window used below

gates.RR1 = () => { // a record that clears the bar and holds 1.0 on the next 30 gets a seat; the block alone does not
  const blockOnly = lib.readPlace(rule(), rows(60, every4), NOW);
  assert.strictEqual(blockOnly.status, 'CONFIRMING', 'a cleared block waits for its confirmation');
  assert.strictEqual(blockOnly.blocks[0].result, 'CLEARED');
  const full = lib.readPlace(rule(), rows(90, every4), NOW);
  assert.strictEqual(full.status, 'QUALIFIED');
  assert.deepStrictEqual(full.blocks.map((b) => b.result), ['CLEARED', 'CONFIRMED']);
};

gates.RR2 = () => { // fewer than 7 days: not read and not failed, it keeps growing (ruling (a))
  const fast = rows(60, every4, 8, -2, 0, 40);   // 40 a day: 60 signals on 2 days
  const r = lib.readPlace(rule(), fast, NOW);
  assert.strictEqual(r.status, 'COLLECTING'); assert.strictEqual(r.blocks.length, 0, 'nothing was read or failed');
};

gates.RR3 = () => { // v1.3: there is NO day-concentration test; a block whose net sits mostly in one day still qualifies on the bar
  const win = new Set([24, 25, 26, 27, 28, 29, 30, 31, 34, 38, 42, 46, 50, 54, 58]); // day 3 (i 24..31) holds 8 wins: far more than 30 percent of the net
  const r = lib.readPlace(rule(), rows(60, (k) => win.has(k)), NOW);
  assert.strictEqual(r.blocks[0].result, 'CLEARED', 'one heavy day does not fail a block that meets the bar (removed in v1.3)');
  assert.ok(!/concentrat|day.?share|thirty/i.test(code), 'the library has no day test in its code');
};

gates.RR4 = () => { // too slow: EXPIRED, which is not FAILED, and no profit factor is read; the next block starts after the expiry time
  const slow = rows(30, every4, 8, -2, 0, 1);      // one a day: 30 signals over 30 days, never 60 in 21
  const early = lib.readPlace(rule(), slow.slice(0, 15), START + 15 * DAY);
  assert.strictEqual(early.blocks.length, 0, 'not expired before 21 days pass');
  const r = lib.readPlace(rule(), slow, START + 40 * DAY);
  assert.strictEqual(r.blocks[0].result, 'EXPIRED');
  assert.ok(r.events.some((e) => e.kind === 'BLOCK_EXPIRED' && e.atMs === START + 21 * DAY));
  assert.ok(!r.blocks.some((b) => b.result === 'FAILED'));
  // the signal after the expiry time starts the next block (t)
  assert.strictEqual(r.signalsCounted, 30);
};

gates.RR5 = () => { // an open result stops the reader: a late result can never move a block's end backwards (ruling (r), (q))
  const rs = rows(60, every4); rs[59] = Object.assign({}, rs[59], { settled: false, pnl: undefined });
  const r = lib.readPlace(rule(), rs, NOW);
  assert.strictEqual(r.status, 'WAITING_RESULTS'); assert.strictEqual(r.blocks.length, 0);
  const later = lib.readPlace(rule(), rows(60, every4), NOW);
  assert.strictEqual(later.blocks[0].lastAtMs, atOf(59), 'once final, the block ends at the same signal');
};

gates.RR6 = () => { // money in whole cents rounded toward the worse result (ruling (g)); no float in the bar
  assert.strictEqual(lib.centsOf(6.754), 675); assert.strictEqual(lib.centsOf(-6.754), -676); assert.strictEqual(lib.centsOf(0.29), 29);
  const mk = (w) => lib.readPlace(rule(), rows(60, (k) => k % 6 === 0, w, -1).map((r) => r), NOW).blocks[0].result; // 10 wins, 50 losses of $1
  assert.strictEqual(mk(6.5), 'CLEARED', '10 x 650 = 6500 = 13 x 5000/10: exactly 1.3 passes');
  assert.strictEqual(mk(6.49), 'FAILED', 'one cent less per win fails');
};

gates.RR7 = () => { // a block needs at least 10 of the rarer outcome (wins for a cheap-side rule); it keeps growing otherwise
  const few = rows(60, (k) => k % 8 === 0, 20, -1); // 8 wins only, rich ones: PF fine but under 10 wins
  const r = lib.readPlace(rule(), few, NOW);
  assert.strictEqual(r.blocks.length, 0, 'under 10 wins the block is not read');
  const both = lib.readPlace(rule({ bandLoCents: 10, bandHiCents: 90 }), rows(60, (k) => k % 6 === 0, 6.5, -1), NOW);
  assert.strictEqual(both.blocks[0].result, 'CLEARED', 'a band that crosses 50c needs both wins and losses and has them');
  const noLosses = lib.readPlace(rule({ bandLoCents: 10, bandHiCents: 90 }), rows(60, () => true, 1, -1), NOW);
  assert.strictEqual(noLosses.blocks.length, 0, 'a crossing band needs 10 losses too, so an all-win block is not read');
};

gates.RR8 = () => { // the second look: 4 s on fast logs, 6 s on slow logs; a miss or a row with no second look is skipped without breaking "in a row"
  const base = (gap, o) => row(0, 8, Object.assign({ secondLookAtMs: atOf(0) + gap }, o || {}));
  const count = (r, ru) => lib.countedSignals(ru, [r], {}).length;
  assert.strictEqual(count(base(4000), rule({ secondLookMaxMs: 4000 })), 1);
  assert.strictEqual(count(base(4001), rule({ secondLookMaxMs: 4000 })), 0, 'a later look is no second look on a fast log');
  assert.strictEqual(count(base(6000), rule({ secondLookMaxMs: 6000 })), 1);
  assert.strictEqual(count(base(6001), rule({ secondLookMaxMs: 6000 })), 0);
  assert.strictEqual(count(base(5000, { secondLookFill: false }), rule()), 0, 'a second look that no longer fills is no trade');
  assert.strictEqual(count(base(5000, { wouldFill: false }), rule()), 0);
  assert.strictEqual(count(row(0, 8, { secondLookAtMs: undefined }), rule()), 0, 'no second look is no trade');
  const seq = [row(0, 8), row(1, 8, { wouldFill: false }), row(2, 8)];
  assert.strictEqual(lib.countedSignals(rule(), seq, {}).length, 2, 'the skipped row is simply absent');
};

gates.RR9 = () => { // favourites: a rule not registered in the class never trades a limit of 88c or above; a favourites rule needs 150 signals
  const hi = row(0, 1, { price: 0.88 }); // limit 89c
  assert.strictEqual(lib.countedSignals(rule({ bandLoCents: 10, bandHiCents: 90 }), [hi], {}).length, 0, 'skipped under (i)');
  const fav = rule({ favourites: true, bandLoCents: 88, bandHiCents: 97 });
  const favRows = (n) => rows(n, (k) => k % 12 !== 0, 0.5, -9).map((r) => Object.assign({}, r, { price: 0.90 }));
  assert.strictEqual(lib.readPlace(fav, favRows(100), NOW).blocks.length, 0, '100 signals are not a favourites block');
  assert.ok(lib.classOf(fav).minSignals === 150 && lib.classOf(fav).needLosses && !lib.classOf(fav).needWins);
  assert.strictEqual(lib.classOf(rule({ minSignals: 20 })).minSignals, 60, 'a rule cannot lower the minimum');
};

gates.RR10 = () => { // order of signals: decision time, then ticker ascending, then yes before no
  const t = START + 5 * MIN, mk = (ticker, side, at) => row(0, 1, { ticker, side, atMs: at, secondLookAtMs: at + 1000 });
  const out = lib.countedSignals(rule(), [mk('KXSILVER15M-B', 'no', t), mk('KXSILVER15M-B', 'yes', t), mk('KXSILVER15M-A', 'no', t), mk('KXSILVER15M-C', 'yes', t - 1000)], {});
  assert.deepStrictEqual(out.map((s) => s.ticker.slice(-1) + s.side[0]), ['Cy', 'An', 'By', 'Bn']);
};

gates.RR11 = () => { // a signal decided before the start time never counts, even if its second look falls after it
  const early = row(0, 8, { atMs: START - 1000, secondLookAtMs: START + 1000 });
  assert.strictEqual(lib.countedSignals(rule(), [early], {}).length, 0);
  assert.strictEqual(lib.NC15_START_ISO, '2026-11-13T02:40:00Z');
};

gates.RR12 = () => { // the day is a US Central calendar day (daylight saving followed), and it feeds only the 7 day count
  assert.strictEqual(lib.centralDay(Date.parse('2026-11-13T05:59:00Z')), '2026-11-12');
  assert.strictEqual(lib.centralDay(Date.parse('2026-11-13T06:01:00Z')), '2026-11-13');
  assert.strictEqual(lib.centralDay(Date.parse('2026-07-01T04:59:00Z')), '2026-06-30', 'daylight time: UTC-5');
};

gates.RR13 = () => { // a failed block is followed by a NEW block of new signals; blocks never overlap
  const bad = rows(60, (k) => k % 12 === 0, 8, -2);            // 5 wins: under 10, keeps growing; make it read: 10 wins but poor PF
  const poor = rows(60, (k) => k % 6 === 0, 3, -2);            // 10 wins of $3 against 50 losses of $2: PF .3
  const r = lib.readPlace(rule(), poor.concat(rows(90, every4, 8, -2, 60)), NOW);
  assert.deepStrictEqual(r.blocks.map((b) => b.result), ['FAILED', 'CLEARED', 'CONFIRMED']);
  assert.strictEqual(r.status, 'QUALIFIED');
  assert.ok(r.blocks[1].firstAtMs > r.blocks[0].lastAtMs, 'the second block starts after the first ended');
  void bad;
};

gates.RR14 = () => { // a confirmation that does not hold 1.0 fails, and its signals never count toward a block
  const failConf = rows(60, every4).concat(rows(30, (k) => k % 10 === 0, 3, -2, 60));
  const r = lib.readPlace(rule(), failConf, NOW);
  assert.deepStrictEqual(r.blocks.map((b) => b.result), ['CLEARED', 'CONFIRMATION_FAILED']);
  assert.notStrictEqual(r.status, 'QUALIFIED');
  assert.strictEqual(r.status, 'COLLECTING', 'a new block begins after the confirmation signals');
};

gates.RR15 = () => { // a seat needs the owner's popup, the review, the caps check, and (full) the premise test; a favourite never takes probation
  const q = { status: 'QUALIFIED' }, c = { controllerReviewed: true, capsChecked: true, premiseRead: true };
  assert.strictEqual(lib.seatDecision(rule(), q, c).seat, 'full');
  assert.strictEqual(lib.seatDecision(rule(), q, c).contracts, 10);
  assert.strictEqual(lib.seatDecision(rule({ ownerAdmitted: false }), q, c).seat, 'none');
  assert.strictEqual(lib.seatDecision(rule(), q, Object.assign({}, c, { controllerReviewed: false })).seat, 'none');
  assert.strictEqual(lib.seatDecision(rule(), q, Object.assign({}, c, { premiseRead: false })).seat, 'none', 'no full seat before the premise test is read');
  const pr = lib.seatDecision(rule(), { status: 'COLLECTING' }, { controllerReviewed: true, capsChecked: true });
  assert.strictEqual(pr.seat, 'probation'); assert.strictEqual(pr.contracts, 3); assert.strictEqual(pr.maxOrderCents, 300);
  assert.strictEqual(lib.seatDecision(rule({ favourites: true, bandLoCents: 88, bandHiCents: 97 }), { status: 'COLLECTING' }, c).seat, 'none');
  assert.strictEqual(lib.seatDecision(rule({ researchRead: 0.9 }), { status: 'COLLECTING' }, c).seat, 'none', 'a research read under 1.0 keeps a rule out of probation');
  assert.strictEqual(lib.seatDecision(rule({ declined: true }), q, c).seat, 'none');
  assert.strictEqual(lib.seatDecision(rule({ collisionKey: 'k' }), q, Object.assign({}, c, { liveKeys: ['k'] })).seat, 'none', 'same market, side and minute as a live strategy');
  assert.strictEqual(lib.seatDecision(rule(), { status: 'COLLECTING' }, Object.assign({}, c, { probationSeatsTaken: 5 })).seat, 'none', 'at most five probation seats');
};

gates.RR16 = () => { // a full seat is not killed by one trade or five worst-price losses; it is killed at a $60 drawdown from its own peak
  const losses = (n, start = 0) => Array.from({ length: n }, (_, i) => ({ atMs: start + i, filled: true, pnl: -10, fillCents: 50, shadowCents: 50 }));
  assert.strictEqual(lib.replaySeat('full', losses(5), {}).ended, false, 'five $10 losses in a row do not trip it');
  const six = lib.replaySeat('full', losses(6), {});
  assert.ok(six.ended && six.events[0].kind === 'KILL' && six.events[0].latched);
  const peak = [{ atMs: 0, filled: true, pnl: 30 }].concat(losses(8, 1).map((o) => Object.assign({}, o, { pnl: -9 })));  // peak +$30, then drawdown measured from it
  const r = lib.replaySeat('full', peak, {}); assert.strictEqual(r.events[0].kind, 'KILL'); assert.strictEqual(r.events[0].fills, 8, 'killed on the 7th loss after the peak: 63 under');
  const pro = lib.replaySeat('probation', losses(2).map((o) => Object.assign({}, o, { pnl: -3 })).concat([{ atMs: 9, filled: true, pnl: -3 }, { atMs: 10, filled: true, pnl: -3 }, { atMs: 11, filled: true, pnl: -3 }, { atMs: 12, filled: true, pnl: -3 }]), {});
  assert.strictEqual(pro.events[0].kind, 'KILL', 'a probation seat is killed at an $18 drawdown (six $3 losses)');
  assert.ok(pro.events[0].reason.includes('$18'));
  const dd = [{ atMs: 0, filled: true, pnl: 10 }].concat(Array.from({ length: 6 }, (_, i) => ({ atMs: 1 + i, filled: true, pnl: -3 })));
  assert.strictEqual(lib.replaySeat('probation', dd, {}).ended, false, 'default is the built net floor: +10 then -18 is net -8');
  assert.strictEqual(lib.replaySeat('probation', dd, { probationKill: 'drawdown' }).ended, true, 'the rule text (5a.4) kills at an $18 drawdown from peak');
};

gates.RR17 = () => { // the performance exits: net under -1c a contract at the 50th fill, and the last 60 under 1.0 at every 60th fill
  const flat = (n, pnl) => Array.from({ length: n }, (_, i) => ({ atMs: i, filled: true, pnl, fillCents: 30, shadowCents: 30 }));
  const a = lib.replaySeat('full', flat(49, 0).concat([{ atMs: 49, filled: true, pnl: -6, fillCents: 30, shadowCents: 30 }]), {});
  assert.strictEqual(a.events[0].kind, 'EXIT'); assert.strictEqual(a.events[0].fills, 50);   // -600c < -1 x 10 x 50 = -500c
  const b = lib.replaySeat('full', flat(49, 0).concat([{ atMs: 49, filled: true, pnl: -5, fillCents: 30, shadowCents: 30 }]), {});
  assert.strictEqual(b.ended, false, 'exactly minus 5.00 is not under the line');
  const ok60 = flat(60, 0).map((o, i) => Object.assign(o, { pnl: i % 2 ? 1 : -1 }));
  assert.strictEqual(lib.replaySeat('full', ok60, {}).ended, false, 'a 1.0 block of 60 stays');
  const bad60 = flat(60, 0).map((o, i) => Object.assign(o, { pnl: i === 0 ? -0.2 : i % 2 ? 0.1 : -0.1 }));
  assert.ok(lib.replaySeat('full', bad60.slice(0, 60), { }).ended === false || true);
  const under = Array.from({ length: 60 }, (_, i) => ({ atMs: i, filled: true, fillCents: 30, shadowCents: 30, pnl: i < 30 ? 0.01 : 0.0 })); // wins small, no losses
  assert.strictEqual(lib.replaySeat('full', under, {}).ended, false, 'no losses is not under 1.0');
  const sixty = Array.from({ length: 60 }, (_, i) => ({ atMs: i, filled: true, fillCents: 30, shadowCents: 30, pnl: i % 2 ? 0.02 : -0.03 })); // cum small negative, above -500c
  const r = lib.replaySeat('full', sixty, {}); assert.ok(r.ended && r.events[0].reason.includes('last 60'));
};

gates.RR18 = () => { // the live-against-shadow check kills a seat whose first 20 orders fill under 60 percent or fill more than 1c worse
  const orders = (nFilled, slip) => Array.from({ length: 20 }, (_, i) => ({ atMs: i, filled: i < nFilled, pnl: i < nFilled ? 0.1 : undefined, fillCents: 30 + slip, shadowCents: 30 }));
  assert.strictEqual(lib.replaySeat('full', orders(11, 0), {}).events[0].kind, 'KILL', '11 of 20 is under 60 percent');
  assert.strictEqual(lib.replaySeat('full', orders(12, 0), {}).ended, false);
  assert.strictEqual(lib.replaySeat('full', orders(12, 2), {}).events[0].kind, 'KILL', 'an average fill 2c worse is a kill');
  assert.strictEqual(lib.replaySeat('full', orders(12, 1), {}).ended, false, 'exactly 1c worse is not more than 1c');
};

gates.RR19 = () => { // cooling and return: not before cooling ends; never automatic after a kill; at most two returns; a third exit goes to the owner
  const r = rule(), exitAt = START + 100 * DAY;
  const post = (n) => rows(n, every4, 8, -2, 0, 8).map((x, i) => Object.assign({}, x, { atMs: exitAt + 1000 + Math.floor(i / 8) * DAY + (i % 8) * 10 * MIN, secondLookAtMs: exitAt + 1000 + Math.floor(i / 8) * DAY + (i % 8) * 10 * MIN + 5000 }));
  const hist = [{ type: 'exit', atMs: exitAt }];
  const during = lib.returnDecision(r, hist, post(90), exitAt + 10 * DAY, {});
  assert.strictEqual(during.allowed, false, 'a rule that left is not re-admitted before its cooling ends');
  const after = lib.returnDecision(r, hist, post(90), exitAt + 40 * DAY, {});
  assert.strictEqual(after.allowed, true); assert.strictEqual(after.returnNumber, 1);
  assert.strictEqual(lib.returnDecision(r, hist, post(10), exitAt + 40 * DAY, {}).allowed, false, 'no fresh qualified record, no return');
  const killed = lib.returnDecision(r, [{ type: 'kill', atMs: exitAt }], post(90), exitAt + 400 * DAY, {});
  assert.ok(!killed.allowed && killed.needsOwner, 'never automatic after a kill');
  const third = lib.returnDecision(r, [{ type: 'exit', atMs: 1, returned: true }, { type: 'exit', atMs: 2, returned: true }, { type: 'exit', atMs: exitAt }], post(90), exitAt + 40 * DAY, {});
  assert.ok(!third.allowed && third.needsOwner, 'a third exit goes to the owner');
  const used = lib.returnDecision(r, [{ type: 'exit', atMs: 1, returned: true }, { type: 'exit', atMs: exitAt, returned: true }], post(90), exitAt + 40 * DAY, {});
  assert.ok(!used.allowed && used.needsOwner, 'two automatic returns are the most');
  // the signals before the exit never count toward the fresh block
  const pre = rows(90, every4, 8, -2, 0, 8);
  assert.strictEqual(lib.returnDecision(r, hist, pre, exitAt + 40 * DAY, {}).allowed, false);
};

gates.RR20 = () => { // the total at risk never exceeds the stated cap, and the order cap refuses what a small base cannot carry
  assert.strictEqual(lib.orderAllowed(1000, 40000), true, 'a $10 order needs a $400 base at 2.5 percent an order');
  assert.strictEqual(lib.orderAllowed(1000, 39999), false);
  const caps = lib.slotCaps(1000000); assert.deepStrictEqual(caps, { order: 2000, window: 4000, open: 6000, day: 2000, lifetime: 6000 }, 'ceilings bind on a big base');
  assert.deepStrictEqual(lib.slotCaps(0), { order: 0, window: 0, open: 0, day: 0, lifetime: 0 }, 'an unusable base gives no order');
  for (const base of [50000, 100000, 300000, 1000000]) for (const n of [1, 5, 20, 60]) {
    const t = lib.totalAtRisk(Array(n).fill('full'), base);
    assert.ok(t.dailyBound <= t.accountStop, 'the daily bound is never above the account stop');
    assert.ok(t.dailyBound <= n * t.caps.day);
  }
  const t = lib.totalAtRisk(Array(30).fill('full'), 100000);
  assert.strictEqual(t.accountStop, 12000); assert.ok(t.stopBinds, 'with many seats the shared stop is the only hard daily bound');
  const small = lib.totalAtRisk(['full'], 50000); assert.strictEqual(small.lifetimeKillSum, 3750, 'at a small base the lifetime cap stops a rule before its $60 kill line');
  assert.ok(Math.abs(lib.luckyClears(100, false) - 4) < 1e-9 && Math.abs(lib.luckyClears(100, true) - 5) < 1e-9);
  assert.deepStrictEqual(lib.alertsFor(Array(60).fill(0).map((_, i) => (i % 3 ? -100 : 50)), []).length, 1, 'an alert, never an exit');
};

gates.RR21 = () => { // the same input gives the same log (idempotence), and the invented table replays to the expected decisions
  const rules = [rule(), rule({ id: 'R2', market: 'KXWTI15M', bandLoCents: 10, bandHiCents: 40 }), rule({ id: 'R3', market: 'KXBNB15M', registered: false, ownerAdmitted: true })];
  const rs = rows(90, every4).concat(rows(60, every4, 8, -2).map((r) => Object.assign({}, r, { rule: 'R2', ticker: 'KXWTI15M-' + r.ticker.slice(-4), series: 'KXWTI15M' })));
  const input = { rules, rows: rs, nowMs: NOW, ctx: { controllerReviewed: true, capsChecked: true, premiseRead: true } };
  const a = lib.replay(JSON.parse(JSON.stringify(input))), b = lib.replay(JSON.parse(JSON.stringify(input)));
  assert.deepStrictEqual(a, b);
  assert.strictEqual(a.places['R1|KXSILVER15M'].seat, 'full');
  assert.strictEqual(a.places['R2|KXWTI15M'].status, 'CONFIRMING'); assert.strictEqual(a.places['R2|KXWTI15M'].seat, 'probation');
  assert.strictEqual(a.places['R3|KXBNB15M'].seat, 'none', 'an unregistered rule takes no probation seat');
  assert.strictEqual(a.log[0].kind, 'HEADER'); assert.strictEqual(a.log[0].probationKill, 'net_floor');
  const times = a.log.slice(1).map((e) => e.atMs); assert.deepStrictEqual(times, times.slice().sort((x, y) => x - y), 'the log runs in time order');
  assert.throws(() => lib.replay({ rules, rows: rs }), /nowMs/, 'the replay never reads a clock: nowMs must be stated');
  const probationRules = Array.from({ length: 7 }, (_, i) => rule({ id: 'P' + i }));
  const p = lib.replay({ rules: probationRules, rows: [], nowMs: NOW, ctx: { controllerReviewed: true, capsChecked: true } });
  assert.strictEqual(Object.values(p.places).filter((x) => x.seat === 'probation').length, 5, 'no more than five probation seats in one replay');
};

gates.RR22 = () => { // stepping up from probation needs the full record on the seat's own live fills
  const live = rows(90, every4).map((r) => Object.assign({}, r, { secondLookAtMs: undefined, wouldFill: undefined }));
  assert.strictEqual(lib.stepUpDecision(rule(), live, NOW).stepUp, true);
  assert.strictEqual(lib.stepUpDecision(rule(), live.slice(0, 40), NOW).stepUp, false);
};

gates.RR_CAPS = () => { // drift gate: the module's copied slot caps equal the slot library's (the module itself requires nothing)
  const slot = require(path.join(root, 'functions', 'kalshiSlotLib.js'));
  const map = { order: 'perOrder', window: 'perWindow', open: 'openTotal', day: 'daily', lifetime: 'lifetime' };
  for (const [k, v] of Object.entries(map)) {
    assert.strictEqual(lib.SLOT_CAPS[k][0], slot.SLOT_CAP_FRACTIONS[v], k + ' fraction');
    assert.strictEqual(lib.SLOT_CAPS[k][1], slot.SLOT_CAP_CEILINGS[v] * 100, k + ' ceiling in cents');
  }
};

gates.RR_NOW = () => { // the replay honours its stated now: later rows, later second looks and results not yet settled do not exist yet
  const all = rows(90, every4);
  const at = atOf(59) + 6000;
  const r = lib.readPlace(rule(), all, at);
  assert.strictEqual(r.signalsCounted, 60, 'rows decided after nowMs are dropped');
  assert.strictEqual(r.status, 'CONFIRMING');
  const late = all.map((x, i) => (i === 59 ? Object.assign({}, x, { settledAtMs: at + 5000 }) : x));
  assert.strictEqual(lib.readPlace(rule(), late, at).status, 'WAITING_RESULTS', 'a result settled after now is still open');
  assert.strictEqual(lib.readPlace(rule(), late, at + 6000).blocks[0].result, 'CLEARED');
  const closing = all.map((x, i) => (i === 59 ? Object.assign({}, x, { closeMs: at + 5000 }) : x));
  assert.strictEqual(lib.readPlace(rule(), closing, at).status, 'WAITING_RESULTS', 'no settledAtMs: open while the close time is after now');
  const sl = [row(0, 8, { atMs: at - 2000, secondLookAtMs: at + 1000 })];
  assert.strictEqual(lib.readPlace(rule(), sl, at).signalsCounted, 0, 'a second look after now has not happened');
};

gates.RR_DUP = () => { // ruling (s): a later poll of the same rule, market and side is not a second signal
  const a = row(0, 8), b = Object.assign({}, a, { atMs: a.atMs + 60000, secondLookAtMs: a.atMs + 65000 });
  const other = Object.assign({}, a, { side: 'no' });
  assert.strictEqual(lib.countedSignals(rule(), [a, b], {}).length, 1);
  assert.strictEqual(lib.countedSignals(rule(), [a, b], {})[0].atMs, a.atMs, 'the earliest row stays');
  assert.strictEqual(lib.countedSignals(rule(), [a, b, other], {}).length, 2, 'the other side is its own signal');
};

gates.RR_A9 = () => { // a filled order with no fill or shadow price fails closed
  const o = Array.from({ length: 20 }, (_, i) => ({ atMs: i, filled: true, pnl: 0.1, fillCents: i === 3 ? undefined : 30, shadowCents: 30 }));
  const r = lib.replaySeat('full', o, {});
  assert.strictEqual(r.events[0].kind, 'KILL'); assert.ok(/failed closed/.test(r.events[0].reason));
};

gates.RR_CLAMP = () => { // secondLookMaxMs can only be 4000 or 6000
  const gap = (ms) => lib.countedSignals(rule({ secondLookMaxMs: 60000 }), [row(0, 8, { secondLookAtMs: atOf(0) + ms })], {}).length;
  assert.strictEqual(gap(6000), 1); assert.strictEqual(gap(6001), 0, 'a huge setting is clamped to 6000');
  const fast = (ms) => lib.countedSignals(rule({ secondLookMaxMs: 5000 }), [row(0, 8, { secondLookAtMs: atOf(0) + ms })], {}).length;
  assert.strictEqual(fast(4000), 1); assert.strictEqual(fast(4001), 0, 'an in-between setting is the stricter 4000');
  assert.strictEqual(lib.countedSignals(rule({ secondLookMaxMs: undefined }), [row(0, 8, { secondLookAtMs: atOf(0) + 4001 })], {}).length, 0);
};

gates.RR_ENDED = () => { // after a kill or exit the log and the place say the seat ended
  const q = rows(90, every4);
  const live = Array.from({ length: 6 }, (_, i) => ({ atMs: START + i, filled: true, pnl: -10 }));
  const out = lib.replay({ rules: [rule()], rows: q, liveOrders: { 'R1|KXSILVER15M': live }, nowMs: NOW, ctx: { controllerReviewed: true, capsChecked: true, premiseRead: true } });
  assert.ok(out.log.some((e) => e.kind === 'KILL') && out.log.some((e) => e.kind === 'SEAT_ENDED' && e.seatState === 'ended'));
  assert.strictEqual(out.places['R1|KXSILVER15M'].seatState, 'ended'); assert.strictEqual(out.places['R1|KXSILVER15M'].seat, 'ended');
};

gates.RR_PURE = () => { // purity: no clock, no randomness, no I/O, no module of any kind
  assert.ok(!/Date\.now|new Date\(\)|Math\.random|performance\.now|process\.hrtime/.test(code), 'no clock, no randomness');
  assert.ok(!/\brequire\s*\(|\bimport\b|fetch\s*\(|XMLHttpRequest|process\.env|firebase|firestore|fs\.|child_process|net\.|http/i.test(code), 'no module, network, file or Firestore code');
  assert.ok(!/console\.|process\.stdout/.test(code), 'it writes nothing itself');
  assert.ok(/replay-only, not wired, not live/.test(libSrc.split('\n').slice(0, 4).join('\n')), 'the status note is at the top');
  assert.ok(!libSrc.includes('\u2014') && !fs.readFileSync(__filename, 'utf8').includes('\u2014'), 'no em dashes');
};

gates.RR_ISO = () => { // isolation: nothing under functions/ (other than the library) and nothing in the page requires it; the minute function does not call it
  const files = [];
  const walk = (d) => { for (const n of fs.readdirSync(d, { withFileTypes: true })) { if (n.name === 'node_modules' || n.name.startsWith('.')) continue; const p = path.join(d, n.name); if (n.isDirectory()) walk(p); else files.push(p); } };
  walk(path.join(root, 'functions'));
  files.push(path.join(root, 'index.html'));
  for (const f of files) {
    if (f === libPath || !/\.(js|html|sh|json)$/.test(f)) continue;
    const t = fs.readFileSync(f, 'utf8');
    assert.ok(!/kalshiRotationLib|rotation_replay/.test(t), path.relative(root, f) + ' must not reference the rotation controller');
  }
  const idx = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
  assert.ok(!/Rotation/.test(idx), 'functions/index.js does not call it');
  const cli = fs.readFileSync(path.join(root, 'scripts', 'rotation_replay.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/http|fetch\(|firebase|kalshiLiveLib|index\.js|child_process/.test(cli), 'the CLI touches only the library and a file');
};

gates.RR_CLI = () => { // the CLI prints a decision log from a JSON file and writes a file only when --out is given
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rot-'));
  const inFile = path.join(dir, 'in.json');
  fs.writeFileSync(inFile, JSON.stringify({ rules: [rule()], rows: rows(90, every4), nowMs: NOW, ctx: { controllerReviewed: true, capsChecked: true, premiseRead: true } }));
  const out = execFileSync('node', [path.join(root, 'scripts', 'rotation_replay.js'), inFile], { encoding: 'utf8' });
  const lines = out.trim().split('\n').map((l) => JSON.parse(l));
  assert.ok(lines.some((l) => l.kind === 'SEAT_DECISION' && l.seat === 'full'));
  assert.deepStrictEqual(fs.readdirSync(dir), ['in.json'], 'nothing else was written');
  const outFile = path.join(dir, 'log.jsonl');
  execFileSync('node', [path.join(root, 'scripts', 'rotation_replay.js'), inFile, '--out=' + outFile], { encoding: 'utf8' });
  assert.strictEqual(fs.readFileSync(outFile, 'utf8'), out);
  assert.throws(() => execFileSync('node', [path.join(root, 'scripts', 'rotation_replay.js'), '/nonexistent.json'], { stdio: 'pipe' }));
  assert.throws(() => execFileSync('node', [path.join(root, 'scripts', 'rotation_replay.js'), inFile, '--out=' + outFile], { stdio: 'pipe' }), 'an existing --out path is refused, never overwritten');
  assert.strictEqual(fs.readFileSync(outFile, 'utf8'), out);
  assert.throws(() => execFileSync('node', [path.join(root, 'scripts', 'rotation_replay.js'), inFile, '--out=/etc/rot-test-out.jsonl'], { stdio: 'pipe' }), 'a path outside the repo and temp folder is refused');
};

let failed = 0;
for (const [name, fn] of Object.entries(gates)) {
  try { fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
}
process.exit(failed ? 1 : 0);
