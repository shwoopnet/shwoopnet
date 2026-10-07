// The server-side order-book recorder. Each gate states the consequence of getting it wrong.

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { parseBook, recordMinute } = require('../functions/kalshiBookLib');

const lib = fs.readFileSync(path.join(__dirname, '..', 'functions', 'kalshiBookLib.js'), 'utf8');
const fnSrc = fs.readFileSync(path.join(__dirname, '..', 'functions', 'index.js'), 'utf8');
const rules = fs.readFileSync(path.join(__dirname, '..', 'firestore.rules'), 'utf8');
const strip = (s) => s.replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');
const gates = {};

const BOOK = { orderbook_fp: { yes_dollars: [['0.3000', '5'], ['0.4000', '10']], no_dollars: [['0.5000', '7'], ['0.5500', '3']] } };

// A yes ask is what the best no bid implies. Wrong here prices every recorded quote off by 1 - x.
gates.B1 = () => {
  const b = parseBook(BOOK);
  assert.strictEqual(b.yb, 0.4); assert.strictEqual(b.nb, 0.55);
  assert.strictEqual(b.ya, 0.45); assert.strictEqual(b.na, 0.6);
};

// An empty side is unknown, never a free price of zero.
gates.B2 = () => {
  const e = parseBook({ orderbook_fp: { yes_dollars: [], no_dollars: [['0.5', '1']] } });
  assert.strictEqual(e.yb, null); assert.strictEqual(e.na, null); assert.strictEqual(e.ya, 0.5);
  assert.strictEqual(parseBook({}).yb, null);
  assert.strictEqual(parseBook(null).nb, null);
};

function harness(getImpl, startMs = 1790000000000) {
  let t = startMs;
  const out = { docs: {}, pruned: [], status: null, sleeps: 0 };
  const args = {
    get: getImpl, now: () => t, sleep: async (ms) => { out.sleeps++; t += ms; },
    store: {
      writeMinute: async (id, d) => { out.docs[id] = d; },
      pruneBefore: async (ts) => { out.pruned.push(ts); },
      setStatus: async (s) => { out.status = s; },
    },
  };
  return { args, out };
}
const okGet = async (p) => p.startsWith('/markets?')
  ? { markets: [{ ticker: 'KXBTC15M-T', yes_bid_dollars: '0.38', yes_ask_dollars: '0.42' }] }
  : BOOK;

// A minute document is keyed by the minute, so two overlapping processes during a deploy write the SAME
// document instead of recording the minute twice.
gates.B3 = async () => {
  const { args, out } = harness(okGet, 1790000012345);
  await recordMinute(args);
  const ids = Object.keys(out.docs);
  assert.deepStrictEqual(ids, ['bk-' + Math.floor(1790000012345 / 60000) * 60000]);
  const d = out.docs[ids[0]];
  assert.ok(d.snaps.length >= 8, 'several snapshots per series per minute, got ' + d.snaps.length);
  assert.deepStrictEqual(d.snaps[0].ly, 0.38, 'the list price is kept beside the book so staleness can be measured');
};

// One series failing must not lose the other's rows, and the failure is recorded rather than swallowed.
gates.B4 = async () => {
  const { args, out } = harness(async (p) => {
    if (p.includes('KXGOLD15M')) throw new Error('HTTP 429');
    return okGet(p);
  });
  const r = await recordMinute(args);
  assert.ok(r.snaps > 0 && r.errs > 0);
  const d = Object.values(out.docs)[0];
  assert.ok(d.snaps.every((x) => x.s === 'KXBTC15M'));
  assert.ok(d.errs.every((x) => x.s === 'KXGOLD15M' && /429/.test(x.e)));
};

// A fully failing minute still writes its document and the heartbeat: silence must be distinguishable from
// "nothing was open", or a dead recorder looks healthy.
gates.B5 = async () => {
  const { args, out } = harness(async () => { throw new Error('down'); });
  await recordMinute(args);
  assert.strictEqual(Object.values(out.docs)[0].snaps.length, 0);
  assert.ok(out.status && out.status.errs > 0 && Number.isFinite(out.status.lastTickMs));
};

// The run ends well inside the function timeout: a run killed by the timeout would write nothing at all.
gates.B6 = async () => {
  const { args, out } = harness(okGet);
  const start = args.now();
  args.sleep = async (ms) => { out.sleeps++; out.t = (out.t || start) + ms; };
  let clock = start;
  args.now = () => clock;
  args.sleep = async (ms) => { clock += ms + 9000; };    // pretend every sleep overran by 9s
  await recordMinute(args);
  assert.ok(clock - start < 58000, 'finished at ' + (clock - start) + 'ms');
};

// Old minutes are pruned (ten days), so the collection cannot grow without bound.
gates.B7 = async () => {
  const { args, out } = harness(okGet, 1790000000000);
  await recordMinute(args);
  assert.strictEqual(out.pruned.length, 1);
  const minute = Math.floor(1790000000000 / 60000) * 60000;
  assert.strictEqual(minute - out.pruned[0], 10 * 86400000);
};

// Read only, keyless, and nowhere near an order. The recorder is also defined before the paper bot.
gates.B8 = () => {
  const code = strip(lib);
  assert.ok(!/portfolio|orders\b(?!\?)|KALSHI-ACCESS|method\s*:|POST|require\(["']\.\/kalshiLive/i.test(code.replace(/\/orderbook/g, '')), 'no order or signing code in the recorder');
  const sched = /exports\.kalshiBookRecorder = onSchedule\(\s*\{([^}]*)\}/.exec(fnSrc);
  assert.ok(sched && !/secrets/.test(sched[1]), 'the recorder holds no secrets');
  assert.ok(fnSrc.indexOf('exports.kalshiBookRecorder') < fnSrc.indexOf('exports.kalshiBot ='), 'defined before the paper bot');
  assert.ok(!/kalshiBook/.test(fnSrc.slice(fnSrc.indexOf('exports.kalshiBot ='))), 'the paper bot never touches the recorder');
};

// Only the admin can read the snapshots, and nobody can write them from a browser.
gates.B9 = () => {
  for (const c of ['kalshiBookSnaps', 'kalshiBookMeta']) {
    const m = new RegExp('match /' + c + '/\\{id\\} \\{([^}]*)\\}').exec(rules);
    assert.ok(m, c + ' has a rule');
    assert.ok(/allow read: if isAdmin\(\);/.test(m[1]) && /allow write: if false;/.test(m[1]), c + ' is admin-read, no client write');
  }
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); }
    catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
