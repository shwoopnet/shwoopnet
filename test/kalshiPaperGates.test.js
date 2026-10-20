'use strict';
// The paper tracker (PAPER1): what L1's rule WOULD have bought on three candidate markets, one contract, no money. Each gate states the consequence. The point of the design: it can be wrong or down, and it
// can never touch an order, a key or the live record.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const paper = require('../functions/kalshiPaperLib');
const live = require('../functions/kalshiLiveLib');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiPaperLib.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const NOW = Date.parse('2026-10-20T20:08:00Z');                       // minute 8 of the quarter hour: inside the entry minutes
const mkt = (over) => Object.assign({ ticker: 'KXAUDUSD15M-26OCT201615-T1', yes_bid_dollars: '0.92', yes_ask_dollars: '0.93', close_time: new Date(NOW + 360000).toISOString() }, over || {});
const gates = {};

// The rule is L1's: on every quote in a grid, the paper pick and the live pick agree on side and price, so a paper result is a result of the rule that trades.
gates.R1 = () => {
  let compared = 0, picked = 0;
  for (let bid = 1; bid <= 99; bid++) for (const spread of [0, 1, 2, 5, 11]) {
    const ask = bid + spread;
    if (ask > 100) continue;
    const m = { yes_bid_dollars: (bid / 100).toFixed(4), yes_ask_dollars: (ask / 100).toFixed(4) };
    const a = paper.pick(m), b = live.l1Pick(m);
    assert.deepStrictEqual(a ? [a.side, a.price] : null, b ? [b.side, b.price] : null, 'bid ' + bid + ' ask ' + ask);
    compared++; if (a) picked++;
  }
  assert.ok(compared > 400 && picked > 30, 'a real grid: ' + compared + ' quotes, ' + picked + ' picks');
  assert.strictEqual(paper.pick({ yes_bid_dollars: '0.001', yes_ask_dollars: '0.999' }), null, 'an empty book is not a quote');
  assert.deepStrictEqual([paper.PAPER_BAND[0], paper.PAPER_BAND[1]], [live.L1_BAND[0], live.L1_BAND[1]], 'the same band');
  assert.deepStrictEqual(paper.PAPER_WINDOW_MS, live.L1_WINDOW_MS, 'the same window');
};

// The three registered candidates, and the entry minutes follow from the window.
gates.R2 = () => {
  assert.deepStrictEqual(paper.PAPER_SERIES, ['KXAUDUSD15M', 'KXUSDCAD15M', 'KXNATGAS15M'], 'exactly what PAPER1 registered; a fourth is a code edit and a README entry first');
  assert.deepStrictEqual(paper.ENTRY_MINUTES, [7, 8, 9, 10]);
  const at = (leftMs) => paper.inWindow({ close_time: new Date(NOW + leftMs).toISOString() }, NOW);
  assert.deepStrictEqual([at(329999), at(330000), at(400000), at(400001)], [false, true, true, false]);
};

// One entry per market however many processes or minutes see it; outside the entry minutes with nothing waiting, it does not even read Kalshi.
gates.R3 = async () => {
  const docs = new Map(), reads = [];
  const store = { async openDocs() { return [...docs.entries()].filter(([, d]) => d.settled === false).map(([id, data]) => ({ id, data })); },
    async create(id, d) { if (docs.has(id)) return false; docs.set(id, d); return true; }, async update(id, p) { Object.assign(docs.get(id), p); } };
  const fetchSeries = async (s) => { reads.push(s); return s === 'KXAUDUSD15M' ? [mkt(), mkt({ ticker: 'KXAUDUSD15M-T2', yes_bid_dollars: '0.40', yes_ask_dollars: '0.41' })] : []; };
  const a = await paper.runPaperTick({ store, fetchSeries, fetchMarket: async () => null, now: NOW });
  assert.deepStrictEqual([a.entries, docs.size], [1, 1], 'only the market inside the band is recorded');
  const doc = docs.get('KXAUDUSD15M-26OCT201615-T1');
  assert.deepStrictEqual([doc.strategy, doc.candidate, doc.side, doc.price, doc.count, doc.settled], ['PAPER', 'KXAUDUSD15M', 'yes', 0.93, 1, false]);
  const b = await paper.runPaperTick({ store, fetchSeries, fetchMarket: async () => null, now: NOW + 20000 });
  assert.strictEqual(b.entries, 0, 'the same market is not recorded twice (a second instance during a deploy)');
  reads.length = 0;
  const idle = await paper.runPaperTick({ store: { openDocs: async () => [], create: async () => true, update: async () => {} }, fetchSeries, fetchMarket: async () => null, now: Date.parse('2026-10-20T20:02:00Z') });
  assert.deepStrictEqual([idle.idle, reads.length], [true, 0], 'outside the entry minutes and nothing to settle: no read at all');
};

// Settling: from the public result, one contract, the research's fee model; a result that is not out yet leaves it open; a failing candidate does not stop the others.
gates.R4 = async () => {
  const win = { price: 0.93, side: 'yes' }, loss = { price: 0.93, side: 'no' };
  const w = paper.settleFields(win, 'yes'), l = paper.settleFields(loss, 'yes');
  assert.ok(Math.abs(w.pnl - (1 - 0.93 - 0.07 * 0.93 * 0.07)) < 1e-4 && w.pnl > 0.06 && w.pnl < 0.07, 'a win pays the last 7c less the fee: ' + w.pnl);
  assert.ok(Math.abs(l.pnl - (-0.93 - 0.07 * 0.93 * 0.07)) < 1e-4, 'a loss costs the price and the fee: ' + l.pnl);
  assert.ok(w.pnlStress < w.pnl, 'the stressed fee is higher');
  const docs = new Map([['A', { settled: false, side: 'yes', price: 0.93, closeTime: new Date(NOW - 120000).toISOString(), ticker: 'A' }], ['B', { settled: false, side: 'yes', price: 0.93, closeTime: new Date(NOW - 120000).toISOString(), ticker: 'B' }],
    ['C', { settled: false, side: 'yes', price: 0.93, closeTime: new Date(NOW + 300000).toISOString(), ticker: 'C' }]]);
  const store = { async openDocs() { return [...docs.entries()].filter(([, d]) => d.settled === false).map(([id, data]) => ({ id, data })); }, async create() { return false; }, async update(id, p) { Object.assign(docs.get(id), p); } };
  const fetchMarket = async (t) => { if (t === 'A') throw new Error('kalshi down'); return t === 'B' ? { result: 'yes' } : { result: '' }; };
  const r = await paper.runPaperTick({ store, fetchSeries: async () => [], fetchMarket, now: NOW });
  assert.strictEqual(r.settled, 1, 'B settles even though A failed');
  assert.strictEqual(docs.get('B').result, 'yes');
  assert.strictEqual(docs.get('A').settled, false, 'A stays open for the next minute');
  assert.strictEqual(docs.get('C').settled, false, 'a market that has not closed is not read');
};

// The registered bar, exactly: 300 entries on 10 days, mean above zero, day clustered z of at least 2.1, both halves, fees x1.2. Too little is NOT_ENOUGH_DATA, never a pass or a fail.
gates.R5 = () => {
  assert.deepStrictEqual([paper.BAR.minN, paper.BAR.minDays, paper.BAR.z, paper.BAR.stress, paper.BAR.earliestRead], [300, 10, 2.1, 1.2, '2026-11-30']);
  const mk = (days, per, mean, wobble = 0.004) => { const out = []; for (let d = 0; d < days; d++) for (let i = 0; i < per; i++) out.push({ settled: true, day: '2026-11-' + String(d + 1).padStart(2, '0'), pnl: mean + wobble * ((d % 3) - 1) + 0.001 * (i % 2), pnlStress: mean - 0.004 + wobble * ((d % 3) - 1) }); return out; };
  assert.strictEqual(paper.bar(mk(5, 100, 0.03)).verdict, 'NOT_ENOUGH_DATA', 'too few days');
  assert.strictEqual(paper.bar(mk(12, 10, 0.03)).verdict, 'NOT_ENOUGH_DATA', 'too few entries');
  assert.strictEqual(paper.bar(mk(12, 30, 0.03)).verdict, 'NOT_YET_FALSIFIED');
  assert.strictEqual(paper.bar(mk(12, 30, -0.03)).verdict, 'FALSIFIED');
  assert.strictEqual(paper.bar(mk(12, 30, 0.003, 0.03)).verdict, 'FALSIFIED', 'a mean inside the noise (z under 2.1) is not a pass');
  const weak = mk(12, 30, 0.03).map((r) => Object.assign({}, r, { pnlStress: -0.001 }));
  assert.strictEqual(paper.bar(weak).verdict, 'FALSIFIED', 'positive only at the base fee is not enough');
  assert.strictEqual(paper.bar([{ settled: false, day: 'x', pnl: 1 }]).verdict, 'NOT_ENOUGH_DATA', 'unsettled rows are not data');
};

// Keyless, read only, and apart from the trading code: no key, no signing, no order, no /portfolio call, no secret on its function, nothing shared with the live library; the function catches everything.
gates.R6 = () => {
  const code = libSrc.replace(/\/\/[^\n]*/g, '');
  assert.ok(!/require\("\.\/kalshi(Live|Account|Push|Book)Lib"\)|KALSHI_LIVE|PRIVATE_KEY|liveRequest|\/portfolio|method: "POST"|\bPOST\b|sign\(/.test(code), 'the library has no key, signing, order or /portfolio');
  const block = fnSrc.slice(fnSrc.indexOf('// ---- The paper tracker (PAPER1), keyless'), fnSrc.indexOf('// ---- Phone alerts (Web Push), admin only'));
  assert.ok(block.length > 500, 'the paper block is in place before the alerts and the recorder');
  const opts = /exports\.kalshiPaperTick = onSchedule\(\s*\{([^}]*)\}/.exec(block);
  assert.ok(opts && !/secrets/.test(opts[1]), 'scheduled with no secrets');
  assert.ok(!/KALSHI_LIVE|PRIVATE_KEY|liveRequest|\/portfolio|method: "POST"/.test(block.replace(/\/\/[^\n]*/g, '')), 'the function reads public markets only');
  assert.ok(/try \{[\s\S]*\} catch \(e\) \{ console\.error\("kalshiPaperTick: "/.test(block), 'it catches every error');
  assert.ok(fnSrc.indexOf('exports.kalshiPaperTick') < fnSrc.indexOf('exports.kalshiBookRecorder'), 'the recorder stays last');
  for (const f of ['kalshiLiveLib.js', 'kalshiAccountLib.js', 'kalshiPushLib.js', 'kalshiBookLib.js']) assert.ok(!/kalshiPaperLib/.test(fs.readFileSync(path.join(root, 'functions', f), 'utf8')), f + ' does not know about the tracker');
  const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
  const rule = /match \/kalshiPaperOrders\/\{id\} \{([^}]*)\}/.exec(rules);
  assert.ok(rule && /allow read: if isAdmin\(\)/.test(rule[1]) && /allow write: if false/.test(rule[1]), 'the admin reads it, nobody writes it from a browser');
};

// The page: its own card and collection, never in the live totals; the figures per candidate, with the bar stated; nothing is ordered from it.
gates.R7 = () => {
  const stats = new Function(/(function kalshiPaperStats\([^)]*\)\{[\s\S]*?\n  \})\n/.exec(html)[1] + '; return kalshiPaperStats;')();
  const rows = [{ candidate: 'A', settled: true, pnl: 0.06, result: 'yes', side: 'yes', day: 'd1' }, { candidate: 'A', settled: true, pnl: -0.94, result: 'no', side: 'yes', day: 'd2' }, { candidate: 'A', settled: false }, { candidate: 'B', settled: true, pnl: 0.06, result: 'yes', side: 'yes', day: 'd1' }];
  const s = stats(rows, 'A');
  assert.deepStrictEqual([s.entries, s.settled, s.wins, s.days], [3, 2, 1, 2]);
  assert.ok(Math.abs(s.perContract - (-0.44)) < 1e-9, 'per contract over the settled ones only');
  assert.strictEqual(stats([], 'A').perContract, null, 'no result yet says so, not zero');
  assert.ok(/id="kalPaperCard"/.test(html) && /Paper candidates \(no money\)/.test(html), 'its own card, labelled');
  assert.ok(/Hypothetical: one contract each[\s\S]{0,200}nothing is ordered/.test(html) && /on or after Nov 30, with at least 300 settled entries on 10 days/.test(html), 'it says what it is and when it can say anything');
  const render = /function renderKalshiPaper\(\)\{[\s\S]*?\n  \}\n/.exec(html)[0];
  assert.ok(!/kalshiLiveOrders|kalshiPerfStats|kalshiLiveTotals/.test(render), 'it never touches the live record');
  assert.ok(/KAL_PAPER = \[\['KXAUDUSD15M'[\s\S]*?'KXUSDCAD15M'[\s\S]*?'KXNATGAS15M'/.test(html), 'the same three candidates as the server');
};

// The deploy: only the tracker and the rule, no secrets, no switch that has to be kept.
gates.R8 = () => {
  const out = execFileSync('bash', [path.join(root, 'functions', 'deploy-paper.sh')], { env: Object.assign({}, process.env, { DRY_RUN: '1' }), encoding: 'utf8' });
  assert.deepStrictEqual(/deploy --only (\S+)/.exec(out)[1].split(',').sort(), ['firestore:rules', 'functions:kalshiPaperTick']);
  const sh = fs.readFileSync(path.join(root, 'functions', 'deploy-paper.sh'), 'utf8').replace(/#.*$/gm, '');
  assert.ok(!/secrets:set|KALSHI_LIVE|sed -i/.test(sh), 'it holds no secret and no order switch');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
