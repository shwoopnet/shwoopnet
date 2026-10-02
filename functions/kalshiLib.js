// Pure helpers for the Kalshi relay and recorder. No Firebase imports, so the
// repo's plain-node tests can load this without installing anything.

const KALSHI_SERIES = ["KXBTC15M", "KXGOLD15M"];
const SNAPSHOT_BUCKET_MS = 60 * 1000;
const SNAPSHOT_TTL_MS = 30 * 24 * 60 * 60 * 1000;

function kalshiNum(x) {
  const n = parseFloat(x);
  return Number.isFinite(n) ? n : null;
}

// Kalshi quotes are dollar strings ("0.0950"). Trim to the fields we use.
function trimMarket(series, m) {
  return {
    series,
    ticker: m.ticker,
    closeTime: m.close_time,
    strike: m.floor_strike == null ? null : m.floor_strike,
    yesBid: kalshiNum(m.yes_bid_dollars),
    yesBidSz: kalshiNum(m.yes_bid_size_fp),
    yesAsk: kalshiNum(m.yes_ask_dollars),
    yesAskSz: kalshiNum(m.yes_ask_size_fp),
    last: kalshiNum(m.last_price_dollars),
  };
}

function bucketStart(tsMs) {
  return Math.floor(tsMs / SNAPSHOT_BUCKET_MS) * SNAPSHOT_BUCKET_MS;
}

// More than one invocation can run for the same minute (Cloud Scheduler can
// deliver twice, and a redeploy briefly overlaps instances). Anything that
// must happen once per market per minute has to key on something every
// invocation computes identically. Using the bucket start, not "now", is what
// makes two runs a few hundred ms apart land on the same document.
function snapshotId(ticker, tsMs) {
  return ticker + "_" + bucketStart(tsMs);
}

function snapshotDoc(market, tsMs) {
  const b = bucketStart(tsMs);
  return Object.assign({}, market, { bucket: b, recordedAt: tsMs, expireAtMs: b + SNAPSHOT_TTL_MS });
}

module.exports = {
  KALSHI_SERIES, SNAPSHOT_BUCKET_MS, SNAPSHOT_TTL_MS,
  kalshiNum, trimMarket, bucketStart, snapshotId, snapshotDoc,
};
