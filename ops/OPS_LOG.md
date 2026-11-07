# Ops log (ops-coo)

## 2026-11-06 evening US Central (first run, owner authorized)
Lifetime cost (first look, no earlier entry): main $1,012.95 (context 491k of 1M), V2 $857.75 (context 639k, compaction at 784k), Refinement $335.26 (context 249k). Rate limit: allowed, not on overage.

Calls (2 of 5):
1. trig_01RYwynqMXjikSmWS52refAm (Research director every 3 days, into Recaps session): enabled true -> false. Duplicate of trig_01Far5BcpuS5Mya1ehBp5dfB, same cron (1:23 PM Central every 3 days), no credit guard line. Undo: update_trigger enabled=true.
2. trig_01Far5BcpuS5Mya1ehBp5dfB (Research director check, into main session): prompt extended only by appending the standing bans and the refinement-circling and total-tried asks from the disabled duplicate; credit guard text untouched. Undo: remove the final "Folded in Nov 6" sentence.

Drafted, not done:
- trig_01USRMUWaukA1Rwo1jdMbc4U FWD2 spread read (Nov 17): NOT superseded. FWD2 reads the bot's own live orders (seen.bid and seen.ask, 250 fills or Dec 1); V2's Nov 12 fwd_reads.py reads fresh public candles. Kept.
- trig_019atfFV5KqHEmxd7a2seAAJ Read E3F and FWD1 (Nov 16, an Oct 13 reminder): older than V2's handoff; ask V2 whether E3F, FWD1 and VOL1 are still wanted, else disable.
- Six disabled reminders on archived session_01YBtv2XtdXEa2LKpXpstiAU (trig_017bKH2FaegXfaKzuE9wkK2n, trig_01S8xWT6V35hZu6gmf7TZYJy, trig_01WEAnmq4mCD7XMab6wbiZ9S, trig_01NbhdVhhrFeh8SzDZd1XNsY, trig_01D9PVkjrKMESmK2pWEZDZSo, trig_01Jod5FaSKPN19myfFEajNKL) and trig_011cUn9j9roZmJgX83of31gC (fired, disabled): safe to delete by the owner.
- Recorders with no stop date: record-quotes, record-book, record-daily, record-ref, record-wxens, record-perps (hourly). Stop dates exist for 15m-book (Nov 13), rain, deribit, sportspre (Dec 31), perps-cash and perps-fast (Feb 26 2027). Not checked which forward tests still read the no-stop ones.
