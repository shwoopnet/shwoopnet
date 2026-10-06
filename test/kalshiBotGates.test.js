// The server-side Kalshi PAPER bot. It makes simulated trades once a minute on Firebase.
// A bug here is not a cosmetic bug: the same loop will later sit in front of real
// orders, so every rule that protects money is stated as a consequence and exercised
// by running the real code against a scripted Kalshi and an in-memory store.
// The cases mirror kalshi-scalper's Python tests.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const lib = require('../functions/kalshiBotLib');
const { runTick } = require('../functions/kalshiBotRun');

const root = path.join(__dirname, '..');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const gates = {};

// ---- helpers: local noon in the owner's timezone (CDT is UTC-5 until Nov 1 2026) ----
const NOON = Date.parse('2026-10-05T17:00:00Z');          // 12:00 CDT
const at = (h, m = 0) => Date.parse('2026-10-05T05:00:00Z') + (h * 60 + m) * 60000;   // local h:m on Oct 5, CDT
const CLOSE = NOON + 15 * 60000;

class MemStore {
  constructor() { this.pos = new Map(); this.events = []; this.status = null; this.control = {}; }
  async getStatus() { return this.status; }
  async getControl() { return this.control; }
  async listOpen() { return [...this.pos.values()].filter((p) => p.status === 'open').map((p) => ({ ...p })); }
  async listClosedSince(ms) { return [...this.pos.values()].filter((p) => p.status === 'closed' && p.settledAt >= ms).map((p) => ({ ...p })); }
  async createPosition(id, data) { if (this.pos.has(id)) return false; this.pos.set(id, { id, ...data }); return true; }
  async closePosition(id, patch) { const p = this.pos.get(id); if (!p || p.status !== 'open') return false; Object.assign(p, patch, { status: 'closed' }); return true; }
  async addEvent(e) { this.events.push(e); }
  async setStatus(s) { this.status = s; }
  kinds(k) { return this.events.filter((e) => e.kind === k).length; }
}
class FakeKalshi {
  constructor() { this.mk = {}; this.result = {}; this.active = true; this.failAll = false; this.failSeries = new Set(); this.marketCalls = 0; }
  async exchangeStatus() { if (this.failAll) throw new Error('exchange down'); return { trading_active: this.active }; }
  async markets(series) { if (this.failAll || this.failSeries.has(series)) throw new Error('markets down'); return this.mk[series] || []; }
  async market(ticker) { this.marketCalls++; return { result: this.result[ticker] || '' }; }
  put(ticker, bid, ask, closeMs, o = {}) {
    const series = o.series || 'KXBTC15M';
    this.mk[series] = (this.mk[series] || []).filter((m) => m.ticker !== ticker).concat([{
      ticker, status: o.status || 'active', close_time: new Date(closeMs).toISOString(),
      yes_bid_dollars: bid.toFixed(4), yes_ask_dollars: ask.toFixed(4),
      yes_ask_size_fp: String(o.askSz ?? 100), yes_bid_size_fp: String(o.bidSz ?? 100),
    }]);
  }
}
const make = () => ({ store: new MemStore(), api: new FakeKalshi() });
const tick = (c, now) => runTick({ store: c.store, api: c.api, now });
const posOf = (c, id) => c.store.pos.get(id);

// ================= pure logic =================

gates.G1 = () => {
  assert.strictEqual(lib.takerFee(0.40, 7), 0.12);        // 11.76c rounds UP to 12c
  assert.strictEqual(lib.takerFee(0.5, 10), 0.18);
  assert.strictEqual(lib.takerFee(0, 5), 0);
  assert.ok(!lib.validQuote(0.001, 1.0) && !lib.validQuote(null, 0.5) && !lib.validQuote(0.3, 0.55));
  assert.ok(lib.validQuote(0.47, 0.49) && lib.validQuote(0.001, 0.01));
};

// The day is the OWNER's day, not the server's. A loss at 11pm CDT yesterday is
// 4am UTC today; counted as today's it would shut the bot for a day it never traded.
gates.G2 = () => {
  assert.strictEqual(lib.localDayStart(NOON), Date.parse('2026-10-05T05:00:00Z'));
  assert.strictEqual(lib.localDayStart(Date.parse('2026-10-06T03:00:00Z')), Date.parse('2026-10-05T05:00:00Z'));
  const yesterdayLateEvening = Date.parse('2026-10-05T04:00:00Z');               // 23:00 CDT Oct 4
  const t = lib.tierState([{ settledAt: yesterdayLateEvening, pnl: -20 }], 300, NOON);
  assert.strictEqual(t.mode, 'ok', 'yesterday evening must not count today');
};

// Same cases as the web page (and the retired Python bot).
gates.G3 = () => {
  const t = lib.tierState([], 300, at(12));
  assert.deepStrictEqual([t.mode, t.cap, t.softLimit, t.hardLimit], ['ok', 3, 9, 15]);
  const two = [{ settledAt: at(9), pnl: -5 }, { settledAt: at(10), pnl: -5 }];
  assert.strictEqual(lib.tierState(two, 300, at(11, 59)).mode, 'break');
  assert.strictEqual(lib.tierState(two, 300, at(11, 59)).cap, 0);
  const half = lib.tierState(two, 300, at(12, 1));
  assert.deepStrictEqual([half.mode, half.cap], ['half', 1.5]);
  assert.strictEqual(lib.tierState(two.concat([{ settledAt: at(10, 30), pnl: 8 }]), 300, at(11)).mode, 'break', 'a later win must not end the break');
  assert.strictEqual(lib.tierState([{ settledAt: at(9), pnl: -16 }, { settledAt: at(9, 30), pnl: 20 }], 300, at(14)).mode, 'done', 'the hard stop is sticky');
  assert.strictEqual(lib.tierState([], 0, at(12)).mode, 'done');
  assert.strictEqual(lib.tierState([], '', at(12)).mode, 'done');
  const own = lib.tierState([], lib.BANKROLL, at(12));      // the owner's $100
  assert.deepStrictEqual([lib.BANKROLL, own.cap, own.softLimit, own.hardLimit], [100, 1, 3, 5]);
};

gates.G4 = () => {
  assert.strictEqual(lib.sizeFor(0.40, 3.0, null), 7);
  assert.strictEqual(lib.sizeFor(0.42, 3.0, null), 6, 'the fee counts: 7 x 42c = $2.94 fits, plus a 12c fee does not');
  assert.strictEqual(lib.sizeFor(0.40, 3.0, 3), 3, 'never more than the touch shows');
  assert.strictEqual(lib.sizeFor(0.40, 0.30, null), 0);
  assert.strictEqual(lib.sizeFor(1.2, 3.0, null) + lib.sizeFor(0.4, 0, null), 0);
  assert.strictEqual(lib.sizeFor(0.40, 1.0, null), 2, 'at $100 a trade is one or two contracts');
};

gates.G5 = () => {
  const q = (bid, ask, extra = {}) => [{ series: 'KXBTC15M', m: { ticker: 'T', status: 'active', close_time: new Date(CLOSE).toISOString(),
    yes_bid_dollars: String(bid), yes_ask_dollars: String(ask), yes_ask_size_fp: '100', yes_bid_size_fp: '100', ...extra } }];
  const yes = lib.planEntries(q(0.39, 0.40), NOON, 3)[0];
  assert.deepStrictEqual([yes.side, yes.band, yes.contracts, yes.price], ['yes', '40c', 7, 0.40]);
  const no = lib.planEntries(q(0.59, 0.61), NOON, 3)[0];
  assert.ok(no.side === 'no' && Math.abs(no.price - 0.41) < 1e-9, 'NO is bought at 1 minus the YES bid');
  assert.strictEqual(lib.planEntries(q(0.55, 0.57), NOON, 3).length, 0, 'outside the bands');
  assert.strictEqual(lib.planEntries(q(0.39, 0.40), CLOSE - 240000, 3).length, 0, 'under 5 minutes left');
  assert.strictEqual(lib.planEntries(q(0.001, 1.0), NOON, 3).length, 0, 'an empty book is not a quote');
  assert.strictEqual(lib.planEntries(q(0.39, 0.40, { status: 'finalized' }), NOON, 3).length, 0);
  assert.strictEqual(lib.planEntries(q(0.39, 0.40, { yes_ask_size_fp: '2' }), NOON, 3)[0].contracts, 2);
};

gates.G6 = () => {
  const pos = { side: 'yes', contracts: 7, entry: 0.40, entryFee: 0.12, entryAt: NOON };
  const m = (bid, ask) => ({ ticker: 'T', status: 'active', close_time: new Date(CLOSE).toISOString(), yes_bid_dollars: String(bid), yes_ask_dollars: String(ask) });
  assert.ok(!lib.exitDue(pos, m(0.85, 0.86), NOON), 'never on the entry tick');
  assert.ok(lib.exitDue(pos, m(0.81, 0.82), NOON + 1));
  assert.ok(!lib.exitDue(pos, m(0.79, 0.80), NOON + 1));
  assert.ok(lib.exitDue({ ...pos, side: 'no' }, m(0.18, 0.20), NOON + 1), 'a NO is sold when the YES ask falls to 20c');
  assert.strictEqual(lib.exitPnl(pos), lib.round2(0.8 * 7 - lib.takerFee(0.8, 7) - 0.4 * 7 - 0.12));
  assert.strictEqual(lib.settlePnl(pos, 'yes'), lib.round2(7 - 0.4 * 7 - 0.12));
  assert.strictEqual(lib.settlePnl(pos, 'no'), lib.round2(-0.4 * 7 - 0.12));
};

// ================= one tick, end to end =================

gates.G7 = async () => {
  const c = make();
  c.api.put('M1', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  const p = posOf(c, 'h2-M1');
  assert.deepStrictEqual([p.side, p.band, p.contracts, p.entry, p.status, p.mode], ['yes', '40c', 2, 0.40, 'open', 'paper']);
  c.api.put('M1', 0.81, 0.82, CLOSE);
  await tick(c, NOON + 60000);
  assert.strictEqual(posOf(c, 'h2-M1').status, 'closed');
  assert.strictEqual(posOf(c, 'h2-M1').pnl, lib.exitPnl(p));
  // After a closed trade the same market is never re-entered, and the record is untouched.
  c.api.put('M1', 0.39, 0.40, CLOSE);
  await tick(c, NOON + 120000);
  assert.strictEqual(c.store.pos.size, 1);
  assert.strictEqual(posOf(c, 'h2-M1').status, 'closed');
  assert.strictEqual(c.store.kinds('entry'), 1);
};

// THE incident, in miniature. Two runs at the same moment (a Scheduler double fire, a
// redeploy overlap) must not enter the same market twice, and must not both close it.
gates.G8 = async () => {
  const c = make();
  c.api.put('M2', 0.39, 0.40, CLOSE);
  await Promise.all([tick(c, NOON), tick(c, NOON)]);
  assert.strictEqual(c.store.pos.size, 1);
  assert.strictEqual(c.store.kinds('entry'), 1, 'a second run must not log a second entry');
  c.api.put('M2', 0.85, 0.86, CLOSE);
  await Promise.all([tick(c, NOON + 60000), tick(c, NOON + 60000)]);
  assert.strictEqual(c.store.kinds('exit'), 1, 'two runs must not both close the same position');
};

gates.G9 = async () => {
  const c = make();
  c.api.put('M3', 0.59, 0.61, CLOSE);
  await tick(c, NOON);
  const p = posOf(c, 'h2-M3');
  assert.ok(p.side === 'no' && Math.abs(p.entry - 0.41) < 1e-9);
  c.api.put('M3', 0.18, 0.20, CLOSE);
  await tick(c, NOON + 60000);
  assert.strictEqual(posOf(c, 'h2-M3').status, 'closed');
};

gates.G10 = async () => {
  // Held to settlement: a loss costs the entry plus the fee; a win pays $1 a contract.
  for (const [result, want] of [['no', (p) => lib.settlePnl(p, 'no')], ['yes', (p) => lib.settlePnl(p, 'yes')]]) {
    const c = make();
    c.api.put('M4', 0.39, 0.40, CLOSE);
    await tick(c, NOON);
    c.api.mk = {}; c.api.result.M4 = result;
    await tick(c, CLOSE + 60000);
    const p = posOf(c, 'h2-M4');
    assert.strictEqual(p.status, 'closed');
    assert.strictEqual(p.pnl, want(p));
  }
  // Not final yet: stays open, asked again next tick.
  const c = make();
  c.api.put('M5', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  c.api.mk = {};
  await tick(c, CLOSE + 60000);
  assert.strictEqual(posOf(c, 'h2-M5').status, 'open');
  // Before the close it must not even ask for a result.
  const d = make();
  d.api.put('M6', 0.39, 0.40, CLOSE);
  await tick(d, NOON); await tick(d, NOON + 60000); await tick(d, NOON + 120000);
  assert.strictEqual(d.api.marketCalls, 0, 'no result lookups before the close');
};

// ================= the safety rules =================

gates.G11 = async () => {
  // A halt from the page stops new entries...
  let c = make(); c.store.control = { halt: true };
  c.api.put('A', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  assert.strictEqual(c.store.pos.size, 0, 'a halt must stop new entries');
  assert.strictEqual(c.store.status.halted, true);
  // ...but must NOT freeze a position that is already open: that is the dangerous act.
  c = make();
  c.api.put('B', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  c.store.control = { halt: true };
  c.api.put('B', 0.81, 0.82, CLOSE);
  await tick(c, NOON + 60000);
  assert.strictEqual(posOf(c, 'h2-B').status, 'closed', 'exits must carry on while halted');
};

gates.G12 = async () => {
  let c = make(); c.api.active = false; c.api.put('A', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  assert.strictEqual(c.store.pos.size, 0, 'an inactive exchange means no entry');
  // Prices unreadable: no entry, a heartbeat that says so, and the error logged ONCE.
  c = make(); c.api.failAll = true;
  await tick(c, NOON); await tick(c, NOON + 60000); await tick(c, NOON + 120000);
  assert.strictEqual(c.store.pos.size, 0);
  assert.strictEqual(c.store.status.ok, false);
  assert.strictEqual(c.store.status.lastTickMs, NOON + 120000, 'the heartbeat must keep beating while prices are down');
  assert.strictEqual(c.store.kinds('error'), 1, 'an outage must not write an error every minute');
  // A PARTLY unreadable feed (Bitcoin readable, gold down) must fail closed too.
  c = make(); c.api.failSeries = new Set(['KXGOLD15M']); c.api.put('A', 0.39, 0.40, CLOSE);
  await tick(c, NOON);
  assert.strictEqual(c.store.pos.size, 0, 'a partly unreadable feed must not trade even the readable part');
};

gates.G13 = async () => {
  let c = make(); c.api.put('A', 0.39, 0.40, NOON + 240000);
  await tick(c, NOON);
  assert.strictEqual(c.store.pos.size, 0, 'under 5 minutes left is no entry');
  c = make(); c.api.put('A', 0.30, 0.55, CLOSE); c.api.put('B', 0.45, 0.46, CLOSE, { status: 'finalized' });
  await tick(c, NOON);
  assert.strictEqual(c.store.pos.size, 0, 'a wide book and a closed market are not entries');
  c = make(); c.api.put('A', 0.39, 0.40, CLOSE, { askSz: 1 });
  await tick(c, NOON);
  assert.strictEqual(posOf(c, 'h2-A').contracts, 1, 'never more than the touch shows');
};

// A hard stop: after enough losses today no new entry, and the reason is logged once.
gates.G14 = async () => {
  const c = make();
  for (let i = 0; i < 3; i++) {
    c.store.pos.set('x' + i, { id: 'x' + i, status: 'closed', pnl: -2, settledAt: at(9, i), side: 'yes', contracts: 2, entry: 0.4, entryFee: 0.04 });
  }
  c.api.put('A', 0.39, 0.40, CLOSE);
  await tick(c, at(12)); await tick(c, at(12, 1));
  assert.strictEqual(c.store.pos.size, 3);
  assert.strictEqual(c.store.kinds('block'), 1, 'the block is logged once, not every minute');
  assert.strictEqual(c.store.status.tierMode, 'done');
  // Half size after a break: $0.50 at 40c is one contract, never two.
  const d = make();
  d.store.pos.set('y1', { id: 'y1', status: 'closed', pnl: -3.2, settledAt: at(9), side: 'yes', contracts: 2, entry: 0.4, entryFee: 0.04 });
  d.api.put('A', 0.39, 0.40, CLOSE);
  await tick(d, at(12));
  assert.strictEqual(posOf(d, 'h2-A').contracts, 1, 'half size after the break');
};

gates.G15 = async () => {
  const c = make();
  c.api.put('A', 0.39, 0.40, CLOSE);
  const r = await tick(c, NOON);
  assert.strictEqual(r.entered, 1);
  const s = c.store.status;
  assert.ok(s.ok && s.mode === 'paper' && s.bankroll === 100 && s.openCount === 1 && s.lastTickMs === NOON, JSON.stringify(s));
  // The page shows what the limits counted, so a mismatch with the trade list is visible.
  assert.strictEqual(s.closedCounted, 0);
  assert.strictEqual(s.dayStart, require('../functions/kalshiBotLib').localDayStart(NOON));
};

// During the 2 hour break no new entry is taken, and the reason is logged; open
// positions are still managed (the tier test alone cannot see this at tick level).
gates.G17 = async () => {
  const c = make();
  c.store.pos.set('y1', { id: 'y1', status: 'closed', pnl: -3.2, settledAt: at(9), side: 'yes', contracts: 2, entry: 0.4, entryFee: 0.04 });
  c.api.put('A', 0.39, 0.40, CLOSE);
  await tick(c, at(10));                                   // the break runs from 9:00 to 11:00
  assert.strictEqual(c.store.pos.size, 1, 'no new entry during the break');
  assert.strictEqual(c.store.status.tierMode, 'break');
  assert.ok(c.store.events.some((e) => e.kind === 'block' && /break/.test(e.detail)));
};

// The real Firestore store is not exercised above (the fake stands in for it), so what
// makes it safe is asserted from its source: creation is an atomic create() that fails
// if the document exists, never a set(), and a close happens inside a transaction that
// re-reads the position and only closes it if it is still open.
gates.G18 = () => {
  const s = fnSrc.slice(fnSrc.indexOf('function firestoreBotStore('), fnSrc.indexOf('exports.kalshiBot ='));
  const create = /async createPosition\(id, data\) \{([\s\S]*?)\n    \},/.exec(s);
  assert.ok(create && /\.create\(data\)/.test(create[1]) && !/\.set\(/.test(create[1]), 'createPosition must use create(), not set()');
  assert.ok(/ALREADY_EXISTS/.test(create[1]) && /return false/.test(create[1]), 'an existing position must be reported, not overwritten');
  const close = /async closePosition\(id, patch\) \{([\s\S]*?)\n    \},/.exec(s);
  assert.ok(close && /runTransaction/.test(close[1]) && /t\.get\(ref\)/.test(close[1]) && /status !== "open"\) return false/.test(close[1]),
    'closePosition must re-check status inside a transaction');
};

// ================= no real orders, anywhere =================

gates.G16 = () => {
  for (const f of ['kalshiBotLib.js', 'kalshiBotRun.js']) {
    const code = fs.readFileSync(path.join(root, 'functions', f), 'utf8').replace(/\/\/[^\n]*/g, '');
    assert.ok(!/portfolio\/events\/orders|KALSHI-ACCESS|private_?key|api_?key|create_?order|place_?order/i.test(code), f + ' must contain no order code');
  }
  const bot = fnSrc.slice(fnSrc.indexOf('exports.kalshiBot ='));
  assert.ok(bot.length > 20, 'kalshiBot not found');
  assert.ok(!/portfolio\/events\/orders|KALSHI-ACCESS|private_?key|create_?order|place_?order/i.test(bot.replace(/\/\/[^\n]*/g, '')), 'the scheduled function must contain no order code');
};

// ================= database rules and the page =================

const rules = fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const block = (re, text) => { const m = re.exec(text); assert.ok(m, 'not found: ' + re); return m[1]; };

// The bot's records are readable by the admin and writable by nobody from a browser.
// The single exception is the halt switch, and only for the admin, only a boolean.
gates.G19 = () => {
  for (const col of ['kalshiBotPositions/{id}', 'kalshiBotEvents/{id}', 'kalshiBotMeta/status']) {
    const b = block(new RegExp('match /' + col.replace(/[{}/]/g, (c) => '\\' + c) + ' \\{([\\s\\S]*?)\\n    \\}'), rules);
    assert.ok(/allow read: if isAdmin\(\);/.test(b), col + ' must be admin read');
    assert.ok(/allow write: if false;/.test(b), col + ' must not be writable from a client');
  }
  const ctl = block(/match \/kalshiBotMeta\/control \{([\s\S]*?)\n    \}/, rules);
  assert.ok(/allow read: if isAdmin\(\);/.test(ctl) && /allow write: if isAdmin\(\)/.test(ctl));
  assert.ok(/hasOnly\(\['halt', 'at'\]\)/.test(ctl) && /halt is bool/.test(ctl), 'the halt switch accepts only a boolean');
  assert.ok(!/kalshiBotPositions[\s\S]{0,200}allow write: if (isAdmin|signedIn)/.test(rules), 'no client may write a position');
};

// The heartbeat is judged against a once-a-minute schedule: 2.5 minutes of silence is
// stale and 5 is down. A bot that never reported must not read as healthy.
gates.G20 = () => {
  const start = html.indexOf('function kalshiBotHealth(');
  let d = 0, end = -1;
  for (let i = html.indexOf('{', start); i < html.length; i++) {
    if (html[i] === '{') d++; else if (html[i] === '}') { d--; if (!d) { end = i + 1; break; } }
  }
  const health = new Function('return (' + html.slice(start, end) + ')')();
  assert.strictEqual(health(30000), 'OK');
  assert.strictEqual(health(149000), 'OK');
  assert.strictEqual(health(150000), 'STALE');
  assert.strictEqual(health(299000), 'STALE');
  assert.strictEqual(health(300000), 'DOWN');
  assert.strictEqual(health(null), 'NEVER RAN');
  assert.strictEqual(health(undefined), 'NEVER RAN');
  assert.strictEqual(health(NaN), 'NEVER RAN');
};

// The page can watch the bot and flip one switch, and cannot touch a trade. The Bot tab
// is the default, resuming entries asks first, and leaving the page stops listening.
gates.G21 = () => {
  const bridge = block(/watchKalshiBot: function\(h\)\{([\s\S]*?)\n    \},\n    setKalshiHalt/, html);
  assert.ok(/kalshiBotPositions/.test(bridge) && /kalshiBotEvents/.test(bridge) && /kalshiBotMeta/.test(bridge));
  assert.ok(!/setDoc|updateDoc|addDoc|deleteDoc/.test(bridge), 'watching must not write');
  const halt = block(/setKalshiHalt: function\(halt\)\{([\s\S]*?)\n    \},/, html);
  assert.ok(/setDoc\(doc\(db, 'kalshiBotMeta', 'control'\), \{ halt: Boolean\(halt\), at: serverTimestamp\(\) \}\)/.test(halt),
    'the halt switch writes exactly { halt, at } to the control document');
  assert.ok(/var kalshiTab = 'bot';/.test(html));
  assert.ok(/if\(halted\)\{ el\.innerHTML \+= '<div class="kal-warn kal-big">Halted from this page/.test(html), 'the halt must show on the card at once');
  assert.ok(/if\(halted && !window\.confirm\(/.test(html), 'resuming entries must ask first');
  assert.ok(/function kalshiOnHide\(\)\{ stopKalshiPoll\(\); stopKalshiBot\(\); \}/.test(html), 'leaving the page must stop listening');
  assert.ok(/!currentUserIsAdmin\)\{ return; \}/.test(block(/function startKalshiBot\(\)\{([\s\S]*?)\n  \}\n  function stopKalshiBot/, html) + ')'), 'only an admin may subscribe');
};

// The Bot tab once showed only the newest 15 closed trades and 12 events with no way to see
// more, which hid most of the day and made the limits look wrong when they were not.
gates.G22 = () => {
  assert.ok(!/limit\((12|40)\)/.test(html), 'the bot queries must not cap the history at a dozen rows');
  assert.ok(!/\.slice\(0, 15\)/.test(html), 'closed trades must not be hard cut at 15');
  assert.ok(/data-more="closed"/.test(html) && /data-more="events"/.test(html), 'both lists need a way to show more');
  assert.ok(/Showing ' \+ closed\.length \+ ' of ' \+ closedTotal/.test(html), 'the page must say how many it is not showing');
};

// The owner added the Net column up by hand to learn how the bot was doing. The page now
// does it, so the sum must match what a person gets: this is the real Oct 5 list, which
// the bot's own status line reported as +$2.07 over 43 trades (27 wins, 16 losses).
gates.G23 = () => {
  const src = block(/(function kalshiBotTotals\(positions, dayOf\)\{[\s\S]*?\n  \})\n/, html);
  const totals = new Function(src + '; return kalshiBotTotals;')();
  const nets = [0.71, 0.75, 0.25, 0.24, -0.80, -0.84, -1, -1, -0.52, 0.57, 0.24, 0.57, -0.84, -0.53, -0.82, -0.82, -1,
    0.57, 0.73, 0.75, 0.57, 0.24, -0.82, 0.26, -0.82, 0.24, -0.54, 0.75, 1.18, -1, 0.77, 0.75, 0.69, 0.57, 0.24, -0.80,
    0.69, 0.71, 0.24, 0.26, 0.75, -0.84, 0.77];
  const day = (ms) => new Date(ms).toISOString().slice(0, 10);
  const D1 = Date.parse('2026-10-05T18:00:00Z'), D2 = D1 + 86400000;
  const closed = nets.map((pnl, i) => ({ status: 'closed', pnl, settledAt: (i < 40 ? D1 : D2) + i * 60000 }));
  const noise = [{ status: 'open', pnl: null, settledAt: null }, { status: 'closed', pnl: null, settledAt: D1 }, null];
  const t = totals(closed.concat(noise), day);
  assert.strictEqual(t.n, 43, 'open and unpriced positions are not trades');
  assert.strictEqual(t.net, 2.07, 'must equal what the bot reported');
  assert.strictEqual(t.wins, 27); assert.strictEqual(t.losses, 16);
  assert.ok(Math.abs(t.winRate - 27 / 43) < 1e-12 && Math.abs(t.perTrade - 2.07 / 43) < 1e-12);
  assert.ok(t.best === 1.18 && t.worst === -1);
  assert.ok(t.breakEven > 0.58 && t.breakEven < 0.61, 'about 59% needed at these average sizes: ' + t.breakEven);
  assert.deepStrictEqual(t.days.map((d) => [d.trades]), [[3], [40]], 'newest day first, grouped by the viewer\'s day');
  assert.strictEqual(Math.round(t.days.reduce((a, d) => a + d.net, 0) * 100) / 100, 2.07, 'the days add up to the total');
  const flat = totals([{ status: 'closed', pnl: 0, settledAt: D1 }, { status: 'closed', pnl: 1, settledAt: D1 }], day);
  assert.ok(flat.n === 2 && flat.wins === 1 && flat.losses === 0, 'a break-even trade is neither a win nor a loss');
  const none = totals([], day);
  assert.ok(none.n === 0 && none.winRate === null && none.breakEven === null, 'no trades must not divide by zero');
  // Wired into the page: a card, the render, and an honest note when the history is cut off.
  assert.ok(/id="kalBotTotals"/.test(html) && /kalshiBotTotals\(pos,/.test(html));
  assert.ok(/pos\.length >= 500/.test(html), 'say so if only the newest 500 trades were counted');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
