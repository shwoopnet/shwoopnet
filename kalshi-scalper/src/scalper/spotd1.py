"""SPOTD1 (workers/SPOTD1_REGISTRATION.md): daily Spotify chart winner markets against a persistence model of the number one title.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. No promote verb.
    python -m scalper.spotd1 fetch   (resumable: market listings, then hourly candles for the registered universe, into data/spotd1/)
    python -m scalper.spotd1 run     (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from . import api
from .econnew1 import fee, line, pick, pnl, stats
from .paths import DATA_DIR

D = DATA_DIR / "spotd1"
RESULT = DATA_DIR / "spotd1_result.txt"
UTC = timezone.utc
TRY_A = ("KXSPOTIFYD",)
TRY_B = ("KXSPOTIFYGLOBALD", "KXSPOTIFYARTISTD")
GAP, MAX_SPREAD, MAX_AGE_S, BURN = 0.08, 0.10, 6 * 3600, 60
BAR_PF, BAR_Z, MIN_MEAN_C, MIN_TRADES = 1.5, 5.27, 2.0, 150


def key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def ev_date(event):
    return datetime.strptime(event.split("-", 1)[1][:7], "%y%b%d").date()


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def look_ts(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())


def events_of(markets, series):
    """{event: dict(date, settle_ts, top key, strikes {ticker: key})} for settled events with exactly one yes strike."""
    ev = defaultdict(list)
    for m in markets:
        if m.get("series") in series:
            ev[m["event_ticker"]].append(m)
    out = {}
    for e, ms in ev.items():
        yes = [m for m in ms if m.get("result") == "yes"]
        st = [ts(m["settlement_ts"]) for m in ms if m.get("settlement_ts")]
        if len(yes) != 1 or not st:
            continue
        top = key(yes[0].get("yes_sub_title")) or key(yes[0].get("expiration_value"))
        out[e] = dict(date=ev_date(e), settle=max(st), top=top, strikes={m["ticker"]: key(m.get("yes_sub_title")) for m in ms}, res={m["ticker"]: m["result"] for m in ms})
    return out


def recent_distinct(tops_by_date, upto, n=3):
    """The first three distinct titles among the last three settled dates (most recent first). tops_by_date: [(date, top)] settled, sorted."""
    last = [t for _, t in tops_by_date[-3:]][::-1]
    seen = []
    for t in last:
        if t and t not in seen:
            seen.append(t)
    return seen[:n]


def predictions(events):
    """{event: (look_ts, [a1..], [r1..])}. Only events settled (settle <= look) before the look feed the titles and the rates (expanding, earlier events only)."""
    evs = sorted(events.items(), key=lambda kv: kv[1]["date"])
    out = {}
    hits = [[0, 0, 0], 0]  # per-j hit counts and event count, over events already settled and scorable
    pend = []  # events whose rates update when they settle: (settle, hit list)
    for e, v in evs:
        L = look_ts(v["date"])
        settled = sorted([(w["date"], w["top"], w["settle"]) for w in events.values() if w["settle"] <= L and w["date"] < v["date"]])
        tb = [(d, t) for d, t, _ in settled]
        a = recent_distinct(tb, None)
        # rates from earlier events settled by L, each judged against ITS own recent distinct titles (expanding)
        cnt, n = [0, 0, 0], 0
        hist = [(d, t, s) for d, t, s in settled]
        for i in range(3, len(hist)):
            prev = [(d, t) for d, t, _ in hist[:i]]
            # the earlier event i was settled by L, and so were its predecessors (they settled earlier)
            ai = recent_distinct(prev, None)
            n += 1
            for j, t in enumerate(ai):
                if hist[i][1] == t:
                    cnt[j] += 1
                    break
        if n >= BURN and a:
            out[e] = (L, a, [(cnt[j] + 0.5) / (n + 1) for j in range(len(a))])
    return out


def thirds(dates):
    ev = sorted(dates)
    n = len(ev)
    c1, c2 = ev[n // 3], ev[(2 * n) // 3]
    return lambda d: "W1" if d < c1 else ("W2" if d < c2 else "W3")


def quote(cs, look):
    q = [c for c in cs if c[0] <= look and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1 and look - c[0] <= MAX_AGE_S]
    return (q[-1][1], q[-1][2]) if q else None


def entry(f, bid, ask, gap=GAP):
    if ask - bid > MAX_SPREAD + 1e-9:
        return None
    if f - ask - 0.07 * ask * (1 - ask) >= gap:
        return "yes", ask
    if bid - f - 0.07 * bid * (1 - bid) >= gap:
        return "no", 1 - bid
    return None


def universe(markets, series):
    events = events_of(markets, series)
    P = predictions(events)
    uni = {}
    for e, (L, a, r) in P.items():
        v = events[e]
        for tk, k in v["strikes"].items():
            if k in a:
                uni[tk] = dict(event=e, date=v["date"].isoformat(), look=L, fair=r[a.index(k)], res=v["res"][tk], series=e.split("-")[0])
    return uni, P


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "markets.json"
    markets = json.loads(mp.read_text())
    uni = {}
    for ser in (TRY_A, TRY_B):
        u, _ = universe(markets, ser)
        uni.update(u)
    (D / "universe.json").write_text(json.dumps(uni))
    print("universe strikes", len(uni), flush=True)
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    for i, (tk, m) in enumerate(uni.items()):
        if tk in have:
            continue
        L = m["look"]
        try:
            d = api._get(f"/historical/markets/{tk}/candlesticks", {"start_ts": L - 12 * 3600, "end_ts": L, "period_interval": 60})
            have[tk] = [(c["end_period_ts"], pick(c.get("yes_bid")), pick(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
        except Exception as e:
            print("skip", tk, str(e)[:60])
            continue
        if i % 50 == 0:
            cp.write_text(json.dumps(have))
            print(i, len(uni), flush=True)
        time.sleep(0.3)
    cp.write_text(json.dumps(have))
    print("done", len(have), flush=True)


def collect(uni, cands, win, mult=1.0, gap=GAP):
    rows = defaultdict(list)
    for tk, m in uni.items():
        q = quote(cands.get(tk, []), m["look"])
        if not q:
            continue
        e = entry(m["fair"], q[0], q[1], gap)
        if e:
            rows[win(m["date"])].append((m["event"], pnl(e[0], e[1], m["res"], mult)))
    return rows


def brier(uni, cands):
    mod = mkt = n = 0
    for tk, m in uni.items():
        q = quote(cands.get(tk, []), m["look"])
        if not q or q[1] - q[0] > MAX_SPREAD + 1e-9:
            continue
        y = 1.0 if m["res"] == "yes" else 0.0
        mod += (m["fair"] - y) ** 2
        mkt += ((q[0] + q[1]) / 2 - y) ** 2
        n += 1
    return (mod / n, mkt / n, n) if n else (None, None, 0)


def score_try(name, uni, cands, out):
    win = thirds(sorted({m["date"] for m in uni.values()}))
    mb, kb, nb = brier(uni, cands)
    out.append(f"== {name}: universe strikes {len(uni)}, events {len({m['event'] for m in uni.values()})}, with candles {sum(1 for t in uni if t in cands)}")
    if nb:
        out.append(f"Brier model {mb:.4f} market mid {kb:.4f} (strikes {nb})")
    r1, r12 = collect(uni, cands, win), collect(uni, cands, win, 1.2)
    S, S12, ok = {}, {}, True
    for w in ("W1", "W2"):
        S[w], S12[w] = stats(r1[w]), stats(r12[w])
        out.append(line(w, S[w]) + f" | fees x1.2 PF {S12[w]['pf']:.2f}")
        ok = ok and S[w]["pf"] >= BAR_PF
    pooled = [x for w in S for x in r1[w]]
    ntr = sum(S[w]["n"] for w in S)
    if ok and nb and mb < kb:
        S["W3"], S12["W3"] = stats(r1["W3"]), stats(r12["W3"])
        out.append(line("W3 (holdout, read because W1 and W2 passed)", S["W3"]))
        pooled += r1["W3"]
        ntr += S["W3"]["n"]
    else:
        out.append("W3 holdout NOT read (W1 and W2 did not both pass, or model Brier not better than the market)")
    ps = stats(pooled)
    out.append(line("pooled read windows", ps))
    for g in (0.05, 0.12):
        rr = collect(uni, cands, win, 1.0, g)
        out.append(f"info gap {g}: " + " ".join(f"{w} n {len(rr[w])}" for w in ("W1", "W2", "W3")))
    why = []
    if not nb:
        return "NOT_RUNNABLE", ["no candles with a quote"], ntr
    if any(S[w]["pf"] < BAR_PF for w in S):
        why.append("PF under 1.5 in a window")
    if any(S12[w]["pf"] < 1.0 for w in S12):
        why.append("not positive at fees x1.2")
    if not mb < kb:
        why.append("model Brier not better than the market")
    if ps["z"] < BAR_Z:
        why.append(f"pooled z {ps['z']:.2f} under {BAR_Z}")
    if ps["mean"] < MIN_MEAN_C:
        why.append("pooled mean under 2c")
    if ntr < MIN_TRADES:
        why.append(f"{ntr} trades under {MIN_TRADES} (NOT_ENOUGH_DATA)")
    verdict = ("FALSIFIED" if any("NOT_ENOUGH" not in w for w in why) else "NOT_ENOUGH_DATA") if why else "NOT_YET_FALSIFIED"
    return verdict, why, ntr


def main(argv):
    if argv and argv[0] == "fetch":
        return fetch()
    if RESULT.exists():
        print("refused: the one scored read has been run; see", RESULT)
        return
    uni = json.loads((D / "universe.json").read_text())
    cands = json.loads((D / "candles.json").read_text())
    out = [f"SPOTD1 run {datetime.now(UTC).isoformat()} N=728702 z bar {BAR_Z} fee 7% x C x p x (1-p) rounded up, C=10"]
    for name, ser in (("A KXSPOTIFYD", TRY_A), ("B KXSPOTIFYGLOBALD+KXSPOTIFYARTISTD", TRY_B)):
        sub = {t: m for t, m in uni.items() if m["series"] in ser}
        v, why, n = score_try(name, sub, cands, out)
        out.append(f"VERDICT {name} {v}: " + "; ".join(why))
    RESULT.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main(sys.argv[1:])
