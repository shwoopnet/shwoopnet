// Pure helpers for the Kalshi relay. No Firebase imports, so the
// repo's plain-node tests can load this without installing anything.

const KALSHI_SERIES = ["KXBTC15M", "KXGOLD15M"];

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

module.exports = { KALSHI_SERIES, kalshiNum, trimMarket };
