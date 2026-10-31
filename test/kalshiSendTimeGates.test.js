'use strict';
// ST-T1 to ST-T3: the send-time log (the owner, Oct 31, 2026: "log send time only", for the refinement chat's Dogecoin timing finding).
// Consequence: every order the bot sends records when the order left (sentAtMs), when Kalshi answered (answeredAtMs) and when the minute function started (tickStartMs), so a late Dogecoin order can be traced
// to a slow step; and recording it never changes whether, what or how much the bot buys.
const assert = require('assert');
const path = require('path');
const fx = require('./fixtures/offEquivalenceScenarios');
const live = require('../functions/kalshiLiveLib.js');
const gates = {};
const run = async (post) => {
  const w = fx.l1World(post ? { post } : {});
  const ret = await live.runL1Tick({ ...w.common, quotes: [fx.q('KXBTC15M', fx.T)] });
  return { w, ret };
};
const posts = (w) => w.r.log.filter((x) => x.kind === 'fetch' && x.method === 'POST');
const orderWrite = (w) => w.r.log.find((x) => x.kind === 'store' && x.call === 'updateTest' && x.args[1] && x.args[1].orderId);
gates['ST-T1 an answered order carries sentAtMs <= answeredAtMs and the tick start'] = async () => {
  const before = Date.now();
  const { w } = await run();
  const after = Date.now();
  const p = orderWrite(w).args[1];
  assert.ok(Number.isFinite(p.sentAtMs) && Number.isFinite(p.answeredAtMs) && p.sentAtMs >= before && p.answeredAtMs <= after && p.sentAtMs <= p.answeredAtMs, 'send time is read around the POST');
  assert.strictEqual(p.tickStartMs, fx.NOW, 'the tick start is the time the minute function started');
};
gates['ST-T2 the timing rides on the existing order write: no extra store write, one order sent'] = async () => {
  const { w } = await run();
  assert.strictEqual(posts(w).length, 1, 'still exactly one order');
  const writes = w.r.log.filter((x) => x.kind === 'store' && x.call === 'updateTest' && x.args[1] && 'sentAtMs' in x.args[1]);
  assert.strictEqual(writes.length, 1, 'the three times are written once, in the write that already followed the answer');
};
gates['ST-T3 a refused order is still refused and the timing never changes the order itself'] = async () => {
  const ok = await run();
  const bad = await run({ status: 400, body: { error: 'nope' } });
  assert.strictEqual(posts(bad.w).length, 1, 'a refused order is not retried');
  assert.ok(!orderWrite(bad.w), 'a refused order records no order id');
  assert.ok(!/sentAtMs|answeredAtMs|tickStartMs/.test(JSON.stringify(posts(ok.w)[0])), 'the timing is never part of the order sent to Kalshi');
};
(async () => {
  let failed = 0;
  for (const [name, fn] of Object.entries(gates)) {
    try { await fn(); console.log('ok   ' + name); } catch (e) { failed++; console.log('FAIL ' + name + ': ' + e.message); }
  }
  process.exit(failed ? 1 : 0);
})();
