// The simulated ETH and SOL run (functions/kalshiSimLib.js): it follows the live bot's path up to the order and never places one. Plain node, no framework.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const sim = require('../functions/kalshiSimLib.js');
const live = require('../functions/kalshiLiveLib.js');
const libSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiSimLib.js'), 'utf8');
const idxSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const rulesSrc = fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8');

const NOW = Date.parse('2026-10-09T20:00:00Z');
const mkt = (series, over = {}) => ({ ticker: series + '-T1', series, status: 'active', close_time: new Date(NOW + 360000).toISOString(),
  yes_bid_dollars: '0.9000', yes_ask_dollars: '0.9100', yes_bid_size_fp: '500.00', yes_ask_size_fp: '500.00', exchange_index: 2, ...over });
function world({ markets, second, state = { active: true }, session = { sizing: true, sizeCap: 12, sizeAddon: 8 }, cash = 553 } = {}) {
  const docs = new Map(), notes = [], reads = {};
  const store = {
    async createTest(id, d) { if (docs.has(id)) return false; docs.set(id, { ...d }); return true; },
    async updateTest(id, patch) { Object.assign(docs.get(id), patch); },
  };
  return { docs, notes, store,
    args: { state, session, cash, now: NOW, active: true, quotes: markets.map((m) => ({ series: m.series, m })), store,
      readMarket: async (t) => { reads[t] = (reads[t] || 0) + 1; return reads[t] === 1 ? markets.find((m) => m.ticker === t) : (second && second[t]) || markets.find((m) => m.ticker === t); },
      sleep: async () => {}, setState: async (p) => { notes.push(p.lastNote); } } };
}

const gates = {};

// S1: the simulation cannot place an order. Its library has no signing, no key, no portfolio call and no POST, and its scheduled function is declared with no secrets.
gates.S1 = () => {
  const code = libSrc.replace(/\/\/.*$/gm, '');
  for (const bad of ['signRequest', 'PRIVATE', 'KEY_ID', '/portfolio', 'POST', 'liveRequest', 'runL1Tick', 'flattenAll', 'createOrder']) assert.ok(!code.includes(bad), 'the simulation library must not contain ' + bad);
  const tick = idxSrc.slice(idxSrc.indexOf('exports.kalshiSimTick = onSchedule('), idxSrc.indexOf('exports.kalshiLiveArmed = onSchedule('));
  assert.ok(/exports\.kalshiSimTick = onSchedule\(\s*\{ schedule: "every 1 minutes", timeoutSeconds: 55, retryCount: 0, memory: "256MiB" \}/.test(tick), 'declared with no secrets');
  assert.ok(!/KALSHI_LIVE_KEY_ID|KALSHI_LIVE_PRIVATE_KEY|secrets:/.test(tick + idxSrc.slice(idxSrc.indexOf('exports.kalshiSimSession'), idxSrc.indexOf('exports.kalshiSimTick'))), 'neither sim function can see the live key');
  assert.ok(idxSrc.indexOf('exports.kalshiSimTick') < idxSrc.indexOf('exports.kalshiBookRecorder'), 'the recorder stays last');
};

// S2: the fill is judged on a second read of the book, the way an immediate-or-cancel order at the touch would be.
gates.S2 = () => {
  const yes = { side: 'yes', price: 0.91, limit: 0.91, worst: 0.91 };
  assert.deepStrictEqual(sim.simFill(yes, 20, mkt('KXETH15M')), { fillCount: 20, price: 0.91, reason: 'filled' }, 'price held, plenty of size: fills in full');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_ask_dollars: '0.9200' })).fillCount, 0, 'the ask moved one cent past the limit: no fill');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_ask_dollars: '0.9000' })).price, 0.9, 'a better ask is paid at the touch');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_ask_size_fp: '7.00' })).fillCount, 7, 'a partial fill, only what rests at the touch');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_ask_size_fp: '0.00' })).fillCount, 0, 'nothing resting is no fill');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_ask_size_fp: undefined })).fillCount, 0, 'an unknown size is no fill, never a guess');
  assert.strictEqual(sim.simFill(yes, 20, mkt('KXETH15M', { yes_bid_dollars: '0.9500', yes_ask_dollars: '0.9100' })).fillCount, 0, 'a crossed book is no fill');
  const no = { side: 'no', price: 0.91, limit: 0.09, worst: 0.91 };
  assert.deepStrictEqual(sim.simFill(no, 20, mkt('KXETH15M', { yes_bid_dollars: '0.0900', yes_ask_dollars: '0.1000' })), { fillCount: 20, price: 0.91, reason: 'filled' }, 'NO side prices off the yes bid');
  assert.strictEqual(sim.simFill(no, 20, mkt('KXETH15M', { yes_bid_dollars: '0.0800', yes_ask_dollars: '0.0900' })).fillCount, 0, 'NO moved to 92c, past the limit');
};

// S3: a trade here is the size a live Bitcoin or gold trade is: the same l1Count on the live session's cap, add-on and the account's cash.
gates.S3 = async () => {
  const w = world({ markets: [mkt('KXETH15M')] });
  await sim.runSimTick(w.args);
  const r = w.docs.get('SIM-KXETH15M-T1');
  const cost1 = 0.91 + require('../functions/kalshiSignalLib.js').takerFee(0.91, 1);
  assert.strictEqual(r.count, live.l1Count(553, cost1, 12, 8), 'same stake as the live rule');
  assert.ok(r.count > 12, 'the base plus the profit add-on, not one contract');
  assert.strictEqual(r.status, 'filled');
  assert.strictEqual(r.mode, 'sim');
  assert.strictEqual(r.calibration, false);
  assert.ok(r.maxCost > 0 && r.addon > 0 && r.addonCost > 0, 'carries the fields the loss stop and the page stats read');
  const off = world({ markets: [mkt('KXETH15M')], session: { sizing: false } });
  await sim.runSimTick(off.args);
  assert.strictEqual(off.docs.get('SIM-KXETH15M-T1').count, 1, 'a session without scaling sends one contract, and so does the sim');
};

// S4: nothing happens when it is off, outside the 6 minute window, or when no side is priced 88c to 97c; one record per market, however often the minute runs.
gates.S4 = async () => {
  const w = world({ markets: [mkt('KXETH15M')], state: { active: false } });
  assert.deepStrictEqual(await sim.runSimTick(w.args), { skipped: 'off' }); assert.strictEqual(w.docs.size, 0);
  const early = world({ markets: [mkt('KXETH15M', { close_time: new Date(NOW + 600000).toISOString() })] });
  await sim.runSimTick(early.args); assert.strictEqual(early.docs.size, 0, '10 minutes left is outside the window');
  const mid = world({ markets: [mkt('KXETH15M', { yes_bid_dollars: '0.4900', yes_ask_dollars: '0.5100' })] });
  await sim.runSimTick(mid.args); assert.strictEqual(mid.docs.size, 0, 'a 50c market is not a signal');
  const twice = world({ markets: [mkt('KXSOL15M')] });
  await sim.runSimTick(twice.args); await sim.runSimTick(twice.args);
  assert.strictEqual(twice.docs.size, 1, 'a second run on the same market simulates nothing new');
  assert.ok(/already simulated/.test(twice.notes[twice.notes.length - 1]));
};

// S5: a price that moves between the decision and the arrival is a no fill, which is what makes the sim's fill rate comparable with the real bot's.
gates.S5 = async () => {
  const w = world({ markets: [mkt('KXETH15M')], second: { 'KXETH15M-T1': mkt('KXETH15M', { yes_bid_dollars: '0.9200', yes_ask_dollars: '0.9400' }) } });
  await sim.runSimTick(w.args);
  const r = w.docs.get('SIM-KXETH15M-T1');
  assert.strictEqual(r.status, 'no fill'); assert.strictEqual(r.fillCount, '0'); assert.ok(/moved/.test(r.reason));
  assert.ok(r.seen && r.seen2 && r.seen2.ask === 0.94, 'both books are kept so a no fill can be explained afterwards');
  const failed = world({ markets: [mkt('KXETH15M')] });
  const rm = failed.args.readMarket; let n = 0;
  failed.args.readMarket = async (t) => { n++; if (n === 2) throw new Error('timeout'); return rm(t); };
  await sim.runSimTick(failed.args);
  assert.strictEqual(failed.docs.get('SIM-KXETH15M-T1').status, 'error', 'a failed second read is an error record, not a guessed fill');
};

// S6: Bitcoin and gold run through the same code only to be compared with the real bot's fills, and are flagged so the page never counts them as candidates.
gates.S6 = async () => {
  const w = world({ markets: [mkt('KXBTC15M'), mkt('KXGOLD15M'), mkt('KXXRP15M')] });
  await sim.runSimTick(w.args);
  assert.strictEqual(w.docs.get('SIM-KXBTC15M-T1').calibration, true);
  assert.strictEqual(w.docs.get('SIM-KXGOLD15M-T1').calibration, true);
  assert.ok(!w.docs.has('SIM-KXXRP15M-T1'), 'only the four named series');
  assert.deepStrictEqual(sim.SIM_SERIES, ['KXETH15M', 'KXSOL15M']);
};

// S7: a simulated order settles with the same arithmetic as a live one, so its profit is comparable.
gates.S7 = async () => {
  const w = world({ markets: [mkt('KXETH15M')] });
  await sim.runSimTick(w.args);
  const r = w.docs.get('SIM-KXETH15M-T1');
  const won = live.settledFields(r, r.side).settledPnl, lost = live.settledFields(r, r.side === 'yes' ? 'no' : 'yes').settledPnl;
  assert.ok(won > 0 && lost < 0, 'a win is positive and a loss is negative');
  assert.ok(Math.abs(lost + r.maxCost) < 1e-6, 'a full loss costs the whole order, which is what the stop counts');
};

// S8: the page can read the records and nothing but the server can write them.
gates.S8 = () => {
  for (const col of ['kalshiSimOrders', 'kalshiSimControl']) {
    const m = rulesSrc.match(new RegExp('match /' + col + '/\\{id\\} \\{[^}]*\\}'));
    assert.ok(m && /allow read: if isAdmin\(\);/.test(m[0]) && /allow write: if false;/.test(m[0]), col + ' is admin read, server write only');
  }
};

// S9: a failure past the admin check names its cause (never a bare "internal" on the page), and a Kalshi outage does not fail the tick before the settle sweep.
gates.S9 = () => {
  const sess = idxSrc.slice(idxSrc.indexOf('exports.kalshiSimSession'), idxSrc.indexOf('exports.kalshiSimTick'));
  assert.ok(/try \{[\s\S]*\} catch \(e\) \{[\s\S]*new HttpsError\("unavailable", "Could not save the simulation switch: "/.test(sess), 'the switch names its failure');
  const tick = idxSrc.slice(idxSrc.indexOf('exports.kalshiSimTick'), idxSrc.indexOf('exports.kalshiLiveArmed'));
  assert.ok(tick.indexOf('This minute could not be read') > -1 && tick.indexOf('This minute could not be read') < tick.indexOf('live.settleOpenOrders'), 'a failed minute is a note, and the settle sweep still runs after it');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
