"use strict";
// The one-time LIVE test order: step 1 of the owner's decision to put a small amount of real money behind this
// (recorded in kalshi-scalper/README.md). It proves the real-money plumbing (production signing, a real fill, the
// real fee, the real duplicate-order behaviour) with ONE contract. It is not the bot and cannot become it:
//
// - One contract, a hard $2.00 cap including the fee, Bitcoin or gold, immediate-or-cancel so nothing rests.
// - Fails closed. It does nothing unless the switch KALSHI_LIVE_ENABLED is "on" (default off), the bot is not
//   halted, the exchange is trading and the account balance is readable and enough.
// - Hard totals: at most 2 a day and 5 ever. Past that this module refuses until a person edits it.
// - NEVER retried. On Kalshi's demo a repeated order id was refused with HTTP 409, but on production that is not
//   yet confirmed (the point of this step). So an ambiguous answer (no reply, a timeout, a 5xx) is recorded as
//   "unknown", tells the owner to look at the Kalshi account, and blocks every further live test until that
//   record is dealt with by hand.
// - The order id is derived from the market (L-<ticker>), never random, and the record is created first and
//   atomically, so a double click or a second instance cannot send it twice.
// - Production host only: every request is checked against the production host before it is sent. The key
//   lives in Firebase secrets, signs and is never logged, recorded or returned.
//
// The scheduled bot (kalshiBotLib.js, kalshiBotRun.js, exports.kalshiBot) still has no order code.

const crypto = require("crypto");
const bot = require("./kalshiBotLib");

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

// The live production prices the bot itself trades from. `api` has exchangeStatus() and markets(series).
async function loadQuotes(api) {
  const st = await api.exchangeStatus();
  const active = Boolean(st.trading_active !== undefined ? st.trading_active : st.exchange_active);
  const quotes = [];
  for (const series of bot.SERIES) for (const m of await api.markets(series)) quotes.push({ series, m });
  return { active, quotes };
}

const LIVE_BASE = "https://external-api.kalshi.com/trade-api/v2";
const LIVE_HOSTS = ["external-api.kalshi.com"];
const API_ROOT = "/trade-api/v2";
const LIVE_CAP = 2.0;               // dollars, fee included. Not a parameter: change it here, in review.
const LIVE_SERIES = ["KXBTC15M", "KXGOLD15M"];   // gold has real volume on production; only the DEMO's gold book is empty
const MAX_PER_DAY = 2;
const MAX_EVER = 5;
const COOLDOWN_MS = 60000;
const MIN_LEFT_MS = 300000;         // a live test needs 5 minutes left, not the demo's 2
// The signal comes from Kalshi's market LIST and the price to pay from the single-market read, and the two differ by
// about 2c at the same instant (measured 2026-10-07: gold 21c/22c on the list, 19c/20c on the detail). A tight
// tolerance therefore refused almost everything. The real test is that the FRESH price, the one actually paid, is
// still inside the strategy's own 40c or 50c band; this wider bound only catches a market that has jumped.
const MOVE_TOLERANCE = 0.05;
const ARM_MS = 3 * 3600 * 1000;     // an armed scan switches itself off after this long, however it ended up
const BALANCE_MARGIN = 0.5;         // dollars that must remain after the order

class NotLive extends Error {}

function assertLive(url) {
  const u = new URL(url);
  if (u.protocol !== "https:" || !LIVE_HOSTS.includes(u.hostname)) {
    throw new NotLive("refusing to send a request to " + u.hostname + ": this module trades on production only");
  }
}

// One request. Never retried, never throws on an HTTP status. A network error or timeout comes back as status 0.
async function liveRequest({ fetchFn, keyId, pem, method, path, params, body, nowMs }) {
  const url = LIVE_BASE + path + (params ? "?" + new URLSearchParams(params).toString() : "");
  assertLive(url);
  const headers = { Accept: "application/json", "User-Agent": "shwoopnet-live/1.0" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (keyId && pem) {
    const ts = String(nowMs !== undefined ? nowMs : Date.now());
    headers["KALSHI-ACCESS-KEY"] = keyId;
    headers["KALSHI-ACCESS-TIMESTAMP"] = ts;
    headers["KALSHI-ACCESS-SIGNATURE"] = signRequest(pem, ts, method, API_ROOT + path);
  }
  try {
    const res = await fetchFn(url, {
      method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(15000),
    });
    const text = await res.text();
    let parsed;
    try { parsed = JSON.parse(text); } catch (e) { parsed = text.slice(0, 300); }
    return { status: res.status, body: parsed };
  } catch (e) {
    if (e instanceof NotLive) throw e;
    return { status: 0, body: String((e && e.message) || e).slice(0, 100) };
  }
}

const isAmbiguous = (status) => status === 0 || status === 429 || status >= 500;
const short = (b) => (typeof b === "string" ? b : JSON.stringify(b)).slice(0, 160);
const no = (reason) => ({ ok: false, reason });
// An outcome after a send was attempted (refused, answer lost, id already used): the caller must not scan again.
const attempted = (reason) => ({ ok: false, attempted: true, reason });
const num = (v) => (v === undefined || v === null || v === "" ? NaN : Number(v));

// Which side of the live book the order takes, and the one contract's cost. A YES buy takes the YES ask; a NO buy
// (a YES sell, economically) takes the YES bid.
function livePlan(signal, market) {
  const yes = signal.side === "yes";
  const touch = num(yes ? market.yes_ask_dollars : market.yes_bid_dollars);
  if (!(touch > 0 && touch < 1)) return { ok: false, why: "the live book has nothing on the side this order would take" };
  const signalYes = yes ? signal.price : 1 - signal.price;
  if (Math.abs(touch - signalYes) > MOVE_TOLERANCE + 1e-9) {
    return { ok: false, why: "the price moved from " + signalYes.toFixed(2) + " to " + touch.toFixed(2) + " since the signal" };
  }
  const sidePrice = Math.round((yes ? touch : 1 - touch) * 100) / 100;   // cents, so 1 - 0.58 is 0.42 and not 0.42000000000000004
  const inBand = Object.keys(bot.BANDS).some((b) => sidePrice >= bot.BANDS[b][0] - 1e-9 && sidePrice <= bot.BANDS[b][1] + 1e-9);
  if (!inBand) return { ok: false, why: "the price moved from " + signalYes.toFixed(2) + " to " + touch.toFixed(2) + " and the side it would buy (" + sidePrice.toFixed(2) + ") is no longer in a 40c or 50c band" };
  const cost = sidePrice + bot.takerFee(sidePrice, 1);
  if (cost > LIVE_CAP + 1e-9) return { ok: false, why: "one contract would cost $" + cost.toFixed(2) + ", above the $" + LIVE_CAP.toFixed(2) + " cap" };
  return { ok: true, touch, sidePrice, cost };
}

// The order body is built from fixed fields only. count is the literal 1.
function liveOrderBody(ticker, touch, side, clientOrderId, exchangeIndex) {
  const body = {
    ticker, side: side === "yes" ? "bid" : "ask", count: "1", price: touch.toFixed(2),
    time_in_force: "immediate_or_cancel", self_trade_prevention_type: "taker_at_cross", client_order_id: clientOrderId,
  };
  if (exchangeIndex !== undefined && exchangeIndex !== null) body.exchange_index = exchangeIndex;
  return body;
}

// Dollars available to this order. Prefers the per-shard breakdown (each shard holds its own funds); falls back to
// the top-level balance, which Kalshi documents in cents. Neither readable: NaN, and the caller refuses.
function availableFor(balanceBody, exchangeIndex) {
  const b = balanceBody && typeof balanceBody === "object" ? balanceBody : {};
  if (Array.isArray(b.balance_breakdown) && b.balance_breakdown.length) {
    const row = b.balance_breakdown.find((r) => r.exchange_index === exchangeIndex);
    return row ? num(row.balance) : 0;
  }
  const cents = num(b.balance);
  return Number.isFinite(cents) ? cents / 100 : NaN;
}

async function findOrder({ fetchFn, keyId, pem, ticker, clientOrderId, nowMs }) {
  const r = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/orders", params: { ticker, limit: "50" }, nowMs });
  const list = r.status === 200 && r.body && Array.isArray(r.body.orders) ? r.body.orders : [];
  return list.find((o) => o.client_order_id === clientOrderId) || null;
}

// store: {halted(), countSince(ts), countEver(), lastTestAt(), hasUnresolved(), createTest(id, data), updateTest(id, patch)}
async function runLiveTest({ quotes, active, enabled, store, now, keyId, pem, fetchFn }) {
  if (enabled !== true) return no("Live test trading is switched off. Set KALSHI_LIVE_ENABLED=on in functions/.env and redeploy to allow it.");
  if (!active) return no("The exchange is not trading right now.");
  if (await store.halted()) return no("The bot is halted. Release the halt before sending a live order.");
  if (await store.hasUnresolved()) return no("An earlier live test is still unresolved (sent, or its answer was lost). Check the Kalshi account, then mark it resolved by hand. Nothing was sent.");
  const startOfDay = new Date(now); startOfDay.setUTCHours(0, 0, 0, 0);
  if ((await store.countEver()) >= MAX_EVER) return no("The live test limit of " + MAX_EVER + " orders has been reached. It takes a code change to raise it.");
  if ((await store.countSince(startOfDay.getTime())) >= MAX_PER_DAY) return no("The limit of " + MAX_PER_DAY + " live tests a day has been reached.");
  const last = await store.lastTestAt();
  if (last && now - last < COOLDOWN_MS) return no("A live test was sent less than a minute ago. Wait a moment.");

  const all = bot.planEntries(quotes, now, LIVE_CAP);
  const signals = all.filter((s) => LIVE_SERIES.includes(s.series));
  if (!signals.length) return no("No Bitcoin or gold signal right now: no market is at a 40c or 50c price with a tradable book. Try again in a few minutes.");

  // Read the balance once. Each market lives on its own shard and each shard holds its own funds, so a signal on a
  // market whose shard is empty is skipped for the next one, instead of the whole test failing on it.
  const bal = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/balance", nowMs: now });
  if (bal.status !== 200) return no("The account balance could not be read (HTTP " + bal.status + "), so nothing was sent.");

  // Refresh the price from the exchange itself, right before sending, and keep only a market that is still open.
  let chosen = null, market = null, plan = null;
  const skipped = [];
  for (const s of signals) {
    const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(s.ticker) });
    const m = mk.status === 200 && mk.body && mk.body.market;
    if (!m) { skipped.push(s.ticker + ": could not read the market (HTTP " + mk.status + ")"); continue; }
    if (!["active", "open"].includes(m.status)) { skipped.push(s.ticker + ": market is " + m.status); continue; }
    if (Date.parse(m.close_time) - now <= MIN_LEFT_MS) { skipped.push(s.ticker + ": closing too soon"); continue; }
    const p = livePlan(s, m);
    if (!p.ok) { skipped.push(s.ticker + ": " + p.why); continue; }
    const avail = availableFor(bal.body, m.exchange_index);
    if (!Number.isFinite(avail)) { skipped.push(s.ticker + ": the balance came back in a shape this code does not recognise"); continue; }
    if (avail < p.cost + BALANCE_MARGIN) {
      skipped.push(s.ticker + ": the account has $" + avail.toFixed(2) + " available" + (m.exchange_index !== undefined ? " on shard " + m.exchange_index : "") + " and this order needs $" + (p.cost + BALANCE_MARGIN).toFixed(2) + ", and funds on another shard do not count, so move money to that shard in the Kalshi app first");
      continue;
    }
    chosen = s; market = m; plan = p;
    break;
  }
  if (!chosen) return no("There is a signal, but nothing safe to send (" + skipped.join("; ") + "). Nothing was sent.");

  const cid = "L-" + chosen.ticker;
  const record = {
    ticker: chosen.ticker, series: chosen.series, side: chosen.side, band: chosen.band, count: 1, price: plan.sidePrice,
    signalPrice: chosen.price, exchangeIndex: market.exchange_index === undefined ? null : market.exchange_index,
    clientOrderId: cid, status: "sending", ts: now, mode: "live", maxCost: Number(plan.cost.toFixed(2)),
  };
  // Record first. If it exists, this market was already attempted: never a second order.
  if (!(await store.createTest(cid, record))) return no("A live order for " + chosen.ticker + " was already attempted. Wait for the next market.");

  const body = liveOrderBody(chosen.ticker, plan.touch, chosen.side, cid, market.exchange_index);
  const res = await liveRequest({ fetchFn, keyId, pem, method: "POST", path: "/portfolio/events/orders", body, nowMs: Date.now() });
  const d = res.body && typeof res.body === "object" ? res.body : {};

  if (res.status >= 200 && res.status < 300 && d.order_id) {
    const filledCount = Number(d.fill_count || 0);
    await store.updateTest(cid, {
      status: filledCount > 0 ? "filled" : "no fill", orderId: d.order_id, fillCount: String(d.fill_count || "0"),
      remainingCount: String(d.remaining_count || "0"), averageFillPrice: d.average_fill_price || null,
      averageFeePaid: d.average_fee_paid || null, sentSide: body.side, sentPrice: body.price,
    });
    return {
      ok: true, live: true, ticker: chosen.ticker, side: chosen.side, count: 1, price: plan.sidePrice, orderId: d.order_id,
      sentSide: body.side, sentPrice: body.price, fillCount: String(d.fill_count || "0"), averageFillPrice: d.average_fill_price || null,
      averageFeePaid: d.average_fee_paid || null, filled: filledCount > 0,
    };
  }
  if (res.status === 409) {
    const found = await findOrder({ fetchFn, keyId, pem, ticker: chosen.ticker, clientOrderId: cid, nowMs: Date.now() });
    await store.updateTest(cid, found
      ? { status: Number(found.fill_count_fp || 0) > 0 ? "filled" : "no fill", orderId: found.order_id, fillCount: String(found.fill_count_fp || "0"), recovered: true, error409: true }
      : { status: "unknown", error: "HTTP 409 and the order could not be found: " + short(res.body) });
    return attempted("Kalshi says an order with this id already exists. Check the Kalshi account for it. This is the first time production has been seen to refuse a repeated id.");
  }
  if (isAmbiguous(res.status)) {
    await store.updateTest(cid, { status: "unknown", error: "HTTP " + res.status + " " + short(res.body) });
    return attempted("The answer from Kalshi was lost (HTTP " + res.status + "). THE ORDER MAY OR MAY NOT HAVE BEEN PLACED. Open the Kalshi account (Portfolio, Orders) and look before doing anything else. Nothing was retried, and further live tests are blocked until this record is resolved by hand.");
  }
  await store.updateTest(cid, { status: "error", error: "HTTP " + res.status + " " + short(res.body) });
  return attempted("Kalshi refused the order: HTTP " + res.status + " " + short(res.body) + ". Nothing was placed.");
}

// One minute of an armed scan. `arm` is the control document ({armed, until}); setArm and recordLast write it and
// the last outcome back. Not armed, or past `until`: nothing happens (and an expired arm is switched off). Armed:
// one ordinary runLiveTest, with every one of its guards. The arm switches off as soon as an order has been SENT
// (filled or not), or its answer was lost or refused, and on any error, so a single arming can never place more
// than one order. A refusal before sending (no signal, price moved, shard empty) leaves it armed to try again.
async function runArmedTick(args) {
  const { arm, now, setArm, recordLast } = args;
  // The log is for the owner's page only. A failure to write it must never change what the scan does.
  const log = async (kind, detail) => { if (args.logEvent) { try { await args.logEvent({ ts: now, kind, detail }); } catch (e) { /* the log is optional */ } } };
  if (!arm || arm.armed !== true) return { skipped: "not armed" };
  if (!(arm.until > now)) {
    await setArm({ armed: false, endedAt: now, endedBecause: "expired" });
    await log("scan ended", "expired after 3 hours with nothing sent");
    return { skipped: "expired" };
  }
  let r;
  try {
    r = await runLiveTest(args);
  } catch (e) {
    await setArm({ armed: false, endedAt: now, endedBecause: "error" });
    await recordLast({ ts: now, ok: false, attempted: false, reason: "The scan stopped on an error: " + String((e && e.message) || e).slice(0, 120) });
    await log("scan ended", "stopped on an error: " + String((e && e.message) || e).slice(0, 100));
    throw e;
  }
  await recordLast({
    ts: now, ok: r.ok === true, attempted: r.ok === true || r.attempted === true, reason: r.reason || null,
    ticker: r.ticker || null, filled: r.filled === true, fillCount: r.fillCount || null,
  });
  if (r.ok === true || r.attempted === true) {
    await setArm({ armed: false, endedAt: now, endedBecause: r.ok === true ? "sent" : "attempted" });
    await log("scan ended", r.ok === true ? "order sent" + (r.filled ? " and filled" : ", no fill") : "an order was attempted and needs a look: " + String(r.reason || "").slice(0, 100));
  }
  return r;
}

module.exports = {
  LIVE_BASE, LIVE_CAP, LIVE_SERIES, MAX_PER_DAY, MAX_EVER, MOVE_TOLERANCE, NotLive, assertLive, liveRequest, livePlan,
  liveOrderBody, availableFor, runLiveTest, runArmedTick, ARM_MS, signRequest, loadQuotes,
};
