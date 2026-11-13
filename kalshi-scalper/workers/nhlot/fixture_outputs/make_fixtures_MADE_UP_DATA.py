#!/usr/bin/env python3
"""MADE-UP DATA for the NHLOT price measurement (card 17 in IDEA_DESK_B_WAVE3.md). Writes, per case, a games.json and a
candle run folder (numbered .json.gz answers and a manifest.json with its job). Nothing here came from Kalshi; every
price is a whole number of cents. Usage: make_fixtures_MADE_UP_DATA.py <out dir>

A "detected" game: both moneylines in the band all window; one total strike undecided until D minutes before the close,
then two strikes decided YES and three decided NO. The cheaper moneyline side then asks 44c; one minute later it asks
43c with a 2c spread ("buyable") or 46c ("not buyable"). An undetected game has moneylines at 80c and 20c.

  survive     150 games, 33 detected, 12 buyable (36%).
  closed      150 games, 33 detected, 9 buyable (27%).
  share_30    150 games, 40 detected, 12 buyable: exactly 30%, which is not under 30%.
  det_29      150 games, 29 detected.
  fire_12     250 games, 30 detected: exactly 12%, inside the range; 15 buyable.
  fire_low    300 games, 30 detected: 10%.
  fire_35     100 games, 35 detected: exactly 35%, inside the range; 15 buyable.
  fire_high   80 games, 30 detected: 37.5%.
  edges       150 games; 37 would-be detections, 17 of them carrying one boundary each (see EDGES below); four of
              those must NOT detect (a mid off the band, three strikes quoted, an ask of 8c, no moneyline candles).
Added after the third amendment (their manifests carry the sha256 and length of each UNPACKED answer, as the runner does):
  equal_asks  150 games, 33 detected; in 12 both moneylines ask 50c at the detection minute and only the ticker that
              sorts first is buyable a minute later; the other 21 are not buyable. 36% if the tie goes the right way.
  one_sided   150 games, 33 detected, 12 buyable; in every detected game the cheaper moneyline shows no ask for two
              minutes, so the state is first readable two minutes later (18 minutes before the close, not 20).
  not_whole   as survive, with a third request that was refused: the reader must refuse.
  bad_sha     as survive, one answer altered after the manifest was written: the reader must refuse.
Added after the fourth amendment (an empty side written the way Kalshi writes it: a bid of 0.00, an ask of 1.00):
  empty_sides 150 games, 33 detected. 6 have one total strike showing 0.00 and 1.00 at the first minute of the state
              (no quote, so the state is read that minute and the game is buyable); 6 have the cheaper moneyline at
              a bid of 30c and an ask of 1.00 for two minutes (no mid, so the state is read two minutes later; buyable);
              3 have the overtime market at 0.00 and 1.00 at the detection minute (buyable; the cross-check reads no
              quote); 3 have the cheaper side at a bid of 0.00 and an ask of 43c a minute later (not buyable); 15 are
              plain and not buyable. 15 of 33 buyable.
"""
import gzip
import hashlib
import json
import os
import sys

BASE = 1794000000 - 1794000000 % 3600          # a whole hour, made up


def cd(t, bid, ask):
    c = {"end_period_ts": t, "volume_fp": "0.00"}
    if bid is not None:
        c["yes_bid"] = {"close_dollars": "%.4f" % (bid / 100.0)}
    if ask is not None:
        c["yes_ask"] = {"close_dollars": "%.4f" % (ask / 100.0)}
    return c


def game(i, kind, d=20, edge=None):
    """Returns (games.json row, {ticker: candles}). kind: 'none', 'buy', 'nobuy'. edge: a boundary variant."""
    name = "26NOV%02dG%03d" % (1 + i % 9, i)
    close = BASE + 3600 * i
    ml = ["KXNHLGAME-%s-AAA" % name, "KXNHLGAME-%s-BBB" % name]
    tot = ["KXNHLTOTAL-%s-%d" % (name, k) for k in (2, 3, 4, 5, 6)]
    ot = "KXNHLOT-%s-1" % name
    out = {t: [] for t in ml + tot + [ot]}
    dd = d - 2 if edge in ("ml_one_sided", "empty_ml") else d   # the minute the state is first readable
    for back in range(50, -2, -1):                 # the candle ending `back` minutes before the close
        t = close - 60 * back
        det = kind != "none" and back <= d
        a, b = ((55, 57), (42, 44)) if kind != "none" else ((79, 81), (19, 21))
        if edge == "mid_on_band":
            a, b = (69, 71), (29, 31)
        if edge == "mid_off_band":
            a, b = (70, 71), (28, 31)
        if edge == "equal_asks":
            a, b = (48, 50), (48, 50)
            if back == d - 1:
                a = (41, 43)
        if edge == "ml_one_sided" and back in (d, d - 1):
            b = (42, None)
        if edge == "empty_ml" and back in (d, d - 1):
            b = (30, 100)
        if kind != "none" and back == dd - 1:     # one minute after detection
            b = (41, 43) if kind == "buy" and edge != "equal_asks" else (44, 46)
            if edge == "empty_next":
                b = (0, 43)
            if edge == "spread_3":
                b = (40, 43)
            if edge == "spread_4":
                b = (39, 43)
        if edge == "now_only" and back == d:
            b = (41, 43)
        if edge == "no_ml":
            pass
        else:
            if not (edge == "no_next" and back == d - 1):
                out[ml[1]].append(cd(t, *b))
            out[ml[0]].append(cd(t, *a))
        for k, tk in enumerate(tot):
            if det:
                q = (95, 97) if k < 2 else (2, 5)
                if edge == "ask_7" and k == 4:
                    q = (5, 7)
                if edge == "ask_8" and k == 4:
                    q = (5, 8)
                if edge == "bid_93" and k == 0:
                    q = (93, 97)
                if edge == "one_sided" and k == 0:
                    q = (96, None)
                if edge == "one_sided" and k == 4:
                    q = (None, 3)
                if edge in ("four_quoted", "three_quoted") and k == 2:
                    continue
                if edge == "empty_strike" and k == 3 and back == d:
                    q = (0, 100)
                if edge == "three_quoted" and k == 3:
                    continue
            else:
                q = (40, 45) if k == 2 else ((95, 97) if k < 2 else (2, 5))
            out[tk].append(cd(t, *q))
        out[ot].append(cd(t, *((0, 100) if (edge == "empty_ot" and back == d) else (92, 95) if det else (3, 5))))
    return {"game": name, "ml": ml, "total": tot, "close_ts": close, "ot": ot}, out


EDGES = [("buy", 20, "mid_on_band"), ("buy", 20, "mid_off_band"), ("buy", 20, "four_quoted"), ("buy", 20, "three_quoted"),
         ("buy", 20, "ask_7"), ("buy", 20, "ask_8"), ("buy", 20, "bid_93"), ("buy", 20, "one_sided"), ("buy", 45, None),
         ("buy", 0, None), ("buy", 20, "no_next"), ("buy", 20, "spread_3"), ("buy", 20, "spread_4"), ("nobuy", 20, "now_only"),
         ("buy", 20, "no_ml"), ("buy", 41, None), ("buy", 40, None)]


def build(out, name, n_games, n_buy, n_nobuy, edges=(), with_sha=False, spoil=None):
    rows, body = [], []
    plan = list(edges) + [("buy", 20, None)] * n_buy + [("nobuy", 20, None)] * n_nobuy
    plan += [("none", 20, None)] * (n_games - len(plan))
    order = sorted(range(len(plan)), key=lambda i: (i * 37) % len(plan))       # mixed, fixed
    for i, j in enumerate(order):
        row, cands = game(i, *plan[j])
        rows.append(row)
        body += [{"market_ticker": t, "candlesticks": c} for t, c in sorted(cands.items()) if c]
    folder = os.path.join(out, name)
    os.makedirs(os.path.join(folder, "candles"))
    json.dump(rows, open(os.path.join(folder, "games.json"), "w"))
    half = len(body) // 2
    reqs, mrows = [], []
    for k, part in enumerate((body[:half], body[half:]), 1):
        fn = "%04d.json.gz" % k
        raw = json.dumps({"markets": part}).encode()
        with open(os.path.join(folder, "candles", fn), "wb") as f:
            f.write(gzip.compress(raw if not (spoil == "bad_sha" and k == 2) else raw + b" "))
        reqs.append({"id": "c%03d" % k, "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(m["market_ticker"] for m in part), "period_interval": 1}})
        row = {"index": k, "id": "c%03d" % k, "page": 1, "status": 200, "file": fn}
        if with_sha:
            row.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "truncated": False})
        mrows.append(row)
    if spoil == "not_whole":
        reqs.append({"id": "c003", "path": "/markets/candlesticks", "params": {"market_tickers": "KXNHLGAME-MADEUP-AAA", "period_interval": 1}})
        mrows.append({"index": 3, "id": "c003", "page": 1, "status": 429, "file": None})
    json.dump({"status": "complete", "job": {"job_id": "MADE_UP", "requests": reqs}, "rows": mrows}, open(os.path.join(folder, "candles", "manifest.json"), "w"))


def main():
    out = sys.argv[1]
    build(out, "survive", 150, 12, 21)
    build(out, "closed", 150, 9, 24)
    build(out, "share_30", 150, 12, 28)
    build(out, "det_29", 150, 12, 17)
    build(out, "fire_12", 250, 15, 15)
    build(out, "fire_low", 300, 15, 15)
    build(out, "fire_35", 100, 15, 20)
    build(out, "fire_high", 80, 15, 15)
    build(out, "edges", 150, 10, 10, EDGES)
    build(out, "equal_asks", 150, 0, 21, [("buy", 20, "equal_asks")] * 12, with_sha=True)
    build(out, "one_sided", 150, 0, 0, [("buy", 20, "ml_one_sided")] * 12 + [("nobuy", 20, "ml_one_sided")] * 21, with_sha=True)
    build(out, "not_whole", 150, 12, 21, with_sha=True, spoil="not_whole")
    build(out, "bad_sha", 150, 12, 21, with_sha=True, spoil="bad_sha")
    build(out, "empty_sides", 150, 0, 15, [("buy", 20, "empty_strike")] * 6 + [("buy", 20, "empty_ml")] * 6 + [("buy", 20, "empty_ot")] * 3 + [("buy", 20, "empty_next")] * 3, with_sha=True)


if __name__ == "__main__":
    main()
