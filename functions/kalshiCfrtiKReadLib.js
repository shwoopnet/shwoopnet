// Keyless reader of the Bitcoin perpetual's public one minute candles. The ticker is fixed here: nothing the engine or a caller passes can read another market.
// liveRequest, fetch and the GET verb are injected by index.js (no signing, 3 s abort, no retry).
function perpCandleReader(liveRequest, fetchFn) {
  return async ({ startTs, endTs, timeoutMs }) => {
    const r = await liveRequest({ fetchFn, method: "GET", path: "/margin/markets/KXBTCPERP/candlesticks",
      params: { period_interval: "1", start_ts: String(startTs), end_ts: String(endTs) }, timeoutMs, noRetry: true });
    return { status: r.status, candles: r.status === 200 && r.body && Array.isArray(r.body.candlesticks) ? r.body.candlesticks : null };
  };
}

module.exports = { perpCandleReader };
