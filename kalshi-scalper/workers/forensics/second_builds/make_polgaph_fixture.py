#!/usr/bin/env python3
"""A MADE-UP fixture for POLGAPH in the pull-run folder shape (manifest.json + NNNN.json.gz): <out>/lists, <out>/hourly and <out>/minute, plus the marker file MADE_UP_DATA.
Nothing here is real: only the series NAMES come from Desk B's POLGAPH_SERIES.json (so the family map applies); events, markets, quotes, volumes and results are invented.
usage: python3 -I make_polgaph_fixture.py <out dir> <POLGAPH_SERIES.json> [seed] [edge] [other_edge] [balanced]
  balanced (the word, optional sixth argument): only the first 10 activity-count series (7 before Amendment 5 shortened the window) are used beside the 7 shipping and 14 single-question series, the count families'
  events last 2 to 3 days with 10 markets each (more events, more picks), `edge` is used for BOTH count families and `other_edge` for single questions only. With edge 0.45 and other_edge -0.3 the pooled
  read passes and BOTH count families supply more than half of the pooled net (possible because the third family is negative): the two-families case of Amendment 4.
  other_edge (optional): the edge used for the shipping and single-question families, while `edge` is used for activity counts only. With edge 0.25 and other_edge -0.45 the
  pooled read fails while activity counts alone would pass: the case that separates "pooled verdict first" (Amendment 4) from "a failed pooled read rescued by one family".
  edge (default 0.0): how far beyond a coin flip an overnight gap points toward the market's result. 0.0 = the gap says nothing; 0.35 = a strong planted effect.
Planted on purpose: markets that open or close exactly at a 07:00 look (that morning is not theirs), missing hourly candles at 22:00, 06:00 or 07:00 ("no look"), empty books
(0.00 and 1.00) and one-sided candles, gaps on a half-cent grid around 5c and 2c (exactly 5c and exactly 2c occur), asks on the band edges (0.10, 0.64, 0.65), spreads of
exactly 4c, a 06:00 ask exactly 1c from the 07:00 ask, 7 day volumes around 200 (volumes come in steps of 25, so exactly 200 occurs), events with several qualifying markets
on one morning (the nearest-50c pick and its ties), events that last many mornings (the block), settled-at-a-price results (voids), and for the fill: mornings with no minute
request, a failed minute request, requests that leave some tickers out, no 07:01 candle, a 07:01 ask at the limit, above it, an empty book and a missing ask."""
import sys, os, json, gzip, random
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
F = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
W0 = int(datetime(2026, 9, 12, tzinfo=timezone.utc).timestamp()); W1 = int(datetime(2026, 11, 4, 23, 59, 59, tzinfo=timezone.utc).timestamp())      # Amendment 5: development closes end Nov 4


def main(out, series_json, seed, edge, other_edge=None, balanced=False):
    rng = random.Random(seed); os.makedirs(out); open(os.path.join(out, "MADE_UP_DATA"), "w").write("invented rows for a build comparison; nothing here is real\n")
    fam = json.load(open(series_json))["families"]
    use = (fam["activity counts"][:10] if balanced else fam["activity counts"]) + fam["shipping counts"] + fam["single questions"]                    # every series of the file (63 since Amendment 5), so the counts clear the 150 and 40 minimums
    cent = lambda x: round(min(0.93, max(0.07, x)), 2)
    lists = {}; hourly = {}; looks = {}; q07 = {}; n_ev = 0
    for s in use:
        single = s in fam["single questions"]; lists[s] = []; e_s = edge if (other_edge is None or s in fam["activity counts"] or (balanced and s in fam["shipping counts"])) else other_edge
        day = datetime(2026, 9, rng.randint(5, 11), tzinfo=ET)
        while True:
            oh, om = rng.choice([(7, 0), (9, 30), (14, 0), (20, 15)]); ch, cm, cs = rng.choice([(7, 0, 0), (10, 0, 0), (16, 0, 0), (23, 59, 59)])
            dur = rng.randint(8, 25) if single else (rng.randint(2, 3) if balanced else rng.randint(2, 6))
            op = int(day.replace(hour=oh, minute=om).timestamp()); cl_dt = (day + timedelta(days=dur)).replace(hour=ch, minute=cm, second=cs); cl = int(cl_dt.timestamp())
            day = (day + timedelta(days=dur + rng.choice([0, 0, 1]))).replace(hour=0, minute=0, second=0)
            if cl > W1: break
            if cl < W0: continue
            n_ev += 1; ev = "%s-%s" % (s, cl_dt.strftime("%y%b%d").upper())
            for k in range(rng.choice([1, 2]) if single else (10 if balanced else 4)):
                tk = "%s-%s%d" % (ev, "Q" if single else "T", k + 1); m = cent(rng.uniform(0.15, 0.85)); truth = rng.random() < m
                vscale = rng.choice([0, 1, 1, 25, 25, 25, 25, 25, 25, 25]); cd = hourly.setdefault(tk, {}); g = 0.0; h = (op // 3600 + 1) * 3600
                while h <= cl:
                    hr = datetime.fromtimestamp(h, ET).hour; key = hr in (22, 6, 7); mid = m
                    if hr == 22:
                        g = rng.choice([0, 0, 0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.05, 0.06, 0.08, 0.10, 0.15]) * (1 if (rng.random() < 0.5 + e_s) == truth else -1)
                    elif hr == 6: mid = cent(m + g - rng.choice([0, 0, 0, 0, 0.01, -0.01, g, g]))
                    elif hr == 7: m = cent(m + g); mid = m; g = 0.0
                    elif 8 <= hr <= 21: m = cent(m + rng.choice([0, 0, 0, 0.01, -0.01])); mid = m
                    sp = rng.choice([0.01, 0.02, 0.02, 0.03, 0.04, 0.04, 0.05, 0.07]); b = round(mid - (sp // 0.02) * 0.01, 2); a = round(b + sp, 2); r = rng.random()
                    vol = vscale * rng.choice([0, 0, 1, 2, 4])
                    if r < (0.05 if key else 0.04 if 8 <= hr <= 21 else 0.35): pass                      # no candle this hour (quiet night hours are often omitted)
                    elif r < 0.07 and key: cd[h] = (0.0, 1.0, 0.0)                                       # an empty book
                    elif r < 0.09 and key: cd[h] = ((None, a, vol) if rng.random() < 0.5 else (b, None, vol))  # one side missing
                    else: cd[h] = (b, a, float(vol))
                    if hr == 7 and op < h < cl:
                        looks.setdefault(datetime.fromtimestamp(h, ET).date().isoformat(), []).append((tk, h)); q07[(tk, h)] = cd.get(h)
                    h += 3600
                res = "yes" if truth else "no"; sv = "1.0000" if truth else "0.0000"
                if rng.random() < 0.03: res = "scalar"; sv = "%.4f" % cent(m)
                lists[s].append({"ticker": tk, "event_ticker": ev, "open_time": F(op), "close_time": F(cl), "result": res, "settlement_value_dollars": sv, "status": "finalized", "title": "made up"})

    def write_run(folder, reqs):
        os.makedirs(folder); rows = []
        for n, (rid, path, params, body) in enumerate(reqs, 1):
            row = {"index": n, "id": rid, "path": path, "params": params, "page": 1, "status": 200 if body is not None else 500, "truncated": False, "body_kind": "object"}
            if body is not None:
                row["file"] = "%04d.json.gz" % n
                with gzip.open(os.path.join(folder, row["file"]), "wt") as f: json.dump(body, f)
            rows.append(row)
        json.dump({"job": {"note": "MADE UP"}, "status": "complete", "requests_sent": len(rows), "rows": rows}, open(os.path.join(folder, "manifest.json"), "w"))
    def cj(ts, b, a, v):
        c = {"end_period_ts": ts, "volume_fp": "%.2f" % v}
        if b is not None: c["yes_bid"] = {"close_dollars": "%.4f" % b}
        if a is not None: c["yes_ask"] = {"close_dollars": "%.4f" % a}
        return c
    write_run(os.path.join(out, "lists"), [("set_" + s, "/markets", {"series_ticker": s, "status": "settled", "limit": 1000}, {"markets": lists[s], "cursor": ""}) for s in use])
    hreq = []
    for s in use:
        tks = [m["ticker"] for m in lists[s]]
        for k in range(0, len(tks), 20):
            grp = tks[k:k + 20]; ts = [t for x in grp for t in hourly[x]]
            hreq.append(("h_%s_%d" % (s, k // 20), "/markets/candlesticks", {"market_tickers": ",".join(grp), "start_ts": min(ts) - 3600 if ts else 0, "end_ts": max(ts) if ts else 0, "period_interval": 60},
                         {"markets": [{"market_ticker": x, "candlesticks": [cj(t, *hourly[x][t]) for t in sorted(hourly[x])]} for x in grp]}))
    write_run(os.path.join(out, "hourly"), hreq)
    mreq = []; n_look = 0
    for d in sorted(looks):
        r = rng.random()
        if r < 0.04: continue                                                                             # no minute request for this morning: "no fill data"
        rows = [x for x in looks[d] if rng.random() > 0.06]                                               # some tickers are left out of the request
        look = rows[0][1] if rows else looks[d][0][1]; params = {"market_tickers": ",".join(t for t, _ in rows), "start_ts": look - 300, "end_ts": look + 300, "period_interval": 1}
        if r < 0.07: mreq.append(("m_" + d, "/markets/candlesticks", params, None)); continue          # the request failed
        mk = []
        for tk, h in rows:
            n_look += 1; q = q07[(tk, h)]; cs = []; kind = rng.random()
            if q is not None and q[0] is not None and q[1] is not None and 0 < q[0] < q[1] < 1:
                b, a = q[0], q[1]
                cs.append(cj(h, b, a, 0.0))                                                              # the minute ending 07:00: never read
                if kind < 0.45: pass                                                                     # no 07:01 candle: an unchanged minute
                elif kind < 0.60: cs.append(cj(h + 60, b, a, 1.0))                                       # unchanged quote, a candle present
                elif kind < 0.72: cs.append(cj(h + 60, round(b + 0.01, 2), round(a + 0.01, 2), 3.0))     # YES ask exactly at a YES limit; NO ask 1c better
                elif kind < 0.80: cs.append(cj(h + 60, round(b - 0.01, 2), round(a - 0.01, 2), 3.0))     # NO ask exactly at a NO limit
                elif kind < 0.88: cs.append(cj(h + 60, round(b + 0.02, 2), round(a + 0.02, 2), 5.0))     # YES ask above a YES limit
                elif kind < 0.93: cs.append(cj(h + 60, round(b - 0.02, 2), round(a - 0.02, 2), 5.0))     # NO ask above a NO limit
                elif kind < 0.96: cs.append(cj(h + 60, 0.0, 1.0, 0.0))                                   # an empty book
                elif kind < 0.98: cs.append(cj(h + 60, None, a, 0.0))                                    # no YES bid: no NO ask
                else: cs.append(cj(h + 60, b, None, 0.0))                                                # no YES ask
                if rng.random() < 0.3: cs.append(cj(h + 120, round(b + 0.05, 2), round(a + 0.05, 2), 1.0))   # the minute ending 07:02: never read
            mk.append({"market_ticker": tk, "candlesticks": cs})
        mreq.append(("m_" + d, "/markets/candlesticks", params, {"markets": mk}))
    write_run(os.path.join(out, "minute"), mreq)
    print("made-up POLGAPH fixture written to %s: %d series, %d events, %d markets, %d hourly requests, %d minute requests over %d mornings, seed %d, edge %s" % (
        out, len(use), n_ev, sum(len(v) for v in lists.values()), len(hreq), len(mreq), len(looks), seed, edge) + ("" if other_edge is None else ", other families %s" % other_edge) + (", balanced" if balanced else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5, float(sys.argv[4]) if len(sys.argv) > 4 else 0.0, float(sys.argv[5]) if len(sys.argv) > 5 else None, len(sys.argv) > 6 and sys.argv[6] == "balanced")
