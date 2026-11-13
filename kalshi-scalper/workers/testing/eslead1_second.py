#!/usr/bin/env python3
"""ESLEAD1 scorer, BUILD 2 (Testing Desk, Nov 13, 2026). A MEASUREMENT: does the ES future lead the KXINX15M mid? Research only: reads files it is given, sends nothing, writes NO file.
Built FROM THE CARD ALONE: Desk B's ESLEAD1_CARD_NOV13.md at 786dc3b2 (sha256 66747c1e) with Amendment 1; blind to Desk B's build 1, expected-figures file and fixture. Hand case: ESLEAD1_SECOND_HAND_CASE.md (committed first).
Test: test_eslead1_second.py (INVENTED rows only). The ES csv is Databento-derived and licensed: nothing ES-derived is ever written to a repo; this module takes the path as an argument, writes no file, and results go by message only.
Windows: KXINX15M markets closing in [2026-11-05T00:00Z, 2026-11-13T00:00Z); others are not touched. A = the candle YES mid (yes bid close + yes ask close) / 2 where both exist (never carried); B = the ES 1 minute close at the same whole minute (the bar with ts_event = t - 60 s).
T = timestamps present in both per window. dA[t] = mid(t) - mid(t - 60 s) (lookback from the whole A series); dB[t] = ln(ES(t) / ES(t - 60 s)) (lookback from the whole ES series; an instrument_id change drops it).
Lag k pairs (dA[t], dB[t - 60 k]), t and t - 60 k in T; POSITIVE lag = Kalshi lags ES. Lags -3..+3; Pearson pooled over all windows' pairs; fewer than min_pairs pooled pairs (a REQUIRED argument) = n/a, zero variance = n/a.
Usage: eslead1_second.py <lists run>... --candles <candle runs>... --es <ES csv> --min-pairs N
"""
import calendar, csv, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorekit as k

TOL = 1e-9
SERIES = "KXINX15M"
CLOSE_FROM = calendar.timegm((2026, 11, 5, 0, 0, 0))
CLOSE_TO = calendar.timegm((2026, 11, 13, 0, 0, 0))
LAGS = tuple(range(-3, 4))
AMBIGUITIES = [
    "T is the set of timestamps present in both series within the window, computed once; a pair needs t and t - 60 k both in T and both changes defined; dA needs mid(t - 60 s) in the whole A series, dB needs ES(t - 60 s) in the whole ES series (the window's first minute uses the close at the window start).",
    "An instrument_id change between the two ES bars of a change drops it (counted as 'roll'); the card is silent.",
    "Rule 18 (Auditor B F1): a candle has a mid only if 0 < bid < ask < 1 (1e-9 slack); an empty, locked or crossed book has none, is never carried, and is counted as not_two_sided. The card line stating it is pending (Head or Desk B).",
    "ES loader (F2): rows read, kept and skipped (timestamp or value) are counted and returned; STOP if none kept or more than 5% skipped (MAX_SKIP_SHARE, my choice, not in the card).",
    "Prediction over the defined lags only; n/a lags are named; a tie at lag 0 passes (1e-9).",
    "The printed line's exact text in CFRTI-K is not known to this desk: the numbers are what compare.",
]


MAX_SKIP_SHARE = 0.05          # the ES loader STOPS if more than this share of rows is skipped, or if no row is kept


def load_es_counted(path):
    """-> ({end_ts: (instrument_id, close)} keyed by the minute END (ts_event + 60 s), counts). A duplicate ts_event stops the run naming the minute.
    counts: rows_read, rows_kept, skipped_ts (ts_event missing or not an ISO string), skipped_value (instrument_id or close does not parse)."""
    out, seen = {}, set()
    st = {"rows_read": 0, "rows_kept": 0, "skipped_ts": 0, "skipped_value": 0}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            st["rows_read"] += 1
            ts = k.iso(r.get("ts_event") or "")
            if ts is None:
                st["skipped_ts"] += 1; continue
            if ts in seen:
                raise SystemExit("STOP: duplicate ES ts_event %s (two rows for one minute)" % r["ts_event"])
            seen.add(ts)
            try:
                out[ts + 60] = (int(r["instrument_id"]), float(r["close"]))
            except (KeyError, TypeError, ValueError):
                st["skipped_value"] += 1; continue
            st["rows_kept"] += 1
    return out, st


def check_es_rows(st):
    """STOP if no ES row was kept or the skipped share is above MAX_SKIP_SHARE; the message carries the counts."""
    skipped = st["skipped_ts"] + st["skipped_value"]
    desc = "rows_read %d, rows_kept %d, skipped_ts %d, skipped_value %d" % (st["rows_read"], st["rows_kept"], st["skipped_ts"], st["skipped_value"])
    if st["rows_kept"] == 0:
        raise SystemExit("STOP: no ES row kept (%s): the file is not in the expected format" % desc)
    if skipped > MAX_SKIP_SHARE * st["rows_read"]:
        raise SystemExit("STOP: more than %.0f%% of ES rows skipped (%s)" % (MAX_SKIP_SHARE * 100, desc))


def load_es(path):
    return load_es_counted(path)[0]


def two_sided(c):
    """Standing rule 18: 0 < bid < ask < 1 with 1e-9 slack. An empty side (0.00 / 1.00), a locked or a crossed book has no mid."""
    b, a = c.get("bid"), c.get("ask")
    return b is not None and a is not None and b > TOL and a < 1.0 - TOL and a - b > TOL


def mids_of(candles, counts=None):
    out = {}
    for c in candles:
        if c.get("bid") is None or c.get("ask") is None:
            continue
        if not two_sided(c):
            if counts is not None:
                counts["not_two_sided"] += 1
            continue
        out[c["ts"]] = (c["bid"] + c["ask"]) / 2.0
    return out


def pearson(xs, ys, min_pairs):
    n = len(xs)
    if n < min_pairs:
        return None, "under the floor (%d pairs, need %d)" % (n, min_pairs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 1e-24 or syy <= 1e-24:
        return None, "zero variance"
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy), None


def prediction(defined):
    """The card's prediction: the lag 0 correlation is the largest (no other defined lag, negative or positive, exceeds it by more than 1e-9). None if lag 0 is not defined."""
    if 0 not in defined:
        return None
    return all(v <= defined[0] + TOL for kk, v in defined.items() if kk != 0)


def measure(markets, cs, es, min_pairs, es_stats=None):
    """markets: scorekit.markets dict; cs: scorekit.candles; es: load_es. -> the result dict (aggregates only)."""
    cnt = {"windows_listed": 0, "outside_dates_not_touched": 0, "windows_used": 0, "windows_without_candles": 0, "dA_missing_lookback": 0, "dB_missing_bar": 0, "dB_roll": 0, "not_two_sided": 0}
    pairs = {k_: ([], []) for k_ in LAGS}
    drops = {k_: 0 for k_ in LAGS}
    for tk in sorted(markets):
        m = markets[tk]
        if m["series"] != SERIES:
            continue
        cnt["windows_listed"] += 1
        c = m["close"]
        if c is None or not (CLOSE_FROM <= c < CLOSE_TO):
            cnt["outside_dates_not_touched"] += 1; continue
        A = mids_of(cs.get(tk, []), cnt)
        if not A:
            cnt["windows_without_candles"] += 1; continue
        cnt["windows_used"] += 1
        T = sorted(t for t in A if t in es)
        Tset = set(T)
        dA, dB = {}, {}
        for t in T:
            if (t - 60) in A:
                dA[t] = A[t] - A[t - 60]
            else:
                cnt["dA_missing_lookback"] += 1
            e1, e0 = es.get(t), es.get(t - 60)
            if e0 is None:
                cnt["dB_missing_bar"] += 1
            elif e0[0] != e1[0]:
                cnt["dB_roll"] += 1
            elif e0[1] > 0 and e1[1] > 0:
                dB[t] = math.log(e1[1] / e0[1])
            else:
                cnt["dB_missing_bar"] += 1
        for kk in LAGS:
            for t in T:
                tb = t - 60 * kk
                if tb not in Tset:
                    continue
                if t in dA and tb in dB:
                    pairs[kk][0].append(dA[t]); pairs[kk][1].append(dB[tb])
                else:
                    drops[kk] += 1
    res = {}
    for kk in LAGS:
        r, why = pearson(pairs[kk][0], pairs[kk][1], min_pairs)
        res[kk] = {"n_pairs": len(pairs[kk][0]), "corr": r, "na_reason": why, "pairs_dropped_missing_change": drops[kk]}
    defined = {kk: v["corr"] for kk, v in res.items() if v["corr"] is not None}
    pred = prediction(defined)
    line = "lead_lag (positive lag = Kalshi lags ES): " + " ".join("%+d:%s" % (kk, ("%.3f" % res[kk]["corr"]) if res[kk]["corr"] is not None else "n/a") for kk in LAGS)
    return {"line": line, "lags": res, "prediction_peak_at_lag_0_passed": pred, "na_lags": [kk for kk in LAGS if res[kk]["corr"] is None], "counts": cnt, "es_rows": es_stats, "min_pairs": min_pairs,
            "defined_peak_lag": (max(defined, key=lambda kk: defined[kk]) if defined else None), "ambiguities": AMBIGUITIES}


def run(lists, candle_runs, es_path, min_pairs):
    for f in list(lists) + list(candle_runs):
        k.guard(f)
    es, st = load_es_counted(es_path)
    check_es_rows(st)
    return measure(k.markets(lists), k.candles(candle_runs), es, min_pairs, st)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--candles" in a and "--es" in a and "--min-pairs" in a:
        import json
        i, j, m = a.index("--candles"), a.index("--es"), a.index("--min-pairs")
        out = run(a[:i], a[i + 1:j], a[j + 1], int(a[m + 1]))
        print(out["line"]); print(json.dumps(out, indent=1, default=str))
    else:
        print(__doc__); print("\n".join(AMBIGUITIES))
