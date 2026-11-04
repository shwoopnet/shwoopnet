"""TRUMPTOPIC1: the speaker's own recent Truth Social text as a topic preview for Trump speech word markets (workers/TRUMPTOPIC1_REGISTRATION.md). Research only.

    python -m scalper.trumptopic1 census          listing + feed only: events, words, coverage, trigger candidates (NO price, NO result)
    python -m scalper.trumptopic1 snapshot        forward: for events from 2026-11-05, write the 24h post counts and quotes at the look (no outcome)
    python -m scalper.trumptopic1 history         the history scorer (only after the registration is pushed; frozen cut 2026-10-03T16:00Z)
    python -m scalper.trumptopic1 forward         THE one forward read (fwdread guard)

Public Kalshi API and CNN's public archive; no key, no order. Cheap side only (ask 3c to 30c), YES side, held to settlement.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from . import fwdread as fr
from .paths import DATA_DIR

ARCHIVE = "https://ix.cnn.io/data/truth-social/truth_archive.json"
SERIES = ("KXTRUMPMENTION", "KXTRUMPMENTIONB")
UTC = timezone.utc
CUT = datetime(2026, 10, 3, 16, 0, tzinfo=UTC)          # history ends here; later events are the forward sample
FWD_START = datetime(2026, 11, 5, tzinfo=UTC)           # forward events: occurrence on or after this
LOOK_BEFORE = timedelta(minutes=10)
WINDOW = timedelta(hours=24)
MIN_POSTS = 2
LOW, HARD, RATIO = 0.03, 0.30, 3.0
MAX_PER_EVENT = 2
FIT_FRAC = 2 / 3
PRIOR_A = 5.0                       # smoothing weight, both levels
QUOTE_MAX_AGE = timedelta(minutes=60)
TRADES_DUE = 150
EVENTS_MIN = 25
NONWORD = "event does not qualify"
SNAP_FILE = DATA_DIR / "trumptopic1_snapshots.csv"
SNAP_FIELDS = ["event", "ticker", "series", "word", "occurrence_utc", "look_utc", "posts_24h", "bucket", "p_model", "bid", "ask", "quote_age_min", "in_band", "signal", "selected",
               "archive_fetched_utc", "archive_latest_post_utc"]


def fee(p, C=10):
    return math.ceil(round(0.07 * C * p * (1 - p) * 100, 9)) / 100 / C


# ------------------------------------------------------------------ stems and counts

def alts(word):
    """Alternatives of a market word: split on '/', lowercase, quotes and spaces trimmed. [] for the non-word market."""
    w = (word or "").strip()
    if not w or w.lower() == NONWORD:
        return []
    return [a.strip().strip('"').strip().lower() for a in w.split("/") if a.strip().strip('"').strip()]


def stem_key(word):
    return " / ".join(sorted(alts(word)))


_RX = {}


def _rx(alt):
    if alt not in _RX:
        body = r"\s+".join(re.escape(t) for t in alt.split())
        _RX[alt] = re.compile(r"(?<![a-z0-9])" + body + r"(?:'s|’s|es|s)?(?![a-z0-9])")
    return _RX[alt]


def post_has(text_lower, word):
    return any(_rx(a).search(text_lower) for a in alts(word))


def posts_prior(posts, word, look):
    """Number of posts in (look - 24h, look] (posts: sorted [(utc datetime, lowercase text)]) that contain the word or one of its alternatives."""
    a = look - WINDOW
    return sum(1 for t, tx in posts if a < t <= look and post_has(tx, word))


def bucket(k):
    return 0 if k == 0 else 1 if k == 1 else 2 if k <= 3 else 3


# ------------------------------------------------------------------ data

def load_posts(raw=None):
    if raw is None:
        req = urllib.request.Request(ARCHIVE, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = json.load(r)
    out = []
    for x in raw:
        try:
            out.append((datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")), (x.get("content") or "").lower()))
        except (KeyError, ValueError):
            continue
    out.sort(key=lambda p: p[0])
    return out


def events_from_listing(markets):
    """[(occurrence, event ticker, series, [markets with a real word])] by occurrence; an event needs an occurrence time."""
    ev = {}
    for m in markets:
        if alts(m.get("yes_sub_title")) and m.get("occurrence_datetime"):
            ev.setdefault(m["event_ticker"], []).append(m)
    out = []
    for e, L in ev.items():
        occ = min(datetime.fromisoformat(x["occurrence_datetime"].replace("Z", "+00:00")) for x in L)
        out.append((occ, e, L[0]["series"], L))
    return sorted(out, key=lambda x: x[0])


def split_history(events):
    """history = occurrence before CUT; fit = first two thirds of the history events (by date), held-out = last third; forward = on or after FWD_START."""
    hist = [e for e in events if e[0] < CUT]
    k = int(len(hist) * FIT_FRAC)
    return hist[:k], hist[k:], [e for e in events if e[0] >= FWD_START]


# ------------------------------------------------------------------ model

def fit(rows):
    """rows: [(stem key, count bucket, 1/0 yes)] from the fit events ONLY. Returns a function (stem, bucket) -> P(yes).
    p_global(bucket) = (yes + A * overall) / (n + A); p_stem(bucket) = (yes + A * p_global(bucket)) / (n + A) on the stem's own rows in that bucket."""
    n_all = len(rows)
    overall = sum(r[2] for r in rows) / n_all if n_all else 0.0
    gb, sb = {}, {}
    for s, b, y in rows:
        g = gb.setdefault(b, [0, 0]); g[0] += 1; g[1] += y
        t = sb.setdefault((s, b), [0, 0]); t[0] += 1; t[1] += y

    def pglob(b):
        n, k = gb.get(b, (0, 0))
        return (k + PRIOR_A * overall) / (n + PRIOR_A)

    def p(stem, b):
        n, k = sb.get((stem, b), (0, 0))
        return (k + PRIOR_A * pglob(b)) / (n + PRIOR_A)
    return p


def select(rows):
    """rows: [(ticker, p_model, ask)]; the rule: ask in [0.03, 0.30], p_model >= 3 x ask, best p/ask first, at most 2."""
    ok = [r for r in rows if LOW <= r[2] <= HARD and r[1] >= RATIO * r[2]]
    ok.sort(key=lambda r: (-r[1] / r[2], r[0]))
    return ok[:MAX_PER_EVENT]


def last_quote(candles, look):
    """candles: [(end_ts, bid, ask)] ascending. The last candle ending at or before the look with a bid and an ask, no older than 60 minutes: (bid, ask, age min) or None."""
    best = None
    for end, bid, ask in candles:
        t = datetime.fromtimestamp(end, UTC)
        if t <= look and bid is not None and ask is not None and ask > 0:
            best = (end, bid, ask)
    if not best:
        return None
    age = look - datetime.fromtimestamp(best[0], UTC)
    return None if age > QUOTE_MAX_AGE else (best[1], best[2], age.total_seconds() / 60)


def net(ask, yes):
    return (1.0 if yes else 0.0) - ask - fee(ask)


def pf(v):
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return float("inf") if l == 0 and w > 0 else (w / l if l else 0.0)


def verdict(n_treated, n_events, mean, pfv, h1, h2, ctrl_mean):
    if n_treated < TRADES_DUE or n_events < EVENTS_MIN:
        return "NOT_ENOUGH_DATA"
    if mean <= 0 or pfv < 1.5 or h1 <= 0 or h2 <= 0 or (mean - ctrl_mean) <= 0:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED (nothing is promoted)"


# ------------------------------------------------------------------ census (no price, no result)

def census(listing, posts, out=print):
    ev = events_from_listing(listing)
    fit_e, held, fwd = split_history(ev)
    pmin, pmax = posts[0][0], posts[-1][0]
    covered = [e for e in ev if e[0] - WINDOW - LOOK_BEFORE >= pmin and e[0] <= pmax]
    out(f"series {SERIES}: markets listed {len(listing)}; events with a real word and an occurrence time {len(ev)}; markets in them {sum(len(e[3]) for e in ev)}")
    for s in SERIES:
        es = [e for e in ev if e[2] == s]
        out(f"  {s}: {len(es)} events, {sum(len(e[3]) for e in es)} markets, {es[0][0]:%Y-%m-%d} to {es[-1][0]:%Y-%m-%d}")
    words = {stem_key(m["yes_sub_title"]) for e in ev for m in e[3]}
    out(f"distinct word keys {len(words)}")
    out(f"feed: {len(posts)} posts {pmin:%Y-%m-%d} to {pmax:%Y-%m-%d %H:%M}Z; events whose 24h window lies inside the feed: {len(covered)} of {len(ev)}")
    out(f"split: fit {len(fit_e)} events (to {fit_e[-1][0]:%Y-%m-%d}), held-out {len(held)} ({held[0][0]:%Y-%m-%d} to {held[-1][0]:%Y-%m-%d}), cut {CUT:%Y-%m-%d %H:%M}Z, forward-eligible already listed {len(fwd)}")
    by = {}
    for e in ev:
        by.setdefault(f"{e[0]:%Y-%m}", [0, 0]); by[f"{e[0]:%Y-%m}"][0] += 1
    out("events per month: " + ", ".join(f"{k} {v[0]}" for k, v in sorted(by.items())))
    # feed-based trigger candidates (no price): markets with >= 2 posts of the stem in the prior 24h at look = occurrence - 10 minutes
    res = {}
    for name, grp in (("fit", fit_e), ("held-out", held), ("all history", fit_e + held)):
        cand = ev_c = 0
        for occ, _e, _s, L in grp:
            look = occ - LOOK_BEFORE
            c = sum(1 for m in L if posts_prior(posts, m["yes_sub_title"], look) >= MIN_POSTS)
            cand += c; ev_c += c > 0
        res[name] = (cand, ev_c, len(grp))
        out(f"trigger candidates ({name}): {cand} markets in {ev_c} of {len(grp)} events (stem posted >= {MIN_POSTS} times in the prior 24h; no price yet, so not yet 'treated')")
    return res


# ------------------------------------------------------------------ candles, history scoring

CACHE = None   # set by the CLI: a directory OUTSIDE the repo


def get_candles(m, look, api, quote_close):
    """[(end_ts, bid, ask)] one minute candles in [look - 60 min, look]; historical endpoint for markets closed before 2026-09-04, live series endpoint after."""
    tk = m["ticker"]
    src = f"/historical/markets/{tk}/candlesticks" if m["close_time"] < "2026-09-04" else f"/series/{m['series']}/markets/{tk}/candlesticks"
    d = api._get(src, {"start_ts": int((look - timedelta(minutes=60)).timestamp()), "end_ts": int(look.timestamp()), "period_interval": 1})
    time.sleep(0.4)
    return [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]


def fit_rows(fit_events, posts):
    """[(stem, bucket, yes)] for every real-word market of the fit events (uses their results)."""
    rows = []
    for occ, _e, _s, L in fit_events:
        look = occ - LOOK_BEFORE
        for m in L:
            if m.get("result") in ("yes", "no"):
                rows.append((stem_key(m["yes_sub_title"]), bucket(posts_prior(posts, m["yes_sub_title"], look)), int(m["result"] == "yes")))
    return rows


def score_events(events, posts, model, candles_fn):
    """Per event: list of dicts for every market with a valid quote (k, p, bid, ask, yes), plus skipped count. Only events with >= 1 feed candidate are fetched."""
    out = []
    for occ, e, s, L in events:
        look = occ - LOOK_BEFORE
        ks = {m["ticker"]: posts_prior(posts, m["yes_sub_title"], look) for m in L}
        if not any(k >= MIN_POSTS for k in ks.values()):
            continue
        rows, skipped = [], 0
        for m in L:
            q = last_quote(candles_fn(m, look), look)
            if not q or m.get("result") not in ("yes", "no"):
                skipped += 1
                continue
            k = ks[m["ticker"]]
            rows.append({"ticker": m["ticker"], "k": k, "p": model(stem_key(m["yes_sub_title"]), bucket(k)), "bid": q[0], "ask": q[1], "yes": m["result"] == "yes"})
        out.append((occ, e, rows, skipped))
    return out


def summarize(scored):
    """(treated nets, control nets, treated rows, halves by event date)."""
    tr, ct = [], []
    n = len(scored)
    for i, (occ, e, rows, _sk) in enumerate(scored):
        half = 0 if i < n // 2 else 1
        for r in rows:
            if LOW <= r["ask"] <= HARD:
                ct.append(net(r["ask"], r["yes"]))
        for t, p, a in select([(r["ticker"], r["p"], r["ask"]) for r in rows if r["k"] >= MIN_POSTS]):
            r = next(x for x in rows if x["ticker"] == t)
            tr.append((half, net(a, r["yes"]), a, r["yes"], e))
    return tr, ct


def report(label, scored, out=print):
    tr, ct = summarize(scored)
    v = [t[1] for t in tr]
    n = len(v)
    mean = sum(v) / n if n else 0.0
    h1 = [t[1] for t in tr if t[0] == 0]; h2 = [t[1] for t in tr if t[0] == 1]
    cm = sum(ct) / len(ct) if ct else 0.0
    nev = len({t[4] for t in tr})
    wr = sum(t[3] for t in tr) / n if n else 0.0
    ap = sum(t[2] for t in tr) / n if n else 0.0
    ver = verdict(n, nev, mean, pf(v) if v else 0.0, sum(h1) / len(h1) if h1 else 0.0, sum(h2) / len(h2) if h2 else 0.0, cm)
    out(f"{label}: events scored {len(scored)} (with a feed candidate); treated {n} on {nev} events; win {wr:.1%} at mean fill {ap:.3f}; mean net {mean * 100:+.2f}c; PF {pf(v) if v else 0:.2f}; "
        f"halves n {len(h1)} {(sum(h1) / len(h1) * 100 if h1 else 0):+.2f}c / n {len(h2)} {(sum(h2) / len(h2) * 100 if h2 else 0):+.2f}c; "
        f"control (all cheap YES, same events) n {len(ct)} mean {cm * 100:+.2f}c PF {pf(ct) if ct else 0:.2f}; VERDICT {ver}")
    return ver


# ------------------------------------------------------------------ forward: listing, model, snapshot, read

DUE = fr.utc(2027, 6, 30)


def list_all():
    """Every market of both series (historical and live lists), with result where settled."""
    from . import api
    allm = {}
    for s in SERIES:
        for path in ("/historical/markets", "/markets"):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    allm[m["ticker"]] = {k: m.get(k) for k in ("ticker", "event_ticker", "close_time", "open_time", "occurrence_datetime", "volume_fp", "yes_sub_title",
                                                                 "custom_strike", "title", "status", "result")} | {"series": s}
                cur = d.get("cursor")
                if not cur or not d.get("markets"):
                    break
                time.sleep(0.4)
    return list(allm.values())


def model_from(listing, posts):
    fit_e, _held, _fwd = split_history(events_from_listing(listing))
    return fit(fit_rows(fit_e, posts))


def snapshot(argv, now=None, posts_fn=None, listing_fn=None, candles_fn=None, path=None, out=print):
    now = now or datetime.now(UTC)
    path = path or SNAP_FILE
    posts, fetched = (posts_fn or (lambda: (load_posts(), datetime.now(UTC))))()
    listing = (listing_fn or list_all)()
    model = model_from(listing, posts)
    have = set()
    if path.exists():
        with open(path, newline="") as fh:
            have = {r["ticker"] for r in csv.DictReader(fh)}
    if candles_fn is None:
        from . import api
        from .candlefield import quote_close
        candles_fn = lambda m, look: get_candles(m, look, api, quote_close)
    new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    wrote = nev = 0
    with open(path, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(SNAP_FIELDS)
        for occ, e, s, L in events_from_listing(listing):
            look = occ - LOOK_BEFORE
            if occ < FWD_START or now < look + timedelta(minutes=1):
                continue
            todo = [m for m in L if m["ticker"] not in have]
            if not todo:
                continue
            rows = []
            for m in todo:
                k = posts_prior(posts, m["yes_sub_title"], look)
                q = last_quote(candles_fn(m, look), look)
                rows.append((m, k, q, model(stem_key(m["yes_sub_title"]), bucket(k))))
            chosen = {t for t, _p, _a in select([(m["ticker"], p, q[1]) for m, k, q, p in rows if q and k >= MIN_POSTS])}
            for m, k, q, p in rows:
                ok = bool(q) and LOW <= q[1] <= HARD
                w.writerow([e, m["ticker"], s, m["yes_sub_title"], occ.isoformat(), look.isoformat(), k, bucket(k), round(p, 5), "" if not q else q[0], "" if not q else q[1],
                            "" if not q else round(q[2], 1), int(ok), int(ok and k >= MIN_POSTS and p >= RATIO * q[1]), int(m["ticker"] in chosen),
                            fetched.isoformat(), posts[-1][0].isoformat() if posts else ""])
                wrote += 1
            nev += 1
    out(f"snapshot: events written {nev}, rows {wrote} -> {path}")
    return 0


SPEC = fr.Spec(
    id="TRUMPTOPIC1",
    title="forward read of Trump speech word markets (KXTRUMPMENTION, KXTRUMPMENTIONB), events from 2026-11-05, CNN archive post content",
    sources=["workers/TRUMPTOPIC1_REGISTRATION.md"],
    rule=[
        "Signal needs k >= 2.",
        "Treated trade: signal (k >= 2), fill ask in [0.03, 0.30] (hard limit 0.30), p_model >= 3 x fill ask.",
        "At most 2 per event (highest p_model / ask, ties by ticker).",
        "**NOT_ENOUGH_DATA**: fewer than 150 treated trades or fewer than 25 events with a treated trade.",
        "**FALSIFIED**: at 150 or more treated trades and 25 events, PF under 1.5 after fee",
    ],
    window=["settled events with occurrence from 2026-11-05T00:00Z in KXTRUMPMENTION and KXTRUMPMENTIONB; archive posts; one minute candles [look - 60 min, look]; results"],
    due=None,
    due_note="at 150 treated trades or on 2027-06-30, whichever is first",
)


def _forward_scored(now, posts_fn=None, listing_fn=None, candles_fn=None):
    posts = (posts_fn or (lambda: (load_posts(), None)))()[0]
    listing = (listing_fn or list_all)()
    model = model_from(listing, posts)
    if candles_fn is None:
        from . import api
        from .candlefield import quote_close
        candles_fn = lambda m, look: get_candles(m, look, api, quote_close)
    fwd = [e for e in events_from_listing(listing) if e[0] >= FWD_START and e[0] + timedelta(hours=1) < now]
    return score_events(fwd, posts, model, candles_fn)


def forward(argv, now=None, posts_fn=None, listing_fn=None, candles_fn=None, out=print):
    now = now or datetime.now(UTC)

    def counts():
        sc = _forward_scored(now, posts_fn, listing_fn, candles_fn)
        tr, _ct = summarize(sc)
        return len(sc), len(tr)

    def ready(n):
        if n >= DUE:
            return None
        ne, nt = counts()
        return None if nt >= TRADES_DUE else f"{nt} forward treated trades on {ne} events with a candidate, under {TRADES_DUE}, and not yet {DUE:%Y-%m-%d}."

    def info():
        ne, nt = counts()
        return [f"forward events with a feed candidate {ne}; treated trades so far {nt} (settled events only; the count reads results of settled markets, but no read is made)"]

    def real():
        lines = []
        sc = _forward_scored(now, posts_fn, listing_fn, candles_fn)
        ver = report("FORWARD", sc, out=lines.append)
        return lines, lines[0] if lines else ver

    return fr.run(SPEC, argv, real, info, now=now, ready=ready, out=out)


main_fwd = fr.cli(forward)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "snapshot":
        return snapshot(argv[2:])
    if cmd == "forward":
        return main_fwd(argv)
    if cmd == "history":
        from . import api
        from .candlefield import quote_close
        import pathlib
        listing = json.load(open(argv[2]))
        posts = load_posts(json.load(open(argv[3])))
        cache = pathlib.Path(argv[4]); cache.mkdir(parents=True, exist_ok=True)
        cp = cache / "candles.json"
        have = json.loads(cp.read_text()) if cp.exists() else {}

        def cf(m, look):
            if m["ticker"] not in have:
                have[m["ticker"]] = get_candles(m, look, api, quote_close)
                if len(have) % 25 == 0:
                    cp.write_text(json.dumps(have))
            return have[m["ticker"]]
        ev = events_from_listing(listing)
        fit_e, held, _fwd = split_history(ev)
        model = fit(fit_rows(fit_e, posts))
        report("HELD-OUT (scored once)", score_events(held, posts, model, cf))
        cp.write_text(json.dumps(have))
        return 0
    if cmd == "census":
        listing = json.load(open(argv[2]))
        posts = load_posts(json.load(open(argv[3])))
        census(listing, posts)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
