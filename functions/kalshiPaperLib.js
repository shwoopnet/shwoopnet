"use strict";
// The paper tracker (PAPER1, kalshi-scalper/README.md, "Pre-registration: PAPER1"): what L1's rule WOULD have bought on a few candidate markets, one contract, no money, and what each would have
// earned. KEYLESS by construction: public market reads only, no signing, no key, no /portfolio call, no order of any kind, no secret on the function that runs it. Its records live in their own
// collection (`kalshiPaperOrders`) and are never shown next to the live record. Nothing here is imported by the trading code, and a failure here cannot touch an order.
const bot = require("./kalshiSignalLib");

// Fixed by the registration, not by any stored value: a candidate is added by a code edit and a README entry written before its first entry.
const PAPER_SERIES = ["KXAUDUSD15M", "KXUSDCAD15M", "KXNATGAS15M"];
const PAPER_BAND = [0.88, 0.97];               // L1's band (the favourite's price)
const PAPER_WINDOW_MS = [330000, 400000];      // L1's window: about 6 minutes before the close
const FEE_RATE = 0.07;
// The minutes of each quarter hour in which an entry can exist: the window is 5.5 to 6.7 minutes before a close, which is minute 8 or 9, with a minute either side for a late or early run.
const ENTRY_MINUTES = (() => { const out = []; for (let m = Math.floor((900000 - PAPER_WINDOW_MS[1]) / 60000) - 1; m <= Math.floor((900000 - PAPER_WINDOW_MS[0]) / 60000) + 1; m++) out.push(m); return out; })();
const minuteOfQuarter = (now) => Math.floor(now / 60000) % 15;
const num = (v) => (v === null || v === undefined || v === "" ? NaN : Number(v));
const r4 = (x) => Math.round(x * 10000) / 10000;

// L1's pick, restated here so this file shares no code with the trading path (a test asserts it agrees with `l1Pick` on a grid of quotes): the favourite whose price is in the band, YES at its ask or NO
// at one minus the bid, from a real two sided book.
function pick(m) {
  const bid = num(m.yes_bid_dollars), ask = num(m.yes_ask_dollars);
  if (!bot.validQuote(Number.isFinite(bid) ? bid : null, Number.isFinite(ask) ? ask : null)) return null;
  const lo = PAPER_BAND[0] - 1e-9, hi = PAPER_BAND[1] + 1e-9;
  if (r4(ask) >= lo && r4(ask) <= hi) return { side: "yes", price: r4(ask) };
  const no = r4(1 - bid);
  if (no >= lo && no <= hi) return { side: "no", price: no };
  return null;
}
const inWindow = (m, now) => { const left = Date.parse(m.close_time) - now; return Number.isFinite(left) && left >= PAPER_WINDOW_MS[0] && left <= PAPER_WINDOW_MS[1]; };
// The research's fee model (kalshi-scalper `scalps.fee`): 7% x p x (1 - p) per contract, not rounded up to a cent per order, so paper figures compare with every earlier result.
const fee = (price, mult = 1) => FEE_RATE * mult * price * (1 - price);
const dayOf = (iso) => String(iso || "").slice(0, 10);

function entryDoc(series, m, pk, now) {
  return { strategy: "PAPER", candidate: series, ticker: m.ticker, side: pk.side, price: pk.price, count: 1, ts: now, closeTime: m.close_time, day: dayOf(m.close_time), settled: false };
}
function settleFields(doc, result) {
  const won = result === doc.side ? 1 : 0;
  return { settled: true, result, pnl: r4(won - doc.price - fee(doc.price)), pnlStress: r4(won - doc.price - fee(doc.price, 1.2)) };
}

// One minute of the tracker. store = { openDocs(): [{id, data}], create(id, doc): Promise<boolean> (false when it exists), update(id, patch) }; fetchSeries(series): open markets; fetchMarket(ticker): one market.
// Idle (no read of Kalshi at all) outside the entry minutes when nothing is waiting to settle. Never throws; each candidate and each settlement is independent.
async function runPaperTick({ store, fetchSeries, fetchMarket, now, log = () => {} }) {
  const out = { entries: 0, settled: 0, idle: false };
  const open = await store.openDocs();
  const entryMinute = ENTRY_MINUTES.includes(minuteOfQuarter(now));
  if (!entryMinute && !open.length) { out.idle = true; return out; }
  if (entryMinute) {
    for (const series of PAPER_SERIES) {
      try {
        for (const m of (await fetchSeries(series)) || []) {
          if (!m || !m.ticker || !inWindow(m, now)) continue;
          const pk = pick(m);
          if (!pk) continue;
          if (await store.create(m.ticker, entryDoc(series, m, pk, now))) out.entries++;
        }
      } catch (e) { log("paper entries " + series + ": " + String((e && e.message) || e).slice(0, 120)); }
    }
  }
  for (const d of open) {
    try {
      if (!(Date.parse(d.data.closeTime) < now - 30000)) continue;
      const mk = await fetchMarket(d.data.ticker);
      const r = mk && mk.result;
      if (r !== "yes" && r !== "no") continue;
      await store.update(d.id, settleFields(d.data, r));
      out.settled++;
    } catch (e) { log("paper settle " + d.id + ": " + String((e && e.message) || e).slice(0, 120)); }
  }
  return out;
}

// The registered read, run ONCE per candidate on or after 2026-11-30 (never to chase a pass): at least 300 entries on at least 10 days, mean net above zero, day clustered z at least 2.1, both halves of
// the days positive, positive with fees x1.2. rows = settled paper documents of ONE candidate. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.
const BAR = { minN: 300, minDays: 10, z: 2.1, stress: 1.2, earliestRead: "2026-11-30" };
function clusterZ(rows) {
  const n = rows.length;
  if (n < 2) return { mean: 0, z: 0 };
  const mean = rows.reduce((a, r) => a + r.pnl, 0) / n, by = {};
  for (const r of rows) by[r.day] = (by[r.day] || 0) + (r.pnl - mean);
  const se = Math.sqrt(Object.values(by).reduce((a, v) => a + v * v, 0)) / n;
  return { mean, z: se > 0 ? mean / se : 0 };
}
function bar(rows) {
  const settled = (rows || []).filter((r) => r && r.settled === true && Number.isFinite(Number(r.pnl)));
  const days = [...new Set(settled.map((r) => r.day))].sort();
  const { mean, z } = clusterZ(settled);
  const firstDays = new Set(days.slice(0, Math.floor(days.length / 2)));
  const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const h1 = avg(settled.filter((r) => firstDays.has(r.day)).map((r) => r.pnl)), h2 = avg(settled.filter((r) => !firstDays.has(r.day)).map((r) => r.pnl));
  const stress = avg(settled.map((r) => (Number.isFinite(Number(r.pnlStress)) ? r.pnlStress : r.pnl)));
  const s = { n: settled.length, days: days.length, mean, z, h1, h2, stress };
  if (s.n < BAR.minN || s.days < BAR.minDays) return { verdict: "NOT_ENOUGH_DATA", stats: s };
  return { verdict: mean > 0 && z >= BAR.z && h1 > 0 && h2 > 0 && stress > 0 ? "NOT_YET_FALSIFIED" : "FALSIFIED", stats: s };
}

module.exports = { PAPER_SERIES, PAPER_BAND, PAPER_WINDOW_MS, ENTRY_MINUTES, BAR, minuteOfQuarter, pick, inWindow, fee, entryDoc, settleFields, runPaperTick, bar, clusterZ };
