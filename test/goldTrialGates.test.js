// Gold trial seat (Nov 13, 2026, the owner's written exception to the return rule; below the research bar). Each gate states a consequence for the account.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');
const gk = require('../functions/kalshiGoldKillLib');
const hsLib = require('../functions/kalshiHardStopLib');
const root = path.join(__dirname, '..');
const iso = (ms) => new Date(ms).toISOString();
const pem = crypto.generateKeyPairSync('ed25519').privateKey.export({ type: 'pkcs8', format: 'pem' });
const START = Date.parse('2026-11-14T00:00:00Z');
const T_IN = START + 3 * 3600000, T_BEFORE = START - 3 * 3600000, T_OLD = Date.parse('2026-10-07T14:00:00Z');
const gates = {};

let n = 0;
const loss = (pnl, ts) => ({ id: 'o' + (++n), strategy: 'L1', series: 'KXGOLD15M', ticker: 'KXGOLD15M-26NOV141500-00', ts, fillCount: 3, count: 3, maxCost: 2.85, side: 'yes', settled: true, result: 'exit', settledPnl: pnl });
const win = (ts) => ({ id: 'o' + (++n), strategy: 'L1', series: 'KXGOLD15M', ticker: 'KXGOLD15M-26NOV141500-00', ts, fillCount: 3, count: 3, maxCost: 2.85, side: 'yes', settled: true, result: 'yes', averageFillPrice: '0.9200', averageFeePaid: '0.0100' });
const at = (i) => START + 3600000 + i * 900000;
function checker(orders, sizing) {
  const wrote = [], events = [], state = { sizing: sizing === undefined ? { base: 1000 } : sizing };
  return { wrote, events, state, io: { now: T_IN, readOrders: async () => orders, readSizing: async () => state.sizing,
    writeGoldKill: async (p) => { wrote.push(p); state.sizing = { ...(state.sizing || {}), goldKill: { ...((state.sizing && state.sizing.goldKill) || {}), ...p } }; },
    logEvent: async (e) => { events.push(e); } } };
}

function world(now) {
  const posts = [], docs = new Map(), notes = [];
  const sess = { active: true, until: now + 3600000, ordersSent: 0, startCash: 100, sizing: true, sizeCap: 15, sizeAddon: 20, sizeBase: 1000, sizeNextReview: now + 86400000 };
  const store = {
    async halted() { return false; }, async hasUnresolved() { return false; },
    async createTest(id, d) { docs.set(id, { ...d }); return true; }, async updateTest(id, p) { Object.assign(docs.get(id), p); },
    async sessionTrades(since) { return [...docs.entries()].filter(([, d]) => d.ts >= since).map(([id, d]) => ({ id, ...d })); },
  };
  const fetchFn = async (url, o) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/candlesticks')) return reply(200, { candlesticks: [] });
    if (url.includes('/markets/')) return reply(200, { market: { status: 'active', close_time: iso(now + 360000), exchange_index: 2, yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } });
    if (url.endsWith('/portfolio/balance')) return reply(200, { balance_breakdown: [{ balance: '1000.0000', exchange_index: 2 }, { balance: '1000.0000', exchange_index: 0 }] });
    if (url.includes('/portfolio/orders')) return reply(200, { orders: [] });
    if (url.includes('/portfolio/fills')) return reply(200, { fills: [] });
    if (o.method === 'POST') { const b = JSON.parse(o.body); posts.push(b); return reply(201, { order_id: 'x', fill_count: String(b.count) + '.00', remaining_count: '0.00', average_fill_price: '0.9100', average_fee_paid: '0.0057' }); }
    throw new Error('unexpected ' + url);
  };
  return { posts, docs, store, fetchFn, sess, notes, now };
}
const state = (now, extra) => ({ hardStop: { rearmAt: hsLib.HARD_STOP.rearmAt, status: 'ok', tripped: false, checkedAt: now - 60000 }, cap: 15, base: 1000, reviewedAt: now - 1000, pool: 50, saved: 0, appliedTs: now - 1000, lastStopAt: null, ...(extra || {}) });
const tick = (w, sizingState) => live.runL1Tick({
  session: w.sess, now: w.now, setSession: async (p) => { Object.assign(w.sess, p); w.notes.push(p.lastNote); },
  quotes: [{ series: 'KXGOLD15M', m: { ticker: 'KXGOLD15M-26NOV141500-06', status: 'active', close_time: iso(w.now + 360000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } }],
  active: true, enabled: true, store: w.store, keyId: 'k', pem, fetchFn: w.fetchFn, sizingState, setSizingState: async () => {},
});

// GT1: during the trial gold never sends more than 3 contracts or any add-on, whatever the ladder, the balance, the pool or a stored cap says.
gates.GT1 = async () => {
  const w = world(T_IN);
  await tick(w, state(T_IN, { cap: 40, pool: 500 }));
  assert.strictEqual(w.posts.length, 1, 'the trial seat trades');
  assert.ok(w.posts[0].count >= 1 && w.posts[0].count <= 3, 'at most 3 contracts, got ' + w.posts[0].count);
  const rec = [...w.docs.values()][0];
  assert.strictEqual(Number(rec.addonCost || 0), 0, 'no profit add-on');
  // the lock itself, behind the sizing code
  assert.strictEqual(live.maxContractsAt('KXGOLD15M', T_IN), 3);
  assert.strictEqual(live.maxContractsFor('KXGOLD15M'), live.L1_ORDER_CEILING, 'the long-run ceiling the report reads is unchanged');
  assert.strictEqual(live.maxContractsAt('KXXRP15M', T_IN), 1, 'other series are untouched');
  // the same tick without the trial (an old date, before the generation) sizes gold as before: this is what the recorded replays see
  const old = world(T_OLD);
  await live.runL1Tick({ session: old.sess, now: T_OLD, setSession: async () => {}, quotes: [{ series: 'KXGOLD15M', m: { ticker: 'KXGOLD15M-26OCT071415-06', status: 'active', close_time: iso(T_OLD + 360000), yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100' } }], active: true, enabled: true, store: old.store, keyId: 'k', pem, fetchFn: old.fetchFn, sizingState: state(T_OLD), setSizingState: async () => {} });
  assert.ok(old.posts.length === 1 && old.posts[0].count > 3, 'before the trial period nothing about gold sizing changed');
};

// GT2: the trial floor latches gold at -$18 net after 5 fills even though the $58.75 drawdown line is far away; 4 fills do not, and it never un-latches.
gates.GT2 = async () => {
  const four = [loss(-5, at(0)), loss(-5, at(1)), loss(-5, at(2)), loss(-5, at(3))];
  const a = checker(four);
  assert.ok(!(await gk.runGoldKillCheck(a.io)).tripped, '4 trades down $20: the floor waits for fill 5');
  const five = four.concat([loss(-0.01, at(4))]);
  const b = checker(five);
  const rb = await gk.runGoldKillCheck(b.io);
  assert.strictEqual(rb.tripped, 'trial', 'the floor binds first');
  assert.ok(gk.goldKillActive(b.state.sizing, 'KXGOLD15M'), 'latched');
  assert.ok(b.events.some((e) => e.kind === 'gold kill'), 'and the owner is told');
  const exactly = checker([loss(-3.6, at(0)), loss(-3.6, at(1)), loss(-3.6, at(2)), loss(-3.6, at(3)), loss(-3.6, at(4))]);   // exactly -18.00: the floor is "under -$18"
  assert.ok(!(await gk.runGoldKillCheck(exactly.io)).tripped, 'exactly -$18 is not under it');
  const wins = five.concat(Array.from({ length: 80 }, (_, i) => win(at(10 + i))));
  const c = checker(wins);
  await gk.runGoldKillCheck(c.io);
  assert.ok(gk.goldKillActive(c.state.sizing, 'KXGOLD15M'), 'later wins do not un-latch it');
  assert.ok(gk.GOLD_KILL.drawdownDollars === 58.75, 'the existing latch line is still in force beside the floor');
  const d = checker([win(at(0)), loss(-59.5, at(1))]);
  assert.ok(['trial', 'drawdown'].includes((await gk.runGoldKillCheck(d.io)).tripped), 'a deep drawdown still latches');
};

// GT3: the trial cannot start before rearmAt. Between the previous generation's re-arm time and the start gold is held off (even with no stored latch), and an order before the start is never sized as a trial.
gates.GT3 = async () => {
  assert.strictEqual(gk.GOLD_KILL.rearmAt, START);
  assert.strictEqual(gk.GOLD_TRIAL.startedAt, gk.GOLD_KILL.rearmAt, 'the trial starts at the re-arm time and nowhere else');
  assert.ok(!gk.goldTrialActive(T_BEFORE) && gk.goldTrialActive(T_IN));
  assert.strictEqual(gk.goldTrialMax('KXGOLD15M', T_BEFORE), null);
  assert.ok(gk.goldNotStarted('KXGOLD15M', T_BEFORE) && !gk.goldNotStarted('KXGOLD15M', T_IN) && !gk.goldNotStarted('KXGOLD15M', T_OLD) && !gk.goldNotStarted('KXXRP15M', T_BEFORE));
  const w = world(T_BEFORE);
  await tick(w, state(T_BEFORE, { hardStop: { rearmAt: hsLib.HARD_STOP.rearmAt, status: 'ok', tripped: false, checkedAt: T_BEFORE - 60000 } }));
  assert.strictEqual(w.posts.length, 0, 'before the start gold places nothing');
  // a trial whose start is not this generation's re-arm time is not active and changes nothing
  assert.ok(!gk.goldTrialActive(T_IN, gk.GOLD_KILL, { ...gk.GOLD_TRIAL, startedAt: START - 1 }));
  const ev = gk.evaluateGold({ orders: Array.from({ length: 13 }, (_, i) => loss(-5, at(i))), trial: { ...gk.GOLD_TRIAL, startedAt: START + 1 } });
  assert.strictEqual(ev.trip.rule, 'drawdown', 'no matching trial, no floor');
  // trades before the start are history: they set no peak and count toward no fill
  const hist = checker(Array.from({ length: 10 }, (_, i) => loss(-5, START - 86400000 + i * 60000)));
  assert.ok(!(await gk.runGoldKillCheck(hist.io)).tripped);
};

// GT4: nothing stored, requested or typed can loosen it: the constants are frozen, the half-size path is off, no callable or page path touches them.
gates.GT4 = async () => {
  assert.ok(Object.isFrozen(gk.GOLD_TRIAL) && Object.isFrozen(gk.GOLD_KILL));
  assert.deepStrictEqual({ c: gk.GOLD_TRIAL.contracts, a: gk.GOLD_TRIAL.addon, f: gk.GOLD_TRIAL.floorNet, n: gk.GOLD_TRIAL.floorAfterFills }, { c: 3, a: 0, f: -18, n: 5 });
  assert.ok(/owner written exception to the return rule, Nov 13, 2026/.test(gk.GOLD_TRIAL.exception));
  assert.strictEqual(gk.GOLD_KILL.rearmIsReturn, false, 'the half size path does not apply: the trial size does');
  assert.ok(!gk.goldHalfSize({ goldKill: { rearmAt: START, half: true } }, 'KXGOLD15M'));
  // a stored value cannot raise the size or lift the trial
  const w = world(T_IN);
  await tick(w, state(T_IN, { cap: 99, maxContracts: 99, goldTrial: { contracts: 50 }, goldKill: { tripped: false, rearmAt: START, trial: { contracts: 50 } } }));
  assert.ok(w.posts.length === 1 && w.posts[0].count <= 3, 'stored values do not move the trial');
  const src = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8') + fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8') + fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(!/request\.data[^\n]*(GOLD_TRIAL|goldTrial)|(GOLD_TRIAL|goldTrial)[^\n]*request\.data/.test(src), 'no callable takes the trial from a caller');
  const lib = fs.readFileSync(path.join(root, 'functions', 'kalshiGoldKillLib.js'), 'utf8').replace(/\/\/.*$/gm, '');
  assert.ok(!/fetch|keyId|pem|\/portfolio|method: "POST"/.test(lib), 'the library still holds no key and sends nothing');
};

// GT5: the exit watch still sells open gold at 25c: it never looks at the trial or the latch.
gates.GT5 = async () => {
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  const code = src.slice(src.indexOf('async function runExitWatch'), src.indexOf('async function flattenAll')).replace(/\/\/.*$/gm, '');
  assert.ok(!/goldKill|goldTrial|GOLD_TRIAL|maxContractsAt/.test(code), 'the exit watch does not name the trial');
};

// GT6: every other L1 rule is unchanged: another series is not capped, the band is the same, and the trial only lowers a count.
gates.GT6 = async () => {
  assert.strictEqual(gk.goldTrialMax('KXBTC15M', T_IN), null);
  assert.strictEqual(live.L1_SIZE_CEILING, 15, 'the ceiling is still 15: it is what applies once the trial ends');
  assert.strictEqual(live.L1_ORDER_CEILING, 50);
  const src = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.ok(/count = Math\.min\(count, trialMax\)/.test(src), 'the trial only ever lowers a count');
};

// GT7: the verdict text and the event say which rule latched, and the page knows the new rule word.
gates.GT7 = async () => {
  const b = checker([loss(-5, at(0)), loss(-5, at(1)), loss(-5, at(2)), loss(-5, at(3)), loss(-5, at(4))]);
  await gk.runGoldKillCheck(b.io);
  assert.ok(/trial/.test(b.state.sizing.goldKill.detail) && /18/.test(b.state.sizing.goldKill.detail));
  assert.ok(/Only a reviewed edit re-arms it/.test(b.events[0].detail));
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(/g\.rule === 'trial'/.test(html), 'the page reads the trial rule');
};

// GT8: the page says plainly that gold is a trial below the research bar, with the written terms and the Nov 19 checkpoint rules.
gates.GT8 = async () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  for (const s of ['Trial: below the research bar', '3 contracts', '-$18 after 5 trades', 'Nov 19']) assert.ok(html.includes(s), 'index.html says: ' + s);
  const reg = JSON.parse(fs.readFileSync(path.join(root, 'strategies-registry.json'), 'utf8'));
  const row = JSON.stringify(reg).includes('Trial: below the research bar');
  assert.ok(row, 'the registry row says it too');
};

(async () => {
  let failed = 0;
  for (const [k, f] of Object.entries(gates)) { try { await f(); console.log('ok   ' + k); } catch (e) { failed++; console.log('FAIL ' + k + '\n' + (e && e.stack || e)); } }
  process.exit(failed ? 1 : 0);
})();
