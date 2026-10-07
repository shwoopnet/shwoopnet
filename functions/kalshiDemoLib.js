"use strict";
// The one-time DEMO test trader. It sends a single, tiny order to Kalshi's DEMO exchange
// (mock funds) from the bot's current signal, so the whole path (signal, signing, order,
// record) is proved before anything is automated.
//
// DEMO ONLY, by construction:
// - The host is a constant, and every request is checked against the demo host list before
//   it is sent. Nothing a caller passes can point this at the real exchange.
// - One order, capped at TEST_CAP dollars including the fee, immediate-or-cancel so nothing
//   is left resting.
// - The order id is derived from the market (t-<ticker>), never random: Kalshi refuses a
//   repeated client_order_id (HTTP 409, measured on the demo), so a double click, a retry or a
//   second instance cannot place it twice. The record is created first, atomically, and a
//   record that already exists blocks the order, so a crash between the record and the order
//   fails closed (nothing is sent twice) and shows up as a "sending" row to look at.
// - The key lives in Firebase secrets, is used only to sign, and is never logged, recorded or
//   returned. Records and results hold no secret.
//
// The bot (kalshiBotLib.js, kalshiBotRun.js) still has no order code; tests assert that.

const crypto = require("crypto");
const bot = require("./kalshiBotLib");

const DEMO_BASE = "https://external-api.demo.kalshi.co/trade-api/v2";
// Kalshi documents two demo front doors, both on the allow list below. The recommended one has returned
// HTTP 503 while the other kept answering with every shard trading (2026-10-06), so a request that fails
// transiently on the first goes to the second.
const DEMO_BASES = [DEMO_BASE, "https://demo-api.kalshi.co/trade-api/v2"];
const DEMO_HOSTS = ["external-api.demo.kalshi.co", "demo-api.kalshi.co"];
const API_ROOT = "/trade-api/v2";
const TEST_CAP = 1.0;            // dollars, fee included
const MIN_LEFT_MS = 120000;      // a market must have at least this long to run
const COOLDOWN_MS = 60000;       // a second test within a minute of the last is refused
// The demo's gold market (KXGOLD15M) has almost no resting orders, so a test there only ever reports "nothing to
// trade against". The paper bot still watches both markets; only this one-off test is limited to Bitcoin.
const DEMO_SERIES = ["KXBTC15M"];
const CROSS_TOLERANCE = 0.05;    // dollars: how far the demo's own price may sit from the live signal price
const RETRY_DELAYS_MS = [500, 1500];   // a transient failure is retried twice before giving up

class NotDemo extends Error {}

function assertDemo(url) {
  const u = new URL(url);
  if (u.protocol !== "https:" || !DEMO_HOSTS.includes(u.hostname)) {
    throw new NotDemo("refusing to send a request to " + u.hostname + ": this is demo only");
  }
}

// Kalshi's scheme: sign timestamp + METHOD + the full path from the API root, query left out.
// RSA keys use PSS with SHA-256 and a salt as long as the digest; Ed25519 signs the message.
function signRequest(pem, timestamp, method, path) {
  const key = crypto.createPrivateKey(String(pem).replace(/\\n/g, "\n"));
  const message = Buffer.from(timestamp + method + String(path).split("?")[0]);
  const type = key.asymmetricKeyType;
  if (type === "ed25519") return crypto.sign(null, message, key).toString("base64");
  if (type === "rsa") {
    return crypto.sign("sha256", message, {
      key, padding: crypto.constants.RSA_PKCS1_PSS_PADDING, saltLength: crypto.constants.RSA_PSS_SALTLEN_DIGEST,
    }).toString("base64");
  }
  throw new Error("unsupported key type: " + type);
}

// One request to the demo API at one base. path is relative to the API root. Signed when keyId and pem are given.
// Never throws on an HTTP error status: the caller reports what the exchange said.
async function demoRequestAt(base, { fetchFn, keyId, pem, method, path, params, body, nowMs }) {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  const url = base + path + query;
  assertDemo(url);
  const headers = { Accept: "application/json", "User-Agent": "shwoopnet-demo/1.0" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (keyId && pem) {
    const ts = String(nowMs !== undefined ? nowMs : Date.now());
    headers["KALSHI-ACCESS-KEY"] = keyId;
    headers["KALSHI-ACCESS-TIMESTAMP"] = ts;
    headers["KALSHI-ACCESS-SIGNATURE"] = signRequest(pem, ts, method, API_ROOT + path);
  }
  const res = await fetchFn(url, {
    method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(15000),
  });
  const text = await res.text();
  let parsed;
  try { parsed = JSON.parse(text); } catch (e) { parsed = text.slice(0, 300); }
  return { status: res.status, body: parsed, base };
}

// Tries each demo front door in turn and stops at the first answer that is not a transient failure. The same
// order id goes to both, which is safe: they front one exchange, and Kalshi refuses a repeated client_order_id
// (HTTP 409), which the caller treats as "an earlier attempt landed".
async function demoRequest(args) {
  let last, thrown = null;
  for (const base of DEMO_BASES) {
    try {
      last = await demoRequestAt(base, args);
      thrown = null;
    } catch (e) {
      if (e instanceof NotDemo) throw e;
      thrown = e;
      last = { status: 0, body: String((e && e.message) || e).slice(0, 100), base };
    }
    if (!isTransient(last.status)) return last;
  }
  if (thrown) throw thrown;
  return last;
}

// Prices on the YES book. Buying YES is a bid at the ask; buying NO at q is selling YES at 1 - q.
function orderFor(signal) {
  const yes = signal.side === "yes";
  return { side: yes ? "bid" : "ask", price: (yes ? signal.price : 1 - signal.price).toFixed(2) };
}

function orderBody(signal, clientOrderId, exchangeIndex) {
  if (!(signal.contracts >= 1 && signal.contracts <= 5)) throw new Error("a test order is 1 to 5 contracts");
  const cost = signal.price * signal.contracts + bot.takerFee(signal.price, signal.contracts);
  if (cost > TEST_CAP + 1e-9) throw new Error("a test order costs at most $" + TEST_CAP.toFixed(2) + ", this one is $" + cost.toFixed(2));
  const o = orderFor(signal);
  const body = {
    ticker: signal.ticker, side: o.side, count: String(signal.contracts), price: o.price,
    time_in_force: "immediate_or_cancel", self_trade_prevention_type: "taker_at_cross", client_order_id: clientOrderId,
  };
  if (exchangeIndex !== undefined && exchangeIndex !== null) body.exchange_index = exchangeIndex;
  return body;
}

// The demo exchange has its own, thin book. An immediate order priced at the LIVE signal price only fills if the
// demo book happens to hold an order at exactly that price, which is why the first tests came back "no fill".
// So price the order to meet the demo's own touch instead: a YES buy takes the demo's YES ask, a NO buy (a YES
// sell) takes its YES bid. The signal still decides WHAT to trade; the demo book decides at what price, and only
// within CROSS_TOLERANCE of the live price, so a test never pays a price the live signal would not have.
function crossPlan(signal, market) {
  const yes = signal.side === "yes";
  const num = (v) => (v === undefined || v === null || v === "" ? NaN : Number(v));
  const touch = yes ? num(market.yes_ask_dollars) : num(market.yes_bid_dollars);
  const size = num(yes ? market.yes_ask_size_fp : market.yes_bid_size_fp);
  if (!(touch > 0 && touch < 1) || size === 0) {
    return { ok: false, why: "the demo book has nothing on the side this order would take (" + (yes ? "no YES ask" : "no YES bid") + ")" };
  }
  const liveYes = yes ? signal.price : 1 - signal.price;
  const gap = Math.abs(touch - liveYes);
  if (gap > CROSS_TOLERANCE + 1e-9) {
    return { ok: false, why: "the demo's price is " + touch.toFixed(2) + " against the live " + liveYes.toFixed(2) + ", more than " + CROSS_TOLERANCE.toFixed(2) + " apart" };
  }
  const sidePrice = yes ? touch : 1 - touch;
  let count = signal.contracts;
  const cost = (n) => sidePrice * n + bot.takerFee(sidePrice, n);
  while (count > 1 && cost(count) > TEST_CAP + 1e-9) count--;
  if (cost(count) > TEST_CAP + 1e-9) return { ok: false, why: "one contract at the demo's price would cost more than $" + TEST_CAP.toFixed(2) };
  return { ok: true, signal: { ...signal, price: sidePrice, contracts: count }, touch };
}

function fundedShards(balanceBody) {
  const out = new Set();
  for (const b of (balanceBody && balanceBody.balance_breakdown) || []) {
    if (Number(b.balance) > 0) out.add(b.exchange_index);
  }
  return out;
}

// The live production prices the bot itself trades from. `api` has exchangeStatus() and markets(series).
async function loadQuotes(api) {
  const st = await api.exchangeStatus();
  const active = Boolean(st.trading_active !== undefined ? st.trading_active : st.exchange_active);
  const quotes = [];
  for (const series of bot.SERIES) for (const m of await api.markets(series)) quotes.push({ series, m });
  return { active, quotes };
}

const realSleep = (ms) => new Promise((r) => setTimeout(r, ms));
// 0 is "no answer at all" (a network error or timeout). 429 and 5xx are the exchange asking us to try again.
const isTransient = (status) => status === 0 || status === 429 || status >= 500;

// The same order is safe to send again after a transient failure: the id is derived from the market and Kalshi
// refuses a repeated client_order_id with HTTP 409 (measured on the demo). So a request whose answer was lost
// can only ever leave ONE order, and a retry that gets 409 means the earlier attempt landed.
async function postWithRetry(args, sleepFn) {
  let res;
  for (let i = 0; i <= RETRY_DELAYS_MS.length; i++) {
    try {
      res = await demoRequest(args);
    } catch (e) {
      if (e instanceof NotDemo) throw e;
      res = { status: 0, body: String((e && e.message) || e).slice(0, 100) };
    }
    if (!isTransient(res.status) || i === RETRY_DELAYS_MS.length) break;
    await sleepFn(RETRY_DELAYS_MS[i]);
  }
  return res;
}

// What Kalshi holds for this client_order_id, for the case where a repeat was refused (the order already exists).
async function findOrder({ fetchFn, keyId, pem, ticker, clientOrderId, nowMs }) {
  const r = await demoRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/orders", params: { ticker, limit: "50" }, nowMs });
  const list = r.status === 200 && r.body && Array.isArray(r.body.orders) ? r.body.orders : [];
  return list.find((o) => o.client_order_id === clientOrderId) || null;
}

const short = (b) => (typeof b === "string" ? b : JSON.stringify(b)).slice(0, 200);
const no = (reason) => ({ ok: false, reason });

// store: { lastTestAt() -> ms|null, createTest(id, data) -> bool, updateTest(id, patch) }
async function runDemoTest({ quotes, active, store, now, keyId, pem, fetchFn, sleepFn }) {
  const sleep = sleepFn || realSleep;
  if (!active) return no("The exchange is not trading right now.");
  const last = await store.lastTestAt();
  if (last && now - last < COOLDOWN_MS) return no("A test was sent less than a minute ago. Wait a moment.");

  const all = bot.planEntries(quotes, now, TEST_CAP);
  const signals = all.filter((s) => DEMO_SERIES.includes(s.series));
  if (!signals.length && all.length) return no("There is a signal, but only on gold, and the demo's gold market is too thin to test against. The demo test trades Bitcoin only. Try again in a few minutes.");
  if (!signals.length) return no("No signal right now: no market is at a 40c or 50c price with a tradable book. Try again in a few minutes.");

  // Say so plainly if the demo exchange is down, before anything is recorded. Kalshi's demo has gone down for
  // stretches (HTTP 503 with trading_active false), and a record written for an order that was never sent would
  // only get in the way of trying again.
  const ex = await demoRequest({ fetchFn, method: "GET", path: "/exchange/status" });
  if (ex.status !== 200 || !ex.body || ex.body.trading_active === false) {
    return no("Kalshi's demo exchange is down right now (HTTP " + ex.status + "). Nothing was sent. Try again in a few minutes.");
  }

  const bal = await demoRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/balance", nowMs: now });
  if (bal.status !== 200) return no("The demo account balance could not be read (HTTP " + bal.status + ").");
  const funded = fundedShards(bal.body);

  let chosen = null, market = null;
  const skipped = [];
  for (const s of signals) {
    const mk = await demoRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(s.ticker) });
    const m = mk.status === 200 && mk.body && mk.body.market;
    if (!m) { skipped.push(s.ticker + ": not on the demo exchange"); continue; }
    if (!["active", "open"].includes(m.status)) { skipped.push(s.ticker + ": demo market is " + m.status); continue; }
    if (Date.parse(m.close_time) - now <= MIN_LEFT_MS) { skipped.push(s.ticker + ": closing too soon"); continue; }
    if (!funded.has(m.exchange_index)) { skipped.push(s.ticker + ": demo shard " + m.exchange_index + " has no funds"); continue; }
    chosen = s; market = m;
    break;
  }
  if (!chosen) return no("There is a signal, but no tradable demo market for it (" + skipped.join("; ") + ").");

  // Price against the demo's own book (see crossPlan). Nothing is recorded if there is nothing to trade against.
  const plan = crossPlan(chosen, market);
  if (!plan.ok) return no("There is a signal on " + chosen.ticker + ", but " + plan.why + ". Nothing was sent. Try again in a few minutes.");
  const live = chosen;
  chosen = plan.signal;

  const cid = "t-" + chosen.ticker;
  const record = {
    ticker: chosen.ticker, series: chosen.series, side: chosen.side, band: chosen.band, count: chosen.contracts,
    price: chosen.price, livePrice: live.price, exchangeIndex: market.exchange_index, clientOrderId: cid, status: "sending", ts: now, mode: "demo",
  };
  // Record first. If it already exists, an order for this market was already attempted: do not send another.
  if (!(await store.createTest(cid, record))) {
    // A record marked unavailable means the exchange was down when we tried: sending the same order again is
    // safe (see postWithRetry). Anything else (sending, placed, filled, error) means this market was already tried.
    const prev = typeof store.getTest === "function" ? await store.getTest(cid) : null;
    if (!(prev && prev.status === "unavailable")) return no("A test order for " + chosen.ticker + " was already sent. Wait for the next market.");
    await store.updateTest(cid, { status: "sending", retriedAt: now });
  }

  let body;
  try {
    body = orderBody(chosen, cid, market.exchange_index);
  } catch (e) {
    await store.updateTest(cid, { status: "refused", error: String(e.message) });
    return no(String(e.message));
  }
  const res = await postWithRetry({ fetchFn, keyId, pem, method: "POST", path: "/portfolio/events/orders", body, nowMs: Date.now() }, sleep);
  const d = res.body && typeof res.body === "object" ? res.body : {};
  if (res.status >= 200 && res.status < 300 && d.order_id) {
    const filledCount = Number(d.fill_count || 0);
    await store.updateTest(cid, {
      status: filledCount > 0 ? "filled" : "no fill", orderId: d.order_id, fillCount: String(d.fill_count || "0"),
      remainingCount: String(d.remaining_count || "0"), averageFillPrice: d.average_fill_price || null,
      averageFeePaid: d.average_fee_paid || null, sentSide: body.side, sentPrice: body.price,
    });
    return {
      ok: true, ticker: chosen.ticker, side: chosen.side, count: chosen.contracts, price: chosen.price,
      sentSide: body.side, sentPrice: body.price, orderId: d.order_id, fillCount: String(d.fill_count || "0"),
      averageFillPrice: d.average_fill_price || null, filled: filledCount > 0,
    };
  }
  if (res.status === 409) {
    // The order already exists: an earlier attempt landed even though its answer was lost. Report what Kalshi holds.
    const found = await findOrder({ fetchFn, keyId, pem, ticker: chosen.ticker, clientOrderId: cid, nowMs: Date.now() });
    if (found) {
      const fillCount = String(found.fill_count_fp || "0");
      const wasFilled = Number(fillCount) > 0;
      await store.updateTest(cid, {
        status: wasFilled ? "filled" : "no fill", orderId: found.order_id, fillCount, recovered: true, sentSide: body.side, sentPrice: body.price,
      });
      return {
        ok: true, recovered: true, ticker: chosen.ticker, side: chosen.side, count: chosen.contracts, price: chosen.price,
        sentSide: body.side, sentPrice: body.price, orderId: found.order_id, fillCount, averageFillPrice: null, filled: wasFilled,
      };
    }
    await store.updateTest(cid, { status: "duplicate refused", error: short(res.body) });
    return no("Kalshi already has an order with this id, so nothing new was sent.");
  }
  if (isTransient(res.status)) {
    await store.updateTest(cid, { status: "unavailable", error: "HTTP " + res.status + " " + short(res.body) });
    return no("Kalshi's demo is not answering (HTTP " + res.status + "). The order may not have been accepted. Pressing the button again is safe: the order id is the same, and Kalshi refuses a duplicate.");
  }
  await store.updateTest(cid, { status: "error", error: "HTTP " + res.status + " " + short(res.body) });
  return no("Kalshi refused the order: HTTP " + res.status + " " + short(res.body));
}

module.exports = {
  DEMO_BASE, TEST_CAP, DEMO_SERIES, CROSS_TOLERANCE, crossPlan, COOLDOWN_MS, NotDemo, assertDemo, signRequest, demoRequest, orderFor, orderBody,
  fundedShards, loadQuotes, runDemoTest,
};
