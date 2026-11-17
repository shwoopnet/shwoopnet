"use strict";
// The perps account snapshot is display only: three fixed GETs, no order, no value invented.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const lib = require("../functions/kalshiPerpsAccountLib");

(async () => {
  const bal = { subaccount_balances: [{ account_equity: "100.5", position_value: "40", maintenance_margin: "3", available_balance: "50" }, { account_equity: 20 }] };
  const pos = { positions: [
    { market_ticker: "KXBTCPERP", position: "2", entry_price: "70000", unrealized_pnl: "1.5", margin_used: "10", fees: "0.1" },
    { market_ticker: "KXETHPERP", position: "-3", entry_price: "3000", unrealized_pnl: "-0.5", margin_used: "5", fees: "0" },
    { market_ticker: "KXSOLPERP", position: "0", entry_price: "1", unrealized_pnl: "9", margin_used: "1" },   // closed row
    { market_ticker: "bad ticker!", position: "1" },                                                          // unsafe ticker
  ] };
  const list = { markets: [{ ticker: "KXBTCPERP", price: "70100", leverage_estimate: "12.5" }] };

  // PA1: the total is the sum of the subaccount equities, closed and malformed rows are dropped, direction comes from the sign, and a missing list value stays null (no made up mark).
  const d = lib.shapePerps(bal, pos, list, 5);
  assert.strictEqual(d.equity, 120.5);
  assert.strictEqual(d.count, 2);
  assert.strictEqual(d.rows[0].up, true);
  assert.strictEqual(d.rows[1].up, false);
  assert.strictEqual(d.rows[1].size, 3);
  assert.strictEqual(d.rows[0].mark, 70100);
  assert.strictEqual(d.rows[1].mark, null);
  assert.strictEqual(d.rows[1].multiplierEstimate, null);
  assert.strictEqual(d.pnlTotal, 1);

  // PA2: the forced-close price, buffer and auto close levels are never derived here (consequence: the page says n/a, never a guess shown as a fact).
  for (const r of d.rows) assert.ok(r.closeAt === null && r.bufferPct === null && r.takeProfit === null && r.stopLoss === null);

  // PA3: empty or missing answers give nulls and no rows, never a zero total.
  const e = lib.shapePerps(null, null, null, 6);
  assert.strictEqual(e.equity, null);
  assert.strictEqual(e.count, 0);

  // PA4: only the two fixed GET paths are called, no retry, and a total failure writes nothing (null).
  const calls = [];
  const ok = await lib.runPerpsAccount({ liveRequest: async (a) => { calls.push(a); return { status: 200, body: a.path === "/margin/balance" ? bal : pos }; }, fetchFn: null, keyId: "k", pem: "p", now: 7, publicGet: async () => list });
  assert.ok(calls.length === 2 && calls.every((c) => c.method === "GET" && c.noRetry === true && lib.PATHS.includes(c.path)));
  assert.strictEqual(ok.count, 2);
  const none = await lib.runPerpsAccount({ liveRequest: async () => ({ status: 403, body: {} }), fetchFn: null, keyId: "k", pem: "p", now: 8, publicGet: async () => list });
  assert.strictEqual(none, null);
  // a failing public list leaves rows with null marks, not a failure
  const nolist = await lib.runPerpsAccount({ liveRequest: async (a) => ({ status: 200, body: a.path === "/margin/balance" ? bal : pos }), fetchFn: null, keyId: "k", pem: "p", now: 9, publicGet: async () => { throw new Error("x"); } });
  assert.ok(nolist && nolist.rows.every((r) => r.mark === null) && nolist.listRead === false);

  // PA5: the library has no order or write word, only the public perps host, and no order code reads the document (consequence: it cannot move a trade).
  const src = fs.readFileSync(path.join(__dirname, "../functions/kalshiPerpsAccountLib.js"), "utf8").replace(/\/\/.*$/gm, "");
  assert.ok(!/POST|createOrder|orders|DELETE|PUT|Firestore|getFirestore/.test(src));
  assert.ok(lib.LIST_URL.startsWith("https://external-api.kalshi.com/"));
  for (const f of ["kalshiLiveLib.js", "kalshiSlotLib.js", "kalshiSlotRunLib.js", "kalshiHardStopLib.js", "kalshiRiskCoreLib.js"]) {
    const p = path.join(__dirname, "../functions", f);
    if (fs.existsSync(p)) assert.ok(!/perpsAccount|kalshiPerpsAccount/i.test(fs.readFileSync(p, "utf8")), f + " must not read the perps account");
  }
  const idx = fs.readFileSync(path.join(__dirname, "../functions/index.js"), "utf8");
  const at = idx.indexOf("exports.kalshiPerpsAccount");
  assert.ok(at > 0 && at < idx.indexOf("exports.kalshiBookRecorder"));
  assert.ok(/readPerpsAccount/.test(idx));
  // PA6: the hourly snapshot carries perpsTotal only when readable; an unreadable perps account never stops or zeroes the prediction balance document.
  const snap = require("../functions/kalshiBalanceSnapshotLib");
  const life = require("../functions/kalshiLiveLib");
  const origReq = life.liveRequest;
  life.liveRequest = async () => ({ status: 200, body: { balance: 12345 } });
  try {
    const wrote = [];
    await snap.runBalanceSnapshot({ now: 3600000 * 5, fetchFn: null, keyId: "k", pem: "p", write: async (id, doc) => wrote.push(doc), readPerpsEquity: async () => 120.456 });
    await snap.runBalanceSnapshot({ now: 3600000 * 6, fetchFn: null, keyId: "k", pem: "p", write: async (id, doc) => wrote.push(doc), readPerpsEquity: async () => NaN });
    await snap.runBalanceSnapshot({ now: 3600000 * 7, fetchFn: null, keyId: "k", pem: "p", write: async (id, doc) => wrote.push(doc), readPerpsEquity: async () => { throw new Error("x"); } });
    assert.strictEqual(wrote.length, 3, "the prediction balance is written every hour whatever the perps read does");
    assert.strictEqual(wrote[0].perpsTotal, 120.46);
    assert.ok(!("perpsTotal" in wrote[1]) && !("perpsTotal" in wrote[2]));
    assert.ok(snap.ALLOWED_FIELDS.includes("perpsTotal"));
  } finally { life.liveRequest = origReq; }
  console.log("perps account gates: ok");
})().catch((e) => { console.error(e); process.exit(1); });
