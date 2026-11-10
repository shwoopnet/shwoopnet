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
const SLOT_ENABLED = true;                            // phase A: off. Turning it on is its own reviewed pull request, after the wiring phases.
// EVENT830's eight markets (Nov 3, 2026) are on the list too, but RESERVED: only the strategy named in SLOT_SERIES_RESERVED may trade them (the validator refuses any other id), so admitting them for the release probe does not open them to anything else.
// None of them is an L1 market, so a position there can never sit against an L1 position.
const EVENT830_SERIES = Object.freeze(["KXSILVER15M", "KXCOPPER15M", "KXWTI15M", "KXEURUSD15M", "KXGBPUSD15M", "KXUSDJPY15M", "KXHYPE15M", "KXBNB15M"]);
// KXXRP15M added Nov 10, 2026 for XRPYES10 (a capped probe, kalshi-scalper/README.md#SLOT-XRPYES10). XRP is paused for L1 in code, so no L1 order can sit against a slot order there.
// KXAUDUSD15M added Nov 10, 2026 for KESTREL (a capped probe, kalshi-scalper/README.md#SLOT-KESTREL) and RESERVED to it. It is NOT an L1 market (it stays off L1_SERIES and on PAUSED_SERIES, so the L1 size lock refuses any L1 order there and no L1 position can sit against a slot one).
const SLOT_SERIES_ALLOWED = Object.freeze(["KXBTC15M", "KXETH15M", "KXGOLD15M", "KXXRP15M"].concat(EVENT830_SERIES, ["KXAUDUSD15M"]));
const SLOT_SERIES_RESERVED = Object.freeze(Object.assign(EVENT830_SERIES.reduce((o, x) => { o[x] = "EVENT830"; return o; }, {}), { KXAUDUSD15M: "KESTREL" }));
const SLOT_MAX_CONTRACTS_PER_ORDER = 10;
const SLOT_MAX_OPEN_CONTRACTS_PER_MARKET = 10;        // the slot's own unsold contracts in one ticker, all strategies together
const SLOT_MAX_SCALE_STEPS = 3;
// Dollar caps SCALE WITH THE SIZING BASE, like L1's own window cap and loss stop (the owner, Oct 29, 2026: the gold ladder makes L1 positions bigger as the account grows, so fixed dollars would be too small
// for a bigger account and too big for a smaller one). Each cap is a share of the sizing base, never above a hard dollar ceiling, so a wrong base can never lift a cap past the ceiling. Per order is below the daily cap.
const SLOT_CAP_FRACTIONS = Object.freeze({ perOrder: 0.01, perWindow: 0.02, openTotal: 0.03, daily: 0.02, lifetime: 0.06 });
const SLOT_CAP_CEILINGS = Object.freeze({ perOrder: 20, perWindow: 40, openTotal: 60, daily: 20, lifetime: 60 });
function slotCaps(sizingBase) {
  const base = isNum(sizingBase) && sizingBase > 0 ? sizingBase : 0;   // an unusable base means every cap is zero: nothing can be sent
  const out = {};
  for (const k of Object.keys(SLOT_CAP_FRACTIONS)) out[k] = Math.min(SLOT_CAP_FRACTIONS[k] * base, SLOT_CAP_CEILINGS[k]);
  return out;
}
// OICORE limit 1c above the touch (Nov 3, 2026, the owner: "build 1", on the refinement chat's S-LIM1 read: 6 of 24 OICORE limits went unfilled because the ask moved up 1c within
// seconds, and 3 of those 6 won). The order still fills at the best ask when the ask has not moved (Kalshi gives price improvement), so this only adds fills that would have been missed,
// at most 1c a contract worse. Never past the strategy's own priceMax. A reviewed edit; at most 2c for any strategy.
const SLOT_LIMIT_SLIP = Object.freeze({ OICORE: 0.01 });
const SLOT_LIMIT_SLIP_MAX = 0.02;
// OICORE skips its very cheap entries (Nov 8, 2026, the owner approved designing small tests of the refinement chat's lead; skip-only, no new strategy). Live fills paid under 8c won
// 1 in 27 and a forward group under 10c 0 in 17, while the simulation says about break-even, so this is a bet that live beats the simulation. It only REMOVES orders (a skipped signal is
// logged as cheap_skipped with its price, and public settlements say what it would have made), never adds or enlarges one. Decision rule, written before the first skip: after 40 skipped
// signals keep it if at most 1 would have won, drop it if 4 or more would, else read to 80. A reviewed edit; the price can be at most 20c.
const SLOT_SKIP_BELOW = Object.freeze({ OICORE: 0.08 });
const SLOT_SKIP_BELOW_MAX = 0.2;
function slotSkipsPrice(strategy, sidePrice) {
  const raw = SLOT_SKIP_BELOW[strategy && strategy.id];
  if (!isNum(raw) || !(raw > 0) || raw > SLOT_SKIP_BELOW_MAX + 1e-9 || !isNum(sidePrice)) return false;
  return sidePrice < raw - 1e-9;
}
function slotLimitFor(strategy, sidePrice) {
  const raw = SLOT_LIMIT_SLIP[strategy && strategy.id];
  const slip = isNum(raw) && raw > 0 && raw <= SLOT_LIMIT_SLIP_MAX + 1e-9 ? raw : 0;
  if (!isNum(sidePrice) || !strategy || !strategy.entry) return sidePrice;
  return Math.round(Math.min(sidePrice + slip, Math.max(sidePrice, strategy.entry.priceMax)) * 100) / 100;
}
// ---- The OICORE size ladder (Nov 3, 2026, the owner: "yes build it", on the refinement chat's scaling spec). ----------------------------------------------
// A strategy listed here may send MORE than its registry contractsPerOrder, one step at a time, but only as its OWN settled record earns it. The step is replayed from the
// strategy's own order documents every time (no stored step, no counter, nothing the page or Firestore can raise), so two instances always compute the same size, and a
// reviewed edit that moves reviewedAt starts the ladder again from the bottom. Each step also needs a sizing base big enough that a 95th percentile losing run plus an L1 bad
// day stays inside the shared 12% stop (minBase, the refinement chat's B4 table); a smaller base holds the size down without changing the replayed step.
// Up: at least upFills fills AND upDays days at the current step, and over those fills a win rate of upWinRate or more, a net of upNetPerContract x contracts or more,
// profit factor upPf or more, and a drawdown since the step began under upMaxDrawdownPerContract x contracts. Down one step at once: drawdown since the step began at
// downDrawdownPerContract x contracts or more, or (with downWindow fills at the step) a win rate under downWinRate or a net under downNetPerContract x contracts over the last
// downWindow; down two when both of the first two hit. Never below the first step, never above SLOT_LADDER_MAX_CONTRACTS.
// For a laddered strategy the base-scaled daily and lifetime loss caps are replaced by caps that scale with the contract count: a daily loss cap of dailyPerContract x
// contracts (at least the base cap, at most dailyMaxFraction of the base and dailyCeiling dollars) and a drawdown stop from its own peak result of stopPerContract x
// contracts (at most stopMaxFraction of the base and stopCeiling dollars). The drawdown stop refuses every new order until a reviewed edit moves reviewedAt.
const SLOT_LADDER_MAX_CONTRACTS = 30;
const SLOT_LADDERS = Object.freeze({
  OICORE: Object.freeze({
    steps: Object.freeze([10, 12, 15, 20, 30]),
    minBase: Object.freeze([0, 825, 900, 1030, 1350]),
    upFills: 20, upDays: 7,   // faster steps (Nov 3, 2026, the owner: "maybe be more aggressive", chose faster steps over lower floors or bigger jumps; was 40 fills and 14 days)
     upWinRate: 0.20, upNetPerContract: 1.0, upPf: 1.3, upMaxDrawdownPerContract: 3,
    downDrawdownPerContract: 3, downWindow: 40, downWinRate: 0.15, downNetPerContract: -2,
    dailyPerContract: 2.5, dailyMaxFraction: 0.06, dailyCeiling: 75,
    stopPerContract: 5, stopMaxFraction: 0.12, stopCeiling: 150,
  }),
});
const SLOT_DEPTH_SHARE = 0.25;                         // never more than this share of the size resting at the touch (Kalshi gives the top level only)
const SLOT_MIN_PRICE = 0.05, SLOT_MAX_PRICE = 0.97;    // entry limit price bounds (YES price for a yes buy, the NO price for a no buy)
const SLOT_ENTRY_LEFT_MIN_SEC = 120, SLOT_ENTRY_LEFT_MAX_SEC = 840;
const SLOT_EXIT_LEFT_FLOOR_SEC = 45;                   // every exit is before settlement: a strategy must be fully out by this long before the close
const SLOT_OPEN_STATUSES = Object.freeze(["filled", "sending", "unknown"]);   // the statuses runL1Tick counts as money in a window; ANY order with fills counts too, whatever its status
const SLOT_WINDOW_SHARE = 0.5;                         // the slot may take at most this share of the shared window cap, so L1 (gold first) is never starved of its room
const SLOT_L1_RESERVE = 1.05;                          // dollars always left in the window for one more L1 contract (a 97c contract plus its fee)
const SLOT_LAST_REVIEWED_ON = "2026-11-10";             // no reviewedAt may be later than this; the edit that admits a strategy moves it to that edit's date (the module has no clock)
const SLOT_TICKER_RE = /^(KXBTC15M|KXETH15M|KXGOLD15M|KXXRP15M|KXAUDUSD15M|KXSILVER15M|KXCOPPER15M|KXWTI15M|KXEURUSD15M|KXGBPUSD15M|KXUSDJPY15M|KXHYPE15M|KXBNB15M)-\d{2}[A-Z]{3}\d{6}-\d{2}$/;   // the only ticker shape a slot order may use; anything else is refused, never thrown on
const L1_WINDOW_CAP_FRACTION_MIRROR = 0.055;           // a test pins this to kalshiLiveLib.L1_WINDOW_CAP_FRACTION; the caller passes the live one

// ---- Release calendars (Nov 3, 2026, EVENT830). A strategy whose entry names a calendar may enter ONLY the window that closes at one of these instants. Frozen in code, append only by a reviewed edit
// (kalshi-scalper/README.md#SLOT-EVENT830): nothing stored, requested or typed on the page can add a date. Each entry carries the window two ways, so both must agree before an order: the UTC close
// Kalshi reports for the market, and the ticker's own window code (Eastern time, YYMMMDDHHMM: 8:30 ET is "0830"). Every row is a US 8:30 AM ET data release; Eastern standard time applies from
// Nov 1, 2026 to Mar 13, 2027, so 8:30 ET is 13:30 UTC (7:30 AM Central). Nov and Dec 2026 only, from workers/EVENT830_CALENDAR.md on the research branch (BEA, Census and the BLS schedule; weekly jobless
// claims by the Thursday rule). Left out on purpose: the holiday-week claims of Nov 26, Dec 24 and Dec 31 (day unconfirmed), and every date after Dec 31, 2026 (no date is guessed).
const calRow = (day, code, kind) => Object.freeze({ closeUtc: day + "T13:30:00Z", window: code, kind });
const SLOT_CALENDARS = Object.freeze({
  EVENT830: Object.freeze([
    calRow("2026-11-05", "26NOV050830", "CLAIMS"), calRow("2026-11-06", "26NOV060830", "JOBS"), calRow("2026-11-10", "26NOV100830", "CPI"),
    calRow("2026-11-12", "26NOV120830", "CLAIMS"), calRow("2026-11-13", "26NOV130830", "PPI"), calRow("2026-11-17", "26NOV170830", "RETAIL"),
    calRow("2026-11-19", "26NOV190830", "CLAIMS"), calRow("2026-11-25", "26NOV250830", "GDP_PCE"),
    calRow("2026-12-03", "26DEC030830", "CLAIMS"), calRow("2026-12-04", "26DEC040830", "JOBS"), calRow("2026-12-10", "26DEC100830", "CPI_CLAIMS"),
    calRow("2026-12-15", "26DEC150830", "PPI"), calRow("2026-12-16", "26DEC160830", "RETAIL"), calRow("2026-12-17", "26DEC170830", "CLAIMS"),
    calRow("2026-12-23", "26DEC230830", "GDP_PCE"),
  ]),
});
// The calendar row a market belongs to, or null. Both the close Kalshi reports (milliseconds) and the ticker's window code must match the SAME row, so a wrong close time or a mislabelled ticker is refused.
function slotCalendarRow(strategy, ticker, closeMs) {
  const name = strategy && strategy.entry ? strategy.entry.calendar : undefined;
  if (name === undefined) return null;
  const rows = Object.prototype.hasOwnProperty.call(SLOT_CALENDARS, name) ? SLOT_CALENDARS[name] : null;
  if (!rows || !isNum(closeMs)) return null;
  const wk = windowKey(String(ticker || ""));
  return rows.find((r) => Date.parse(r.closeUtc) === closeMs && r.window === wk) || null;
}
// The series whose quotes the minute function must read NOW for a calendar strategy, because one of its listed windows is about to enter its entry time. Empty on every other minute, so the bot reads
// nothing extra on a day with no release (and on a release day only around the one minute that can enter). Pure: the caller passes the clock and the strategies.
const SLOT_CALENDAR_LEAD_MS = 30 * 1000;               // read from 30 seconds before the entry window opens, so a function that starts a little early still has the quotes
function slotCalendarSeriesDue(strategies, now) {
  const out = [];
  if (!isNum(now)) return out;
  for (const s of strategies || []) {
    if (!s || !s.entry || s.entry.calendar === undefined) continue;
    const rows = Object.prototype.hasOwnProperty.call(SLOT_CALENDARS, s.entry.calendar) ? SLOT_CALENDARS[s.entry.calendar] : [];
    const due = rows.some((r) => { const c = Date.parse(r.closeUtc); return now >= c - s.entry.leftMaxSec * 1000 - SLOT_CALENDAR_LEAD_MS && now <= c - s.entry.leftMinSec * 1000; });
    if (due) for (const x of s.series) if (!out.includes(x)) out.push(x);
  }
  return out;
}

// The series whose quotes the minute function must read NOW for an EVERY-WINDOW strategy (no calendar) because the 15 minute window it trades is inside its entry span (plus the lead). Used for a market that is not in L1's own
// list (KESTREL's AUD/USD); the caller drops any series already read. Empty outside that span, so it is about one public market read in the minute or two before the entry, never on other minutes. Pure: clock and strategies are passed in.
const SLOT_WINDOW_SEC = 900;
function slotRollingSeriesDue(strategies, now) {
  const out = [];
  if (!isNum(now)) return out;
  const left = SLOT_WINDOW_SEC - (Math.floor(now / 1000) % SLOT_WINDOW_SEC);    // seconds to the next quarter hour close
  for (const s of strategies || []) {
    if (!s || !s.entry || s.entry.calendar !== undefined) continue;
    if (left >= s.entry.leftMinSec && left <= s.entry.leftMaxSec + SLOT_CALENDAR_LEAD_MS / 1000) for (const x of s.series) if (!out.includes(x)) out.push(x);
  }
  return out;
}

// ---- The registry. EMPTY in phase A. An entry is admitted only by a reviewed edit of this array. -----------------------------------------
// Shape of an entry (every field required, unknown fields rejected):
//   id            2 to 10 capitals or digits (it goes into the client order id)
//   readme        path to the pre-registration, e.g. "kalshi-scalper/README.md#SLOT-XYZ"
//   series        non-empty subset of SLOT_SERIES_ALLOWED
//   entry         { sideRule: "yes"|"no"|"favourite"|"cheap", priceMin, priceMax, leftMaxSec, leftMinSec [, oiRiseMin] }   "cheap" buys the side with the LOWER price
//   exit          { stopBid, targetBid, mustExitLeftSec }           bids are on the side held; always an immediate-or-cancel close
//   contractsPerOrder, scaleIn { maxSteps, minGapSec, sameSideOnly: true, requirePriorFilled: true }
//   killRules     { maxConsecutiveLosses, minNet: { afterFills, net } }
//   forwardReadDate  "YYYY-MM-DD", when the forward test is read
//   reviewedAt    "YYYY-MM-DD", the date a human last re-armed it, not after SLOT_LAST_REVIEWED_ON; only results settled on or after it count toward the kill rules, and a kill latch older than it no longer blocks (the only way back on)
// OICORE (Oct 30, 2026, the owner: "i wanna get this live", "start at 5", "scale to 10 quickly"): the research session's GEN6 open interest core on Bitcoin. Pre-registration: kalshi-scalper/README.md#SLOT-OICORE.
// Buys the CHEAPER side (5c to 50c) in the 180 to 120 s before the close when open interest rose by 86,300 contracts or more over the 3 minutes to the candle ending 180 s before the close, and holds to settlement
// (the one reviewed hold exception, SLOT_HOLD_ALLOWED). 5 contracts an order for the first 15 filled trades, then a reviewed edit to 10. Win rate is about 28%, so a losing streak is NORMAL: the streak kill is 18 (a streak of 5
// would end it by chance within days); the real brakes are the net floor below and the slot's dollar caps (lifetime 6% of the sizing base, at most $60), which end it with no loss rule needed.
const SLOT_STRATEGIES = Object.freeze([
  Object.freeze({
    id: "OICORE", readme: "kalshi-scalper/README.md#SLOT-OICORE", series: Object.freeze(["KXBTC15M"]),
    entry: Object.freeze({ sideRule: "cheap", priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, oiRiseMin: 86300 }),
    exit: Object.freeze({ holdToSettle: true }), contractsPerOrder: 10,
    scaleIn: Object.freeze({ maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true }),
    killRules: Object.freeze({ maxConsecutiveLosses: 24, minNet: Object.freeze({ afterFills: 40, net: -6 }) }),
    forwardReadDate: "2026-11-13", reviewedAt: "2026-10-30",
  }),
  // EVENT830 (Nov 3, 2026, a held, capped live probe; pre-registration kalshi-scalper/README.md#SLOT-EVENT830, research record workers/EVENT830_REGISTRATION.md). On a listed US 8:30 AM ET release day only
  // (SLOT_CALENDARS.EVENT830), in the eight L1-free 15 minute markets above, in the window that CLOSES at the release: 3 to 2 minutes before the close, if the YES spread is 10c or less, buy the CHEAPER side
  // when its price is 5c to 50c, hard limit 50c (no slip), 1 contract, held to settlement. BELOW the research bar: the slice was picked after its parent test failed, and the registration's own prior is that it
  // loses (profit factor central 1.05). Kill rules as close as the validator can say them: any time after 40 settled fills the strategy is latched off if its net is below $0 (profit factor under 1.0; the
  // registered line is 1.2, which the validator cannot express), and the streak kill is the most the validator allows (20; at a 19% win rate a 10 loss run is expected). Worst single loss $0.52.
  Object.freeze({
    id: "EVENT830", readme: "kalshi-scalper/README.md#SLOT-EVENT830", series: EVENT830_SERIES,
    entry: Object.freeze({ sideRule: "cheap", priceMin: 0.05, priceMax: 0.5, leftMaxSec: 180, leftMinSec: 120, maxSpread: 0.1, calendar: "EVENT830" }),
    exit: Object.freeze({ holdToSettle: true }), contractsPerOrder: 1,
    scaleIn: Object.freeze({ maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true }),
    killRules: Object.freeze({ maxConsecutiveLosses: 20, minNet: Object.freeze({ afterFills: 40, net: 0 }) }),
    forwardReadDate: "2026-12-07", reviewedAt: "2026-11-05",
  }),
  // XRPYES10 (Nov 10, 2026, the owner granted the favourite-and-hold exception for this strategy only on Nov 10, 2026; it goes live when this is merged and deployed, there is no other switch; pre-registration kalshi-scalper/README.md#SLOT-XRPYES10). XRP 15 minute markets: buy YES when it is 88c to 97c,
  // 9.5 to 10.7 minutes (640 to 570 s) before the close, never NO, 3 contracts (the owner chose 3 on Nov 10, inside today's caps), held to settlement (no 25c stop). BELOW the research bar: selected from about 120 cells, no forward signal yet, and live XRP under L1 was
  // profit factor 0.49 over 86 fills. Kill rules: 3 losses in a row, or net under -$15 at any point from 20 settled fills (3 contracts: about -$2.9 a loss). Worst single loss about $2.92.
  Object.freeze({
    id: "XRPYES10", readme: "kalshi-scalper/README.md#SLOT-XRPYES10", series: Object.freeze(["KXXRP15M"]),
    entry: Object.freeze({ sideRule: "yes", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 640, leftMinSec: 570 }),
    exit: Object.freeze({ holdToSettle: true }), contractsPerOrder: 3,
    scaleIn: Object.freeze({ maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true }),
    killRules: Object.freeze({ maxConsecutiveLosses: 3, minNet: Object.freeze({ afterFills: 20, net: -15 }) }),
    forwardReadDate: "2026-12-14", reviewedAt: "2026-11-10",
  }),
  // KESTREL (Nov 10, 2026, the owner's explicit favourite-and-hold exception for THIS id only; option A; pre-registration kalshi-scalper/README.md#SLOT-KESTREL). AUD/USD 15 minute markets: L1's own entry shape on a market L1 does not trade,
  // the favourite side priced 88c to 97c about 6 minutes before the close (400 to 330 s), 3 contracts, no slip, held to settlement (no 25c stop). BELOW the research bar: 59 cash trades (PF 1.37), best of several probe markets, no counterparty named.
  // Kill rules: 3 losses in a row, or net under -$15 from 20 settled fills. Worst single loss about $2.70 plus the fee. AUD/USD is on exchange shard 0: with no money there it sends nothing and logs shard_short.
  Object.freeze({
    id: "KESTREL", readme: "kalshi-scalper/README.md#SLOT-KESTREL", series: Object.freeze(["KXAUDUSD15M"]),
    entry: Object.freeze({ sideRule: "favourite", priceMin: 0.88, priceMax: 0.97, leftMaxSec: 400, leftMinSec: 330 }),
    exit: Object.freeze({ holdToSettle: true }), contractsPerOrder: 3,
    scaleIn: Object.freeze({ maxSteps: 1, minGapSec: 30, sameSideOnly: true, requirePriorFilled: true }),
    killRules: Object.freeze({ maxConsecutiveLosses: 3, minNet: Object.freeze({ afterFills: 20, net: -15 }) }),
    forwardReadDate: "2026-12-22", reviewedAt: "2026-11-10",
  }),
  // FLOW1 (seller-flow probe, live Nov 4, 2026) was REMOVED the same day after the research session's FLOW1 history test (2,568 windows, low-flow PF 1.13 to 1.23, low minus high -3.6c,
  // p 0.49) and the refinement chat's second out-of-sample block both found no reliable edge. The flowMax entry field and flowFromTrades stay in code; a re-admission is a reviewed edit.
]);

const ENTRY_KEYS = ["sideRule", "priceMin", "priceMax", "leftMaxSec", "leftMinSec"];
// Optional (Oct 30, 2026, the open interest core): the open interest on the market must have risen by at least this many contracts over the 3 minutes to the signal candle, or no order. Absent means no such condition.
const ENTRY_KEYS_OI = ENTRY_KEYS.concat(["oiRiseMin"]);
// Optional (Nov 3, 2026, EVENT830): maxSpread, the widest YES spread (ask minus bid) at which an order may go; calendar, the name of a frozen list in SLOT_CALENDARS (it must be the strategy's own id).
const ENTRY_KEYS_CAL = ENTRY_KEYS.concat(["maxSpread", "calendar"]);
// Optional (Nov 4, 2026, FLOW1): taker flow on the side bought over the 3 minutes before the look must be at or below this (net selling). A missing or unreadable flow means no order.
const ENTRY_KEYS_FLOW = ENTRY_KEYS.concat(["flowMax"]);
const EXIT_KEYS = ["stopBid", "targetBid", "mustExitLeftSec"];
// The ONE reviewed exception to "every exit is before settlement" (the owner, Oct 30, 2026: "we can remove that rule in this specific instance"): a strategy whose id is listed here may hold to
// the close (exit is exactly { holdToSettle: true }: no stop, no target, no sale). The research validated the open interest core held to settlement (profit factor 1.85); selling at 60 s kept about half
// the edge. It stays a loss of at most the order's cost (counted as lost in the shared stop from the moment it exists). Every other strategy keeps the time rule. Adding an id here is a reviewed edit.
// KESTREL added 2026-11-10: the owner's explicit favourite-and-hold exception for this one id only (kalshi-scalper/README.md#SLOT-KESTREL).
const SLOT_HOLD_ALLOWED = Object.freeze(["OICORE", "EVENT830", "XRPYES10", "KESTREL"]);   // FLOW1 was on this list Nov 4, 2026 and left it with its removal the same day   // EVENT830 added Nov 3, 2026: its registration holds every trade to settlement
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
  if (Array.isArray(s.series)) for (const x of s.series) if (Object.prototype.hasOwnProperty.call(SLOT_SERIES_RESERVED, x) && SLOT_SERIES_RESERVED[x] !== s.id) e.push(x + " is reserved for " + SLOT_SERIES_RESERVED[x]);
  if (!exactKeys(s.entry, ENTRY_KEYS) && !exactKeys(s.entry, ENTRY_KEYS_OI) && !exactKeys(s.entry, ENTRY_KEYS_CAL) && !exactKeys(s.entry, ENTRY_KEYS_FLOW)) e.push("entry has the wrong fields");
  else {
    const x = s.entry;
    if (!["yes", "no", "favourite", "cheap"].includes(x.sideRule)) e.push("entry.sideRule must be yes, no, favourite or cheap");
    if (Object.prototype.hasOwnProperty.call(x, "oiRiseMin") && !(isNum(x.oiRiseMin) && x.oiRiseMin >= 1000)) e.push("entry.oiRiseMin must be a number of contracts, at least 1000");
    if (Object.prototype.hasOwnProperty.call(x, "flowMax") && !(isNum(x.flowMax) && x.flowMax >= -1 && x.flowMax <= 0)) e.push("entry.flowMax must be a share from -1 to 0 (net selling)");
    if (Object.prototype.hasOwnProperty.call(x, "maxSpread") && !(isNum(x.maxSpread) && x.maxSpread >= 0.01 && x.maxSpread <= 0.2)) e.push("entry.maxSpread must be 0.01 to 0.20");
    if (Object.prototype.hasOwnProperty.call(x, "calendar") && !(x.calendar === s.id && Object.prototype.hasOwnProperty.call(SLOT_CALENDARS, x.calendar) && SLOT_CALENDARS[x.calendar].length > 0)) e.push("entry.calendar must name this strategy's own frozen calendar in SLOT_CALENDARS");
    if (!isNum(x.priceMin) || !isNum(x.priceMax) || x.priceMin < SLOT_MIN_PRICE || x.priceMax > SLOT_MAX_PRICE || !(x.priceMin < x.priceMax)) e.push("entry price bounds must sit inside " + SLOT_MIN_PRICE + " to " + SLOT_MAX_PRICE + " with priceMin below priceMax");
    if (!isNum(x.leftMaxSec) || !isNum(x.leftMinSec) || x.leftMaxSec > SLOT_ENTRY_LEFT_MAX_SEC || x.leftMinSec < SLOT_ENTRY_LEFT_MIN_SEC || !(x.leftMinSec < x.leftMaxSec)) e.push("entry time left must sit inside " + SLOT_ENTRY_LEFT_MIN_SEC + " to " + SLOT_ENTRY_LEFT_MAX_SEC + " seconds");
  }
  if (isObj(s.exit) && Object.prototype.hasOwnProperty.call(s.exit, "holdToSettle")) {
    if (!(exactKeys(s.exit, ["holdToSettle"]) && s.exit.holdToSettle === true)) e.push("exit.holdToSettle must be the only exit field, and true");
    if (!SLOT_HOLD_ALLOWED.includes(s.id)) e.push("this strategy is not on the reviewed list that may hold to settlement");
  } else if (!exactKeys(s.exit, EXIT_KEYS)) e.push("exit has the wrong fields");
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
    if (!Number.isInteger(k.maxConsecutiveLosses) || k.maxConsecutiveLosses < 1 || k.maxConsecutiveLosses > 30) e.push("killRules.maxConsecutiveLosses must be 1 to 30");
    if (!exactKeys(k.minNet, ["afterFills", "net"])) e.push("killRules.minNet needs afterFills and net");
    else {
      if (!Number.isInteger(k.minNet.afterFills) || k.minNet.afterFills < 5 || k.minNet.afterFills > 100) e.push("killRules.minNet.afterFills must be 5 to 100");
      if (!isNum(k.minNet.net) || k.minNet.net > 0 || k.minNet.net < -SLOT_CAP_CEILINGS.lifetime) e.push("killRules.minNet.net must be zero or a loss no bigger than the lifetime ceiling");
    }
  }
  if (!isDate(s.forwardReadDate)) e.push("forwardReadDate must be YYYY-MM-DD");
  if (!isDate(s.reviewedAt)) e.push("reviewedAt must be YYYY-MM-DD");
  else if (s.reviewedAt > SLOT_LAST_REVIEWED_ON) e.push("reviewedAt must not be after " + SLOT_LAST_REVIEWED_ON + " (a future date would blind the kill rules)");
  return { ok: e.length === 0, errors: e };
}

// The strategies that may act. Fails closed three ways: the switch is off, any entry is invalid (the whole registry is refused, so a typo
// cannot quietly drop one guard and keep the rest), or an id repeats.
function activeSlotStrategiesWith(flags) {
  const f = flags || {};
  const enabled = f.enabled === undefined ? SLOT_ENABLED : f.enabled;
  const registry = f.registry === undefined ? SLOT_STRATEGIES : f.registry;
  if (enabled !== true || !Array.isArray(registry)) return [];
  const ids = new Set();
  for (const s of registry) { if (!validateSlotStrategy(s).ok || ids.has(s.id)) return []; ids.add(s.id); }
  return registry.slice();
}
// The production entry point: no argument, so nothing a caller passes can change the switch or the registry.
const activeSlotStrategies = () => activeSlotStrategiesWith({});
// The ONE gate the wiring uses (docs/SECOND_SLOT_WIRING.md section 0): a pure function of this module's own two constants. Nothing stored, requested or typed on the page can feed it.
const slotActive = () => SLOT_ENABLED === true && SLOT_STRATEGIES.length > 0;
// WATCHING is wider than ENTERING. Entering needs slotActive(). But once any slot order has ever existed, turning the slot off (SLOT_ENABLED=false) or deleting a strategy must NOT orphan a live
// position: its exits, its settle sweep, its dollars in the shared loss stop and window cap, the direction lock and L1's contract clamp all keep running. A constant, not stored data, so nothing
// outside a reviewed edit can move it. The pull request that first admits a strategy MUST set it to true (a gate fails if slotActive() is true while it is false), and it is never set back.
const SLOT_EVER_USED = true;
const slotWatch = () => slotActive() || SLOT_EVER_USED === true;
// Contracts of an order the account may still hold (the conservative reading): a settled or hand-closed order holds none; an order still in flight (no answer yet) is assumed to hold everything
// it asked for, so it can only LOWER what the other engine may sell.
function slotUnsoldOf(t) {
  if (!t || t.settled === true) return 0;
  const want = num(t.count) > 0 ? num(t.count) : 1;
  const status = String(t.status || "").toLowerCase();
  if (status === "sending" || status === "unknown") return want;
  const got = Math.min(num(t.fillCount) > 0 ? num(t.fillCount) : 0, want);
  const sold = num(t.exitCount) > 0 ? num(t.exitCount) : 0;
  return Math.max(0, Math.floor(got - sold + 1e-9));
}
// What L1's hand-sold check must not trust: every entry and exit order id of the slot's orders (their fills are not a sale by hand), plus a marker "ticker:<T>" for every market where a slot
// entry or exit has no clear answer (status or exitStatus sending or unknown). Such an order has NO order id to ignore, so its fill could be read as a hand sale of an L1 order; the marker makes
// closedByHand answer "unknown" for that market, which leaves the L1 order open and counted as lost (the safe direction).
function slotIgnoreSet(orders) {
  const ids = new Set();
  for (const o of orders || []) {
    if (!o) continue;
    if (o.orderId) ids.add(o.orderId);
    if (o.exitOrderId) ids.add(o.exitOrderId);
    if (o.strategy === "SLOT" && o.ticker && (["sending", "unknown"].includes(String(o.status || "").toLowerCase()) || ["sending", "unknown"].includes(String(o.exitStatus || "").toLowerCase()))) ids.add("ticker:" + o.ticker);
  }
  return ids;
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
const normTicker = (x) => String(x === undefined || x === null ? "" : x).trim().toUpperCase();
const normStatus = (x) => String(x === undefined || x === null ? "" : x).trim().toLowerCase();
// null, undefined and "" are NOT zero here (Number(null) is 0, which would turn a missing settledPnl into a free loss): they are unreadable.
const num = (x) => { if (x === null || x === undefined || x === "") return NaN; const n = Number(x); return Number.isFinite(n) ? n : NaN; };
// Decides whether `side` may be bought on `ticker`, from every source that could disagree:
//   l1Orders / slotOrders  the order documents of both collections (money in flight counts; so does ANY order with fills, whatever its status)
//   lock                   the kalshiLiveDirection/{ticker} document { side } read in the same transaction that creates the order (see the design doc)
//   position               the account's signed position in the ticker (yes positive, no negative), or null when it could not be read
// Ticker case and spaces and status case are normalised before comparing, so a lower-cased ticker cannot slip past. Anything unreadable, malformed or contradictory refuses. Pure.
function directionDecision({ ticker, side, l1Orders, slotOrders, lock, position }) {
  if (side !== "yes" && side !== "no") return { allow: false, reason: "the side must be yes or no" };
  if (!ticker) return { allow: false, reason: "no ticker" };
  if (!Array.isArray(l1Orders) || !Array.isArray(slotOrders)) return { allow: false, reason: "the orders could not be read, so the direction is unknown" };
  const want = normTicker(ticker), sides = new Set();
  for (const t of [...l1Orders, ...slotOrders]) {
    if (!t || normTicker(t.ticker) !== want || t.settled === true) continue;
    const holds = num(t.fillCount) > 0 || SLOT_OPEN_STATUSES.includes(normStatus(t.status));
    if (!holds) continue;
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
function isSlotOrder(t) { return !!t && t.strategy === "SLOT" && typeof t.slotId === "string"; }

// ONE accounting rule for a slot order, mirroring kalshiLiveLib.botRisk (a parity gate runs the same fixtures through both) with two deliberate, stricter differences:
//   - an order still in flight (sending / unknown, no fill yet) counts in full as open, because the order may exist at Kalshi;
//   - an unreadable maxCost is assumed to be the biggest order allowed, and an exit with no readable pnl books the whole amount paid as lost.
// Any order with fills counts, whatever its status ('error' after a fill is still money). Returns:
//   counted     it is a slot trade in the figures      net        realised result (settled, plus the sold part of an open order)
//   openCost    dollars still at risk, counted as lost  openContracts  contracts still held      final   the result is complete (kill rules read only these)
//   spend       gross dollars put into the window (maxCost, whether or not later sold or settled), as runL1Tick's windowUsed counts
function accountOrder(t) {
  const z = { counted: false, net: 0, openCost: 0, openContracts: 0, final: false, spend: 0 };
  if (!isSlotOrder(t)) return z;
  const rawCost = num(t.maxCost), cost = rawCost >= 0 ? rawCost : SLOT_CAP_CEILINGS.perOrder;
  const want = num(t.count) > 0 ? num(t.count) : 1, filled = num(t.fillCount) > 0, got = Math.min(filled ? num(t.fillCount) : 0, want);
  const inFlight = !filled && t.settled !== true && ["sending", "unknown"].includes(normStatus(t.status));
  if (!filled && !inFlight) return z;
  if (inFlight) return { counted: true, net: 0, openCost: cost, openContracts: want, final: false, spend: cost };
  const paid = cost * (got / want), sold = num(t.exitCount) > 0 ? Math.min(num(t.exitCount), got) : 0, soldShare = got > 0 ? sold / got : 0;
  const proceeds = sold > 0 && Number.isFinite(num(t.exitProceeds)) ? num(t.exitProceeds) : 0;
  const base = { counted: true, spend: cost };
  if (t.settled === true && t.result === "hand") return { ...z, ...base };                  // closed by hand: not the slot's result (botRisk skips it the same way)
  if (t.settled === true && t.result === "exit") {
    const pnl = num(t.settledPnl);
    return { ...z, ...base, net: Number.isFinite(pnl) ? pnl : -paid, final: true };
  }
  if (t.settled === true && (t.result === "yes" || t.result === "no")) {
    const pnl = num(t.settledPnl), derived = (t.result === t.side ? got - sold : 0) + proceeds - fillCost(t, got, want);
    return { ...z, ...base, net: Number.isFinite(pnl) ? pnl : derived, final: true };      // a null pnl on a settled loss is derived from the result, never zero
  }
  // Open (or settled with a result nobody can read): the sold part is realised, the rest is counted as lost.
  return { ...z, ...base, net: proceeds - paid * soldShare, openCost: paid * (1 - soldShare), openContracts: Math.max(0, got - sold) };
}
// An unreadable or missing ts counts as inside every window (fail closed): the order would otherwise vanish from the daily and lifetime figures.
const inRange = (t, from) => { const ts = num(t.ts); return !Number.isFinite(ts) || ts >= from; };
const openAtRisk = (t) => accountOrder(t).openCost;
const openContracts = (t) => accountOrder(t).openContracts;

// What runL1Tick needs for the WINDOW cap: slot gross spend in a window, on the same terms as runL1Tick's windowUsed (maxCost of every order that is
// or was money in the window, whether or not later sold or settled; slot orders have no add-on). This, and NOT the at-risk figure, feeds windowUsed.
function slotWindowSpent(slotOrders, ticker) {
  const wk = windowKey(normTicker(ticker));
  return (slotOrders || []).filter((t) => t && windowKey(normTicker(t.ticker)) === wk).reduce((a, t) => a + accountOrder(t).spend, 0);
}
// What botRisk needs for the LOSS STOP, in botRisk's own return shape so the wiring can add the two: net (realised result since `since`, including the sold part of
// an order still open), openCost (counted as lost), worst.
function slotRiskForBotRisk(slotOrders, since) {
  const from = Number.isFinite(since) ? since : 0;
  let net = 0, openCost = 0, trades = 0;
  for (const t of slotOrders || []) {
    if (!isSlotOrder(t) || !inRange(t, from)) continue;
    const a = accountOrder(t);
    if (!a.counted) continue;
    trades += 1; net += a.net; openCost += a.openCost;
  }
  return { net, openCost, worst: net - openCost, addonAtRisk: 0, trades };
}
// The full figures the guards read: open dollars total and per window, open contracts per ticker, 24 hour and lifetime nets (open counted as lost).
function slotRiskContract(slotOrders, now) {
  const day = slotRiskForBotRisk(slotOrders, now - 24 * 3600 * 1000), life = slotRiskForBotRisk(slotOrders, 0);
  const byWindow = {}, byTicker = {};
  let openTotal = 0;
  for (const t of slotOrders || []) {
    const a = accountOrder(t);
    if (a.openCost > 0) { openTotal += a.openCost; const w = windowKey(normTicker(t.ticker)); byWindow[w] = (byWindow[w] || 0) + a.openCost; }
    if (a.openContracts > 0) { const k = normTicker(t.ticker); byTicker[k] = (byTicker[k] || 0) + a.openContracts; }
  }
  return { openTotal, openByWindow: byWindow, openContractsByTicker: byTicker, day, lifetime: life };
}

// ---- 3. Kill rules (fail closed, sticky, stay off until a reviewed edit) --------------------------------------------------------------
// Evaluated on one strategy's own final results, in SETTLEMENT order (settledAt if the wiring wrote it, else ts), and STICKY: the strategy is killed if ANY prefix of
// that history trips a rule, so a late win can never un-kill it. Only results on or after reviewedAt count, which is how a reviewed edit re-arms a strategy killed
// by a streak or a net rule; a latch (kalshiSlotControl/killed, written by the wiring in the SAME transaction that records the settle) blocks while latch.killedAt is
// at or after reviewedAt. Stored data can only switch a strategy OFF.
function killCheck(strategy, slotOrders, latch) {
  const re = Date.parse(strategy.reviewedAt + "T00:00:00Z");
  if (latch && isObj(latch) && latch.killedAt !== undefined) {
    const at = Number(latch.killedAt);
    if (!Number.isFinite(at) || !Number.isFinite(re) || at >= re) return { killed: true, reason: "a kill latch is set and no reviewed edit has re-armed " + strategy.id };
  } else if (latch !== null && latch !== undefined) return { killed: true, reason: "the kill latch is unreadable" };
  const when = (t) => { const s = num(t.settledAt); if (Number.isFinite(s)) return s; const ts = num(t.ts); return Number.isFinite(ts) ? ts : Infinity; };
  const mine = (slotOrders || []).filter((t) => isSlotOrder(t) && t.slotId === strategy.id).map((t) => ({ t, a: accountOrder(t), at: when(t) }))
    .filter((x) => x.a.counted && x.a.final && !(x.t.settled === true && x.t.result === "hand") && (!Number.isFinite(re) || x.at >= re)).sort((x, y) => x.at - y.at);
  const k = strategy.killRules.minNet;
  let streak = 0, net = 0, n = 0;
  for (const x of mine) {
    n += 1; net += x.a.net; streak = x.a.net < 0 ? streak + 1 : 0;
    if (streak >= strategy.killRules.maxConsecutiveLosses) return { killed: true, reason: streak + " losses in a row", latch: true };
    if (n >= k.afterFills && net < k.net) return { killed: true, reason: "net $" + net.toFixed(2) + " after " + n + " fills is below $" + k.net.toFixed(2), latch: true };
  }
  return { killed: false, reason: "" };
}

// ---- The ladder, replayed from the strategy's own record (pure) --------------------------------------------------------------------------------
function validLadder(L, strategy) {
  if (!isObj(L) || !Array.isArray(L.steps) || !Array.isArray(L.minBase) || L.steps.length < 1 || L.steps.length !== L.minBase.length) return false;
  if (L.steps[0] !== strategy.contractsPerOrder) return false;
  for (let k = 0; k < L.steps.length; k++) {
    if (!Number.isInteger(L.steps[k]) || L.steps[k] < 1 || L.steps[k] > SLOT_LADDER_MAX_CONTRACTS || !isNum(L.minBase[k]) || L.minBase[k] < 0) return false;
    if (k > 0 && !(L.steps[k] > L.steps[k - 1] && L.minBase[k] >= L.minBase[k - 1])) return false;
  }
  const pos = ["upFills", "upDays", "upNetPerContract", "upPf", "upMaxDrawdownPerContract", "downDrawdownPerContract", "downWindow", "dailyPerContract", "dailyMaxFraction", "dailyCeiling", "stopPerContract", "stopMaxFraction", "stopCeiling"];
  if (pos.some((k) => !(isNum(L[k]) && L[k] > 0))) return false;
  if (!(isNum(L.upWinRate) && L.upWinRate > 0 && L.upWinRate < 1) || !(isNum(L.downWinRate) && L.downWinRate >= 0 && L.downWinRate < L.upWinRate) || !(isNum(L.downNetPerContract) && L.downNetPerContract <= 0)) return false;
  return L.dailyMaxFraction <= 0.12 && L.stopMaxFraction <= 0.12;
}
// One strategy's own final results since reviewedAt, in settlement order (the same order and the same filter as killCheck), plus what its unsettled orders would add if counted as lost.
function ownResults(strategy, slotOrders) {
  const re = Date.parse(strategy.reviewedAt + "T00:00:00Z");
  const when = (t) => { const s = num(t.settledAt); if (Number.isFinite(s)) return s; const ts = num(t.ts); return Number.isFinite(ts) ? ts : Infinity; };
  const rows = [];
  let openWorst = 0;
  for (const t of slotOrders || []) {
    if (!isSlotOrder(t) || t.slotId !== strategy.id) continue;
    const a = accountOrder(t);
    if (!a.counted || (t.settled === true && t.result === "hand")) continue;
    if (!a.final) { openWorst += a.net - a.openCost; continue; }
    const at = when(t);
    if (Number.isFinite(re) && at < re) continue;
    rows.push({ at, net: a.net, id: String(t.id || t.clientOrderId || "") });
  }
  rows.sort((x, y) => x.at - y.at || (x.id < y.id ? -1 : x.id > y.id ? 1 : 0));
  return { rows, openWorst };
}
// Returns { laddered, step, size, fillsAtStep, drawdown, ddStop, dailyCap }. A strategy with no (valid) ladder sends its registry size and keeps the base-scaled caps.
function slotLadderState(strategy, slotOrders, sizingBase) {
  const L = SLOT_LADDERS[strategy && strategy.id];
  const base = isNum(sizingBase) && sizingBase > 0 ? sizingBase : 0;
  if (!strategy || !L || !validLadder(L, strategy)) return { laddered: false, step: 0, size: strategy ? strategy.contractsPerOrder : 0, fillsAtStep: 0, drawdown: 0, ddStop: 0, dailyCap: 0 };
  const { rows, openWorst } = ownResults(strategy, slotOrders);
  const DAY = 86400000, last = L.steps.length - 1;
  let idx = 0, cum = 0, peak = 0, stepAt = Date.parse(strategy.reviewedAt + "T00:00:00Z"), stepPeak = 0, at = [];
  const reset = (x) => { stepAt = x.at; stepPeak = cum; at = []; };
  for (const x of rows) {
    cum += x.net; peak = Math.max(peak, cum); stepPeak = Math.max(stepPeak, cum); at.push(x.net);
    const c = L.steps[idx], ddStep = stepPeak - cum;
    const w = at.slice(-L.downWindow), full = w.length >= L.downWindow;
    const wWin = full ? w.filter((v) => v > 0).length / w.length : 1, wNet = w.reduce((a, v) => a + v, 0);
    const hitDd = ddStep >= L.downDrawdownPerContract * c - 1e-9, hitWin = full && wWin < L.downWinRate, hitNet = full && wNet < L.downNetPerContract * c;
    if (idx > 0 && (hitDd || hitWin || hitNet)) { idx = Math.max(0, idx - (hitDd && hitWin ? 2 : 1)); reset(x); continue; }
    if (idx < last && at.length >= L.upFills && Number.isFinite(stepAt) && x.at - stepAt >= L.upDays * DAY) {
      const wins = at.filter((v) => v > 0), losses = at.filter((v) => v < 0);
      const gw = wins.reduce((a, v) => a + v, 0), gl = -losses.reduce((a, v) => a + v, 0), net = gw - gl;
      const pf = gl > 0 ? gw / gl : (gw > 0 ? Infinity : 0);
      if (wins.length / at.length >= L.upWinRate && net >= L.upNetPerContract * c - 1e-9 && pf >= L.upPf && ddStep < L.upMaxDrawdownPerContract * c) { idx += 1; reset(x); }
    }
  }
  let eff = idx;
  while (eff > 0 && !(base >= L.minBase[eff])) eff -= 1;
  const size = L.steps[eff];
  const baseCaps = slotCaps(base);
  const dailyCap = Math.min(Math.max(baseCaps.daily, L.dailyPerContract * size), L.dailyMaxFraction * base, L.dailyCeiling);
  const ddStop = Math.min(L.stopPerContract * size, L.stopMaxFraction * base, L.stopCeiling);
  const drawdown = Math.max(0, peak - (cum + openWorst));
  return { laddered: true, step: idx, size, fillsAtStep: at.length, drawdown, ddStop, dailyCap };
}

// ---- The one gate every slot order passes ----------------------------------------------------------------------------------------------
// Returns { allowed, count, reasons, cost, cid }. `count` is the wanted count cut down to whatever every cap allows; allowed is false when that is under 1.
// Never throws on bad input. Inputs: strategyId, ticker, side, limit (price of the side bought), step, wanted (optional, default contractsPerOrder), depthAtTouch (size resting at the
// touch being hit), slotOrders and l1Orders (every order of each collection, read completely), slotOrdersComplete (true only if the slot collection was read in full),
// lockTxn (true only when the caller read and wrote kalshiLiveDirection/{ticker} in the SAME transaction that creates the order: no proof, no order), lock, position,
// sizingBase, windowCapFraction (the live L1_WINDOW_CAP_FRACTION), killLatch, secondsLeft, now.
function slotOrderCheckWith(flags, input) {
  const no = (reason) => ({ allowed: false, count: 0, reasons: [reason], cost: 0, cid: null });
  const i = input || {};
  const strategy = activeSlotStrategiesWith(flags).find((s) => s.id === i.strategyId);
  if (!strategy) return no("no active slot strategy with that id (the switch is off, or it is not in the registry)");
  if (typeof i.ticker !== "string" || !SLOT_TICKER_RE.test(i.ticker)) return no("the ticker is not a slot market ticker");
  const series = i.ticker.split("-")[0];
  if (!strategy.series.includes(series)) return no(series + " is not one of this strategy's markets");
  if (i.side !== "yes" && i.side !== "no") return no("the side must be yes or no");
  if (strategy.entry.sideRule !== "favourite" && strategy.entry.sideRule !== "cheap" && strategy.entry.sideRule !== i.side) return no("this strategy only buys " + strategy.entry.sideRule);
  // The open interest condition: no readable rise, or a rise below the line, is no order (fail closed). `oiRise` is the caller's reading of the public candles; the line is the strategy's, in code.
  if (Object.prototype.hasOwnProperty.call(strategy.entry, "flowMax") && !(isNum(i.flow) && i.flow >= -1 && i.flow <= strategy.entry.flowMax + 1e-12)) return no("the taker flow is missing or above " + strategy.entry.flowMax);
  if (Object.prototype.hasOwnProperty.call(strategy.entry, "oiRiseMin") && !(isNum(i.oiRise) && i.oiRise >= strategy.entry.oiRiseMin)) return no("the open interest rise is missing or below " + strategy.entry.oiRiseMin + " contracts");
  // A calendar strategy enters only the window that closes at a listed release (the close Kalshi reports and the ticker's window code must both match one frozen row); a spread rule refuses a missing or wide spread.
  if (Object.prototype.hasOwnProperty.call(strategy.entry, "calendar") && !slotCalendarRow(strategy, i.ticker, i.closeTime)) return no("this market's window is not a listed release window");
  if (Object.prototype.hasOwnProperty.call(strategy.entry, "maxSpread") && !(isNum(i.spread) && i.spread >= 0 && i.spread <= strategy.entry.maxSpread + 1e-9)) return no("the spread is missing or wider than " + strategy.entry.maxSpread);
  if (!Array.isArray(i.slotOrders) || !Array.isArray(i.l1Orders) || i.slotOrdersComplete !== true) return no("the order books were not read in full, so the caps cannot be checked");
  if (i.slotOrders.some((t) => isSlotOrder(t) && !Number.isFinite(num(t.ts)))) return no("a slot order has no readable time, so the loss figures cannot be trusted");
  if (i.lockTxn !== true) return no("no proof that the direction lock was taken in the same transaction as the order");
  const k = killCheck(strategy, i.slotOrders, i.killLatch === undefined ? null : i.killLatch);
  if (k.killed) return no("killed: " + k.reason);
  const e = strategy.entry;
  if (!isNum(i.limit) || i.limit < e.priceMin - 1e-9 || i.limit > e.priceMax + 1e-9) return no("the price is outside the strategy's entry band");
  if (!isNum(i.secondsLeft) || i.secondsLeft > e.leftMaxSec || i.secondsLeft < e.leftMinSec) return no("not inside the strategy's entry time window");
  const d = directionDecision({ ticker: i.ticker, side: i.side, l1Orders: i.l1Orders, slotOrders: i.slotOrders, lock: i.lock, position: i.position });
  if (!d.allow) return no(d.reason);
  // Scale-in. One attempt per step, ever: a step that failed ('no fill', 'error') is NOT retried under the same id. Step n only while step n-1 is still open, and never
  // after any earlier step of this strategy on the ticker was sold (averaging down into a position the strategy just stopped out of).
  const step = i.step;
  if (!Number.isInteger(step) || step < 1 || step > strategy.scaleIn.maxSteps) return no("bad scale-in step");
  const mineHere = i.slotOrders.filter((t) => isSlotOrder(t) && t.slotId === strategy.id && normTicker(t.ticker) === i.ticker);
  if (mineHere.some((t) => t.step === step)) return no("this step was already attempted, and a failed step is not retried");
  if (step > 1) {
    if (mineHere.some((t) => num(t.exitCount) > 0 || t.result === "exit" || t.settled === true)) return no("an earlier step was already sold, so there is no scaling in");
    const prior = mineHere.find((t) => t.step === step - 1 && normStatus(t.status) === "filled" && num(t.fillCount) > 0);
    if (!prior) return no("the previous step has not filled");
    if (!(num(prior.fillCount) - (num(prior.exitCount) > 0 ? num(prior.exitCount) : 0) > 0)) return no("the previous step is no longer open");
    if (!isNum(i.now) || !isNum(prior.ts) || i.now - prior.ts < strategy.scaleIn.minGapSec * 1000) return no("too soon after the previous step");
  }
  if (!(isNum(i.sizingBase) && i.sizingBase > 0) || !(isNum(i.windowCapFraction) && i.windowCapFraction > 0 && i.windowCapFraction <= L1_WINDOW_CAP_FRACTION_MIRROR + 1e-9)) return no("the sizing base or the window cap is not usable");
  if (!isNum(i.now)) return no("no clock");
  const risk = slotRiskContract(i.slotOrders, i.now);
  const caps = slotCaps(i.sizingBase);
  // A laddered strategy (SLOT_LADDERS) has caps that grow with its contract count: a daily loss cap and a drawdown stop from its own peak, in place of the base-scaled daily and lifetime caps.
  const lad = slotLadderState(strategy, i.slotOrders, i.sizingBase);
  if (lad.laddered) caps.daily = lad.dailyCap;
  if (risk.day.worst <= -caps.daily + 1e-9) return no("the slot's own daily loss cap is reached");
  if (lad.laddered) { if (lad.drawdown >= lad.ddStop - 1e-9) return no("the strategy's drawdown stop is reached ($" + lad.drawdown.toFixed(2) + " from its best result)"); }
  else if (risk.lifetime.worst <= -caps.lifetime + 1e-9) return no("the slot's own lifetime loss cap is reached");
  // How many contracts every cap allows. Depth is the top of the book only, so unknown depth refuses rather than guesses.
  if (!isNum(i.depthAtTouch) || !(i.depthAtTouch > 0)) return no("the size resting at the touch is unknown");
  const sizeNow = lad.laddered ? lad.size : strategy.contractsPerOrder;
  const wanted = Number.isInteger(i.wanted) ? i.wanted : sizeNow;
  const reasons = [];
  let n = Math.min(wanted, sizeNow, lad.laddered ? SLOT_LADDER_MAX_CONTRACTS : SLOT_MAX_CONTRACTS_PER_ORDER);
  const openHere = risk.openContractsByTicker[i.ticker] || 0;
  const openLimit = lad.laddered ? Math.min(Math.max(SLOT_MAX_OPEN_CONTRACTS_PER_MARKET, sizeNow), SLOT_LADDER_MAX_CONTRACTS) : SLOT_MAX_OPEN_CONTRACTS_PER_MARKET;
  n = Math.min(n, openLimit - openHere, Math.floor(i.depthAtTouch * SLOT_DEPTH_SHARE + 1e-9));
  const wk = windowKey(i.ticker);
  const l1Used = i.l1Orders.filter((t) => t && windowKey(normTicker(t.ticker)) === wk && (num(t.fillCount) > 0 || SLOT_OPEN_STATUSES.includes(normStatus(t.status)))).reduce((a, t) => a + Math.max(0, (num(t.maxCost) || 0) - (num(t.addonCost) || 0)), 0);
  const slotUsed = slotWindowSpent(i.slotOrders, i.ticker);
  const costOf = (c) => i.limit * c + bot.takerFee(i.limit, c);
  const windowCap = i.windowCapFraction * i.sizingBase;
  // The slot takes at most half of the shared window cap and always leaves one L1 contract of room, so L1's first order in a window is never starved.
  const windowRoom = Math.min(windowCap - l1Used - slotUsed - SLOT_L1_RESERVE, windowCap * SLOT_WINDOW_SHARE - slotUsed);
  // The new order's own cost must fit under what is left of the daily and lifetime loss caps (worst is zero or negative), so one order can never overshoot them.
  const dailyRoom = caps.daily + risk.day.worst, lifeRoom = lad.laddered ? lad.ddStop - lad.drawdown : caps.lifetime + risk.lifetime.worst;
  while (n >= 1) {
    const c = costOf(n);
    if (c <= caps.perOrder + 1e-9 && c <= caps.perWindow - slotUsed + 1e-9 && c <= caps.openTotal - risk.openTotal + 1e-9 && c <= windowRoom + 1e-9 && c <= dailyRoom + 1e-9 && c <= lifeRoom + 1e-9) break;
    n -= 1;
  }
  if (n < 1) return no("no whole contract fits the caps (per order, per market, depth share, window, total, the shared window limit, or what is left of the daily and lifetime loss caps)");
  if (n < wanted) reasons.push("cut from " + wanted + " to " + n + " by the caps");
  let cid;
  try { cid = slotClientOrderId(strategy.id, i.ticker, step); } catch (err) { return no("the client order id could not be built"); }
  return { allowed: true, count: n, reasons, cost: Number(costOf(n).toFixed(4)), cid };
}
// The production gate: no flags argument, so nothing a caller passes can turn the switch on or add a strategy.
const slotOrderCheck = (input) => slotOrderCheckWith({}, input);

// ---- 5. Own contracts only: how many a slot close may sell -------------------------------------------------------------------------------
// min(this order's unsold filled contracts, what the account holds on that side minus what every OTHER engine still holds there). Zero when the order is not an
// open, filled, unsettled slot order (settled, closed by hand, errored or unfilled orders sell nothing), when the account holds nothing or the opposite side (a sell then would OPEN
// the opposite position), when the position or the other engines' holding is unreadable, or when the close lease on the market is not held. `othersUnsold` is the sum of
// the unsold contracts of L1 and of the slot's other orders on that ticker and side. The caller takes claimClose(store, ticker, "slot", now) BEFORE reading the position.
function slotSellCount({ order, position, haveClaim, othersUnsold }) {
  if (haveClaim !== true || !isSlotOrder(order) || (order.side !== "yes" && order.side !== "no") || !isNum(position) || !isNum(othersUnsold) || othersUnsold < 0) return 0;
  if (normStatus(order.status) !== "filled" || order.settled === true) return 0;
  const want = num(order.count) > 0 ? num(order.count) : 1, got = Math.min(num(order.fillCount) || 0, want);
  const own = Math.floor(got - (num(order.exitCount) > 0 ? num(order.exitCount) : 0) + 1e-9);
  if (!(own > 0)) return 0;
  const holding = order.side === "yes" ? Math.max(0, position) : Math.max(0, -position);
  return Math.max(0, Math.min(own, Math.floor(holding - othersUnsold + 1e-9)));
}
// What a filled order really cost in cash (Nov 7, 2026, the owner: "have the bot's stops read fill-booked (real cash) P/L"). An order is booked at its limit
// price plus fee (maxCost) when sent; the fill is usually better, so a win was booked low and a loss high, about $30 a week worse than cash. Once the answer carries
// the average fill price and the per-contract fee, the cost of the contracts that filled is (price of the side bought + fee) x contracts. Kalshi gives averageFillPrice as the YES
// price, so a NO order pays 1 minus it. Anything unreadable, or a cash figure above the limit booking, falls back to the limit booking (fails closed). An order still OPEN is
// never booked at cash: it stays at its worst case in the stops. kalshiLiveLib has an identical copy (a test pins them equal), so a slot result and an L1 result stay on one footing.
function fillCost(t, got, want) {
  const worst = num(t.maxCost) * (got / want);
  if (!(got > 0) || !(want > 0)) return worst;
  const avg = num(t.averageFillPrice), fee = num(t.averageFeePaid);
  if (t.averageFillPrice === null || t.averageFillPrice === undefined || t.averageFillPrice === "" || !Number.isFinite(avg) || !(avg > 0 && avg < 1)) return worst;
  if (t.averageFeePaid === null || t.averageFeePaid === undefined || t.averageFeePaid === "" || !Number.isFinite(fee) || !(fee >= 0 && fee < 1)) return worst;
  const side = t.side === "yes" ? avg : t.side === "no" ? 1 - avg : NaN;
  if (!Number.isFinite(side) || !Number.isFinite(worst)) return worst;
  const cash = (side + fee) * got;
  return cash <= worst + 1e-9 ? cash : worst;
}
// The same pnl rule as kalshiLiveLib.settledFields (a test pins them equal), so a slot result and an L1 result are on one footing in the shared loss stop.
// The slot exit engine records a completed early sale with slotSettledFields(order, "exit") (settled: true, result: "exit", the realised settledPnl), exactly as L1's exit
// watch does, so a stop-out is a loss in the shared stop the moment it happens and not only when a settle sweep runs. The wiring also writes settledAt beside it.
function slotSettledFields(t, result) {
  const want0 = num(t.count) > 0 ? num(t.count) : 1, got0 = Math.min(num(t.fillCount), want0);
  const sold = num(t.exitCount) > 0 ? Math.min(num(t.exitCount), got0) : 0;
  const proceeds = sold > 0 && Number.isFinite(num(t.exitProceeds)) ? num(t.exitProceeds) : 0;
  return { settled: true, result, settledPnl: Number((((result === t.side ? got0 - sold : 0)) + proceeds - fillCost(t, got0, want0)).toFixed(4)) };
}

// ---- Named entry points for the later wiring ---------------------------------------------------------------------------------------------
// There is ONE entry gate, slotOrderCheck. The earlier slotMayEnter and slotSideRule were removed: they accepted a caller-built strategy, hard-coded the position and skipped
// the kill, band, time and step checks, which made them a way around the gate.
const validateStrategy = (entry) => validateSlotStrategy(entry);

// The contract the later L1 wiring reads. windowSpent (gross, sold or not) is what feeds runL1Tick's windowUsed; the slotRiskForBotRisk figures feed botRisk;
// openAtRisk is informational only and must NOT be used for the window cap, because a sold position still occupies its window.
function slotRiskForL1({ slotOrders, windowKey: wk, now }) {
  const orders = Array.isArray(slotOrders) ? slotOrders : [];
  const inWindow = orders.filter((t) => t && windowKey(normTicker(t.ticker)) === wk);
  const day = slotRiskForBotRisk(orders, now - 24 * 3600 * 1000);
  return { windowSpent: inWindow.reduce((a, t) => a + accountOrder(t).spend, 0), openAtRisk: inWindow.reduce((a, t) => a + accountOrder(t).openCost, 0), settledPnl24h: day.net, openCost24h: day.openCost };
}

// Kill rules on one strategy's orders, without a stored latch (the latch is applied by killCheck when the wiring reads it).
const slotKillStatus = (orders, strategy) => killCheck(strategy, orders, null);

// The shape of a kalshiSlotOrders document. The document id is the client order id. Money fields match an L1 order so the pure functions read them unchanged.
function slotOrderRecord({ strategyId, ticker, side, step, count, limit, maxCost, ts }) {
  const cid = slotClientOrderId(strategyId, ticker, step);
  return { id: cid, clientOrderId: cid, strategy: "SLOT", slotId: strategyId, ticker, side, step, count, limit, maxCost, ts,
    status: "sending", fillCount: 0, settled: false, settledPnl: null, exitCount: 0, exitProceeds: 0 };
}

module.exports = {
  validateStrategy, slotOrderCheck, slotRiskForL1, slotKillStatus, slotOrderRecord,
  SLOT_ENABLED, SLOT_STRATEGIES, SLOT_HOLD_ALLOWED, SLOT_SERIES_ALLOWED, SLOT_MAX_CONTRACTS_PER_ORDER, SLOT_MAX_OPEN_CONTRACTS_PER_MARKET, SLOT_MAX_SCALE_STEPS, SLOT_CAP_FRACTIONS, SLOT_CAP_CEILINGS, slotCaps,
  SLOT_LIMIT_SLIP, SLOT_LIMIT_SLIP_MAX, slotLimitFor, SLOT_SKIP_BELOW, SLOT_SKIP_BELOW_MAX, slotSkipsPrice,
  EVENT830_SERIES, SLOT_SERIES_RESERVED, SLOT_CALENDARS, slotCalendarRow, slotCalendarSeriesDue, slotRollingSeriesDue, SLOT_CALENDAR_LEAD_MS,
  SLOT_LADDERS, SLOT_LADDER_MAX_CONTRACTS, slotLadderState, validLadder,
  SLOT_DEPTH_SHARE, SLOT_OPEN_STATUSES, SLOT_WINDOW_SHARE, SLOT_L1_RESERVE,
  SLOT_LAST_REVIEWED_ON, L1_WINDOW_CAP_FRACTION_MIRROR,
  validateSlotStrategy, activeSlotStrategies, slotActive, slotWatch, SLOT_EVER_USED, slotUnsoldOf, slotIgnoreSet, slotClientOrderId, slotExitClientOrderId, slotOrderDocId, windowKey, directionDecision,
  openAtRisk, slotWindowSpent, slotRiskForBotRisk, slotRiskContract, killCheck, slotSellCount, slotSettledFields, fillCost,
  // Test-only: the flags-taking variants. Production code must call slotOrderCheck and activeSlotStrategies (a gate fails if the wiring references this).
  _testOnly: Object.freeze({ slotOrderCheckWith, activeSlotStrategiesWith }),
};
