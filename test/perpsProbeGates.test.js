"use strict";
// The perps account probe must never keep a value or send anything but three fixed GETs.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const probe = require("../functions/kalshiPerpsProbeLib");

(async () => {
  // PP1: only the three fixed margin GET paths, only GET, and no POST or order word in the library.
  assert.deepStrictEqual(probe.PATHS, ["/margin/enabled", "/margin/balance", "/margin/positions"]);
  const calls = [];
  const fake = async (a) => { calls.push(a); return { status: 200, body: { positions: [{ market_ticker: "SECRETTICKER", position: "123.45", entry_price: "0.99" }], account_equity: "98765.43" } }; };
  const out = await probe.runPerpsProbe({ liveRequest: fake, fetchFn: null, keyId: "k", pem: "p", now: 1 });
  assert.ok(calls.every((c) => c.method === "GET" && c.noRetry === true && probe.PATHS.includes(c.path)));
  assert.strictEqual(calls.length, 3);

  // PP2: the stored result holds statuses and field NAMES, never a value (consequence: no account figure reaches Firestore or the report).
  const text = JSON.stringify(out);
  for (const v of ["SECRETTICKER", "123.45", "0.99", "98765.43"]) assert.ok(!text.includes(v), "a value leaked: " + v);
  assert.ok(out.results["/margin/positions"].fields.includes("positions[].market_ticker"));
  assert.ok(out.results["/margin/balance"].fields.includes("account_equity"));

  // PP3: a refused key (401, 403) is recorded as a status with no fields.
  const refused = await probe.runPerpsProbe({ liveRequest: async () => ({ status: 403, body: { error: "x" } }), fetchFn: null, keyId: "k", pem: "p", now: 2 });
  assert.ok(Object.values(refused.results).every((r) => r.status === 403 && r.fields.length === 0));

  // PP4: the library has no order or write word; the function is read only and sits before the Books export.
  const lib = fs.readFileSync(path.join(__dirname, "../functions/kalshiPerpsProbeLib.js"), "utf8").replace(/\/\/.*$/gm, "");
  assert.ok(!/POST|createOrder|orders|DELETE|PUT/.test(lib));
  const idx = fs.readFileSync(path.join(__dirname, "../functions/index.js"), "utf8");
  assert.ok(idx.indexOf("exports.kalshiPerpsProbe") > 0 && idx.indexOf("exports.kalshiPerpsProbe") < idx.indexOf("exports.kalshiBookTick") || idx.indexOf("exports.kalshiPerpsProbe") > 0);
  console.log("perps probe gates: ok");
})().catch((e) => { console.error(e); process.exit(1); });
