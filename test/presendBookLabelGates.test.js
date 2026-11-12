'use strict';
// Gates for the book-read labels and update stamps (Nov 12, 2026, the owner, log only). The book read is made AFTER the order's POST was answered, so it is labelled "after_send" with how long after;
// nobody may mistake it for the book the order met. Consequences: no order, size, price, count or timing changes whether the logging works, fails or is absent; nothing that decides an order reads the new fields.
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const fx = require('./fixtures/offEquivalenceScenarios');
const live = require('../functions/kalshiLiveLib.js');
const report = require('../functions/kalshiReportLib');

const root = path.join(__dirname, '..');
const read = (...p) => fs.readFileSync(path.join(root, ...p), 'utf8');
const code = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
const BOOK = { orderbook_fp: { yes_dollars: [['0.72', '12'], ['0.71', '40']], no_dollars: [['0.27', '30']] }, updated_time: '2026-11-12T10:00:00Z', depth: { updated_time: 'nested' } };
const isBook = (url) => /\/orderbook$/.test(String(url).split('?')[0]);
const gates = {};

const run = async ({ book, marketStamp }) => {
  const w = fx.l1World({});
  const inner = w.common.fetchFn;
  w.common.fetchFn = async (url, o) => {
    if (isBook(url)) { w.r.log.push({ kind: 'fetch', method: o.method, url, body: null }); return book(url, o); }
    const res = await inner(url, o);
    if (marketStamp && /\/markets\/[^/?]+(\?|$)/.test(String(url)) && o.method === 'GET') {
      const t = JSON.parse(await res.text());
      if (t.market) t.market.updated_time = '2026-11-12T09:59:59Z';
      return { ...res, text: async () => JSON.stringify(t) };
    }
    return res;
  };
  const ret = await live.runL1Tick({ ...w.common, quotes: [fx.q('KXBTC15M', fx.T)] });
  return { w, ret };
};
const okBook = () => ({ status: 200, text: async () => JSON.stringify(BOOK) });
const posts = (w) => w.r.log.filter((x) => x.kind === 'fetch' && x.method === 'POST').map((x) => JSON.stringify(x.body));
const bookWrite = (w) => w.r.log.filter((x) => x.kind === 'store' && x.call === 'updateTest' && x.args[1] && 'bookYes5' in x.args[1]).map((x) => x.args[1])[0];
const VOLATILE = ['at', 'sentAtMs', 'answeredAtMs', 'tickStartMs', 'bookReadMs', 'bookReadAfterSendMs'];
const norm = (w, drop) => JSON.parse(JSON.stringify(w.r.log.filter((x) => x.kind === 'store' && !(x.args && x.args[1] && 'bookYes5' in x.args[1])), (k, v) => (drop && k === 'seenUpdate' ? undefined : VOLATILE.includes(k) ? 0 : v)));

gates['PB1 the book is labelled as read after the send, with how long after, and the read really is after the POST'] = async () => {
  const { w } = await run({ book: okBook });
  const p = bookWrite(w);
  assert.ok(p, 'a book write exists');
  assert.strictEqual(p.bookReadWhen, 'after_send');
  assert.ok(Number.isFinite(p.bookReadAfterSendMs) && p.bookReadAfterSendMs >= 0, 'milliseconds after the send');
  const idx = (f) => w.r.log.findIndex(f);
  assert.ok(idx((x) => x.kind === 'fetch' && isBook(x.url)) > idx((x) => x.kind === 'fetch' && x.method === 'POST'), 'no book read before the POST');
  assert.strictEqual(w.r.log.filter((x) => x.kind === 'fetch' && isBook(x.url)).length, 1, 'no extra request was added');
};
gates['PB2 the update stamps of the book answer are kept beside the book; an answer without them adds none'] = async () => {
  const p = bookWrite((await run({ book: okBook })).w);
  assert.deepStrictEqual(p.bookUpdate, { updated_time: '2026-11-12T10:00:00Z' }, 'top level scalars only');
  const plain = bookWrite((await run({ book: () => ({ status: 200, text: async () => JSON.stringify({ orderbook_fp: BOOK.orderbook_fp }) }) })).w);
  assert.ok(!('bookUpdate' in plain));
};
gates['PB3 the market update stamp is stored beside the seen quote on the order, and never when the market carries none'] = async () => {
  const withStamp = await run({ book: okBook, marketStamp: true });
  const created = withStamp.w.r.log.find((x) => x.kind === 'store' && x.call === 'createTest');
  assert.ok(created, 'the order record was created');
  assert.deepStrictEqual(created.args[1].seenUpdate, { updated_time: '2026-11-12T09:59:59Z' });
  const none = await run({ book: okBook });
  assert.ok(!('seenUpdate' in none.w.r.log.find((x) => x.kind === 'store' && x.call === 'createTest').args[1]));
};
gates['PB4 the order sent is byte-identical with the logging working, failing, throwing or the market carrying stamps'] = async () => {
  const base = await run({ book: okBook });
  for (const [book, stamp] of [[okBook, true], [() => ({ status: 500, text: async () => '{}' }), false], [() => { throw new Error('boom'); }, true], [() => ({ status: 200, text: async () => 'not json' }), false]]) {
    const r = await run({ book, marketStamp: stamp });
    assert.deepStrictEqual(posts(r.w), posts(base.w), 'same order body');
    assert.deepStrictEqual(r.ret, base.ret, 'same return');
    assert.deepStrictEqual(norm(r.w, true), norm(base.w, true), 'every other store call unchanged');
    if (!(book === okBook)) assert.ok(!bookWrite(r.w), 'a failed read writes nothing');
  }
};
gates['PB5 nothing that decides an order reads the new fields'] = () => {
  const names = /bookReadWhen|bookReadAfterSendMs|bookUpdate|seenUpdate/;
  const dir = path.join(root, 'functions');
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith('.js') && !/^kalshiReportLib\.js$/.test(x))) {
    let src = code(read('functions', f));
    if (f === 'kalshiLiveLib.js') {
      const a = src.indexOf('function updateFields'), b = src.indexOf('async function logBook');
      src = src.slice(0, a) + src.slice(src.indexOf('\n}\n', b) + 3);
      src = src.replace(/\{ const su = updateFields\(m\); if \(Object\.keys\(su\)\.length\) record\.seenUpdate = su; \}/, '');
    }
    assert.ok(!names.test(src), f + ' must not name the new logged fields');
  }
};
gates['PB6 the report carries the label and the delay as compact values with no ids'] = () => {
  const ord = { ts: Date.now() - 1000, ticker: 'KXGOLD15M-X', series: 'KXGOLD15M', side: 'yes', status: 'filled', orderId: 'SECRET-ID', clientOrderId: 'L1-SECRET', fillCount: '1', count: 1,
    bookYes5: [{ p: 0.7, q: 3 }], bookReadMs: 1, bookReadWhen: 'after_send', bookReadAfterSendMs: 420 };
  const r = report.buildReport([ord, Object.assign({}, ord, { bookReadWhen: 'before_send; DROP', bookReadAfterSendMs: undefined })], Date.now(), 24, true);
  assert.strictEqual(r.orders[0].bookReadWhen, 'after_send'); assert.strictEqual(r.orders[0].bookReadAfterSendMs, 420);
  assert.strictEqual(r.orders[1].bookReadWhen, null); assert.strictEqual(r.orders[1].bookReadAfterSendMs, null);
  assert.ok(!/SECRET/.test(JSON.stringify(r)));
};
(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
