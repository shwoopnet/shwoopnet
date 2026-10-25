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
// The signal library, the book recorder and the watchdog have no order code.

const crypto = require("crypto");
const bot = require("./kalshiSignalLib");

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
// The markets the bot's L1 rule trades: Bitcoin, gold and Ethereum, all by the same rule, size and stop (the owner folded Ethereum in on Oct 10, 2026; it was a separate switch before).
// A hard list in code: adding a series is a deliberate edit and review, never something a stored value can do. Solana is deliberately not on it. Order matters: when a window's room
// runs short (L1_WINDOW_CAP_FRACTION) the later series goes without, so Ethereum is last. LIVE_SERIES above is the older single-order path and is left alone.
// XRP and Dogecoin were appended on 2026-10-20 at the owner's choice, on the strength of kalshi-scalper/README.md (E3, E3B: +1.4c and +1.5c, then +1.8c on 29 older days; forward read E3F due 2026-11-16).
// They go LAST, so they only take a window's second slot when Bitcoin, gold and Ethereum left room.
// The PROBE markets (2026-10-21, the owner's choice: "live forward testing", no more paper): L1's own rule on AUD/USD, USD/CAD and natural gas, which history could not settle (12 days of AUD/USD and
// USD/CAD, a near miss on gas; kalshi-scalper/README.md PAPER1). ALWAYS one contract per order, whatever the size ladder says, so each costs about $0.90 at risk; they are the LAST in the list, so they only
// take what Bitcoin, gold, Ethereum, XRP and Dogecoin left in a window's combined limit, and they count toward the same loss stop, pool and 25c exit as every other L1 order. Adding to this list is a code edit.
const PROBE_SERIES = ["KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M"];
// GOLD FIRST (2026-10-21, the owner's choice after docs/GOLD_FIRST_PROPOSAL.md, option A). The first 302 settled bot trades: gold +$28.35 (2 losses in 98), Bitcoin -$20.55, Ethereum -$4.40, XRP -$3.63,
// Dogecoin -$2.66; the 68 day backtest agrees on gold and on nothing else; and Ethereum's losses came in the same window as Bitcoin's. So gold is the ONLY market that keeps the size ladder and it goes
// FIRST in the list (it gets a window's room before anything else); Bitcoin, Ethereum, XRP and Dogecoin are CAPPED at one contract like the probes, so they keep trading and keep their record growing,
// but a bad run on them costs about $0.90 a trade, not $4. A capped market earns its ladder size back only from its own live record (150 settled trades at one contract, a result above +0.5c a contract in
// both halves) and a ladder-sized market drops back if its last 100 trades are negative: either is a reviewed edit of THIS list, never a stored value. The 12% stop, the 5.5% window limit and the 25c exit are unchanged.
const CAPPED_SERIES = ["KXBTC15M", "KXETH15M", "KXXRP15M", "KXDOGE15M"];
// FIXED ORDER SIZES (2026-10-23, the owner: "yeah build", on the research session's proposal from kalshi-scalper/README.md "Sizing look at a $500 balance"). With the balance near $500, three markets that
// the history supports trade a little larger than the one-contract cap: XRP and Dogecoin 3 contracts, natural gas (a probe) 2. Bitcoin, Ethereum and the other probes stay at one contract, and gold keeps
// the ladder. This is a hard list in code like the lists above: no stored value and no callable can change it. It is leverage on an edge that has to persist, not a new edge, so nothing else moves: the 12% loss
// stop, the 5.5% window limit, one crypto order per window, the 25c exit and the profit add-on rule (still never used on these markets) are all unchanged. Review point: the owner's 2026-11-17 export; if the
// Dogecoin or XRP loss rate is above 7% there, step back to 1 or 2 by editing this list.
const FIXED_CONTRACTS = { KXXRP15M: 3, KXDOGE15M: 3, KXNATGAS15M: 2 };
// SERIES ORDER (2026-10-23, the owner: "reorder so XRP comes before Bitcoin and Dogecoin before Ethereum, gold stays first"). Markets are tried in this order within a tick, and only ONE capped crypto order is placed per 15 minute window, so the order decides which
// crypto market gets the window when several qualify at once. XRP and Dogecoin trade 3 contracts (FIXED_CONTRACTS) and Bitcoin and Ethereum one, so a 1 contract order no longer takes the slot from a 3 contract one in the same tick. The research session raised it: Bitcoin and XRP are both
// looked at about 10 minutes before the close, Ethereum and Dogecoin about 6, so the pairs that tie within a tick are exactly these. Nothing else moves: sizes, stops, window limit, entry times and the one crypto order per window rule are unchanged.
const L1_SERIES = ["KXGOLD15M", "KXXRP15M", "KXBTC15M", "KXDOGE15M", "KXETH15M", ...PROBE_SERIES];
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

// One request. An order (anything but a GET) is never retried, and nothing throws on an HTTP status. A network error or timeout comes back as status 0.
// A GET that Kalshi answers with 429 (too many requests) is asked once more after a short wait (Oct 22, 2026): the balance and position reads share one key with the
// exit watch's 10 second loop, and a single refused read made the account card say "could not be read". A read has no effect, so asking twice is safe; a second 429 comes back as is.
async function liveRequest(args) {
  const first = await liveRequestOnce(args);
  if (first.status !== 429 || args.method !== "GET") return first;
  await new Promise((r) => setTimeout(r, RATE_LIMIT_RETRY_MS));
  return liveRequestOnce({ ...args, nowMs: args.nowMs === undefined ? undefined : args.nowMs + RATE_LIMIT_RETRY_MS });
}
const RATE_LIMIT_RETRY_MS = 1200;
async function liveRequestOnce({ fetchFn, keyId, pem, method, path, params, body, nowMs }) {
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

// The order body is built from fixed fields only. count is 1 unless the owner turned on size scaling, and then a whole number
// from 1 to L1_ORDER_CEILING; anything else is refused here rather than sent.
function liveOrderBody(ticker, touch, side, clientOrderId, exchangeIndex, count = 1) {
  if (!Number.isInteger(count) || count < 1 || count > L1_ORDER_CEILING) throw new Error("refusing to build an order for " + count + " contracts");
  const body = {
    ticker, side: side === "yes" ? "bid" : "ask", count: String(count), price: touch.toFixed(2),
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
      skipped.push(s.ticker + ": the account has $" + avail.toFixed(2) + " available" + (m.exchange_index !== undefined ? " on shard " + m.exchange_index : "") + " and this order needs $" + (p.cost + BALANCE_MARGIN).toFixed(2) + ", and funds on another shard do not count (see functions/DEPLOY.md, 'Moving money between shards')");
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

// ---------------------------------------------------------------------------------------------------------------
// L1 session: the owner's 24 hour automatic run of strategy L1 (README: "Live waiver: L1 for 24 hours"). Same module,
// same order path, same production-only host and never-retry rules as the one contract test above, with its own limits.
// The rule is L1 exactly as pre-registered: about 6 minutes before the close, buy ONE contract of the side whose fresh
// price is 88c to 97c, at the touch, immediate-or-cancel, held to settlement. Nothing is tuned and nothing reads a result.
const L1_BAND = [0.88, 0.97];
const L1_WINDOW_MS = [330000, 400000];     // time left at which a market is eligible: about 6 minutes
// Early entry probes (the research session's FWD7, the owner: "live probes at 10 minutes", Oct 21, 2026). XRP and natural gas are entered about 10 minutes before the close INSTEAD of 6, one contract, to test whether
// entering earlier beats the 6 minute rule (the 69 day history says it might; it has not been tested live). It is the same rule on the same market, never a second position: both entries use the client
// order id "L1-" + ticker, and these two series no longer have a 6 minute window at all, so a market is decided once, at 10 minutes. Every order records
// which lead it was entered at (entryLead) so the two can be read apart afterwards.
const EARLY_PROBE_SERIES = ["KXXRP15M", "KXNATGAS15M"];   // Bitcoin left this list on Oct 23, 2026: it now decides at the 6 minute look, on a smooth climb only (SMOOTH_SERIES)
const EARLY_WINDOW_MS = [570000, 640000];   // about 10 minutes left
function entryLead(series, left) {
  // XRP and natural gas decide ONLY at 10 minutes (the owner's choice, Oct 21, 2026): a market not in the band then is skipped, not tried again at 6, so the 10 minute claim is tested on its own.
  if (EARLY_PROBE_SERIES.includes(series)) return left >= EARLY_WINDOW_MS[0] && left <= EARLY_WINDOW_MS[1] ? "10m" : null;
  return left >= L1_WINDOW_MS[0] && left <= L1_WINDOW_MS[1] ? "6m" : null;
}
// Not a trading limit. Bitcoin and gold have 192 markets in a day (96 each), so 200 orders in any rolling 24 hours can never be reached by
// normal trading; it only stops a runaway loop from sending orders without end. Past it the bot waits (it does not end the session) and carries
// on by itself once older orders fall out of the window. The loss stop is the real limit.
const L1_MAX_ORDERS = 200;
// A session has no end time any more (the owner removed it on Oct 8, 2026): it runs until the owner stops it or a stop below ends it. What stayed
// is the DAY: the loss stop and the order limit both look at the last 24 hours, so a long run cannot hide a bad day behind old profits.
const L1_WINDOW_DAY_MS = 24 * 3600 * 1000;
// Logging only (Oct 22, 2026, the research session's JUMP1 lead, the owner: "log it"). How far the side's mid price rose over the last 3 minutes, written on every new order (10 minute and 6 minute) AFTER the whole minute's orders
// have been sent, from the public one minute candles. It never decides anything: no order waits for it, it reads no key, and a read that fails or is thin leaves the order exactly as it was. The figure is for the side
// that was bought (a NO order's side rises when the YES mid falls). The research reads it with the order's own price and result.
const RISE_LOOKBACK_S = 180;
function riseFromCandles(candles, side, nowSec) {
  const mids = new Map();
  for (const c of Array.isArray(candles) ? candles : []) {
    const end = Number(c && c.end_period_ts), b = num(c && c.yes_bid && c.yes_bid.close_dollars), a = num(c && c.yes_ask && c.yes_ask.close_dollars);
    if (Number.isFinite(end) && Number.isFinite(b) && Number.isFinite(a) && end <= nowSec + 60) mids.set(end, (b + a) / 2);
  }
  if (!mids.size) return null;
  const latest = Math.max(...mids.keys());
  if (nowSec - latest > 150) return null;          // stale: the latest candle must be from about now
  const then = mids.get(latest - RISE_LOOKBACK_S);
  if (!Number.isFinite(then)) return null;
  const dir = side === "no" ? -1 : 1, now = mids.get(latest);
  // rng5 (Oct 22, 2026, the research session's FLAT2 lead, the owner: "yes, log rng5"): the max minus the min of the mid over the six minute marks from 5 minutes ago to now, so a quiet market reads small.
  // A range is the same for either side (a NO mid is one minus the YES mid), so it needs no direction. Any missing mark leaves it out; the order is never held for it.
  const marks = [0, 60, 120, 180, 240, 300].map((d) => mids.get(latest - d));
  const rng = marks.every(Number.isFinite) ? Number((Math.max(...marks) - Math.min(...marks)).toFixed(4)) : null;
  return { rise: Number((dir * (now - then)).toFixed(4)), midNow: Number(now.toFixed(4)), midThen: Number(then.toFixed(4)), candleAt: latest, rng };
}
// flips0 (Oct 23, 2026, the research session's FLIPS0 lead, the owner: "go", logging only). The path shape of the side being bought: the side's mid for every 1 minute candle from the market's first candle to the decision candle.
// `flips` counts direction changes in that path after ignoring minute changes of 0.004 or less; `flips0` is true when there are at least 4 earlier candles and no flip at all (a steady climb). Same rules as rise3: written
// after the orders are sent, from public candles, never able to change a trade. Parity vectors: test/kalshiL1Gates.test.js FL1 (from the research session's flips0_parity_vectors_2026-10-23.json).
const FLIP_MIN_STEP = 0.004;
function flipsOf(mids) {
  const steps = [];
  for (let i = 1; i < mids.length; i++) {
    const d = Number((mids[i] - mids[i - 1]).toFixed(6));
    if (Math.abs(d) > FLIP_MIN_STEP) steps.push(d);
  }
  let flips = 0;
  for (let i = 1; i < steps.length; i++) if ((steps[i] > 0) !== (steps[i - 1] > 0)) flips++;
  return flips;
}
// The favourite side's mid for every 1 minute candle up to the decision candle, oldest first; null when there is nothing or the latest candle is stale.
function sideMids(candles, side, nowSec) {
  const mids = new Map();
  for (const c of Array.isArray(candles) ? candles : []) {
    const end = Number(c && c.end_period_ts), b = num(c && c.yes_bid && c.yes_bid.close_dollars), a = num(c && c.yes_ask && c.yes_ask.close_dollars);
    if (Number.isFinite(end) && Number.isFinite(b) && Number.isFinite(a) && end <= nowSec + 60) mids.set(end, side === "no" ? 1 - (b + a) / 2 : (b + a) / 2);
  }
  if (!mids.size) return null;
  const ends = [...mids.keys()].sort((x, y) => x - y);
  if (nowSec - ends[ends.length - 1] > 150) return null;    // stale: the decision candle must be from about now
  return ends.map((e) => mids.get(e));
}
function pathShape(candles, side, nowSec) {
  const path = sideMids(candles, side, nowSec);
  if (!path) return null;
  const flips = flipsOf(path), earlier = path.length - 1;
  const steps = path.slice(1).map((v, i) => v - path[i]);
  // minStep and climb are plain float arithmetic on the mids, exactly as the research session's parity vectors were made (a pullback of exactly 0.005 computes to -0.0050000000000000044 and is NOT smooth).
  const minStep = steps.length ? Math.min(...steps) : null, climb = path[path.length - 1] - path[0];
  return { flips, flips0: earlier >= 4 && flips === 0, earlierCandles: earlier, minStep: minStep === null ? null : Number(minStep.toFixed(4)), climb: Number(climb.toFixed(4)), smooth: earlier >= 4 && minStep !== null && minStep >= -SMOOTH_MIN_STEP && climb >= SMOOTH_MIN_CLIMB };
}
// Smooth climb only (Oct 23, 2026, the research session's SMOOTH2 lead, the owner: "1"): Bitcoin and Ethereum order ONLY when the side being bought has climbed without a real pullback since the market opened: at least 4 earlier
// candles, no minute change below -0.005, and a total climb of at least 0.10. Anything else, or a path that cannot be read, places no order (fail closed). It only ever removes Bitcoin and Ethereum orders: size, band, stops,
// caps, the 25c exit and the one crypto order per window are unchanged. Kill rules (registered in the README): 3 or more losses in the first 40 smooth fills, net under $0 after 100 fills, or the 2026-11-12 forward read falsified.
const SMOOTH_SERIES = ["KXBTC15M", "KXETH15M"];
const SMOOTH_MIN_STEP = 0.005, SMOOTH_MIN_CLIMB = 0.10;
async function smoothGate({ fetchFn, series, ticker, side, nowMs }) {
  try {
    const nowSec = Math.floor(nowMs / 1000);
    const res = await liveRequest({ fetchFn, method: "GET", path: "/series/" + encodeURIComponent(series) + "/markets/" + encodeURIComponent(ticker) + "/candlesticks",
      params: { start_ts: String(nowSec - 7200), end_ts: String(nowSec + 60), period_interval: "1" }, nowMs });
    if (res.status !== 200 || !res.body || !Array.isArray(res.body.candlesticks)) return { ok: false, reason: "no order: the price path could not be read (HTTP " + res.status + ")" };
    const shape = pathShape(res.body.candlesticks, side, nowSec);
    if (!shape) return { ok: false, reason: "no order: the price path is missing or out of date" };
    if (!shape.smooth) return { ok: false, reason: "no order: not a smooth climb (" + shape.earlierCandles + " earlier candles, worst minute " + shape.minStep + ", climb " + shape.climb + ")" };
    return { ok: true, shape };
  } catch (e) { return { ok: false, reason: "no order: the price path could not be read" }; }
}
// Two-stage entry, LOGGING ONLY (Oct 24, 2026, the research session's TWOSTAGE log request, the owner said "go" there and "Yes, build it (log only)" here). For one market, at the three looks 600, 480 and 360 seconds before the close, the side
// whose price is inside the entry band (l1Pick's rule applied to that minute's candle: YES at its ask, NO at 1 minus the YES bid), its price, and whether there was one; and `twoStageLeft`, the earliest of the three looks that was in
// band. The candle used is the one whose end is EXACTLY that many seconds before the close: a neighbouring candle is never substituted, and a missing candle means no value (null), not "not in band". It decides nothing: it is written
// on the order record after the orders are sent, from public candles, and no order, size, entry time, cap or series reads it. An XRP or natural gas order (decided at 10 minutes) has no 8 or 6 minute candle yet, so those stay null.
const TWO_STAGE_LOOKS = [[600, "10"], [480, "8"], [360, "6"]];
function twoStageFromCandles(candles, closeSec) {
  if (!Number.isFinite(closeSec)) return null;
  const byEnd = new Map();
  for (const c of Array.isArray(candles) ? candles : []) {
    const end = Number(c && c.end_period_ts), b = num(c && c.yes_bid && c.yes_bid.close_dollars), a = num(c && c.yes_ask && c.yes_ask.close_dollars);
    if (Number.isFinite(end) && Number.isFinite(b) && Number.isFinite(a)) byEnd.set(end, { bid: b, ask: a });
  }
  const out = {}, r4 = (x) => Math.round(x * 10000) / 10000, lo = L1_BAND[0] - 1e-9, hi = L1_BAND[1] + 1e-9;
  let left = null, any = false;
  for (const [secs, tag] of TWO_STAGE_LOOKS) {
    const q = byEnd.get(closeSec - secs);
    if (!q || !bot.validQuote(q.bid, q.ask)) { out["ask" + tag] = null; out["side" + tag] = null; out["inBand" + tag] = null; continue; }
    any = true;
    let side = null, price = null;
    if (r4(q.ask) >= lo && r4(q.ask) <= hi) { side = "yes"; price = r4(q.ask); }
    else if (r4(1 - q.bid) >= lo && r4(1 - q.bid) <= hi) { side = "no"; price = r4(1 - q.bid); }
    out["ask" + tag] = price; out["side" + tag] = side; out["inBand" + tag] = side !== null;
    if (side !== null && left === null) left = secs;
  }
  if (!any) return null;
  out.twoStageLeft = left;
  return out;
}
async function logRise({ fetchFn, store, cid, series, ticker, side, nowMs, ask, closeSec }) {
  try {
    const nowSec = Math.floor(nowMs / 1000);
    const res = await liveRequest({ fetchFn, method: "GET", path: "/series/" + encodeURIComponent(series) + "/markets/" + encodeURIComponent(ticker) + "/candlesticks",
      params: { start_ts: String(nowSec - 7200), end_ts: String(nowSec + 60), period_interval: "1" }, nowMs });
    if (res.status !== 200 || !res.body || !Array.isArray(res.body.candlesticks)) return false;
    const r = riseFromCandles(res.body.candlesticks, side, nowSec), shape = pathShape(res.body.candlesticks, side, nowSec), two = twoStageFromCandles(res.body.candlesticks, closeSec);
    if (!r && !shape && !two) return false;
    await store.updateTest(cid, {
      ...(r ? { rise3: r.rise, riseMidNow: r.midNow, riseMidThen: r.midThen, ...(r.rng === null ? {} : { rng5: r.rng }) } : {}),
      ...(shape ? { flips: shape.flips, flips0: shape.flips0, earlierCandles: shape.earlierCandles, minStep: shape.minStep, climb: shape.climb, smooth: shape.smooth, ...(Number.isFinite(ask) ? { askAtDecision: ask } : {}) } : {}),
      ...(two || {}),
    });
    return true;
  } catch (e) { return false; }      // logging only: never allowed to affect a trade
}

// Cost (Oct 21, 2026, the owner: "cut costs"). The bot re-read the whole last 24 hours of orders every minute only to count them and sum their results. Orders older than OLDER_AFTER_MS are final
// (the exit watch acts within minutes of a buy and the settle sweep within minutes of the close), so they are read once and kept in this instance's memory for REFRESH_MS; only the recent block is read
// each minute. The recent block starts at a fixed point and grows until the older part is read again, so no order ever falls between the two. This can only make the bot's picture STALER in
// the cautious direction: a stale copy shows an order as unsettled or unsold, which the loss stop counts as lost, and any new order (from this or another instance) is inside the recent block
// because it is minutes old. The cache is per instance and never shared, so two instances during a deploy each keep their own. A failed read throws, exactly as the plain read did (the tick then sends nothing).
const L1_OLDER_AFTER_MS = 30 * 60 * 1000, L1_OLDER_REFRESH_MS = 15 * 60 * 1000;
function makeRecentOrderReader(readSince) {
  let older = null, olderAt = 0, olderSince = 0, split = 0;
  return async function read(since, now) {
    if (!older || now - olderAt >= L1_OLDER_REFRESH_MS || since < olderSince) {
      const all = await readSince(since);
      split = now - L1_OLDER_AFTER_MS;
      older = all.filter((t) => !(Number(t.ts) >= split)); olderAt = now; olderSince = since;
      return all;
    }
    const recent = await readSince(split);
    return older.filter((t) => Number(t.ts) >= since).concat(recent);
  };
}
// Size scaling (off unless the owner ticks it when starting a session). Each order risks about 2% of the account's cash, at
// least one contract and never more than L1_SIZE_MAX, and the loss stop becomes 10% of the starting cash instead of the flat $10. Raised by the owner on
// Oct 8, 2026 (from 1% and 7%/$7). At 2% a $106 account buys two contracts (two need about $92 to $98 of cash, three about $138 to $146).
const L1_SIZE_MAX = 3;
// One position's account-funded part never risks more than 2% of cash (the owner's choice, Oct 9, 2026, up from 1% set the day before). Two markets can trade
// the same window; the second is sized on the cash left after the first, so both together stay at about 4%. The profit add-on sits on top of this.
const L1_SIZE_FRACTION = 0.02;
// 5%, tightened from 10% on Oct 8, 2026 at the owner's choice: 10% of a $344 balance is $34, more than the worst modelled day at 5 contracts (about $20), so it
// never tripped. 5% is about $17, a real circuit breaker that a bad day at 4 to 5 contracts can reach.
// Raised from 5% to 6% on Oct 20, 2026 at the owner's choice, together with the per-window limit (4.5% to 5.5%), so that one window alone still cannot reach the stop. 6% is about $11.76 of a $196 base.
// Raised again from 6% to 12% on Oct 20, 2026 (the owner's choice, the same night) after the stop ended the bot with $6.06 SETTLED down and a full window ($8.43) open: an open order is counted as lost, so with the
// window limit at 5.5% a full open window left only about $0.80 to $2.30 of room for real losses, and one ordinary loss (about $3.70) was enough to stop it. At 12% a full window leaves about $10.60 of room. Open
// orders are STILL counted as lost, so the true worst case is unchanged in kind: the stop holds the account to 12% of the base (about 10% of the balance) however the open window ends.
const L1_SIZED_STOP_FRACTION = 0.12;
function l1Count(cash, costPerContract, cap = L1_SIZE_MAX, addon = 0) {
  if (!Number.isFinite(cash) || !(costPerContract > 0)) return 1;
  // The 2% of cash rule bounds the part funded by the account (the review's cap). The add-on, bought with reinvested PROFIT (the pool), sits outside it: the owner's
  // choice, Oct 8, 2026, so profit keeps compounding into size instead of waiting for the balance to catch up. Its risk is bounded by the pool, which holds only
  // profit (one extra contract needs one full contract cost of it, and a loss comes out of the pool first). L1_ORDER_CEILING is the only fixed limit left on a single order.
  const base = Math.max(1, Math.min(cap, L1_ORDER_CEILING, Math.floor((cash * L1_SIZE_FRACTION) / costPerContract + 1e-9)));
  return Math.min(base + Math.max(0, Math.floor(addon || 0)), L1_ORDER_CEILING);
}

// The cap on contracts per order follows the account, slowly (the owner keeps adding to it like a savings account). One contract per
// SCALE_DOLLARS_PER_CONTRACT of balance is the target. The cap FALLS to the target at once when the balance falls, and RISES at most one step
// per SCALE_REVIEW_MS (3 days). A loss stop no longer holds the climb (the owner, Oct 23, 2026: "i asked to have that removed"; the add-on hold went on Oct 13, the cap hold was left in by mistake). The loss stop is a fraction of the balance AT THE LAST REVIEW, so size and
// stop move together, every review. L1_SIZE_CEILING is a hard limit in code that no balance can pass. The first review starts at L1_SIZE_MAX
// (3, what the owner was running), or lower if the balance is lower. Pure: the caller keeps the state.
// Raised from 10 to 25 on Oct 9, 2026 with the 2% base, or the ceiling would hold the base near 1% of a $550 account; then to 40 at the owner's request, which keeps
// 10 contracts of room under L1_ORDER_CEILING (50) for the profit add-on. 25 was a judgement call, not a measured depth limit; the book recorder's data should say how
// many contracts the touch can fill at 93c before this is raised again.
const L1_SIZE_CEILING = 40;
// The balance-driven cap stops at L1_SIZE_CEILING, but contracts bought with reinvested PROFIT (the add-on) no longer have their own limit (Oct 8, 2026, the owner's
// choice). What bounds them: the pool holds only skimmed profit, one extra contract needs one full contract cost of it, a loss comes out of the pool first, and the
// 1% of cash rule in l1Count still caps every order, so the original capital is never put at more risk than before. L1_ORDER_CEILING is only a fat-finger guard on a
// single order body, far above anything those rules allow; it is not a sizing rule.
const L1_ORDER_CEILING = 50;
// $43 (was $85) so the ladder's target is about 2% of balance at a 93c contract, matching L1_SIZE_FRACTION; at $85 it, not the 2% rule, would have set the base.
const SCALE_DOLLARS_PER_CONTRACT = 43;
// Steps were weekly at first and the owner asked for faster ones (Oct 8, 2026): a review, and at most one step up, every 3 days. Nothing holds the climb after a
// loss stop any more (the profit add-on hold was removed Oct 13, 2026 and the cap hold Oct 23, 2026, both at the owner's request); the 12% loss stop is what bounds a bad run.
const SCALE_REVIEW_MS = 3 * 24 * 3600 * 1000;
const SCALE_STEP = 1;
function scaleTarget(cash) {
  return Number.isFinite(cash) ? Math.max(1, Math.min(L1_SIZE_CEILING, Math.floor(cash / SCALE_DOLLARS_PER_CONTRACT + 1e-9))) : 1;
}
// A balance that is LOW is not the same as one that LOST money: cash locked in an open position (the bot's own orders for 15 minutes, or a manual trade of any
// size) leaves the balance for as long as it is open. On Oct 8, 2026 a manual trade of the whole account left the balance near $0, "falls at once" read that as a
// real drop, and it cut the cap to 1 and the stop's base to 40c, which the 3 day steps then needed about 12 days to climb back from. So a fall now has to HOLD:
// the cap is cut only when the target has stayed below it for SCALE_FALL_CONFIRM_MS. Real losses are still bounded in the meantime by the loss stop (which keeps
// its old base while waiting), and money that was only locked comes back inside the window and clears the wait.
const SCALE_FALL_CONFIRM_MS = 2 * 3600 * 1000;
// Starting a session with scaling on sets state.reseed. The next review then raises the cap to the balance's target (never lowers it) and re-bases the stop on the current balance, so an owner who restarts after a collapse is not stuck waiting out the slow steps.
function reviewSizing(state, cash, now) {
  const target = scaleTarget(cash);
  if (!state || !Number.isInteger(state.cap) || !Number.isFinite(state.reviewedAt) || !Number.isFinite(state.base)) {
    return { state: { ...(state || {}), cap: Math.min(L1_SIZE_MAX, target), base: cash, reviewedAt: now, lastStopAt: state && Number.isFinite(state.lastStopAt) ? state.lastStopAt : null, reseed: false, lowSince: null }, changed: true };
  }
  let { cap, base, reviewedAt } = state;
  let lowSince = Number.isFinite(state.lowSince) ? state.lowSince : null;
  const lastStopAt = Number.isFinite(state.lastStopAt) ? state.lastStopAt : null;
  if (state.reseed === true) {
    cap = Math.max(cap, target);   // Start is the owner's deliberate act, so it goes straight to the target instead of the slow steps
    base = cash; reviewedAt = now; lowSince = null;
    cap = Math.max(1, Math.min(cap, L1_SIZE_CEILING));
    return { state: { ...state, cap, base, reviewedAt, lastStopAt, reseed: false, lowSince }, changed: true };
  }
  if (target < cap) {
    if (lowSince === null) lowSince = now;
    else if (now - lowSince >= SCALE_FALL_CONFIRM_MS) { cap = target; base = cash; lowSince = null; }
  } else {
    lowSince = null;
    if (now - reviewedAt >= SCALE_REVIEW_MS) {
      base = cash; reviewedAt = now;
      if (target > cap) cap = Math.min(cap + SCALE_STEP, target);
    }
  }
  cap = Math.max(1, Math.min(cap, L1_SIZE_CEILING));
  return { state: { ...state, cap, base, reviewedAt, lastStopAt, lowSince }, changed: cap !== state.cap || base !== state.base || reviewedAt !== state.reviewedAt || lowSince !== (Number.isFinite(state.lowSince) ? state.lowSince : null) };
}
const L1_LOSS_STOP = 10.0;                 // dollars the bot's own trades may be down (open ones counted as lost); was $7 until Oct 8, 2026

// The side whose FRESH price is inside the band, or null. YES is bought at its ask; NO at 1 minus the YES bid. Kalshi
// prices run in tenths of a cent mid-book, so the limit sent is rounded in the direction that can only cross (YES up to
// the next cent, NO down to the cent) and the worst price actually paid is bounded by it. The band is judged on the real
// price, not the rounded one.
function l1Pick(m) {
  const bid = num(m.yes_bid_dollars), ask = num(m.yes_ask_dollars);
  if (!bot.validQuote(Number.isFinite(bid) ? bid : null, Number.isFinite(ask) ? ask : null)) return null;
  const lo = L1_BAND[0] - 1e-9, hi = L1_BAND[1] + 1e-9;
  const r4 = (x) => Math.round(x * 10000) / 10000;
  if (r4(ask) >= lo && r4(ask) <= hi) {
    const limit = Math.ceil(r4(ask) * 100 - 1e-9) / 100;
    return { side: "yes", price: r4(ask), limit, worst: limit };
  }
  const noPrice = r4(1 - bid);
  if (noPrice >= lo && noPrice <= hi) {
    const limit = Math.floor(r4(bid) * 100 + 1e-9) / 100;
    return { side: "no", price: noPrice, limit, worst: r4(1 - limit) };
  }
  return null;
}

// The touch and the size resting on it, read off the market the order was decided on. Field names are Kalshi's; any
// that are absent come back null instead of a guess.
function bookSeen(m) {
  const n = (v) => { const x = num(v); return Number.isFinite(x) ? x : null; };
  return { bid: n(m.yes_bid_dollars), ask: n(m.yes_ask_dollars), bidSize: n(m.yes_bid_size_fp), askSize: n(m.yes_ask_size_fp), at: new Date().toISOString() };
}

const totalCash = (balanceBody) => {
  const b = balanceBody && typeof balanceBody === "object" ? balanceBody : {};
  if (Array.isArray(b.balance_breakdown) && b.balance_breakdown.length) {
    const rows = b.balance_breakdown.map((r) => num(r.balance));
    return rows.every(Number.isFinite) ? rows.reduce((a, x) => a + x, 0) : NaN;
  }
  const cents = num(b.balance);
  return Number.isFinite(cents) ? cents / 100 : NaN;
};

// What one filled order made once its market settled, by the one rule used everywhere: the order's worst-case cost (maxCost) is paid in
// proportion to what filled, and each winning contract pays $1. A win is therefore booked slightly low and a loss slightly high.
// An order the exit watch sold some or all of (exitCount contracts, exitProceeds dollars after the exit fee) pays $1 only on the contracts still held at the close, and the
// proceeds of the sale are added. An order with no exit has exitCount 0 and is computed exactly as before.
function settledFields(t, result) {
  const cost = Number(t.maxCost);
  const want0 = Number(t.count) > 0 ? Number(t.count) : 1, got0 = Math.min(Number(t.fillCount), want0);
  const sold = Number(t.exitCount) > 0 ? Math.min(Number(t.exitCount), got0) : 0;
  const proceeds = sold > 0 && Number.isFinite(Number(t.exitProceeds)) ? Number(t.exitProceeds) : 0;
  return { settled: true, result, settledPnl: Number((((result === t.side ? got0 - sold : 0)) + proceeds - cost * (got0 / want0)).toFixed(4)) };
}

// A position the owner closed BY HAND (a manual sell, or Flatten) is not a trade the bot held to the end, but the market's result is all settledFields has to go on, so it booked a win or a loss
// the owner never got: into the stats, the loss stop and the profit pool. This asks the account. The order is "closed by hand" only when the account's sell fills on its market and side, made
// after the order and NOT by the bot's own exit order, cover everything the bot still held (a partly sold position is left to the old rule, which books the rest as held: counted, not hidden,
// because hiding the rest of a loss from the loss stop is the unsafe direction). The exit watch's own "skipped" (it found nothing held when the price touched its line) says the same thing
// without a read. Anything that cannot be read is `unknown`: the order stays open, which the loss stop counts as lost, until the next look. Never places or changes an order.
async function closedByHand({ fetchFn, keyId, pem, t, nowMs }) {
  // Oct 21, 2026: this used to treat the exit watch's "skipped" as proof of a hand sale and to read the bot's OWN entry fill as a sale. Kalshi's order API books everything on the YES side
  // (a NO buy is sent as side "ask"), so the fill for a NO buy can read as action "sell", side "no": every NO order the bot bought looked like a position the owner sold, and was left out of
  // the stats, the loss stop and the pool, losses included. Now: without the entry order's id the entry cannot be told from a sale, so the order is NOT called hand (a loss stays counted, the
  // safe direction); the entry's own fill is never a sale; and "skipped" alone is no evidence (the position can simply have settled before the exit watch looked).
  if (!t.orderId) return { hand: false, sold: 0 };
  const r = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/fills", params: { ticker: t.ticker, limit: "100" }, nowMs });
  if (r.status !== 200 || !r.body || !Array.isArray(r.body.fills)) return { unknown: true };
  const want = Number(t.count) > 0 ? Number(t.count) : 1, got = Math.min(Number(t.fillCount), want);
  const botSold = Number(t.exitCount) > 0 ? Math.min(Number(t.exitCount), got) : 0;
  let sold = 0;
  for (const f of r.body.fills) {
    if (!f || (f.ticker || f.market_ticker) !== t.ticker || f.action !== "sell" || f.side !== t.side) continue;
    if (t.exitOrderId && f.order_id === t.exitOrderId) continue;
    if (f.order_id === t.orderId) continue;                // the bot's own entry, whatever Kalshi calls it
    const at = Date.parse(f.created_time);
    if (Number.isFinite(at) && Number.isFinite(Number(t.ts)) && at < Number(t.ts) - 5000) continue;
    const c = num(f.count_fp !== undefined ? f.count_fp : f.count);
    if (Number.isFinite(c) && c > 0) sold += c;
  }
  return sold > 0 && sold + 1e-9 >= got - botSold ? { hand: true, sold } : { hand: false, sold };
}
// What the order document records for a position closed by hand: settled (so nothing waits on it or counts it open), no profit figure (so no stat, stop or pool can use one), and a result the
// page reads as "sold by hand".
function handFields(h) { return Object.assign({ settled: true, result: "hand" }, Number.isFinite(h.sold) ? { handSold: h.sold } : {}); }

// Settles filled orders whose market has finished, whether or not a session is running. The session's own check stops when the session ends, so a
// trade that settled after a stop (or just after the 24 hours) stayed "open" in the records for ever and never reached the page's loss and win
// counts. Called every minute by the scheduled function; reads at most `max` public markets, never places or changes an order, and a failed read
// leaves the order open for the next minute.
async function settleOpenOrders({ store, fetchFn, nowMs, max = 12, keyId, pem, repair = true }) {
  const open = (await store.openFilled()).filter((t) => t.settled !== true && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)) && t.ticker && (t.side === "yes" || t.side === "no"));
  let settled = 0;
  for (const t of open.slice(0, max)) {
    const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs });
    const r = mk.status === 200 && mk.body && mk.body.market ? mk.body.market.result : null;
    if (r !== "yes" && r !== "no") continue;
    // With the account's key, ask whether the owner closed it by hand first (see closedByHand). Without a key (older callers) the old rule applies.
    const h = keyId && pem ? await closedByHand({ fetchFn, keyId, pem, t, nowMs }) : { hand: false };
    if (h.unknown) continue;
    await store.updateTest(t.id, h.hand ? handFields(h) : settledFields(t, r));
    settled += 1;
  }
  // Repair (Oct 21, 2026): orders the old check wrongly marked "hand" (every NO order, see closedByHand) are asked again with the fixed check, and the ones that were never sold by hand are settled as the
  // win or loss they were, so the stats, the loss stop and the pool see them. A genuine hand sale stays hand and is marked checked so it is not asked again. Reads only, like the rest of this sweep.
  let repaired = 0;
  if (repair && keyId && pem && typeof store.handOrders === "function") {
    const flagged = (await store.handOrders()).filter((t) => t.result === "hand" && t.handChecked !== true && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)) && t.ticker && (t.side === "yes" || t.side === "no"));
    for (const t of flagged.slice(0, max)) {
      const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs });
      const r = mk.status === 200 && mk.body && mk.body.market ? mk.body.market.result : null;
      if (r !== "yes" && r !== "no") continue;
      const h = await closedByHand({ fetchFn, keyId, pem, t, nowMs });
      if (h.unknown) continue;
      await store.updateTest(t.id, h.hand ? { handChecked: true } : Object.assign(settledFields(t, r), { handChecked: true, handRepaired: true }));
      if (!h.hand) repaired += 1;
    }
  }
  return { settled, repaired, looked: Math.min(open.length, max) };
}

// What the bot's own filled trades in this session have done. A settled trade is read once from the public market and
// kept on its record; a trade not yet settled is counted at its full cost, as if it lost. Costs are the order's worst-case
// price plus fee (maxCost), so a win is booked slightly low and a loss slightly high: the error is on the safe side.
// `orders` is a list the caller has already read (the tick reads the last 24 hours once and shares it, so the same documents are not billed twice a minute); without it the store is asked.
async function botRisk({ store, since, fetchFn, nowMs, orders, keyId, pem }) {
  const from = Number.isFinite(since) ? since : 0;
  const read = Array.isArray(orders) ? orders.filter((t) => Number(t.ts) >= from) : await store.sessionTrades(from);
  const trades = read.filter((t) => t.strategy === "L1" && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)));
  let net = 0, openCost = 0, addonAtRisk = 0;
  for (const t of trades) {
    const cost = Number(t.maxCost);
    let result = t.settled === true ? t.result : null;
    if (t.settled !== true) {
      const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs });
      const r = mk.status === 200 && mk.body && mk.body.market ? mk.body.market.result : null;
      if (r === "yes" || r === "no") {
        const h = keyId && pem ? await closedByHand({ fetchFn, keyId, pem, t, nowMs }) : { hand: false };
        if (h.hand) { await store.updateTest(t.id, handFields(h)); continue; }     // closed by hand: not the bot's result, so not in its net, its stop or its open cost
        if (!h.unknown) { result = r; await store.updateTest(t.id, settledFields(t, r)); }     // unreadable: stays open and counted as lost until the next look
      }
    }
    if (t.settled === true && t.result === "hand") continue;
    // A partial fill costs and pays in proportion; orders from before size scaling have count 1.
    const want = Number(t.count) > 0 ? Number(t.count) : 1, got = Math.min(Number(t.fillCount), want), paid = cost * (got / want);
    const addonPaid = Number.isFinite(Number(t.addonCost)) && Number(t.addonCost) > 0 ? Number(t.addonCost) * (got / want) : 0;
    // Sold early by the exit watch (completely): the realised figure on the record is the result, and a loss burned its share of the profit-funded add-on.
    if (t.settled === true && t.result === "exit") {
      const pnl = Number(t.settledPnl);
      net += Number.isFinite(pnl) ? pnl : -paid;
      if (!Number.isFinite(pnl) || pnl < 0) addonAtRisk += paid > 0 ? (Number.isFinite(pnl) ? -pnl : paid) * (addonPaid / paid) : 0;
      continue;
    }
    const sold = Number(t.exitCount) > 0 ? Math.min(Number(t.exitCount), got) : 0, soldShare = got > 0 ? sold / got : 0;
    const proceeds = sold > 0 && Number.isFinite(Number(t.exitProceeds)) ? Number(t.exitProceeds) : 0;
    if (result === "yes" || result === "no") {
      net += (result === t.side ? got - sold : 0) + proceeds - paid;
      if (result !== t.side) addonAtRisk += addonPaid;   // only a LOST order burned the profit that bought its add-on
    } else { net += proceeds - paid * soldShare; openCost += paid * (1 - soldShare); addonAtRisk += addonPaid * (1 - soldShare); }   // an open order is counted as lost, so its add-on is too
  }
  return { net, openCost, worst: net - openCost, addonAtRisk, trades: trades.length };
}

// Profit reinvestment with a skim (the owner's idea, Oct 8, 2026). Only NEW net profit is split: the cumulative settled result since the state began
// has a high-water mark, and when it rises to a new high, SKIM_REINVEST of the rise goes to a pool that buys extra contracts on later orders (one per full contract cost
// in the pool, no fixed limit, outside the 2% of cash rule) and the rest is set aside as savings. The weekly review does NOT count
// savings as balance, so skimmed money is never sized up on a second time. Skimming each win separately was tried first and is wrong: wins here are
// 6c and losses 90c, so half of every WIN banks far more than the net profit and the base shrinks underneath it (in a replay, savings of $150 on a net
// of -$6). A win that only recovers an earlier drop skims nothing. A loss comes out of the pool first (never below zero); a loss stop empties the
// pool (extras come back as wins refill it; there is no hold on them since Oct 13, 2026). Orders are folded in once, in time order, behind a cursor that only moves past a run of orders that have
// all settled, so an older order settling late is never skipped and nothing is counted twice. Orders from before the state existed are history. Pure.
const SKIM_REINVEST = 0.5;
// opts.everyWin (the owner's choice, Oct 10, 2026; fixed on, with no setting, on Oct 12, 2026: runL1Tick always passes true): the pool rebuilds from half of EVERY win and loses every loss, so after a loss it starts filling at once instead of waiting
// to get back above the old high. The original "new highs" rule stays here only as the default of this pure function, the baseline its replay tests and the README table compare against. Savings are untouched: they still take half of a NEW high only. Why not the literal "restart the high-water mark on every loss": that makes half of every win
// a saving, savings never absorb a loss, so the sizing balance (cash minus savings) shrinks while the account is flat; replayed on 69 days it more than halved the 90 day gain. Rebuilding only the pool
// (a bookkeeping allowance, not segregated money) kept the profit and raised it about 47%, at about 60% deeper drawdowns: README, "Pool rebuilds after every win".
function foldSkim(state, orders, opts = {}) {
  let pool = Number.isFinite(state.pool) ? state.pool : 0, saved = Number.isFinite(state.saved) ? state.saved : 0;
  let cum = Number.isFinite(state.cum) ? state.cum : 0, hwm = Number.isFinite(state.hwm) ? state.hwm : 0;
  let cursor = Number.isFinite(state.appliedTs) ? state.appliedTs : (Number.isFinite(state.reviewedAt) ? state.reviewedAt : 0);
  const rows = (orders || []).filter((t) => t.strategy === "L1" && Number(t.fillCount) > 0 && Number.isFinite(Number(t.maxCost)) && Number.isFinite(t.ts) && t.ts > cursor)
    .sort((a, b) => a.ts - b.ts || String(a.id).localeCompare(String(b.id)));
  let blocked = null;   // the first order the cursor could not pass (not settled yet), so a pool that does not move can say why
  for (const t of rows) {
    if (t.settled === true && t.result === "hand") { cursor = t.ts; continue; }     // closed by hand: not the bot's trade, passed without a profit or a loss
    if (t.settled !== true || !Number.isFinite(Number(t.settledPnl))) { blocked = { ticker: t.ticker || null, ts: t.ts }; break; }
    const pnl = Number(t.settledPnl);
    cum += pnl;
    if (opts.everyWin === true) {
      if (cum > hwm) { const rise = cum - hwm; hwm = cum; saved += (1 - SKIM_REINVEST) * rise; }
      if (pnl > 0) pool += SKIM_REINVEST * pnl;
      else if (pnl < 0) pool = Math.max(0, pool + pnl);
    } else if (cum > hwm) { const rise = cum - hwm; hwm = cum; pool += SKIM_REINVEST * rise; saved += (1 - SKIM_REINVEST) * rise; }
    else if (pnl < 0) pool = Math.max(0, pool + pnl);
    cursor = t.ts;
  }
  const r4 = (x) => Number(x.toFixed(4));
  pool = r4(pool); saved = r4(saved); cum = r4(cum); hwm = r4(hwm);
  return { pool, saved, cum, hwm, appliedTs: cursor, blocked, changed: pool !== state.pool || saved !== state.saved || cum !== state.cum || hwm !== state.hwm || cursor !== state.appliedTs };
}
// No pause after a loss stop (the owner's rule, Oct 13, 2026: the profit add-on must keep sizing up). A stop already empties the pool, so extras only come back as wins
// refill it, one per full contract cost; the week-long hold now applies to the base size's steps up (reviewSizing) only. `now` is kept so callers do not change.
function skimAddon(state, now, perContract = 0.93) {
  return Math.max(0, Math.floor((Number.isFinite(state.pool) ? state.pool : 0) / perContract + 1e-9));
}

// One minute of the session. session = {active, startCash, ordersSent}; setSession merges fields into it.
// Every refusal before an order leaves the session running; the session ends (and stays ended until the owner starts
// another) on the loss stop, an unresolved order, and any order whose answer was lost or refused.
// A window is the 15 minutes a market closes in, shared by every series: the part of the ticker after the series name (KXBTC15M-26OCT101200-00 gives 26OCT101200).
// Raised from 4.5% to 5.5% at the owner's request (Oct 20, 2026), after Dogecoin, last in the list, got 1 contract while XRP got 4. The loss stop (L1_SIZED_STOP_FRACTION) was raised with it, from 5% to 6%,
// so the window limit still sits UNDER the stop and one window alone cannot reach it.
const L1_WINDOW_CAP_FRACTION = 0.055;
function windowKey(ticker) { const p = String(ticker || "").split("-"); return p.length >= 2 ? p[1] : String(ticker || ""); }

// The probe drop rule (DL1, the research session, Oct 21, 2026; the owner: "do it"). A probe market (PROBE_SERIES) is dropped when its last PROBE_DROP_WINDOW settled entries net negative.
// It is an ADMISSION filter for markets that have not earned a place, NOT a short-term brake: on the five live series the same rule would have hurt, because they bounce after a bad stretch, so it is
// never applied to them. It only ever REMOVES a series from what the tick may trade, never adds one, and a dropped probe stays dropped (no new entries arrive to change its record), so putting one
// back is a deliberate code edit or deleting the record by hand, never something the page can do. Fails closed: if the record cannot be read or saved, no probe trades that minute.
// The record is built from the 24 hours of orders the tick already reads (no extra order reads) and holds only settled, finite results of the bot's own entries; orders closed by hand are not the
// bot's result and are left out, as everywhere else. Entries from before the record existed are not in it, so the rule cannot fire until the record itself holds PROBE_DROP_WINDOW entries.
const PROBE_DROP_WINDOW = 200;
function probeRingUpdate(record, orders, now) {
  const cur = record && typeof record === "object" ? record : {};
  const rings = {};
  for (const sr of PROBE_SERIES) rings[sr] = Array.isArray(cur.rings && cur.rings[sr]) ? cur.rings[sr].filter((e) => e && typeof e.id === "string" && Number.isFinite(e.pnl) && Number.isFinite(e.ts)) : [];
  let changed = false;
  for (const sr of PROBE_SERIES) {
    const have = new Set(rings[sr].map((e) => e.id));
    const seen = new Set();
    const fresh = (orders || []).filter((t) => t && t.id && t.series === sr && t.strategy === "L1" && t.settled === true && t.result !== "hand" && Number(t.fillCount) > 0
      && Number.isFinite(Number(t.settledPnl)) && Number.isFinite(Number(t.ts)) && !have.has(t.id) && !seen.has(t.id) && seen.add(t.id));
    if (!fresh.length) continue;
    changed = true;
    rings[sr] = rings[sr].concat(fresh.map((t) => ({ id: t.id, ts: Number(t.ts), pnl: Number(t.settledPnl) }))).sort((a, b) => a.ts - b.ts).slice(-PROBE_DROP_WINDOW);
  }
  const droppedAt = Object.assign({}, cur.droppedAt), newlyDropped = [];
  for (const sr of PROBE_SERIES) if (probeNet(rings[sr]) !== null && probeNet(rings[sr]) < 0 && !Number.isFinite(droppedAt[sr])) { droppedAt[sr] = now; newlyDropped.push(sr); changed = true; }
  return { record: { rings, droppedAt }, changed, newlyDropped };
}
// The net of a probe's record, or null while it holds fewer than PROBE_DROP_WINDOW entries (too few to judge: never dropped on a short record).
function probeNet(ring) { return Array.isArray(ring) && ring.length >= PROBE_DROP_WINDOW ? Number(ring.reduce((a, e) => a + e.pnl, 0).toFixed(4)) : null; }
// Dropped once the record said so and it still does (a stored drop alone is enough: the record cannot gain entries without trading).
function probeDropped(record, series) { return Boolean(record && record.droppedAt && Number.isFinite(record.droppedAt[series])); }

async function runL1Tick(args) {
  const { session, now, setSession, enabled, active, store, keyId, pem, fetchFn, quotes } = args;
  const log = async (kind, detail) => { if (args.logEvent) { try { await args.logEvent({ ts: now, kind, detail }); } catch (e) { /* the log is optional */ } } };
  if (!session || session.active !== true) return { skipped: "no session" };
  const end = async (why, detail) => { await setSession({ active: false, endedAt: now, endedBecause: why }); await log("session ended", detail); return { ended: why }; };
  const note = async (text, extra) => { await setSession(Object.assign({ lastTickAt: now, lastNote: String(text).slice(0, 300) }, extra || {})); };
  if (enabled !== true) { await note("The server switch is off (KALSHI_LIVE_ENABLED), so nothing is sent."); return { skipped: "switch off" }; }
  if (!active) { await note("The exchange is not trading right now."); return { skipped: "exchange inactive" }; }
  if (await store.halted()) { await note("The bot is halted, so nothing is sent."); return { skipped: "halted" }; }
  if (await store.hasUnresolved()) return end("attempted", "an earlier order is unresolved (sent, or its answer was lost). Check the Kalshi account before starting again");
  const sent = session.ordersSent || 0;
  // Orders in the last 24 hours, whether or not they filled. Fails closed: if they cannot be counted, nothing is sent this minute.
  const dayStart = now - L1_WINDOW_DAY_MS;
  let recentOrders, recentList;
  try { recentList = (await (typeof store.sessionTradesCached === "function" ? store.sessionTradesCached(dayStart, now) : store.sessionTrades(dayStart))).filter((t) => t.strategy === "L1"); recentOrders = recentList.length; }
  catch (e) { await note("The bot's recent orders could not be counted, so nothing was sent."); return { skipped: "orders unreadable" }; }
  if (recentOrders >= L1_MAX_ORDERS) { await note("The limit of " + L1_MAX_ORDERS + " orders in 24 hours has been reached. It carries on by itself once older orders drop out."); return { skipped: "order limit" }; }

  const bal = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/balance", nowMs: now });
  if (bal.status !== 200) { await note("The balance could not be read (HTTP " + bal.status + "), so nothing was sent."); return { skipped: "balance unreadable" }; }
  const cash = totalCash(bal.body);
  if (!Number.isFinite(cash)) { await note("The balance came back in a shape this code does not recognise, so nothing was sent."); return { skipped: "balance unrecognised" }; }
  let startCash = session.startCash;
  if (!Number.isFinite(startCash)) { startCash = cash; await setSession({ startCash }); }
  // The stop follows the BOT's trades, not the account: the owner trades the same account by hand, and a manual trade must
  // neither trip the stop nor hide a bot loss. Fails closed: if the bot's trades cannot be read, nothing is sent this minute.
  let risk;
  try { risk = await botRisk({ store, since: Number.isFinite(session.since) ? Math.max(session.since, dayStart) : dayStart, fetchFn, nowMs: now, orders: recentList, keyId, pem }); }
  catch (e) { await note("The bot's own trades could not be read, so nothing was sent."); return { skipped: "bot trades unreadable" }; }
  const sizing = session.sizing === true;
  // With scaling on, the cap and the stop's base come from the weekly review. Fails closed: a review that cannot be saved sends nothing this minute.
  let sizeCap = L1_SIZE_MAX, sizeBase = startCash, sizeState = null, sizeAddon = 0;
  if (sizing) {
    // The weekly review sees the balance WITHOUT what has been skimmed to savings, so saved profit is never sized up on.
    const priorSaved = args.sizingState && Number.isFinite(args.sizingState.saved) ? args.sizingState.saved : 0;
    const rv = reviewSizing(args.sizingState, Math.max(0, cash - priorSaved), now);
    // The pool always rebuilds after every win. Nothing stored on the session document can change that (the owner removed the switch, Oct 12, 2026).
    const fs = foldSkim(rv.state, recentList, { everyWin: true });
    sizeState = { ...rv.state, pool: fs.pool, saved: fs.saved, cum: fs.cum, hwm: fs.hwm, appliedTs: fs.appliedTs };
    sizeCap = sizeState.cap; sizeBase = sizeState.base; sizeAddon = skimAddon(sizeState, now);
    if ((rv.changed || fs.changed) && args.setSizingState) {
      try { await args.setSizingState(sizeState); } catch (e) { await note("The size review could not be saved, so nothing was sent."); return { skipped: "size review unsaved" }; }
    }
    await setSession({ sizeCap, sizeAddon, sizePool: sizeState.pool, sizePoolRule: "wins", sizePoolThrough: sizeState.appliedTs, sizePoolBlocked: fs.blocked ? fs.blocked.ticker : null, sizeSaved: sizeState.saved, sizeBase: Number(sizeBase.toFixed(2)), sizeNextReview: rv.state.reviewedAt + SCALE_REVIEW_MS });
  }
  const stopAt = sizing ? L1_SIZED_STOP_FRACTION * sizeBase : L1_LOSS_STOP;
  // Optional high-point stop (chosen when the session starts): the stop is measured from the best SETTLED result the session has reached, so gains
  // are protected too. The peak only ever rises, is never below zero, and is kept on the session so a restart of the function cannot lose it.
  const trailing = session.trailing === true;
  let peak = 0;
  if (trailing) {
    // A peak from before the window describes trades that no longer count, so it is not carried over.
    const fresh = Number.isFinite(session.peakAt) && session.peakAt > dayStart;
    peak = Math.max(0, fresh && Number.isFinite(session.peakNet) ? session.peakNet : 0, risk.net);
    if (!(fresh && Number.isFinite(session.peakNet) && session.peakNet >= peak)) await setSession({ peakNet: Number(peak.toFixed(4)), peakAt: now });
  }
  // The stop protects the ACCOUNT, not the profit already made: the part of a lost or open order that was bought with reinvested profit (the add-on) does not count
  // toward it. Without this a big enough add-on would make one loss, or even one open order counted as lost, reach the stop on its own and lock the bot out
  // (the owner's rule, Oct 9, 2026). The account's own share of the loss is still held to the same 6% of the balance at the last review.
  const allowance = Number.isFinite(risk.addonAtRisk) ? risk.addonAtRisk : 0;
  const floor = peak - (stopAt + allowance);
  if (risk.worst <= floor + 1e-9) {
    if (sizeState && args.setSizingState) { try { await args.setSizingState({ ...sizeState, lastStopAt: now, pool: 0 }); } catch (e) { /* the stop still ends the session */ } }
    return end("loss stop", trailing
      ? "the bot's trades are down $" + (peak - risk.worst).toFixed(2) + " from their best (+$" + peak.toFixed(2) + ", now " + (risk.net >= 0 ? "+" : "-") + "$" + Math.abs(risk.net).toFixed(2) + " settled with $" + risk.openCost.toFixed(2) + " open counted as lost), which reaches the $" + stopAt.toFixed(2) + " give-back stop"
      : "the bot's trades are down $" + (-risk.net).toFixed(2) + " settled with $" + risk.openCost.toFixed(2) + " still open, counted as lost, which reaches the $" + (stopAt + allowance).toFixed(2) + " stop" + (allowance > 0 ? " ($" + stopAt.toFixed(2) + " plus $" + allowance.toFixed(2) + " of reinvested profit that was at risk)" : ""));
  }

  // Probe drop rule (see PROBE_DROP_WINDOW). Only probes can be removed. A record that cannot be read or saved removes ALL probes this minute; the other series trade as usual.
  let dropped = [];
  if (typeof args.updateProbeRecord === "function") {
    try {
      let newly = [];
      const rec = await args.updateProbeRecord((cur) => { const u = probeRingUpdate(cur, recentList, now); newly = u.newlyDropped; return u; });
      for (const sr of PROBE_SERIES) if (probeDropped(rec, sr)) dropped.push(sr);
      for (const sr of newly) await log("probe dropped", sr + " is dropped: its last " + PROBE_DROP_WINDOW + " settled entries net $" + probeNet(rec.rings && rec.rings[sr]) + ". It stays off until the record is reset by hand.");
    } catch (e) { dropped = PROBE_SERIES.slice(); }
  }
  const tradable = L1_SERIES.filter((x) => !dropped.includes(x));
  // In list order (Bitcoin, gold, Ethereum): when the window's room runs short it is the later series that goes without.
  const candidates = (quotes || []).filter((q) => tradable.includes(q.series) && ["active", "open"].includes(q.m.status)
    && entryLead(q.series, Date.parse(q.m.close_time) - now) !== null)
    .sort((x, y) => L1_SERIES.indexOf(x.series) - L1_SERIES.indexOf(y.series));
  if (!candidates.length) {
    // When the next entry window opens, so the page can say so: a market closing in 3 minutes is past its window and the next one is not yet in it.
    const opens = (quotes || []).filter((q) => tradable.includes(q.series) && ["active", "open"].includes(q.m.status))
      .map((q) => Date.parse(q.m.close_time) - (EARLY_PROBE_SERIES.includes(q.series) ? EARLY_WINDOW_MS[1] : L1_WINDOW_MS[1])).filter((t) => t > now);
    await note("Watching. Orders go in about 6 minutes before a close (10 for Bitcoin, XRP and natural gas), and no market is at that point right now.", { cash, botNet: Number(risk.net.toFixed(2)), botOpen: Number(risk.openCost.toFixed(2)), nextLookAt: opens.length ? Math.min(...opens) : null });
    return { skipped: "no market in the window" };
  }

  const results = [];
  const riseLog = [];   // every order of this minute, to log the 3 minute rise on after all of them are sent
  let ordersSent = sent;
  // Bitcoin and gold close together and share a shard, and the balance above is read once. Money already committed to an
  // order earlier in this same tick is taken off what the next market on that shard may use.
  const committed = {};
  const cryptoTaken = {};   // windows where a crypto order is already placed THIS tick (the store does not hold it yet)
  const windowSpent = {};   // account money put into each window earlier in THIS tick (the store does not hold it yet)
  for (const c of candidates) {
    if (recentOrders + (ordersSent - sent) >= L1_MAX_ORDERS) { results.push("order limit reached"); break; }   // the limit also holds inside one tick
    const ticker = c.m.ticker;
    const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(ticker) });
    const m = mk.status === 200 && mk.body && mk.body.market;
    if (!m) { results.push(ticker + ": could not read the market (HTTP " + mk.status + ")"); continue; }
    const left = Date.parse(m.close_time) - now;
    const lead = entryLead(c.series, left);
    if (!["active", "open"].includes(m.status) || !lead) { results.push(ticker + ": not open in its entry window"); continue; }
    const pick = l1Pick(m);
    if (!pick) { results.push(ticker + ": no side is priced 88c to 97c"); continue; }
    // Bitcoin and Ethereum only on a smooth climb (see SMOOTH_SERIES). Read after the band check so the candles are only fetched for a market that would otherwise be bought.
    if (SMOOTH_SERIES.includes(c.series)) {
      const sg = await smoothGate({ fetchFn, series: c.series, ticker, side: pick.side, nowMs: now });
      if (!sg.ok) { results.push(ticker + ": " + sg.reason); continue; }
    }
    const cost1 = pick.worst + bot.takerFee(pick.worst, 1);
    if (cost1 > LIVE_CAP + 1e-9) { results.push(ticker + ": would cost $" + cost1.toFixed(2) + ", above the cap"); continue; }
    // The cash the size is judged on is what is left after this tick's earlier orders, so two markets cannot both take the full share.
    const cashLeft = cash - Object.values(committed).reduce((a, x) => a + x, 0);
    let count = sizing ? l1Count(cashLeft, cost1, sizeCap, sizeAddon) : 1;
    // How many of these contracts were bought with reinvested profit (the add-on), kept on the order so the loss stop can tell profit money from account money.
    let addonUsed = sizing ? Math.max(0, count - l1Count(cashLeft, cost1, sizeCap, 0)) : 0;
    // A probe market is one contract, always: no ladder step and no reinvested profit goes into a market that has not earned it.
    if (PROBE_SERIES.includes(c.series) || CAPPED_SERIES.includes(c.series)) { count = sizing && FIXED_CONTRACTS[c.series] ? FIXED_CONTRACTS[c.series] : 1; addonUsed = 0; }
    // The combined cap: these markets close together and move together, so what one window may put at risk is held to one number across
    // all of them. Only the account's own money counts (the add-on is profit, which the loss stop already treats separately), and orders
    // from earlier ticks in the same window count too. The loss stop is 12% of the base and a window may use 5.5% (6% and 5.5% from Oct 20, 2026, the stop 12% from the same night), so one window alone cannot reach it.
    const wkey = windowKey(ticker);
    // One crypto order per window (Oct 22, 2026, the research session's live diagnosis, the owner's choice): Bitcoin, Ethereum, XRP and Dogecoin
    // flip together, and 72% of the recent loss dollars came from three windows where two of them lost at once. An order that did not fill
    // does not count, so a missed first order leaves the window open to the next series. Gold and the probes are not part of this rule.
    if (CAPPED_SERIES.includes(c.series)) {
      const held = cryptoTaken[wkey] || recentList.some((t) => windowKey(t.ticker) === wkey && CAPPED_SERIES.includes(t.series) && ["filled", "sending", "unknown"].includes(t.status));
      if (held) { results.push(ticker + ": another crypto market already holds this window"); continue; }
    }
    const windowUsed = recentList.filter((t) => windowKey(t.ticker) === wkey && ["filled", "sending", "unknown"].includes(t.status))
      .reduce((a, t) => a + Math.max(0, (Number(t.maxCost) || 0) - (Number(t.addonCost) || 0)), 0) + (windowSpent[wkey] || 0);
    const room = L1_WINDOW_CAP_FRACTION * sizeBase - windowUsed;
    // The first order in a window is never cut to nothing by a tiny base (the single-order size rules already bound it); the cap is for the second and third.
    const allowed = Math.max(windowUsed <= 0 ? 1 : 0, Math.floor(room / cost1 + 1e-9));
    if (sizing && count - addonUsed > allowed) {
      if (allowed + addonUsed < 1) { results.push(ticker + ": this window already has $" + windowUsed.toFixed(2) + " at risk, and the combined limit is $" + (L1_WINDOW_CAP_FRACTION * sizeBase).toFixed(2)); continue; }
      count = allowed + addonUsed;
    }
    const cost = pick.worst * count + bot.takerFee(pick.worst, count);
    const shardKey = String(m.exchange_index);
    const avail = availableFor(bal.body, m.exchange_index) - (committed[shardKey] || 0);
    if (!Number.isFinite(avail)) { results.push(ticker + ": the balance came back in a shape this code does not recognise"); continue; }
    if (avail < cost + BALANCE_MARGIN) { results.push(ticker + ": only $" + avail.toFixed(2) + " on its shard, and money on another shard does not count"); continue; }

    const cid = "L1-" + ticker;
    const record = {
      accountId: DEFAULT_ACCOUNT_ID, ticker, series: c.series, side: pick.side, band: "88-97c", strategy: "L1", entryLead: lead, count, addon: addonUsed, addonCost: Number((cost * addonUsed / count).toFixed(4)), price: pick.price, limit: pick.limit,
      exchangeIndex: m.exchange_index === undefined ? null : m.exchange_index, clientOrderId: cid, status: "sending", ts: now,
      mode: "live", maxCost: Number(cost.toFixed(2)),
      // Written false so the settle sweep can ask for "filled and not settled" and read a handful of documents each minute instead of every order ever filled (a Firestore read is billed).
      settled: false,
      // What the book showed when the order was decided (null where Kalshi did not send a field), so a "no fill" can be
      // explained afterwards: thin size at the touch, or a price that moved away.
      seen: bookSeen(m),
    };
    // Flatten and Stop can land while this tick was reading the balance and the markets (seconds, with timeouts), after the halt was first read. Read it again immediately before the order is recorded and sent.
    if (await store.halted()) { results.push(ticker + ": the bot was halted while this minute ran, so nothing was sent"); continue; }
    if (!(await store.createTest(cid, record))) { results.push(ticker + ": already attempted"); continue; }   // never a second order on a market
    riseLog.push({ cid, series: c.series, ticker, side: pick.side, ask: pick.price, closeSec: Date.parse(m.close_time) / 1000 });
    committed[shardKey] = (committed[shardKey] || 0) + cost;
    if (CAPPED_SERIES.includes(c.series)) cryptoTaken[wkey] = true;
    windowSpent[wkey] = (windowSpent[wkey] || 0) + Math.max(0, cost - (record.addonCost || 0));

    const body = liveOrderBody(ticker, pick.limit, pick.side, cid, m.exchange_index, count);
    const res = await liveRequest({ fetchFn, keyId, pem, method: "POST", path: "/portfolio/events/orders", body, nowMs: Date.now() });
    const d = res.body && typeof res.body === "object" ? res.body : {};
    if (res.status >= 200 && res.status < 300 && d.order_id) {
      const filledCount = Number(d.fill_count || 0);
      await store.updateTest(cid, {
        status: filledCount > 0 ? "filled" : "no fill", orderId: d.order_id, fillCount: String(d.fill_count || "0"),
        remainingCount: String(d.remaining_count || "0"), averageFillPrice: d.average_fill_price || null,
        averageFeePaid: d.average_fee_paid || null, sentSide: body.side, sentPrice: body.price,
      });
      ordersSent += 1;
      await setSession({ ordersSent });
      await log("order", pick.side + " " + count + " at " + (pick.price * 100).toFixed(1) + "c on " + ticker + ": " + (filledCount > 0 ? "filled" : "no fill"));
      results.push(ticker + ": " + (filledCount > 0 ? "filled" : "no fill"));
      continue;
    }
    if (res.status === 409) {
      const found = await findOrder({ fetchFn, keyId, pem, ticker, clientOrderId: cid, nowMs: Date.now() });
      await store.updateTest(cid, found
        ? { status: Number(found.fill_count_fp || 0) > 0 ? "filled" : "no fill", orderId: found.order_id, fillCount: String(found.fill_count_fp || "0"), recovered: true, error409: true }
        : { status: "unknown", error: "HTTP 409 and the order could not be found: " + short(res.body) });
      return end("attempted", "Kalshi says an order with id " + cid + " already exists. Check the Kalshi account for it");
    }
    if (isAmbiguous(res.status)) {
      await store.updateTest(cid, { status: "unknown", error: "HTTP " + res.status + " " + short(res.body) });
      return end("attempted", "the answer for " + ticker + " was lost (HTTP " + res.status + "). THE ORDER MAY OR MAY NOT EXIST. Check the Kalshi account (Portfolio, Orders) before starting again. Nothing was retried");
    }
    await store.updateTest(cid, { status: "error", error: "HTTP " + res.status + " " + short(res.body) });
    return end("attempted", "Kalshi refused the order for " + ticker + ": HTTP " + res.status + " " + short(res.body).slice(0, 80));
  }
  for (const r of riseLog) await logRise({ fetchFn, store, cid: r.cid, series: r.series, ticker: r.ticker, side: r.side, nowMs: now, ask: r.ask, closeSec: r.closeSec });
  await note(results.join("; ") || "Nothing to do.", { cash, botNet: Number(risk.net.toFixed(2)), botOpen: Number(risk.openCost.toFixed(2)) });
  return { ok: true, results };
}

// ---- The exit watch (the owner's decision, Oct 10, 2026; fixed at 50c and always selling, Oct 12, 2026; moved to 25c the same day at the owner's request) -----------------------------------------
// L1 holds every trade to settlement, so a favourite that reverses costs the whole stake. This watches the bot's OWN open L1 positions every few seconds and, when the
// side's bid falls to EXIT_THRESHOLD (25c) or lower, sells them. It began at 70c behind an off / log only / sell switch (README, "Exploratory read ... Friday's loss" and
// "Pre-registration: X8"); the owner removed the switch and moved the line to 50c, then to 25c, on Oct 12, 2026, so there is no mode any more and nothing stored on the session
// document can turn it off. A 25c line is a later, looser stop than 50c or 70c: it stops fewer winners that would have recovered and keeps less of a slide. On a 93c entry a triggered exit now costs about 68c a contract, not 44c, so a stopped trade loses more; it still caps the loss below holding to zero.
// The one thing that makes it record instead of sell is the server's own live switch being off (`enabled`): it then logs when it WOULD have sold (exitShadow on the order) and sends nothing.
// What it will not do, by construction:
//   - touch a position that is not one of the bot's own records (it iterates the bot's order documents, nothing else), or sell more than that order filled;
//   - sell unless the live account actually holds the position (a YES sell on a position that is already gone would OPEN the opposite one);
//   - send the same sell twice (the sell is claimed atomically on the order document and carries a fixed client order id), or retry an answer that was lost;
//   - ever buy: its only order is an immediate-or-cancel close of an existing long.
// A lost answer to a sell ends the bot's session and says so, like a lost answer to a buy.
const EXIT_THRESHOLD = 0.25;
const EXIT_SLIPPAGE = 0.15;          // how far past the bid it saw the immediate-or-cancel sell may go; it still fills at the book's own prices
const EXIT_MAX_TRIES = 3;
const EXIT_LOOKBACK_MS = 25 * 60 * 1000;

// The exit watch loops for most of every minute, and compute time is what a scheduled function is billed for. Most minutes there is nothing for it to watch: no open position, and
// not a minute in which L1 can buy. L1 buys only when 5.5 to 6.7 minutes are left (L1_WINDOW_MS), which is minute 8 or 9 of each quarter hour (markets close on the quarter hour, and the
// epoch starts on one), so the minutes either side are covered too. Idle means ALL of: outside those minutes, and no filled L1 order that is not settled. Anything that cannot be
// read counts as NOT idle: skipping the watch is the unsafe direction, running it for nothing only costs compute.
const EXIT_BUY_MINUTES = (() => {
  const first = Math.floor((900000 - Math.max(L1_WINDOW_MS[1], EARLY_WINDOW_MS[1])) / 60000) - 1, last = Math.floor((900000 - L1_WINDOW_MS[0]) / 60000) + 1;
  const out = []; for (let m = first; m <= last; m++) out.push(m);
  return out;
})();
async function exitWatchIdle({ store, now }) {
  try {
    if (EXIT_BUY_MINUTES.includes(Math.floor(now / 60000) % 15)) return false;
    const recent = await store.recentFilled(now - EXIT_LOOKBACK_MS);
    return !recent.some((t) => t.strategy === "L1" && t.settled !== true && Number(t.fillCount) > 0);
  } catch (e) { return false; }
}

// The exit watch and Flatten both close positions, and each reads the position a moment before it sells. With nothing shared, one could sell between the other's read and its sell, and the second
// sell then goes out on a position that is gone: a YES sell with nothing held OPENS the opposite position, real exposure nobody intended. So both take a short claim on the MARKET first (a document
// per ticker, taken in a transaction) and read the position only after holding it. A claim held by the other closer refuses; the same closer may take it again (the exit watch's own instances are
// kept apart by claimExit on the order). It lapses after CLOSE_CLAIM_MS by itself, so a function that died holding one cannot block the next closer for long. Fails closed: a claim that
// cannot be made means nothing is sold for that market this time, and the caller says so.
const CLOSE_CLAIM_MS = 90 * 1000;
async function claimClose(store, ticker, who, now) {
  try { return !!store && typeof store.claimClose === "function" && (await store.claimClose(ticker, who, now, CLOSE_CLAIM_MS)) === true; } catch (e) { return false; }
}

function exitBody(ticker, side, count, limit, cid, exchangeIndex) {
  if (!Number.isInteger(count) || count < 1 || count > L1_ORDER_CEILING) throw new Error("refusing to build an exit for " + count + " contracts");
  if (!(limit >= 0.01 && limit <= 0.99)) throw new Error("refusing to build an exit at " + limit);
  // Closing a long YES is a YES sell (side "ask"); closing a long NO is a YES buy (side "bid"). The price is the YES price the order may go to.
  const body = {
    ticker, side: side === "yes" ? "ask" : "bid", count: String(count), price: limit.toFixed(2),
    time_in_force: "immediate_or_cancel", self_trade_prevention_type: "taker_at_cross", client_order_id: cid,
  };
  if (exchangeIndex !== undefined && exchangeIndex !== null) body.exchange_index = exchangeIndex;
  return body;
}

async function runExitWatch(args) {
  const { store, fetchFn, keyId, pem, now, enabled, setSession, logEvent, threshold = EXIT_THRESHOLD } = args;
  const log = async (kind, detail) => { if (logEvent) { try { await logEvent({ ts: now, kind, detail }); } catch (e) { /* the log is optional */ } } };
  const selling = enabled === true;
  const r4 = (x) => Math.round(x * 10000) / 10000;
  const list = (await store.recentFilled(now - EXIT_LOOKBACK_MS)).filter((t) => t.strategy === "L1" && t.settled !== true && Number(t.fillCount) > 0
    && Number.isFinite(Number(t.maxCost)) && t.ticker && (t.side === "yes" || t.side === "no") && t.exitStatus !== "sold" && t.exitStatus !== "unknown" && t.exitStatus !== "sending" && t.exitStatus !== "skipped");
  const results = [];
  for (const t of list) {
    const want = Number(t.count) > 0 ? Number(t.count) : 1, got = Math.min(Number(t.fillCount), want);
    const sold = Number(t.exitCount) > 0 ? Number(t.exitCount) : 0;
    const remaining = Math.floor(got - sold + 1e-9);
    if (remaining < 1) continue;
    const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(t.ticker), nowMs: now });
    const m = mk.status === 200 && mk.body && mk.body.market;
    if (!m || !["active", "open"].includes(m.status)) continue;
    const yb = num(m.yes_bid_dollars), ya = num(m.yes_ask_dollars);
    if (!bot.validQuote(Number.isFinite(yb) ? yb : null, Number.isFinite(ya) ? ya : null)) continue;
    const ourBid = t.side === "yes" ? r4(yb) : r4(1 - ya);
    if (!(ourBid > 0) || ourBid > threshold + 1e-9) continue;
    const left = Date.parse(m.close_time) - now;
    if (!selling) {
      if (t.exitShadow) continue;     // logged once per order
      await store.updateTest(t.id, { exitShadow: { at: now, bid: ourBid, left: Number.isFinite(left) ? left : null, wouldSell: remaining } });
      await log("exit (log only)", t.ticker + ": the " + t.side.toUpperCase() + " side's bid fell to " + (ourBid * 100).toFixed(0) + "c with " + (Number.isFinite(left) ? Math.round(left / 1000) + " s" : "unknown time") + " left; it would have sold " + remaining + " contracts. Nothing was sent, because the server's order switch is off.");
      results.push(t.ticker + ": logged");
      continue;
    }
    const tries = Number(t.exitTries) > 0 ? Number(t.exitTries) : 0;
    if (tries >= EXIT_MAX_TRIES) continue;
    // Flatten may be closing this market right now; if it holds the claim, leave it (the position is about to be, or already is, gone).
    if (!(await claimClose(store, t.ticker, "exit", now))) { results.push(t.ticker + ": Flatten is closing it (or the claim could not be made), nothing sold"); continue; }
    // The live account must hold the position, or a sell would open the opposite one.
    const pos = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/positions", params: { ticker: t.ticker, limit: "20" }, nowMs: now });
    let held = NaN;
    if (pos.status === 200 && pos.body && Array.isArray(pos.body.market_positions)) {
      const row = pos.body.market_positions.find((x) => x.ticker === t.ticker);
      held = row ? num(row.position_fp !== undefined ? row.position_fp : row.position) : 0;     // readable and absent: nothing held
    }
    if (!Number.isFinite(held)) { results.push(t.ticker + ": the position could not be read, nothing sold"); continue; }
    const holding = t.side === "yes" ? Math.max(0, held) : Math.max(0, -held);     // YES is a positive position, NO a negative one
    const count = Math.min(remaining, Math.floor(holding + 1e-9));
    if (count < 1) { await store.updateTest(t.id, { exitStatus: "skipped", exitNote: "the account holds no " + t.side.toUpperCase() + " position in it (already closed?)" }); results.push(t.ticker + ": no position held, nothing sold"); continue; }
    if (!(await store.claimExit(t.id, tries))) continue;     // another instance has it
    const limit = t.side === "yes" ? Math.max(0.01, r4(ourBid - EXIT_SLIPPAGE)) : Math.min(0.99, r4(ya + EXIT_SLIPPAGE));
    const cid = "X-" + t.ticker + "-" + (tries + 1);
    const body = exitBody(t.ticker, t.side, count, Math.round(limit * 100) / 100, cid, m.exchange_index);
    const res = await liveRequest({ fetchFn, keyId, pem, method: "POST", path: "/portfolio/events/orders", body, nowMs: Date.now() });
    const d = res.body && typeof res.body === "object" ? res.body : {};
    if (res.status >= 200 && res.status < 300 && d.order_id) {
      const filled = Number(d.fill_count || 0);
      let p = Number(d.average_fill_price);
      if (!Number.isFinite(p) || p <= 0 || p >= 1) p = t.side === "yes" ? ourBid : r4(1 - ourBid);     // a YES price either way; the book price we saw is the fallback
      const soldPrice = t.side === "yes" ? p : r4(1 - p);                    // what each contract fetched on OUR side
      const fee = filled > 0 ? bot.takerFee(soldPrice, filled) : 0;
      const exitCount = sold + filled, exitProceeds = Number(((Number(t.exitProceeds) || 0) + filled * soldPrice - fee).toFixed(4));
      const patch = { exitStatus: filled >= count - 1e-9 ? "sold" : (filled > 0 ? "partly sold" : "no fill"), exitCount, exitProceeds, exitAvg: filled > 0 ? soldPrice : (t.exitAvg || null), exitAt: now, exitBid: ourBid, exitOrderId: d.order_id };
      if (exitCount >= Math.floor(got + 1e-9) - 1e-9 && filled > 0) Object.assign(patch, settledFields({ ...t, exitCount, exitProceeds }, "exit"));
      await store.updateTest(t.id, patch);
      await log("exit", t.ticker + ": " + t.side.toUpperCase() + " bid at " + (ourBid * 100).toFixed(0) + "c, " + patch.exitStatus + " " + filled + " of " + count + (filled > 0 ? " at about " + (soldPrice * 100).toFixed(0) + "c" : ""));
      results.push(t.ticker + ": " + patch.exitStatus);
      continue;
    }
    if (res.status === 409) {
      await store.updateTest(t.id, { exitStatus: "unknown", exitNote: "HTTP 409: an order with id " + cid + " already exists" });
      await log("exit", t.ticker + ": Kalshi says the exit order " + cid + " already exists. Check the Kalshi account for it");
      results.push(t.ticker + ": id already used");
      continue;
    }
    if (isAmbiguous(res.status)) {
      await store.updateTest(t.id, { exitStatus: "unknown", exitNote: "HTTP " + res.status + " " + short(res.body) });
      if (setSession) await setSession({ active: false, endedAt: now, endedBecause: "attempted" });
      await log("session ended", "the answer for the exit sell on " + t.ticker + " was lost (HTTP " + res.status + "). THE SELL MAY OR MAY NOT HAVE HAPPENED. Check the Kalshi account (Portfolio, Orders) before starting again. Nothing was retried");
      return { ended: true, results };
    }
    await store.updateTest(t.id, { exitStatus: "error", exitNote: "HTTP " + res.status + " " + short(res.body), exitTries: tries + 1 });
    await log("exit", t.ticker + ": Kalshi refused the exit sell: HTTP " + res.status + " " + short(res.body).slice(0, 80));
    results.push(t.ticker + ": refused");
  }
  return { ok: true, results };
}

// ---- Flatten: the owner's emergency exit -----------------------------------------------------------------------------------------
// Sells every open position in the account (the bot's AND any the owner opened by hand) at whatever the book will pay, immediately, one
// immediate-or-cancel order each, never retried. A long YES position is closed by a YES sell (side "ask") at the 1c floor, a long NO position by a
// YES buy (side "bid") at the 99c ceiling; the limit only says how far the order may go, each contract fills at the book's own price, so
// this takes the best available bids first and accepts the loss. The count is exactly the position held, so it can close the position and
// never flip it. A market that is no longer open cannot be traded and settles on its own, so it is reported and skipped. The client order
// id carries the minute, so a second press inside the same minute is refused by Kalshi instead of selling twice. Not capped by LIVE_CAP:
// that cap bounds what a BUY may risk, and this only reduces exposure.
async function flattenAll({ fetchFn, keyId, pem, now, store }) {
  const pos = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/positions", params: { limit: "200" }, nowMs: now });
  if (pos.status !== 200 || !pos.body || typeof pos.body !== "object") return { ok: false, reason: "The positions could not be read (HTTP " + pos.status + "). Nothing was sold.", results: [] };
  const list = Array.isArray(pos.body.market_positions) ? pos.body.market_positions : [];
  const held = list.map((p) => ({ ticker: p.ticker, position: num(p.position_fp !== undefined ? p.position_fp : p.position) }))
    .filter((p) => p.ticker && Number.isFinite(p.position) && p.position !== 0);
  const results = [];
  for (const p of held) {
    // The list above was read before this market's turn came, and the exit watch may have sold it since. Take the claim, THEN read this one position again and sell exactly that: a count from
    // the older list could be of a position that is already closed, and selling it would open the opposite one.
    if (!(await claimClose(store, p.ticker, "flatten", now))) { results.push({ ticker: p.ticker, position: p.position, status: "skipped", detail: "the exit watch is closing it right now (or the claim could not be made), press again in a minute" }); continue; }
    const fresh = await liveRequest({ fetchFn, keyId, pem, method: "GET", path: "/portfolio/positions", params: { ticker: p.ticker, limit: "20" }, nowMs: now });
    if (fresh.status !== 200 || !fresh.body || !Array.isArray(fresh.body.market_positions)) { results.push({ ticker: p.ticker, position: p.position, status: "error", detail: "could not read the position again (HTTP " + fresh.status + "), nothing sent for it" }); continue; }
    const row = fresh.body.market_positions.find((x) => x.ticker === p.ticker);
    const nowPos = row ? num(row.position_fp !== undefined ? row.position_fp : row.position) : 0;
    if (!Number.isFinite(nowPos) || nowPos === 0) { results.push({ ticker: p.ticker, position: p.position, status: "skipped", detail: "already closed" }); continue; }
    p.position = nowPos;
    const count = Math.abs(p.position);
    const mk = await liveRequest({ fetchFn, method: "GET", path: "/markets/" + encodeURIComponent(p.ticker), nowMs: now });
    const m = mk.status === 200 && mk.body && mk.body.market;
    if (!m) { results.push({ ticker: p.ticker, position: p.position, status: "error", detail: "could not read the market (HTTP " + mk.status + "), nothing sent for it" }); continue; }
    if (!["active", "open"].includes(m.status)) { results.push({ ticker: p.ticker, position: p.position, status: "skipped", detail: "market is " + m.status + ", it settles on its own" }); continue; }
    const longYes = p.position > 0;
    const body = {
      ticker: p.ticker, side: longYes ? "ask" : "bid", count: String(count), price: longYes ? "0.01" : "0.99",
      time_in_force: "immediate_or_cancel", self_trade_prevention_type: "taker_at_cross",
      client_order_id: "FLAT-" + p.ticker + "-" + Math.floor(now / 60000),
    };
    if (m.exchange_index !== undefined && m.exchange_index !== null) body.exchange_index = m.exchange_index;
    const res = await liveRequest({ fetchFn, keyId, pem, method: "POST", path: "/portfolio/events/orders", body, nowMs: Date.now() });
    const d = res.body && typeof res.body === "object" ? res.body : {};
    if (res.status >= 200 && res.status < 300 && d.order_id) {
      const filled = Number(d.fill_count || 0);
      results.push({ ticker: p.ticker, position: p.position, status: filled >= count - 1e-9 ? "sold" : (filled > 0 ? "partly sold" : "no fill"),
        filled, wanted: count, averageFillPrice: d.average_fill_price || null, detail: filled >= count - 1e-9 ? "" : "the book had too little to take it all, run it again" });
    } else if (res.status === 409) {
      results.push({ ticker: p.ticker, position: p.position, status: "skipped", detail: "already sent in the last minute" });
    } else {
      results.push({ ticker: p.ticker, position: p.position, status: "error", detail: isAmbiguous(res.status) ? "no clear answer (HTTP " + res.status + "), check the Kalshi account before pressing again" : "refused: " + short(res.body) });
    }
  }
  return { ok: true, results };
}

// The account every order and event belongs to. There is one account today ("main"), so this changes no behaviour: it only stamps new records so a second account's records can
// be told apart later (docs: second account design). Nothing reads it yet, and a record without it is "main".
const DEFAULT_ACCOUNT_ID = "main";

module.exports = {
  flipsOf, pathShape, sideMids, twoStageFromCandles, SMOOTH_SERIES, smoothGate,
  DEFAULT_ACCOUNT_ID,
  flattenAll, claimClose, CLOSE_CLAIM_MS, runExitWatch, exitWatchIdle, EXIT_BUY_MINUTES, exitBody, EXIT_THRESHOLD, EXIT_MAX_TRIES, L1_SERIES, PROBE_SERIES, CAPPED_SERIES, FIXED_CONTRACTS,
  LIVE_BASE, LIVE_CAP, LIVE_SERIES, MAX_PER_DAY, MAX_EVER, MOVE_TOLERANCE, NotLive, assertLive, liveRequest, livePlan,
  liveOrderBody, availableFor, runLiveTest, runArmedTick, ARM_MS, signRequest, loadQuotes,
  botRisk, settleOpenOrders, settledFields, closedByHand, l1Count, reviewSizing, foldSkim, skimAddon, SKIM_REINVEST, scaleTarget, SCALE_FALL_CONFIRM_MS, L1_SIZE_CEILING, L1_ORDER_CEILING, SCALE_DOLLARS_PER_CONTRACT, SCALE_REVIEW_MS, L1_SIZE_MAX, L1_SIZE_FRACTION, L1_SIZED_STOP_FRACTION, L1_BAND, L1_WINDOW_MS, L1_MAX_ORDERS, L1_WINDOW_DAY_MS, L1_LOSS_STOP, l1Pick, totalCash, runL1Tick, riseFromCandles, EARLY_PROBE_SERIES, EARLY_WINDOW_MS, entryLead, makeRecentOrderReader, L1_OLDER_AFTER_MS, L1_OLDER_REFRESH_MS, windowKey, L1_WINDOW_CAP_FRACTION, PROBE_DROP_WINDOW, probeRingUpdate, probeNet, probeDropped,
};
