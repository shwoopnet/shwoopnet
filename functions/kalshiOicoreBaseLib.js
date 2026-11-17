"use strict";
// OICORE's sizing base (Nov 16, 2026, the owner: "i want it to go based off account balance, we can move between shards if it runs out"; the Risk Analyst reviews the numbers).
// OICORE's size, its per order, daily and drawdown figures are worked out from a base. Until now that base was prediction cash only. For OICORE ALONE it is now prediction cash plus the perps account's equity,
// so the owner's total account sizes it, and ONLY when the perps figure is fresh. Everything else keeps the prediction cash base: the account stops (12% a day, the 40% hard stop), the window cap, the other seats' caps and L1's
// ladder never see the perps figure (gate AT5 allows this one file and nothing else). Fail closed: a missing, stale, non-finite or negative perps figure gives prediction cash only, which is the cap of docs/RISK_CORE.md and the
// size cap (SLOT_LADDERS.OICORE.sizeCapFraction), so a failure of the perps read can only make OICORE smaller, never larger.
//
// Pure: no I/O, no clock (the caller passes `now`). The caller reads the perps document and hands it in.
const STRATEGY_ID = "OICORE";
const MIN_PREDICTION_CASH = 150;         // OICORE sends nothing while the prediction cash base is under this (dollars; the Risk Analyst's guard)
const PERPS_STALE_MS = 20 * 60000;       // the document is refreshed every 5 minutes; older than 20 minutes is treated as missing (same line the page uses)
const CLOCK_SKEW_MS = 60000;             // a document stamped more than a minute in the future is not trusted

// { base, source, perps } where source is "total" or "prediction_only". `predictionBase` is the sizing base the tick already worked out (prediction cash less saved).
function oicoreBase({ predictionBase, perpsDoc, now } = {}) {
  const pred = Number(predictionBase);
  if (!Number.isFinite(pred) || !(pred > 0)) return { base: 0, source: "prediction_only", perps: 0 };
  const d = perpsDoc && typeof perpsDoc === "object" ? perpsDoc : null;
  const eq = d ? Number(d.equity) : NaN, at = d ? Number(d.at) : NaN, t = Number(now);
  if (!d || !Number.isFinite(eq) || !(eq > 0) || !Number.isFinite(at) || !Number.isFinite(t)) return { base: pred, source: "prediction_only", perps: 0 };
  const age = t - at;
  if (age > PERPS_STALE_MS || age < -CLOCK_SKEW_MS) return { base: pred, source: "prediction_only", perps: 0 };
  return { base: Number((pred + eq).toFixed(2)), source: "total", perps: Number(eq.toFixed(2)) };
}

module.exports = { STRATEGY_ID, MIN_PREDICTION_CASH, PERPS_STALE_MS, CLOCK_SKEW_MS, oicoreBase };
