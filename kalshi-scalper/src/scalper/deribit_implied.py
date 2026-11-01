"""DERIBIT-IMPLIED (workers/DERIBIT_IMPLIED_REGISTRATION.md): the hourly Bitcoin ladder (KXBTCD) against the digital probability implied by Deribit's
option surface, recorder scripts/record_deribit.py (branch quote-data, under deribit/). Research only. Verdict words: NOT_ENOUGH_DATA, FALSIFIED,
NOT_YET_FALSIFIED. Nothing here means trade.

    python -m scalper.deribit_implied count   qualifying rows and dates only (quotes and Deribit rows at the 45 minute look). Never opens the
                                              results file, never prints a result, a win rate or a PnL.
    python -m scalper.deribit_implied read    THE ONE READ. Refuses before 2027-01-01 00:00 UTC and a second time. Prints one verdict per try.

Written and committed BEFORE any recorded outcome was read. Every fixed number below is copied from the registration; the places where the
registration is silent are listed in AMBIGUITIES and nothing else is decided at the read.
"""
from __future__ import annotations

import calendar
import csv
import gzip
import io
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import NormalDist, median

from .mm1 import clustered_z, order_fee, pf
from .paths import DATA_DIR

ROOT = DATA_DIR.parent
WORKERS = ROOT / "workers"
RESULT_MD = WORKERS / "DERIBIT_IMPLIED_RESULT.md"
RESULT_TXT = DATA_DIR / "deribit_implied_result.txt"
MARKER = DATA_DIR / "deribit_implied_started"
REPO_SLUG = "shwoopnet/shwoopnet"
PREFIX = "deribit/"
KALSHI = "https://external-api.kalshi.com/trade-api/v2"
SERIES, SERIES_15M = "KXBTCD", "KXBTC15M"

READ_NOT_BEFORE = datetime(2027, 1, 1, tzinfo=timezone.utc).timestamp()
NORM = NormalDist()
YEAR_MS = 365.0 * 24 * 3600 * 1000

# Every fixed setting, copied from the registration.
LOOK_LEFT_MIN_S, LOOK_LEFT_MAX_S = 44 * 60 + 30, 45 * 60 + 30     # recorded minute with 44:30 to 45:29 left: [2670, 2730)
BAND = 0.03                 # strikes within 3% of S0
MAX_SPREAD = 0.04           # (yes ask - yes bid) at most 4c
MIN_EDGE = 0.05             # trade the better side if its edge is at least 5c
C = 10                      # contracts per order
FEE_RATE = 0.07
P_CLIP = (0.001, 0.999)
NEEDED_TRADES = 150
PF_EACH_HALF = 1.3
Z_MIN = 3.0
RUNNING_COUNT = 728_694     # after this card; z bar about 5.27
TRIES = ("A", "B")

AMBIGUITIES = [
    'tie rule: the registration has none ("one trade per close (the best across strikes)"). Fixed here: larger edge wins; an exact tie (within 1e-12) goes to the strike nearer S0, then the lower strike, then YES.',
    'holdout rule: the registration has no holdout beyond "the recorded span split at its midpoint date". Fixed here: UTC dates of the recorded closes, midpoint = first + (last - first) // 2 days, first half is dates up to and including it.',
    'clip: "dsigma/dK ... with sigma as decimals, clipped to [0.001, 0.999]" is read as clipping P_B (not sigma) to [0.001, 0.999]; P_A is not clipped.',
    'OICORE skip: a close whose same-instant KXBTC15M window had the OICORE rule fire is skipped; a close whose 15 minute data is missing is KEPT and counted as unknown (the registration marks every candidate paper only anyway).',
    'trade count for NOT_ENOUGH_DATA: settled trades after the OICORE skip, per try.',
]


# ---------------------------------------------------------------- small helpers

def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def epoch(iso):
    return calendar.timegm(datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").timetuple())


def utc_date(close):
    return datetime.fromtimestamp(close, timezone.utc).date().isoformat()


MONTHS = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}


def expiry_of(name):
    """'BTC-13NOV26-83000-P' -> expiry epoch (08:00 UTC that date), or None."""
    try:
        d = name.split("-")[1]
        return int(datetime(2000 + int(d[-2:]), MONTHS[d[-5:-2]], int(d[:-5]), 8, tzinfo=timezone.utc).timestamp())
    except Exception:
        return None


# ---------------------------------------------------------------- the model (registration "The math, fixed now")

def otm_ivs(rows, forward):
    """{strike: sigma decimal} from one expiry's rows: the out-of-the-money option at each strike (put below the forward, call at or above), mark_iv of 0 or missing dropped."""
    out = {}
    for r in rows:
        k, iv = num(r.get("strike")), num(r.get("mark_iv"))
        if k is None or not iv or iv <= 0:
            continue
        kind = r.get("kind")
        if (kind == "P" and k < forward) or (kind == "C" and k >= forward):
            out[k] = iv / 100.0
    return out


def sigma_at(ivs, k):
    """(sigma(K), K1, sigma1, K2, sigma2) by linear interpolation between the two adjacent listed strikes K1 <= K <= K2, or None outside the listed strikes (no extrapolation)."""
    ks = sorted(ivs)
    if not ks or k < ks[0] or k > ks[-1]:
        return None
    lo = [x for x in ks if x <= k]
    hi = [x for x in ks if x > k]
    if hi:
        k1, k2 = lo[-1], hi[0]
    elif len(lo) >= 2:                       # K is exactly the top strike: use the pair below it
        k1, k2 = lo[-2], lo[-1]
    else:
        return None
    s1, s2 = ivs[k1], ivs[k2]
    return s1 + (s2 - s1) * (k - k1) / (k2 - k1), k1, s1, k2, s2


def probabilities(k, ivs, f_t, tau_t):
    """(P_A, P_B) for 'final above K', or None when the strike cannot be priced."""
    s = sigma_at(ivs, k)
    if s is None or tau_t <= 0 or f_t <= 0 or k <= 0:
        return None
    sig, k1, s1, k2, s2 = s
    w = sig * sig * tau_t
    if w <= 0:
        return None
    sw = math.sqrt(w)
    d2 = (math.log(f_t / k) - w / 2) / sw
    d1 = d2 + sw
    p_a = NORM.cdf(d2)
    vega = f_t * NORM.pdf(d1) * math.sqrt(tau_t)
    p_b = min(P_CLIP[1], max(P_CLIP[0], p_a - vega * (s2 - s1) / (k2 - k1)))
    return p_a, p_b


def curve_inputs(deribit_rows, s0, t_close_ms):
    """(ivs of E1, F_T, tau_T) from the rank 1 rows of one poll minute, or None. t = median creation_timestamp, F_E1 = median underlying_price."""
    e1 = [r for r in deribit_rows if str(r.get("expiry_rank")) == "1"]
    if not e1 or not s0:
        return None
    exp = expiry_of(e1[0].get("instrument_name") or "")
    t = median(x for x in (num(r.get("creation_timestamp")) for r in e1) if x)  if any(num(r.get("creation_timestamp")) for r in e1) else None
    f_e1 = median(x for x in (num(r.get("underlying_price")) for r in e1) if x) if any(num(r.get("underlying_price")) for r in e1) else None
    if exp is None or t is None or f_e1 is None:
        return None
    tau_e1, tau_t = (exp * 1000 - t) / YEAR_MS, (t_close_ms - t) / YEAR_MS
    if tau_e1 <= 0 or tau_t <= 0:
        return None
    ivs = otm_ivs(e1, f_e1)
    return ivs, s0 * (f_e1 / s0) ** (tau_t / tau_e1), tau_t


# ---------------------------------------------------------------- the look, the universe, the rule

def universe_rows(kalshi_rows, s0):
    """Quotes of the look minute that pass the cost screen: within 3% of S0, two-sided, spread at most 4c. [(strike, ticker, yes_bid, yes_ask)]."""
    out = []
    for r in kalshi_rows:
        k, b, a = num(r.get("strike")), num(r.get("yes_bid")), num(r.get("yes_ask"))
        if k is None or b is None or a is None or abs(k / s0 - 1.0) > BAND:
            continue
        if b > 0 and a < 1 and a - b <= MAX_SPREAD + 1e-9:
            out.append((k, r.get("ticker"), b, a))
    return out


def fee(p):
    return order_fee(FEE_RATE, C, p)


def pick_trade(uni, probs, s0):
    """The one trade of a close for one try. uni: universe_rows; probs: {strike: P}. Returns (side, strike, ticker, ask, edge) or None.
    edge_YES = P - yes_ask; edge_NO = (1 - P) - no_ask with no_ask = 1 - yes_bid. Larger edge wins, at least MIN_EDGE; tie: nearer S0, lower strike, YES."""
    best = None
    for k, tk, b, a in uni:
        if k not in probs:
            continue
        p = probs[k]
        for side, ask, edge in (("yes", a, p - a), ("no", 1.0 - b, (1.0 - p) - (1.0 - b))):
            if edge < MIN_EDGE - 1e-12:
                continue
            key = (-round(edge, 12), abs(k - s0), k, 0 if side == "yes" else 1)
            if best is None or key < best[0]:
                best = (key, (side, k, tk, ask, edge))
    return best[1] if best else None


def net_pnl(side, ask, result, mult=1.0):
    """Net dollars of one C = 10 order held to settlement (fee charged at the fill, win or lose)."""
    win = (result == "yes") == (side == "yes")
    return (C * (1.0 - ask) if win else -C * ask) - fee(ask) * mult


# ---------------------------------------------------------------- reading the recorder files

def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True).stdout


class GitSource:
    """File names and gzipped CSV blobs of origin/quote-data under deribit/. Tests pass a dict-backed source instead."""

    def names(self):
        _git("fetch", "-q", "origin", "+refs/heads/quote-data:refs/remotes/origin/quote-data")
        return [n for n in _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split() if n.startswith(PREFIX)]

    def blob(self, path):
        raw = _git("show", f"origin/quote-data:{path}")
        if not raw:
            r = subprocess.run(["gh", "api", f"repos/{REPO_SLUG}/contents/{path}?ref=quote-data", "-H", "Accept: application/vnd.github.raw"], capture_output=True)
            raw = r.stdout
        return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def in_look(close, ts_ms):
    left = close - num(ts_ms) / 1000.0
    return LOOK_LEFT_MIN_S <= left < LOOK_LEFT_MAX_S


def load_looks(src):
    """{close_epoch: look dict} from the kalshi, deribit and index files only (NEVER the results file). A look is the first recorded minute in the
    44:30 to 45:29 window that has all three of a Kalshi row, a Deribit row and an index price. Overlapping runs are merged by timestamp."""
    runs = sorted({n.rsplit("/", 1)[0] for n in src.names() if n.endswith("/coverage.csv.gz")})
    kal, der, idx = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list)), defaultdict(dict)
    for run in runs:
        for r in src.blob(f"{run}/index.csv.gz"):
            c, ts, px = epoch(r["close_time"]), r["poll_ts_local_ms"], num(r["index_price"])
            if px and in_look(c, ts):
                idx[c][ts] = px
        for r in src.blob(f"{run}/kalshi.csv.gz"):
            c = epoch(r["close_time"])
            if in_look(c, r["poll_ts_local_ms"]):
                kal[c][r["poll_ts_local_ms"]].append(r)
        for r in src.blob(f"{run}/deribit.csv.gz"):
            c = epoch(r["close_time"])
            if in_look(c, r["poll_ts_local_ms"]):
                der[c][r["poll_ts_local_ms"]].append(r)
    seen = {c for c in list(kal) + list(der) + list(idx)}
    out = {}
    for c in sorted(seen):
        both = sorted((ts for ts in kal[c] if ts in der[c] and ts in idx[c]), key=lambda t: num(t))
        out[c] = ({"ts": both[0], "s0": idx[c][both[0]], "kalshi": kal[c][both[0]], "deribit": der[c][both[0]]} if both else None)
    return out


def priced_look(c, look):
    """(s0, universe rows, {try: {strike: P}}) for one close, or None when the look cannot be priced. Uses quotes and Deribit rows only."""
    if not look:
        return None
    s0 = look["s0"]
    ci = curve_inputs(look["deribit"], s0, c * 1000)
    uni = universe_rows(look["kalshi"], s0)
    if ci is None or not ci[0] or not uni:
        return None
    ivs, f_t, tau_t = ci
    probs = {"A": {}, "B": {}}
    for k, _tk, _b, _a in uni:
        pr = probabilities(k, ivs, f_t, tau_t)
        if pr:
            probs["A"][k], probs["B"][k] = pr
    return s0, uni, probs


def candidates(looks):
    """({try: [trade dict]}, stats) with the trade rule applied to each look. No outcome is touched: a trade has a ticker, a side, an ask, a date."""
    trades = {t: [] for t in TRIES}
    unpriced = 0
    for c, look in sorted(looks.items()):
        pl = priced_look(c, look)
        if pl is None:
            unpriced += 1
            continue
        s0, uni, probs = pl
        for t in TRIES:
            tr = pick_trade(uni, probs[t], s0)
            if tr:
                trades[t].append({"close": c, "date": utc_date(c), "side": tr[0], "strike": tr[1], "ticker": tr[2], "ask": tr[3], "edge": tr[4]})
    return trades, {"closes": len(looks), "unpriced": unpriced}


def span_halves(dates):
    """(first, mid, last) UTC dates of the recorded closes; the first half is dates up to and including mid."""
    ds = sorted(set(dates))
    a, b = date.fromisoformat(ds[0]), date.fromisoformat(ds[-1])
    return a.isoformat(), (a + timedelta(days=(b - a).days // 2)).isoformat(), b.isoformat()


# ---------------------------------------------------------------- count (no outcomes)

def count(src=None, out=print):
    """Qualifying rows and dates only. Opens kalshi, deribit and index files; never the results file."""
    looks = load_looks(src or GitSource())
    trades, st = candidates(looks)
    got = sorted(c for c, l in looks.items() if l)
    out(f"DERIBIT-IMPLIED count (quotes only, nothing settled is read): closes with any recorded look row {st['closes']}, with a complete look {len(got)}, priced {len(got) - st['unpriced']}")
    if got:
        dates = sorted({utc_date(c) for c in got})
        out(f"dates (UTC) {dates[0]} to {dates[-1]}, {len(dates)} dates")
    for t in TRIES:
        ds = sorted({x["date"] for x in trades[t]})
        out(f"try {t}: qualifying trades (before the OICORE skip) {len(trades[t])}" + (f" on {len(ds)} dates, {ds[0]} to {ds[-1]}" if ds else "") + f"; registered minimum {NEEDED_TRADES}")
    return {t: len(trades[t]) for t in TRIES}


# ---------------------------------------------------------------- read

def z_bar(n=RUNNING_COUNT):
    return NormalDist().inv_cdf(1 - 0.05 / n)


def fetch_results(close):
    """{strike: result} from Kalshi's public settled markets of the close (the scorer's own fetch, as the registration says)."""
    q = urllib.parse.urlencode({"series_ticker": SERIES, "status": "settled", "min_close_ts": close, "max_close_ts": close, "limit": 1000})
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{KALSHI}/markets?{q}", headers={"User-Agent": "shwoopnet-research-scorer"}), timeout=20) as r:
            ms = json.load(r).get("markets", [])
    except Exception:
        return {}
    return {num(m.get("floor_strike")): m.get("result") for m in ms if m.get("result") in ("yes", "no")}


def load_results(src):
    """{close: {strike: result}} from the recorder's results files (the read only)."""
    out = defaultdict(dict)
    for run in sorted({n.rsplit("/", 1)[0] for n in src.names() if n.endswith("/coverage.csv.gz")}):
        for r in src.blob(f"{run}/results.csv.gz"):
            if r.get("result") in ("yes", "no") and num(r.get("strike")) is not None:
                out[epoch(r["close_time"])][num(r["strike"])] = r["result"]
    return out


def oicore_held(closes):
    """{close: True/False} for the KXBTC15M window closing at the same instant, by OICORE's published rule from data/fresh.sqlite; a close with no candles is absent (unknown)."""
    import sqlite3
    from . import oifeed as O
    out = {}
    try:
        db = sqlite3.connect(f"file:{O.FRESH}?mode=ro", uri=True)
    except Exception:
        return out
    try:
        for tk, ct in db.execute("select ticker, close_ts from market where series=?", (SERIES_15M,)):
            if ct not in closes:
                continue
            q = {e: (b, a, oi) for e, b, a, oi in db.execute("select end_ts, bid_c, ask_c, oi from candle where ticker=? and end_ts in (?, ?)", (tk, ct - O.LOOK, ct - O.BACK))}
            s, p = q.get(ct - O.LOOK), q.get(ct - O.BACK)
            if not s or not p or s[0] is None or s[1] is None or s[2] is None or p[2] is None:
                continue
            cand = any(O.LO - 1e-9 <= a <= O.HI + 1e-9 for a in (s[1], round(1 - s[0], 4)))
            out[ct] = bool(cand and s[2] - p[2] > O.THRESH)
    finally:
        db.close()
    return out


def judge(tr, brier, span, name):
    """Registered verdict for one try. tr: settled trades with pnl, pnl_stress, date. brier: (kalshi, deribit, n). Returns (verdict, lines)."""
    n = len(tr)
    first, mid, last = span
    h1 = [x for x in tr if x["date"] <= mid]
    h2 = [x for x in tr if x["date"] > mid]
    pf1, pf2 = pf([x["pnl"] for x in h1]), pf([x["pnl"] for x in h2])
    vals = [x["pnl"] for x in tr]
    z = clustered_z(vals, [x["date"] for x in tr]) if n > 1 else 0.0
    zb = z_bar()
    L = [f"try {name}: settled trades {n}; PF {pf(vals):.2f} (fees x1.2 {pf([x['pnl_stress'] for x in tr]):.2f}); halves split at {mid} (span {first} to {last}): "
         f"first {len(h1)} trades PF {pf1:.2f}, second {len(h2)} trades PF {pf2:.2f}; day-clustered z {z:.2f} (deflated bar {zb:.2f}); "
         f"net {sum(vals):+.2f} dollars at C {C}; Brier Kalshi mid {brier[0]:.4f} vs Deribit {brier[1]:.4f} on {brier[2]} strikes"]
    if n < NEEDED_TRADES:
        return "NOT_ENOUGH_DATA", L + [f"try {name}: {n} trades is under {NEEDED_TRADES}; nothing else is judged."]
    why = []
    if pf1 < PF_EACH_HALF:
        why.append(f"PF {pf1:.2f} under {PF_EACH_HALF} in the first half")
    if pf2 < PF_EACH_HALF:
        why.append(f"PF {pf2:.2f} under {PF_EACH_HALF} in the second half")
    if brier[2] == 0 or brier[0] <= brier[1]:
        why.append(f"Kalshi's Brier {brier[0]:.4f} is at or below Deribit's {brier[1]:.4f}")
    if z < Z_MIN:
        why.append(f"z {z:.2f} under {Z_MIN}")
    if z < zb:
        why.append(f"z {z:.2f} under the deflated bar {zb:.2f}")
    if why:
        return "FALSIFIED", L + [f"try {name} FALSIFIED: " + "; ".join(why)]
    return "NOT_YET_FALSIFIED", L + [f"try {name} NOT_YET_FALSIFIED (never proven; the next step is a larger forward window)"]


def brier_of(looks, results):
    """{try: (kalshi Brier, deribit Brier, n)} over every universe strike at the look that has a result and a P for that try."""
    acc = {t: [0.0, 0.0, 0] for t in TRIES}
    for c, look in looks.items():
        pl = priced_look(c, look)
        if pl is None:
            continue
        _s0, uni, probs = pl
        for k, _tk, b, a in uni:
            res = results.get(c, {}).get(k)
            if res is None:
                continue
            y = 1.0 if res == "yes" else 0.0
            for t in TRIES:
                if k in probs[t]:
                    acc[t][0] += ((b + a) / 2 - y) ** 2
                    acc[t][1] += (probs[t][k] - y) ** 2
                    acc[t][2] += 1
    return {t: ((v[0] / v[2], v[1] / v[2], v[2]) if v[2] else (float("nan"), float("nan"), 0)) for t, v in acc.items()}


def run(now=None, src=None, held_fn=None, fetch_fn=None):
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if RESULT_TXT.exists():
        print(f"Refusing to run again: {RESULT_TXT} exists.")
        return None
    if now < READ_NOT_BEFORE:
        print(f"Refusing: the read date is {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC.")
        return None
    if MARKER.exists():
        print(f"Refusing: {MARKER} exists without a result (a crashed run is never quietly read twice; the lead decides).")
        return None
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(f"started {datetime.now(timezone.utc).isoformat()}\n")
    src = src or GitSource()
    looks = load_looks(src)
    cands, st = candidates(looks)
    got = [c for c, l in looks.items() if l]
    if not got:
        return _write({t: "NOT_ENOUGH_DATA" for t in TRIES}, ["no complete look was recorded; nothing scored."], now)
    span = span_halves([utc_date(c) for c in got])
    held = (held_fn or oicore_held)(set(got))
    results = load_results(src)
    for c in got:
        if c not in results:
            results[c] = (fetch_fn or fetch_results)(c)
    brier = brier_of(looks, results)
    lines = [f"closes with a complete look {len(got)}, priced {len(got) - st['unpriced']}; OICORE fired on {sum(1 for c in got if held.get(c))}, unknown for {sum(1 for c in got if c not in held)} (kept)",
             "every candidate is PAPER ONLY (L1 / OICORE overlap, registration)"]
    verdicts = {}
    for t in TRIES:
        settled, unsettled, skipped = [], 0, 0
        for x in cands[t]:
            if held.get(x["close"]):
                skipped += 1
                continue
            res = results.get(x["close"], {}).get(x["strike"])
            if res is None:
                unsettled += 1
                continue
            settled.append(dict(x, pnl=net_pnl(x["side"], x["ask"], res), pnl_stress=net_pnl(x["side"], x["ask"], res, 1.2)))
        lines.append(f"try {t}: {len(cands[t])} candidates, {skipped} skipped by OICORE, {unsettled} without a result, {len(settled)} scored")
        verdicts[t], more = judge(settled, brier[t], span, t)
        lines += more
    return _write(verdicts, lines, now)


def _write(verdicts, lines, now):
    head = "DERIBIT-IMPLIED VERDICT " + "; ".join(f"try {t}: {v}" for t, v in verdicts.items()) + f" (2 tries; running count about {RUNNING_COUNT:,})"
    body = "\n".join([head] + lines) + "\n"
    RESULT_TXT.parent.mkdir(parents=True, exist_ok=True)
    RESULT_TXT.write_text(body)
    RESULT_MD.write_text(f"# DERIBIT-IMPLIED result (read once at {datetime.fromtimestamp(now, timezone.utc):%Y-%m-%d %H:%M} UTC; research only)\n\n```\n{body}```\n")
    print(body)
    return verdicts


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "count":
        count()
    elif cmd == "read":
        run()
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
