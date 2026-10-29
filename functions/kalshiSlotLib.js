"use strict";
// The second slot, PHASE A: guard rails only (docs/SECOND_SLOT_DESIGN.md). INERT BY CONSTRUCTION.
//
// This module is pure. It has no network call, no Firestore, no clock and no order code, nothing in functions/index.js or any other
// library imports it, and SLOT_STRATEGIES is empty and SLOT_ENABLED is false. It exists so that a research survivor can later be
// admitted by a small reviewed edit of the list below, and so that the rules that edit has to live inside are already written and tested.
//
// What the rules protect (the owner's decisions, Oct 29, 2026):
//   - a slot order may share a market and window with L1 only in the SAME direction; the opposite side would be a hedge and is blocked;
//   - sizes above one contract are allowed, inside hard caps in code;
//   - L1 and the slot are ONE risk budget: slot dollars count against the same window cap and the same 12% loss stop;
//   - each strategy sells only its own contracts.
// Nothing stored (Firestore, the page, a request) can add a strategy, change a cap or turn SLOT_ENABLED on. Every number is here.

const bot = require("./kalshiSignalLib");

// ---- The master switch and the hard caps. Changing any of these is a reviewed code edit, never a stored value. ----------------------------
const SLOT_ENABLED = false;                            // phase A: off. Turning it on is its own reviewed pull request, after the wiring phases.
const SLOT_SERIES_ALLOWED = Object.freeze(["KXBTC15M", "KXETH15M", "KXGOLD15M"]);
const SLOT_MAX_CONTRACTS_PER_ORDER = 10;
const SLOT_MAX_OPEN_CONTRACTS_PER_MARKET = 10;        // the slot's own unsold contracts in one ticker, all strategies together
const SLOT_MAX_SCALE_STEPS = 3;
const SLOT_MAX_RISK_PER_ORDER = 6.0;                   // dollars, worst case, fee included
const SLOT_MAX_RISK_PER_WINDOW = 8.0;                  // slot dollars put into one window (gross, like L1's own window sum)
const SLOT_MAX_RISK_TOTAL = 12.0;                      // slot dollars open at once across all markets (unsold, unsettled, counted as lost)
const SLOT_DEPTH_SHARE = 0.25;                         // never more than this share of the size resting at the touch (Kalshi gives the top level only)
const SLOT_DAILY_LOSS_CAP = 5.0;                       // slot-only: last 24 hours, open counted as lost
const SLOT_LIFETIME_LOSS_CAP = 15.0;                   // slot-only: since the first slot order, open counted as lost
const SLOT_MIN_PRICE = 0.05, SLOT_MAX_PRICE = 0.97;    // entry limit price bounds (YES price for a yes buy, the NO price for a no buy)
const SLOT_ENTRY_LEFT_MIN_SEC = 120, SLOT_ENTRY_LEFT_MAX_SEC = 840;
const SLOT_EXIT_LEFT_FLOOR_SEC = 45;                   // every exit is before settlement: a strategy must be fully out by this long before the close
const SLOT_OPEN_STATUSES = Object.freeze(["filled", "sending", "unknown"]);   // the statuses runL1Tick counts as money in a window
const L1_WINDOW_CAP_FRACTION_MIRROR = 0.055;           // a test pins this to kalshiLiveLib.L1_WINDOW_CAP_FRACTION; the caller passes the live one

// ---- The registry. EMPTY in phase A. An entry is admitted only by a reviewed edit of this array. -----------------------------------------
// Shape of an entry (every field required, unknown fields rejected):
//   id            2 to 10 capitals or digits (it goes into the client order id)
//   readme        path to the pre-registration, e.g. "kalshi-scalper/README.md#SLOT-XYZ"
//   series        non-empty subset of SLOT_SERIES_ALLOWED
//   entry         { sideRule: "yes"|"no"|"favourite", priceMin, priceMax, leftMaxSec, leftMinSec }
//   exit          { stopBid, targetBid, mustExitLeftSec }           bids are on the side held; always an immediate-or-cancel close
//   contractsPerOrder, scaleIn { maxSteps, minGapSec, sameSideOnly: true, requirePriorFilled: true }
//   killRules     { maxConsecutiveLosses, minNet: { afterFills, net } }
//   forwardReadDate  "YYYY-MM-DD", when the forward test is read
//   reviewedAt    "YYYY-MM-DD", the date a human last re-armed it; a kill latch older than this no longer blocks (the only way back on)
const SLOT_STRATEGIES = Object.freeze([]);

const ENTRY_KEYS = ["sideRule", "priceMin", "priceMax", "leftMaxSec", "leftMinSec"];
const EXIT_KEYS = ["stopBid", "targetBid", "mustExitLeftSec"];
const SCALE_KEYS = ["maxSteps", "minGapSec", "sameSideOnly", "requirePriorFilled"];
const KILL_KEYS = ["maxConsecutiveLosses", "minNet"];
const TOP_KEYS = ["id", "readme", "series", "entry", "exit", "contractsPerOrder", "scaleIn", "killRules", "forwardReadDate", "reviewedAt"];
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const isObj = (x) => x && typeof x === "object" && !Array.isArray(x);
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && Number.isFinite(Date.parse(s + "T00:00:00Z"));
const exactKeys = (o, keys) => isObj(o) && Object.keys(o).sort().join() === keys.slice().sort().join();

// Returns { ok, errors }. Never throws. Anything out of bounds is a reason to reject the whole entry.
function validateSlotStrategy(s) {
  const e = [];
  if (!exactKeys(s, TOP_KEYS)) return { ok: false, errors: ["the entry must have exactly these fields: " + TOP_KEYS.join(", ")] };
  if (!/^[A-Z0-9]{2,10}$/.test(s.id)) e.push("id must be 2 to 10 capitals or digits");
  if (typeof s.readme !== "string" || !/^[\w./-]+\.md(#[\w-]+)?$/.test(s.readme)) e.push("readme must point at a pre-registration file");
  if (!Array.isArray(s.series) || !s.series.length || s.series.some((x) => !SLOT_SERIES_ALLOWED.includes(x)) || new Set(s.series).size !== s.series.length) e.push("series must be a non-empty subset of " + SLOT_SERIES_ALLOWED.join(", "));
  if (!exactKeys(s.entry, ENTRY_KEYS)) e.push("entry has the wrong fields");
  else {
    const x = s.entry;
    if (!["yes", "no", "favourite"].includes(x.sideRule)) e.push("entry.sideRule must be yes, no or favourite");
    if (!isNum(x.priceMin) || !isNum(x.priceMax) || x.priceMin < SLOT_MIN_PRICE || x.priceMax > SLOT_MAX_PRICE || !(x.priceMin < x.priceMax)) e.push("entry price bounds must sit inside " + SLOT_MIN_PRICE + " to " + SLOT_MAX_PRICE + " with priceMin below priceMax");
    if (!isNum(x.leftMaxSec) || !isNum(x.leftMinSec) || x.leftMaxSec > SLOT_ENTRY_LEFT_MAX_SEC || x.leftMinSec < SLOT_ENTRY_LEFT_MIN_SEC || !(x.leftMinSec < x.leftMaxSec)) e.push("entry time left must sit inside " + SLOT_ENTRY_LEFT_MIN_SEC + " to " + SLOT_ENTRY_LEFT_MAX_SEC + " seconds");
  }
  if (!exactKeys(s.exit, EXIT_KEYS)) e.push("exit has the wrong fields");
  else if (isObj(s.entry) && isNum(s.entry.priceMin)) {
    const x = s.exit;
    if (!isNum(x.stopBid) || x.stopBid < 0.01 || x.stopBid >= s.entry.priceMin) e.push("exit.stopBid must be at least 0.01 and below entry.priceMin (a stop is a loss line)");
    if (!isNum(x.targetBid) || x.targetBid > 0.99 || x.targetBid <= s.entry.priceMax) e.push("exit.targetBid must be above entry.priceMax and at most 0.99");
    if (!isNum(x.mustExitLeftSec) || x.mustExitLeftSec < SLOT_EXIT_LEFT_FLOOR_SEC || x.mustExitLeftSec >= s.entry.leftMinSec) e.push("exit.mustExitLeftSec must be at least " + SLOT_EXIT_LEFT_FLOOR_SEC + " and below entry.leftMinSec (every exit is before settlement)");
  }
  if (!Number.isInteger(s.contractsPerOrder) || s.contractsPerOrder < 1 || s.contractsPerOrder > SLOT_MAX_CONTRACTS_PER_ORDER) e.push("contractsPerOrder must be a whole number from 1 to " + SLOT_MAX_CONTRACTS_PER_ORDER);
  if (!exactKeys(s.scaleIn, SCALE_KEYS)) e.push("scaleIn has the wrong fields");
  else {
    const x = s.scaleIn;
    if (!Number.isInteger(x.maxSteps) || x.maxSteps < 1 || x.maxSteps > SLOT_MAX_SCALE_STEPS) e.push("scaleIn.maxSteps must be 1 to " + SLOT_MAX_SCALE_STEPS);
    if (!isNum(x.minGapSec) || x.minGapSec < 30) e.push("scaleIn.minGapSec must be at least 30");
    if (x.sameSideOnly !== true || x.requirePriorFilled !== true) e.push("scaleIn.sameSideOnly and requirePriorFilled must be true");
    if (Number.isInteger(x.maxSteps) && Number.isInteger(s.contractsPerOrder) && x.maxSteps * s.contractsPerOrder > SLOT_MAX_OPEN_CONTRACTS_PER_MARKET) e.push("maxSteps times contractsPerOrder must not exceed " + SLOT_MAX_OPEN_CONTRACTS_PER_MARKET + " open contracts per market");
  }
  if (!exactKeys(s.killRules, KILL_KEYS)) e.push("killRules has the wrong fields");
  else {
    const k = s.killRules;
    if (!Number.isInteger(k.maxConsecutiveLosses) || k.maxConsecutiveLosses < 1 || k.maxConsecutiveLosses > 5) e.push("killRules.maxConsecutiveLosses must be 1 to 5");
    if (!exactKeys(k.minNet, ["afterFills", "net"])) e.push("killRules.minNet needs afterFills and net");
    else {
      if (!Number.isInteger(k.minNet.afterFills) || k.minNet.afterFills < 5 || k.minNet.afterFills > 100) e.push("killRules.minNet.afterFills must be 5 to 100");
      if (!isNum(k.minNet.net) || k.minNet.net > 0 || k.minNet.net < -SLOT_LIFETIME_LOSS_CAP) e.push("killRules.minNet.net must be zero or a loss no bigger than the lifetime cap");
    }
  }
  if (!isDate(s.forwardReadDate)) e.push("forwardReadDate must be YYYY-MM-DD");
  if (!isDate(s.reviewedAt)) e.push("reviewedAt must be YYYY-MM-DD");
  return { ok: e.length === 0, errors: e };
}

// The strategies that may act. Fails closed three ways: the switch is off, any entry is invalid (the whole registry is refused, so a typo
// cannot quietly drop one guard and keep the rest), or an id repeats.
function activeSlotStrategies(flags) {
  const f = flags || {};
  const enabled = f.enabled === undefined ? SLOT_ENABLED : f.enabled;
  const registry = f.registry === undefined ? SLOT_STRATEGIES : f.registry;
  if (enabled !== true || !Array.isArray(registry)) return [];
  const ids = new Set();
  for (const s of registry) { if (!validateSlotStrategy(s).ok || ids.has(s.id)) return []; ids.add(s.id); }
  return registry.slice();
}

// ---- Order identity --------------------------------------------------------------------------------------------------------------------
// Deterministic, so two function instances computing the same entry compute the same id and Kalshi's own uniqueness check refuses the second
// (the lesson of the 15 duplicate orders). One id per strategy, market and scale-in step. The L1 id is "L1-" + ticker, the exit watch's is "X-..." and Flatten's is "FLAT-...", so none collide.
function slotClientOrderId(strategyId, ticker, step) {
  if (!/^[A-Z0-9]{2,10}$/.test(String(strategyId))) throw new Error("bad strategy id");
  if (!/^KX[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+$/.test(String(ticker))) throw new Error("bad ticker");
  if (!Number.isInteger(step) || step < 1 || step > SLOT_MAX_SCALE_STEPS) throw new Error("bad scale-in step");
  return "S-" + strategyId + "-" + ticker + "-" + step;
}
// The close of a slot order: its own prefix, the slot order's id and the try number, so it can never equal an L1 exit id ("X-" + ticker + "-" + try).
function slotExitClientOrderId(slotOrderId, tries) {
  if (typeof slotOrderId !== "string" || !slotOrderId.startsWith("S-")) throw new Error("not a slot order id");
  if (!Number.isInteger(tries) || tries < 0 || tries > 2) throw new Error("bad try number");
  return "SX-" + slotOrderId.slice(2) + "-" + (tries + 1);
}
// The document id in kalshiSlotOrders is the client order id: creating it is the atomic "claim" (create fails if present).
const slotOrderDocId = slotClientOrderId;
// Mirror of kalshiLiveLib.windowKey (a test pins them equal); copied, not imported, so the later wiring cannot make a require cycle.
function windowKey(ticker) { const p = String(ticker || "").split("-"); return p.length >= 2 ? p[1] : String(ticker || ""); }

// ---- 1. Direction: same side only ------------------------------------------------------------------------------------------------------
// Decides whether `side` may be bought on `ticker`, from every source that could disagree:
//   l1Orders / slotOrders  the order documents of both collections for that ticker (money in flight counts: sending and unknown hold their side)
//   lock                   the kalshiLiveDirection/{ticker} document { side } read in the same transaction that creates the order (see the design doc)
//   position               the account's signed position in the ticker (yes positive, no negative), or null when it could not be read
// Anything unreadable, malformed or contradictory refuses. Pure.
function directionDecision({ ticker, side, l1Orders, slotOrders, lock, position }) {
  if (side !== "yes" && side !== "no") return { allow: false, reason: "the side must be yes or no" };
  if (!ticker) return { allow: false, reason: "no ticker" };
  if (!Array.isArray(l1Orders) || !Array.isArray(slotOrders)) return { allow: false, reason: "the orders could not be read, so the direction is unknown" };
  const sides = new Set();
  for (const t of [...l1Orders, ...slotOrders]) {
    if (!t || t.ticker !== ticker) continue;
    if (!SLOT_OPEN_STATUSES.includes(t.status) || t.settled === true) continue;
    if (t.side !== "yes" && t.side !== "no") return { allow: false, reason: "an order on this market has no readable side" };
    sides.add(t.side);
  }
  if (sides.size > 1) return { allow: false, reason: "the books already show both sides on this market; nothing more is added" };
  if (sides.size === 1 && !sides.has(side)) return { allow: false, reason: "an order on the other side already holds this market, and the opposite side would be a hedge" };
  if (lock !== null && lock !== undefined) {
    if (!isObj(lock) || (lock.side !== "yes" && lock.side !== "no")) return { allow: false, reason: "the direction lock is unreadable" };
    if (lock.side !== side) return { allow: false, reason: "the direction lock for this market is " + lock.side + ", not " + side };
  }
  if (!isNum(position)) return { allow: false, reason: "the account position could not be read" };
  if (position > 0 && side === "no") return { allow: false, reason: "the account holds YES here, so a NO buy would hedge it" };
  if (position < 0 && side === "yes") return { allow: false, reason: "the account holds NO here, so a YES buy would hedge it" };
  return { allow: true, reason: "", needsLock: !lock };
}

// ---- 4. The shared risk budget as pure functions -------------------------------------------------------------------------------------
const num = (x) => { const n = Number(x); return Number.isFinite(n) ? n : NaN; };
function filledOf(t) { const want = num(t.count) > 0 ? num(t.count) : 1; return { want, got: Math.min(num(t.fillCount) || 0, want) }; }
function isSlotOrder(t) { return !!t && t.strategy === "SLOT" && typeof t.slotId === "string"; }

// Dollars the slot has AT RISK in an order that is not settled: counted as lost, exactly like L1's open orders in botRisk.
// sending / unknown count in full (the order may exist); filled counts what was paid for the contracts not yet sold.
function openAtRisk(t) {
  if (!isSlotOrder(t) || t.settled === true || !SLOT_OPEN_STATUSES.includes(t.status)) return 0;
  const cost = num(t.maxCost);
  if (!(cost >= 0)) return SLOT_MAX_RISK_PER_ORDER;     // an order whose cost is unreadable is assumed to be the biggest allowed
  if (t.status !== "filled") return cost;
  const { want, got } = filledOf(t);
  if (!(got > 0)) return 0;
  const sold = num(t.exitCount) > 0 ? Math.min(num(t.exitCount), got) : 0;
  return cost * (got / want) * (1 - sold / got);
}
function openContracts(t) {
  if (!isSlotOrder(t) || t.settled === true || !SLOT_OPEN_STATUSES.includes(t.status)) return 0;
  const { want, got } = filledOf(t);
  if (t.status !== "filled") return want;               // in flight: assume it fills
  const sold = num(t.exitCount) > 0 ? num(t.exitCount) : 0;
  return Math.max(0, got - sold);
}
const settledPnlOf = (t) => (isSlotOrder(t) && t.settled === true && t.result !== "hand" && Number.isFinite(num(t.settledPnl)) && num(t.fillCount) > 0 ? num(t.settledPnl) : null);

// What runL1Tick needs for the WINDOW cap: slot gross spend in a window, on the same terms as runL1Tick's windowUsed (maxCost of orders whose status is
// filled, sending or unknown, whether or not later sold or settled; slot orders have no add-on).
function slotWindowSpent(slotOrders, ticker) {
  const wk = windowKey(ticker);
  return (slotOrders || []).filter((t) => isSlotOrder(t) && windowKey(t.ticker) === wk && SLOT_OPEN_STATUSES.includes(t.status)).reduce((a, t) => a + Math.max(0, num(t.maxCost) || 0), 0);
}
// What botRisk needs for the LOSS STOP, in botRisk's own return shape so the wiring can add the two: net (settled pnl since `since`), openCost (counted as lost), worst.
function slotRiskForBotRisk(slotOrders, since) {
  const from = Number.isFinite(since) ? since : 0;
  let net = 0, openCost = 0, trades = 0;
  for (const t of slotOrders || []) {
    if (!isSlotOrder(t) || !(num(t.ts) >= from) || !(num(t.fillCount) > 0 || t.status === "sending" || t.status === "unknown")) continue;
    trades += 1;
    const p = settledPnlOf(t);
    if (p !== null) net += p; else openCost += openAtRisk(t);
  }
  return { net, openCost, worst: net - openCost, addonAtRisk: 0, trades };
}
// The full figures the guards read: open dollars total and per window, open contracts per ticker, 24 hour and lifetime nets (open counted as lost).
function slotRiskContract(slotOrders, now) {
  const day = slotRiskForBotRisk(slotOrders, now - 24 * 3600 * 1000), life = slotRiskForBotRisk(slotOrders, 0);
  const byWindow = {}, byTicker = {};
  let openTotal = 0;
  for (const t of slotOrders || []) {
    const r = openAtRisk(t);
    if (r > 0) { openTotal += r; byWindow[windowKey(t.ticker)] = (byWindow[windowKey(t.ticker)] || 0) + r; }
    const c = openContracts(t);
    if (c > 0) byTicker[t.ticker] = (byTicker[t.ticker] || 0) + c;
  }
  return { openTotal, openByWindow: byWindow, openContractsByTicker: byTicker, day, lifetime: life };
}

// ---- 3. Kill rules (fail closed, stay off until a reviewed edit) -------------------------------------------------------------------
// Evaluated on one strategy's own settled orders. A latch (kalshiSlotControl/killed, written by the later wiring) blocks the strategy while latch.killedAt
// is at or after the strategy's reviewedAt; a reviewed edit that moves reviewedAt later than the latch is the only way back on. Stored data can only switch a strategy OFF.
function killCheck(strategy, slotOrders, latch) {
  const mine = (slotOrders || []).filter((t) => isSlotOrder(t) && t.slotId === strategy.id).sort((a, b) => num(a.ts) - num(b.ts));
  if (latch && isObj(latch) && latch.killedAt !== undefined) {
    const at = Number(latch.killedAt), re = Date.parse(strategy.reviewedAt + "T00:00:00Z");
    if (!Number.isFinite(at) || !Number.isFinite(re) || at >= re) return { killed: true, reason: "a kill latch is set and no reviewed edit has re-armed " + strategy.id };
  } else if (latch !== null && latch !== undefined) return { killed: true, reason: "the kill latch is unreadable" };
  const pnls = mine.map(settledPnlOf).filter((p) => p !== null);
  let streak = 0;
  for (let i = pnls.length - 1; i >= 0 && pnls[i] < 0; i--) streak += 1;
  if (streak >= strategy.killRules.maxConsecutiveLosses) return { killed: true, reason: streak + " losses in a row", latch: true };
  const k = strategy.killRules.minNet, net = pnls.reduce((a, p) => a + p, 0);
  if (pnls.length >= k.afterFills && net < k.net) return { killed: true, reason: "net $" + net.toFixed(2) + " after " + pnls.length + " fills is below $" + k.net.toFixed(2), latch: true };
  return { killed: false, reason: "" };
}

// ---- The one gate every slot order passes ----------------------------------------------------------------------------------------------
// Returns { allowed, count, reasons, cost, cid }. `count` is the wanted count cut down to whatever every cap allows; allowed is false when that is under 1.
// Inputs: strategyId, ticker, side, limit (price of the side bought), step, wanted (optional, default contractsPerOrder), depthAtTouch (size resting at the touch being hit),
// slotOrders and l1Orders (every order of each collection, read completely), slotOrdersComplete (true only if the slot collection was read in full: the lifetime cap needs all of it),
// lock, position, sizingBase, windowCapFraction (the live L1_WINDOW_CAP_FRACTION), killLatch, secondsLeft, now, lastStepAt.
function slotOrderCheckWith(flags, input) {
  const no = (reason) => ({ allowed: false, count: 0, reasons: [reason], cost: 0, cid: null });
  const i = input || {};
  const strategy = activeSlotStrategies(flags).find((s) => s.id === i.strategyId);
  if (!strategy) return no("no active slot strategy with that id (the switch is off, or it is not in the registry)");
  const series = String(i.ticker || "").split("-")[0];
  if (!strategy.series.includes(series)) return no(series + " is not one of this strategy's markets");
  if (i.side !== "yes" && i.side !== "no") return no("the side must be yes or no");
  if (strategy.entry.sideRule !== "favourite" && strategy.entry.sideRule !== i.side) return no("this strategy only buys " + strategy.entry.sideRule);
  if (!Array.isArray(i.slotOrders) || !Array.isArray(i.l1Orders) || i.slotOrdersComplete !== true) return no("the order books were not read in full, so the caps cannot be checked");
  const k = killCheck(strategy, i.slotOrders, i.killLatch === undefined ? null : i.killLatch);
  if (k.killed) return no("killed: " + k.reason);
  const e = strategy.entry;
  if (!isNum(i.limit) || i.limit < e.priceMin - 1e-9 || i.limit > e.priceMax + 1e-9) return no("the price is outside the strategy's entry band");
  if (!isNum(i.secondsLeft) || i.secondsLeft > e.leftMaxSec || i.secondsLeft < e.leftMinSec) return no("not inside the strategy's entry time window");
  const d = directionDecision({ ticker: i.ticker, side: i.side, l1Orders: i.l1Orders, slotOrders: i.slotOrders, lock: i.lock, position: i.position });
  if (!d.allow) return no(d.reason);
  // Scale-in: step 1 only when this strategy has nothing on the ticker; step n only after step n-1 filled, and never twice.
  const step = i.step;
  if (!Number.isInteger(step) || step < 1 || step > strategy.scaleIn.maxSteps) return no("bad scale-in step");
  const mineHere = i.slotOrders.filter((t) => isSlotOrder(t) && t.slotId === strategy.id && t.ticker === i.ticker);
  if (mineHere.some((t) => t.step === step && !["no fill", "error"].includes(t.status))) return no("this step was already attempted");
  if (step > 1) {
    const prior = mineHere.find((t) => t.step === step - 1 && t.status === "filled" && num(t.fillCount) > 0);
    if (!prior) return no("the previous step has not filled");
    if (!isNum(i.now) || !isNum(prior.ts) || i.now - prior.ts < strategy.scaleIn.minGapSec * 1000) return no("too soon after the previous step");
  }
  if (!(isNum(i.sizingBase) && i.sizingBase > 0) || !(isNum(i.windowCapFraction) && i.windowCapFraction > 0 && i.windowCapFraction <= L1_WINDOW_CAP_FRACTION_MIRROR + 1e-9)) return no("the sizing base or the window cap is not usable");
  if (!isNum(i.now)) return no("no clock");
  const risk = slotRiskContract(i.slotOrders, i.now);
  if (risk.day.worst <= -SLOT_DAILY_LOSS_CAP + 1e-9) return no("the slot's own daily loss cap is reached");
  if (risk.lifetime.worst <= -SLOT_LIFETIME_LOSS_CAP + 1e-9) return no("the slot's own lifetime loss cap is reached");
  // How many contracts every cap allows. Depth is the top of the book only, so unknown depth refuses rather than guesses.
  if (!isNum(i.depthAtTouch) || !(i.depthAtTouch > 0)) return no("the size resting at the touch is unknown");
  const wanted = Number.isInteger(i.wanted) ? i.wanted : strategy.contractsPerOrder;
  const reasons = [];
  let n = Math.min(wanted, strategy.contractsPerOrder, SLOT_MAX_CONTRACTS_PER_ORDER);
  const openHere = risk.openContractsByTicker[i.ticker] || 0;
  n = Math.min(n, SLOT_MAX_OPEN_CONTRACTS_PER_MARKET - openHere, Math.floor(i.depthAtTouch * SLOT_DEPTH_SHARE + 1e-9));
  const wk = windowKey(i.ticker);
  const l1Used = i.l1Orders.filter((t) => t && windowKey(t.ticker) === wk && SLOT_OPEN_STATUSES.includes(t.status)).reduce((a, t) => a + Math.max(0, (num(t.maxCost) || 0) - (num(t.addonCost) || 0)), 0);
  const slotUsed = slotWindowSpent(i.slotOrders, i.ticker);
  const costOf = (c) => i.limit * c + bot.takerFee(i.limit, c);
  const windowRoom = i.windowCapFraction * i.sizingBase - l1Used - slotUsed;
  while (n >= 1) {
    const c = costOf(n);
    if (c <= SLOT_MAX_RISK_PER_ORDER + 1e-9 && c <= SLOT_MAX_RISK_PER_WINDOW - slotUsed + 1e-9 && c <= SLOT_MAX_RISK_TOTAL - risk.openTotal + 1e-9 && c <= windowRoom + 1e-9) break;
    n -= 1;
  }
  if (n < 1) return no("no whole contract fits the caps (per order, per market, depth share, window, total, or the shared window limit)");
  if (n < wanted) reasons.push("cut from " + wanted + " to " + n + " by the caps");
  return { allowed: true, count: n, reasons, cost: Number(costOf(n).toFixed(4)), cid: slotClientOrderId(strategy.id, i.ticker, step) };
}
function slotOrderCheck(input) { return slotOrderCheckWith({}, input); }

// ---- 5. Own contracts only: how many a slot close may sell -------------------------------------------------------------------------------
// min(this order's unsold filled contracts, what the account holds on that side). Zero when the account holds nothing or the opposite side (a sell then would OPEN the opposite
// position), when the position is unreadable, or when the close lease on the market is not held. The caller takes claimClose(store, ticker, "slot", now) BEFORE reading the position.
function slotSellCount({ order, position, haveClaim }) {
  if (haveClaim !== true || !isSlotOrder(order) || (order.side !== "yes" && order.side !== "no") || !isNum(position)) return 0;
  const { got } = filledOf(order);
  const own = Math.floor(got - (num(order.exitCount) > 0 ? num(order.exitCount) : 0) + 1e-9);
  const holding = order.side === "yes" ? Math.max(0, position) : Math.max(0, -position);
  return Math.max(0, Math.min(own, Math.floor(holding + 1e-9)));
}
// The same pnl rule as kalshiLiveLib.settledFields (a test pins them equal), so a slot result and an L1 result are on one footing in the shared loss stop.
function slotSettledFields(t, result) {
  const cost = num(t.maxCost);
  const want0 = num(t.count) > 0 ? num(t.count) : 1, got0 = Math.min(num(t.fillCount), want0);
  const sold = num(t.exitCount) > 0 ? Math.min(num(t.exitCount), got0) : 0;
  const proceeds = sold > 0 && Number.isFinite(num(t.exitProceeds)) ? num(t.exitProceeds) : 0;
  return { settled: true, result, settledPnl: Number((((result === t.side ? got0 - sold : 0)) + proceeds - cost * (got0 / want0)).toFixed(4)) };
}

module.exports = {
  SLOT_ENABLED, SLOT_STRATEGIES, SLOT_SERIES_ALLOWED, SLOT_MAX_CONTRACTS_PER_ORDER, SLOT_MAX_OPEN_CONTRACTS_PER_MARKET, SLOT_MAX_SCALE_STEPS, SLOT_MAX_RISK_PER_ORDER,
  SLOT_MAX_RISK_PER_WINDOW, SLOT_MAX_RISK_TOTAL, SLOT_DEPTH_SHARE, SLOT_DAILY_LOSS_CAP, SLOT_LIFETIME_LOSS_CAP, SLOT_OPEN_STATUSES, L1_WINDOW_CAP_FRACTION_MIRROR,
  validateSlotStrategy, activeSlotStrategies, slotClientOrderId, slotExitClientOrderId, slotOrderDocId, windowKey, directionDecision,
  openAtRisk, slotWindowSpent, slotRiskForBotRisk, slotRiskContract, killCheck, slotOrderCheck, slotOrderCheckWith, slotSellCount, slotSettledFields,
};
