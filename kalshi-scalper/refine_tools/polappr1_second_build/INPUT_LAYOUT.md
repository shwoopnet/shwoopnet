# POLAPPR1 second build: made-up inputs and layout (Nov 13, 2026). No real figure, no expected output.

The scorer's input is a CONVERTED table, not the raw pull folders: one JSON object per MARKET, one per line,
in a file called cand_all.jsonl (plus a marker file, POLAPPR1_PULL_COMPLETE, that only says the pull is complete;
you do not need it to test a second build). The raw pull folders (manifest plus gz answers) are the converter's
input; you can ignore them and test on the converted rows.

Row fields:
- t: market ticker. e: event ticker. s: series ticker (the family follows from the series, see the registration).
- ct: market close time, unix seconds. res: "yes" or "no" (the settled result of the market).
- src: free text. c: hourly candles, ascending, each [end_ts, yes_ask, yes_bid, price, volume]:
  end_ts = candle end, unix seconds; yes_ask, yes_bid, price = DOLLAR STRINGS with 4 decimals ("0.3200", 0 to 1,
  not cents); volume = a string. A candle may have a null or empty price field in real data.
- An event's close is the latest close among its markets in the file (the registration, "event close").
- Thirds are decided by the cut file entries for each family, in POL_APPR1_CUTS.json (and POL_APPR1_CUTS_A3.json for
  APPR_538): TRAIN ct < cut1, VALIDATE cut1 <= ct < cut2, HELD-OUT ct >= cut2, by the event's close. The made-up
  events use no entry of the cut files' event lists: they are placed by close time against the APPR_DAILY cuts
  (the registration's rule for an event that is not listed). All made-up events here close BEFORE cut2, so none is
  held-out.

MADEUP_CAND.jsonl: 4 made-up approval events of series KXTRUMPAPPROVE (2 closing in TRAIN, 2 in VALIDATE), 3 markets
each, plus a generic-ballot event of series KXGENERICBALLOTVOTEHUB closing in the GCB TRAIN range (2 markets), with
invented tickers, closes, results and hourly prices. They exist only to run your reader and compare it with mine
on the same rows; the prices are random walks and mean nothing.
