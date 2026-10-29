'use strict';
// Gates for "Flatten all + halt" (real money, the owner's emergency exit). Each states the consequence, not the mechanism.
const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const live = require('../functions/kalshiLiveLib');

const root = path.join(__dirname, '..');
const fnSrc = fs.readFileSync(path.join(root, 'functions', 'index.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const NOW = Date.parse('2026-10-08T15:00:00Z');
const ed = crypto.generateKeyPairSync('ed25519');
const pem = ed.privateKey.export({ type: 'pkcs8', format: 'pem' });
const gates = {};

function world({ positions, markets = {}, postStatus = 201, post, posStatus = 200, closing = {}, later } = {}) {
  const posts = [], reads = [], held = new Map(Object.entries(closing));
  const fetchFn = async (url, o) => {
    const reply = (status, body) => ({ status, text: async () => JSON.stringify(body) });
    if (url.includes('/portfolio/positions')) {
      const tk = new URL(url).searchParams.get('ticker');
      reads.push(tk);
      // `later` is what the account holds on the read that follows the claim, after something else may have sold it
      return reply(posStatus, { market_positions: tk && later ? later : (positions || []) });
    }
    if (url.includes('/markets/')) {
      const tk = decodeURIComponent(url.split('/markets/')[1].split('?')[0]);
      return reply(200, { market: { status: 'active', exchange_index: 2, ...(markets[tk] || {}) } });
    }
    if (o.method === 'POST') {
      const b = JSON.parse(o.body); posts.push(b);
      return reply(postStatus, post || { order_id: 'o' + posts.length, fill_count: b.count, remaining_count: '0.00', average_fill_price: '0.5000' });
    }
    throw new Error('unexpected ' + o.method + ' ' + url);
  };
  const store = { async claimClose(ticker, who, now, ttl) { const c = held.get(ticker); if (c && c.by !== who && now - c.at < ttl) return false; held.set(ticker, { by: who, at: now }); return true; } };
  return { posts, reads, held, run: () => live.flattenAll({ fetchFn, keyId: 'k', pem, now: NOW, store }) };
}
const TA = 'KXBTC15M-26OCT081115-15', TB = 'KXGOLD15M-26OCT081115-15';

// Every open position is closed, exactly its size, in the right direction: a held YES is sold, a held NO is closed by buying YES back.
gates.F1 = async () => {
  const w = world({ positions: [{ ticker: TA, position_fp: '3.00' }, { ticker: TB, position_fp: '-2.00' }] });
  const r = await w.run();
  assert.ok(r.ok && r.results.map((x) => x.status).join() === 'sold,sold');
  const [a, b] = w.posts;
  assert.deepStrictEqual([a.side, a.count, a.price, a.time_in_force], ['ask', '3', '0.01', 'immediate_or_cancel'], 'a held YES is sold down to the floor, all of it, immediately');
  assert.deepStrictEqual([b.side, b.count, b.price], ['bid', '2', '0.99'], 'a held NO is closed by buying YES, never by selling more');
  assert.ok(a.client_order_id === 'FLAT-' + TA + '-' + Math.floor(NOW / 60000), 'the id carries the minute, so a double press cannot sell twice');
  assert.strictEqual(a.exchange_index, 2);
};

// Nothing is sold that cannot be, and nothing is guessed.
gates.F2 = async () => {
  const closed = world({ positions: [{ ticker: TA, position_fp: '1.00' }], markets: { [TA]: { status: 'closed' } } });
  const r = await closed.run();
  assert.deepStrictEqual([closed.posts.length, r.results[0].status], [0, 'skipped'], 'a market that is no longer open settles on its own and is not traded');
  const bad = world({ posStatus: 500 });
  const rb = await bad.run();
  assert.deepStrictEqual([rb.ok, bad.posts.length], [false, 0], 'positions that cannot be read: nothing is sold');
  const none = world({ positions: [{ ticker: TA, position_fp: '0.00' }] });
  assert.deepStrictEqual([(await none.run()).results.length, none.posts.length], [0, 0], 'a zero position is nothing to sell');
};

// An order whose answer is lost is reported and never retried; a partial fill says the book was too thin; a repeat in the same minute is refused by Kalshi.
gates.F3 = async () => {
  const lost = world({ positions: [{ ticker: TA, position_fp: '1.00' }], postStatus: 503, post: 'oops' });
  const r = await lost.run();
  assert.deepStrictEqual([lost.posts.length, r.results[0].status], [1, 'error'], 'not retried');
  assert.ok(/check the Kalshi account/.test(r.results[0].detail));
  const part = world({ positions: [{ ticker: TA, position_fp: '4.00' }], post: { order_id: 'o', fill_count: '1.00', remaining_count: '3.00' } });
  const rp = await part.run();
  assert.strictEqual(rp.results[0].status, 'partly sold');
  const dup = world({ positions: [{ ticker: TA, position_fp: '1.00' }], postStatus: 409, post: { error: 'exists' } });
  assert.strictEqual((await dup.run()).results[0].status, 'skipped');
};

// The bot is stopped BEFORE anything is sold, with database writes only, so a failure of the exchange calls cannot leave it running.
gates.F4 = () => {
  const f = fnSrc.slice(fnSrc.indexOf('exports.kalshiFlattenAll'));
  const body = f.slice(0, f.indexOf('exports.kalshiLiveArmed'));
  assert.ok(/assertKalshiAdmin\(request\.auth\)/.test(body), 'admin only');
  const halt = body.indexOf('halt: true'), sess = body.indexOf('active: false'), arm = body.indexOf('armed: false'), sell = body.indexOf('live.flattenAll(');
  assert.ok(halt > 0 && halt < sell && sess < sell && arm < sell, 'halt, session end and disarm all come before the sells');
  assert.ok(/catch \(e\)/.test(body.slice(sell - 60)) && /halted: true/.test(body), 'if the sells throw, the answer still says the bot is halted');
  assert.ok(!/LIVE_CAP/.test(live.flattenAll.toString()), 'the buy cap does not apply to a sell');
};

// The button: in the Tools menu, first in it, asks twice, and the menu no longer claims it cannot change anything.
gates.F5 = () => {
  const tools = /id="kalTools"[\s\S]*?<\/details>\s*<details class="kal-layout" id="kalLayout"/.exec(html)[0];
  const menu = /id="kalBotMenu"[\s\S]*?id="kalBotHaltMsg"/.exec(html)[0];
  assert.ok(menu.indexOf('id="kalFlatten"') > menu.indexOf('id="kalBotHalt"') && tools.indexOf('id="kalFlatten"') < 0, 'one place for the bot controls: Flatten sits with Pause in the Running menu, not in Tools');
  assert.ok(/id="kalFlattenConfirm" hidden/.test(html) && /go\.addEventListener\('click', function\(\)\{ ask\(true\); \}\)/.test(html), 'the first click only asks');
  assert.ok(/kalshiFlattenAll\(\)/.test(html.slice(html.indexOf("var yes = document.getElementById('kalFlattenYes')"))), 'only the confirm click sends');
  assert.ok(!/it cannot place or change anything/.test(tools), 'the menu does not claim to be read only');
};

// F6: if the exit watch is closing a market, Flatten leaves that one alone and still closes the others.
gates.F6 = async () => {
  const w = world({ positions: [{ ticker: TA, position_fp: '3.00' }, { ticker: TB, position_fp: '2.00' }], closing: { [TA]: { by: 'exit', at: NOW - 5000 } } });
  const r = await w.run();
  assert.deepStrictEqual(r.results.map((x) => x.ticker + ':' + x.status), [TA + ':skipped', TB + ':sold']);
  assert.deepStrictEqual(w.posts.map((b) => b.ticker), [TB], 'only the market nobody else holds is sold');
  assert.ok(/exit watch is closing it/.test(r.results[0].detail));
};

// F7: the count sold is what the account holds AFTER the claim, not what the earlier list said. A position the exit watch sold in between is not sold again (that would open the opposite one),
// and one that shrank is sold at its new size.
gates.F7 = async () => {
  const gone = world({ positions: [{ ticker: TA, position_fp: '3.00' }], later: [{ ticker: TA, position_fp: '0.00' }] });
  const r = await gone.run();
  assert.deepStrictEqual([gone.posts.length, r.results[0].status, r.results[0].detail], [0, 'skipped', 'already closed'], 'sold in between: nothing is sent');
  const shrunk = world({ positions: [{ ticker: TA, position_fp: '3.00' }], later: [{ ticker: TA, position_fp: '1.00' }] });
  await shrunk.run();
  assert.deepStrictEqual(shrunk.posts.map((b) => b.count), ['1'], 'sold at the size held now, not the size listed');
  const flipped = world({ positions: [{ ticker: TA, position_fp: '3.00' }], later: [{ ticker: TA, position_fp: '-2.00' }] });
  await flipped.run();
  assert.deepStrictEqual(flipped.posts.map((b) => [b.side, b.count]), [['bid', '2']], 'a position that is now the other side is closed in that direction');
};

// F8: no claim store (or a claim that fails) means no sell, and the result says so; and the exit watch and Flatten share ONE claim function, so neither can drift from the other.
gates.F8 = async () => {
  const w = world({ positions: [{ ticker: TA, position_fp: '3.00' }] });
  const r = await live.flattenAll({ fetchFn: async () => { throw new Error('should not be reached'); }, keyId: 'k', pem, now: NOW, store: null }).catch((e) => ({ ok: false, thrown: e.message }));
  assert.ok(r.ok === false || (r.results || []).every((x) => x.status !== 'sold'), 'nothing is sold without a store');
  const libSrc = fs.readFileSync(path.join(root, 'functions', 'kalshiLiveLib.js'), 'utf8');
  assert.strictEqual((libSrc.match(/await claimClose\(store, /g) || []).length, 2, 'the exit watch and Flatten each call the one shared claimClose');
  assert.ok(/store: firestoreLiveStore\(db\)/.test(fnSrc), 'the Flatten callable passes the claim store');
  assert.ok(/kalshiLiveClosing/.test(fnSrc) && !/kalshiLiveClosing/.test(fs.readFileSync(path.join(root, 'firestore.rules'), 'utf8')), 'the claim documents have no client rule, so only the server can touch them');
};

(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + (e && e.message)); }
  }
  process.exit(failed ? 1 : 0);
})();
