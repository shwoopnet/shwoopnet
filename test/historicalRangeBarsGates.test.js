'use strict';
// fetchHistoricalRangeBars is what lets the trade detail modal show "how
// this trade played out" for a CLOSED position -- unlike every other
// history fetch in this file, it has to reach an arbitrary PAST date
// range, not "the most recent N bars". These gates pin the request it
// actually builds: the right interval for the trade's own span, and an
// end_date that reaches past the exit (so the exit bar itself is
// included).

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function lift(name) {
  const start = html.indexOf('  function ' + name + '(');
  assert.notStrictEqual(start, -1, 'could not find function ' + name + ' in index.html');
  let depth = 0;
  const open = html.indexOf('{', start);
  for (let j = open; j < html.length; j++) {
    if (html[j] === '{') depth++;
    else if (html[j] === '}') { depth--; if (depth === 0) return html.slice(start, j + 1); }
  }
  throw new Error('unbalanced braces for ' + name);
}

function build(fetchImpl) {
  const src = `
    var TWELVE_DATA_URL = 'https://proxy.example/twelvedata/time_series';
    var ALPACA_CRYPTO_DATA_BASE = 'https://data.alpaca.markets/v1beta3/crypto/us';
    function twelveDataProxyHeaders(){ return { Authorization: 'Bearer test' }; }
    function alpacaHeaders(){ return { 'APCA-API-KEY-ID': 'k', 'APCA-API-SECRET-KEY': 's' }; }
    var fetch = FETCH_IMPL;
    ${lift('twelveDataDateParam')}
    ${lift('fetchHistoricalRangeBars')}
    return fetchHistoricalRangeBars;
  `;
  return new Function('FETCH_IMPL', src)(fetchImpl);
}

function jsonResponse(body) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body) });
}

function main() {
  return (async () => {
    // ---- Same-day equities trade: 5-minute bars ----
    {
      let capturedUrl;
      const fetchHistoricalRangeBars = build((url) => { capturedUrl = url; return jsonResponse({ values: [
        { open:'10', high:'11', low:'9', close:'10.5', volume:'100', datetime:'2026-09-08 14:35:00' },
        { open:'10.5', high:'11', low:'10', close:'10.8', volume:'80', datetime:'2026-09-08 18:00:00' },
      ] }); });
      const entryTime = new Date('2026-09-08T14:35:00Z');
      const exitTime = new Date('2026-09-08T18:00:00Z');
      const result = await fetchHistoricalRangeBars('SOFI', entryTime, exitTime);
      assert.ok(capturedUrl.includes('interval=5min'), `a same-day trade must fetch 5min bars, got: ${capturedUrl}`);
      assert.strictEqual(result.tf, '5m');
      assert.strictEqual(result.data.length, 2);
      assert.ok(capturedUrl.includes('end_date='), 'end_date must be set so the window reaches the exit');
      // end_date must be AT OR AFTER the exit, not before it -- otherwise
      // the exit bar itself would never be in the response.
      const endDateParam = decodeURIComponent(capturedUrl.match(/end_date=([^&]+)/)[1]).replace(' ', 'T') + 'Z';
      assert.ok(new Date(endDateParam).getTime() >= exitTime.getTime(), 'end_date must not be before the trade\'s own exit');
      console.log('G1 PASS a same-day equities trade fetches 5min bars with end_date past the exit');
    }

    // ---- Multi-day equities trade (an ORB held across sessions): 30-minute bars ----
    {
      let capturedUrl;
      const fetchHistoricalRangeBars = build((url) => { capturedUrl = url; return jsonResponse({ values: [
        { open:'10', high:'11', low:'9', close:'10.5', volume:'100', datetime:'2026-09-03 14:35:00' },
        { open:'10.5', high:'11', low:'10', close:'10.8', volume:'80', datetime:'2026-09-08 18:00:00' },
      ] }); });
      const result = await fetchHistoricalRangeBars('SOFI', new Date('2026-09-03T14:35:00Z'), new Date('2026-09-08T18:00:00Z'));
      assert.ok(capturedUrl.includes('interval=30min'), `a multi-day (< 10 day) hold must fetch 30min bars, got: ${capturedUrl}`);
      assert.strictEqual(result.tf, '30m');
      console.log('G2 PASS a multi-day equities hold (ORB across sessions) fetches 30min bars');
    }

    // ---- Long-span equities trade: daily bars, non-intraday tf label ----
    {
      let capturedUrl;
      const fetchHistoricalRangeBars = build((url) => { capturedUrl = url; return jsonResponse({ values: [
        { open:'10', high:'11', low:'9', close:'10.5', volume:'100', datetime:'2026-06-01 00:00:00' },
        { open:'10.5', high:'11', low:'10', close:'10.8', volume:'80', datetime:'2026-09-08 00:00:00' },
      ] }); });
      const result = await fetchHistoricalRangeBars('SOFI', new Date('2026-06-01T14:35:00Z'), new Date('2026-09-08T18:00:00Z'));
      assert.ok(capturedUrl.includes('interval=1day'), `a long hold must fetch daily bars, got: ${capturedUrl}`);
      assert.strictEqual(result.tf, '1M', 'the tf label must not be an INTRADAY_TFS value (e.g. "1D") for daily bars, or axis labels would show time-of-day on a daily chart');
      console.log('G3 PASS a long-span equities trade fetches daily bars with a non-intraday axis label');
    }

    // ---- A failed/empty upstream response rejects rather than silently returning nothing ----
    {
      const fetchHistoricalRangeBars = build(() => jsonResponse({ values: [] }));
      let threw = false;
      try {
        await fetchHistoricalRangeBars('SOFI', new Date('2026-09-08T14:35:00Z'), new Date('2026-09-08T18:00:00Z'));
      } catch (err) {
        threw = true;
      }
      assert.ok(threw, 'no usable data must reject, not resolve with an empty/fabricated chart');
      console.log('G5 PASS no usable historical data rejects instead of silently resolving empty');
    }

    console.log('\nAll historical range bars gates passed.');
  })();
}

main().catch((err) => { console.error(err); process.exit(1); });
