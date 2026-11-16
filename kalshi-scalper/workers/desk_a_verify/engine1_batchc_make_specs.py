"""Writes the four batch C spec files (ENGC1ETHMOM, ENGC2OIACC, ENGC3TOD, ENGC4GOLDX) from the ENGB4XBTC spec as the template (same data, split, gates, costs, holds, fee form), changing only what each spec is about. Specs only: nothing is run. Prints each file's sha256.
  python3 -I engine1_batchc_make_specs.py <specs dir>"""
import sys, os, json, copy, hashlib
SERIES19 = ["KXBTC15M","KXETH15M","KXGOLD15M","KXDOGE15M","KXXRP15M","KXBNB15M","KXHYPE15M","KXSOL15M","KXNEAR15M","KXZEC15M","KXSILVER15M","KXWTI15M","KXCOPPER15M","KXNATGAS15M","KXEURUSD15M","KXGBPUSD15M","KXUSDJPY15M","KXPALLADIUM15M","KXPLATINUM15M"]
CRYPTO9 = ["KXBTC15M","KXETH15M","KXDOGE15M","KXXRP15M","KXBNB15M","KXHYPE15M","KXSOL15M","KXNEAR15M","KXZEC15M"]
BASE = 13 * 18 * 4 * 6        # buckets x bands x side rules x exits = 5,616; a filter with k options gives 5,616 k rules a series
def spec(t, sid, card, wall, k, feature, needs, closest, diff, flag, sub, pred, look, extra_hold):
    s = copy.deepcopy(t); s["id"] = sid; s["card"] = card; s["needs_new_code"] = [needs]
    s["uniqueness"]["closest_existing"] = closest; s["uniqueness"]["difference"] = diff; s["uniqueness"]["family_flag"] = flag
    s["data"]["ticker_wall"] = wall; s["grid"]["filters"] = ["new:" + feature]
    n = BASE * k * len(wall)
    s["tries"] = {"rules_this_spec": n, "rules_per_series": BASE * k, "series_in_wall": len(wall), "prior_m": "6,290,660 (the Head's ruling of Nov 16 for every print) plus the earlier specs of this batch C, from the TALLY; counted per series: %d rules x %d series; every rule counts whether it passes the gate or not" % (BASE * k, len(wall))}
    s["subset_rationale"] = sub; s["prediction"] = pred; s["look_ahead"]["features"] = look
    s["holds"] = s["holds"] + extra_hold
    s["spec_note"] = "written for the Head's batch C order of 2026-11-16 (specs only, frozen and hashed before any read); not run; the code change needs Auditor B's CLEAN and a second build (rule 16b) first. Batch A and B features checked: oi3, oi6, vol3, mom1, mom3, mom5, spread (run 2), btcmom3 (ENGB4XBTC), vspike, swid and TA3 or TA5 time stops (B2)"
    s.pop("heldout_read_registered", None)
    s["heldout_read_registered"] = {"date": "2026-11-16", "rule": "each batch C survivor (VALIDATE bar passed) is read ONCE on the held-out window of its market (closes 2026-10-03T16:00Z to before 2026-10-28T00:00Z for BTC, ETH, XRP, DOGE, GOLD; to before 2026-11-03T16:00Z for the other series) with the held-out plan v3 bar, after the 190's read; a cross-series input reads the other market's held candles of the same close"}
    return s
def main(out):
    t = json.load(open(os.path.join(out, "ENGB4XBTC.spec.json")))
    nb = [x for x in SERIES19 if x != "KXETH15M"]
    hb = {"label": "H09 held KXBTC15M price path (Bitcoin closes to Nov 20; a shadow start on a pick that trades KXBTC15M is not before 2026-11-21T00:00Z)", "start_epoch": 1791043200, "end_epoch": 1795219200, "card": "H09", "status": "HELD (the Head and Auditor B, Nov 16: BTC15M closes held to 2026-11-21T00:00Z; the start is the archive freeze H01 and the table row itself is for Auditor B to confirm). Batch C never reads or trades a BTC15M close in this window: it reads archive closes before 2026-10-03T16:00Z only, and a shadow start on any pick that trades KXBTC15M is not before 2026-11-21T00:00Z. ETH and gold inputs are archive closes before H01, so no further hold applies"}
    S = [
     spec(t, "ENGC1ETHMOM", "ENGC1", nb, 3, "ethmom3", "cross-series feature ethmom3 in the driver and enumerator: the YES mid change of the KXETH15M market with the SAME close time from e - 180 to e (both candles at or before e, the ETH market must exist and be two sided), classes up, flat, down by the enumerator's cls(); the loader hands the driver the ETH candles by close time. Mirrors btcmom3",
          ["btcmom3 (ENGB4XBTC, Bitcoin's 3 minute move)", "ENGINE1 mom3 (the series' own 3 minute move)"],
          "the ETH 3 minute move at the same instant as a filter on the OTHER 18 series (not on Ethereum). ETH and BTC move together, so this is expected to be strongly correlated with btcmom3 on crypto series (flag: near-duplicate of ENGB4XBTC there; the value is the non-crypto series and BTC itself, where BTC's own move is not a filter). Co-movement at the entry, not lead-lag.",
          "none identified; any survivor is flagged by the driver's family function and compared with ENGB4XBTC's passes (correlation of the per-day signals; 0.3 or more is a duplicate on the declined list)",
          "Ethereum's move as a filter on the 18 other series, 16,848 rules a series; aligned by the identical close time.",
          "Co-movement is already in each market's price; prediction: no rule survives, and any that does repeats ENGB4XBTC's passes.",
          "candles ending at or before the entry candle end e (the cross-series feature uses the KXETH15M market of the SAME close time, candles ending at or before e)", [hb]),
     spec(t, "ENGC2OIACC", "ENGC2", SERIES19, 3, "oiacc", "own-market feature oiacc in the driver and enumerator: the change in the 3 minute open interest change, (oi at e minus oi at e - 180) minus (oi at e - 180 minus oi at e - 360), from the candles' open_interest_fp (else open_interest), all three candles ending at or before e and present; classes up, flat, down by cls(); a market with a missing candle has no feature and no entry",
          ["ENGINE1 oi3 and oi6 (the level of the change, not its change)", "OICORE (Bitcoin open interest rise, 180 to 120 s before the close)"],
          "the second difference of open interest: is the open interest change speeding up or fading. oi3 and oi6 give the change over 3 or 6 minutes; oiacc compares two consecutive 3 minute changes, so a market with a steady rise reads flat here and flat in neither oi3 class. Its passes are checked against OICORE (Bitcoin, cheap side) and flagged as an open-interest trigger.",
          "open-interest trigger family (flagged by the driver's family function; a Bitcoin cheap side pass is compared with OICORE before any step beyond shadow)",
          "open interest acceleration as a filter on all 19 series, 16,848 rules a series; own-market candles only.",
          "Open interest rose into the entry is what OICORE uses; prediction: the acceleration adds nothing over oi3 and no rule survives.",
          "candles ending at or before the entry candle end e (oi at e, e - 180 and e - 360 of the series own market)", [hb]),
     spec(t, "ENGC3TOD", "ENGC3", SERIES19, 4, "todct", "own-market feature todct in the driver and enumerator: the US Central clock hour of the entry candle end e (the UTC epoch converted with the America/Chicago offset read at that instant, DST included) in four bands: 00:00 to 05:59, 06:00 to 11:59, 12:00 to 17:59, 18:00 to 23:59; every entry has one",
          ["MKTTIME1 (gold hours, V2, the older block-by-hour reads)", "gold quiet hours 20:00 to 23:59 CT (lifted Oct 30, 2026, a table entry in code)"],
          "a clock filter: it carries no market information, only the hour. Prior reads on hours (MKTTIME1) were gold and Bitcoin specific and read by hand; this is the whole grid on every series. Weekend and holiday effects are not separated (a weekend hour is the same band as a weekday one); a day-of-week split would be its own spec.",
          "none identified (a clock band is not an entry mechanism); a pass is a regime tag, never a standalone strategy",
          "four Central time bands as a filter on all 19 series, 22,464 rules a series; the band is read from the entry candle end e only.",
          "Prediction: no rule survives; hours are the oldest data-mined cut and 4 bands over 19 series gives many chances to find noise.",
          "the clock reading of the entry candle end e (no market data)", [hb]),
     spec(t, "ENGC4GOLDX", "ENGC4", [x for x in CRYPTO9], 3, "goldmom3", "cross-series feature goldmom3 in the driver and enumerator: the YES mid change of the KXGOLD15M market with the SAME close time from e - 180 to e (both candles at or before e, the gold market must exist and be two sided; no feature on a closed weekend or break), classes up, flat, down by cls(); the loader hands the driver the gold candles by close time. A filter on the 9 crypto series only",
          ["btcmom3 and ethmom3 (crypto on crypto)", "gold L1 (gold's own entry; here gold is only a filter)"],
          "gold's 3 minute move as a filter on crypto: a risk-on or risk-off read from a different asset class. NO index market exists in the archive (the ticker wall holds no index 15 minute series), so no index move is possible here; an index filter needs a data source the owner has not approved and is not part of this spec. Gold only trades part of the week, so the filter is missing on weekends and most entries are dropped there.",
          "none identified; a gold-as-filter pass is not a gold strategy and is compared with gold L1 only if it trades gold",
          "gold's move as a filter on the 9 crypto series, 16,848 rules a series; aligned by the identical close time.",
          "Prediction: no rule survives; gold and crypto share little at 3 minutes, and the gold feature is missing at weekends.",
          "candles ending at or before the entry candle end e (the cross-series feature uses the KXGOLD15M market of the SAME close time, candles ending at or before e)", [hb]),
    ]
    for s in S:
        p = os.path.join(out, s["id"] + ".spec.json"); json.dump(s, open(p, "w"), indent=1)
        print(s["id"], s["tries"]["rules_this_spec"], hashlib.sha256(open(p, "rb").read()).hexdigest())
    print("batch C tries", sum(s["tries"]["rules_this_spec"] for s in S))
if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
