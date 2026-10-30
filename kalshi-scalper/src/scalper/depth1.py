"""DEPTH1 (workers/DEPTH1_REGISTRATION.md): five-level order-book imbalance in the 15 minute gold and Bitcoin markets, recorder R6.
Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade.

    python -m scalper.depth1 freeze      print the sha256 of the 10 feature definitions and the fixed settings; write
                                         workers/DEPTH1_FROZEN.md and workers/DEPTH1_frozen.json (done BEFORE any R6 row is opened)
    python -m scalper.depth1 readiness   count R6 recorder runs from the file NAMES on origin/quote-data (no file is opened), estimate
                                         the windows per market, project to the recorder's end and say if 300 per market is on track
    python -m scalper.depth1 read        THE ONE READ. Refuses before 2026-11-14 00:00 UTC and a second time; below 300 scored windows
                                         in either market it writes NOT_ENOUGH_DATA and scores nothing.

The registered rule, the features and the reasons for every fixed number are in workers/DEPTH1_REGISTRATION.md. Changing a feature or a
fixed setting changes the hash in FEATURE_HASH, and tests/test_depth1.py fails against workers/DEPTH1_frozen.json.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import inspect
import io
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import NormalDist
from zoneinfo import ZoneInfo

from . import r6tests as R6
from .mm1 import central_date, clustered_z, order_fee, pf
from .paths import DATA_DIR
from .quote2b import Poll

CT = ZoneInfo("America/Chicago")
ROOT = DATA_DIR.parent
WORKERS = ROOT / "workers"
FROZEN_JSON = WORKERS / "DEPTH1_frozen.json"
FROZEN_MD = WORKERS / "DEPTH1_FROZEN.md"
RESULT_MD = WORKERS / "DEPTH1_RESULT.md"
RESULT_TXT = DATA_DIR / "depth1_result.txt"
MARKER = DATA_DIR / "depth1_started"
REPO_SLUG = "shwoopnet/shwoopnet"

READ_NOT_BEFORE = datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp()
END_UTC = datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc).timestamp()      # the recorder opens no window at or after this
FIRST_DATE = "2026-10-30"                                                      # US Central date of a window's close; earlier is excluded
BLOCKS = (("2026-10-30", "2026-11-03"), ("2026-11-04", "2026-11-08"), ("2026-11-09", "2026-11-13"))
GOLD, BTC = "KXGOLD15M", "KXBTC15M"
UNIVERSE = (GOLD, BTC)
NEEDED = 300
EPS = 5e-5

# Every fixed setting. Hashed with the feature source: change one and the frozen hash no longer matches.
CONFIG = {
    "markets": list(UNIVERSE),
    "decision_s_before_close": 480, "decision_poll_max_early_s": 10,
    "lookback_poll_max_early_s": 6, "tape_lookback_s": 60,
    "fill": "first poll at or after decision + 1.0 s, best ask of the implied side, 1 contract, held to settlement",
    "live_delay_s": 1.0, "fill_poll_max_late_s": 20,
    "ask_band": [0.10, 0.90], "min_ask_size": 1.0,
    "sign_rule": "feature > 0 buys YES, < 0 buys NO, 0 or undefined: no trade; no threshold",
    "fee": "7% x C x p x (1-p) rounded up to the cent per order, C = 1; stress = fee x 1.2",
    "blocks_by_central_close_date": [list(b) for b in BLOCKS], "first_date": FIRST_DATE,
    "usable": {"min_ok_polls": R6.MIN_OK, "max_gap_ms": R6.MAX_GAP_MS, "tape_pages_min": 1, "bad_notes": list(R6.BAD_NOTES),
               "first_recv_at_or_before_s": 545, "last_recv_at_or_after_s": 470, "result": "yes or no"},
    "needed_windows_per_market": NEEDED, "second_look": {"accuracy": 0.55, "n": 300},
    "bar": {"pf_each_block": 1.5, "pf_pooled": 1.5, "halves_pf_above": 1.0, "stress_pf_above": 1.2, "z_bar_N": 728628 + 20, "n_trades": 300},
    "control": {"shuffles": 1000, "seed": 20261114, "stat": "mean net per trade, best of 20 tries per shuffle round", "p": 0.01},
    "overlap": {"gold": "L1: exactly one side's ask 0.88 to 0.97 at the poll ending 360 s before the close",
                "btc": "OICORE: a side's ask 0.05 to 0.50 at the candle ending 180 s before the close and open interest up more than 86299.56 over the 3 minutes before"},
    "read_not_before_utc": "2026-11-14T00:00:00Z", "recorder_end_utc": "2026-11-13T23:59:00Z",
}


# ---------------------------------------------------------------- the 10 features (frozen)
# Book of one poll, YES terms: yb / ybs = YES bid prices / sizes, best first; nb / nbs = NO bid prices / sizes, best first (5 levels at most).
# YES ask = 1 - nb[0]; NO ask = 1 - yb[0]. A NO bid is a resting offer to sell YES at 1 - nb. Every feature is signed: positive buys YES,
# negative buys NO. A feature returns None when its inputs are missing (then no trade). Ctx: S the decision poll, P30 / P60 the polls
# about 30 / 60 s earlier (or None), tape the trades (t, yes_px, n, side) in the 60 s up to S.

def _sums(p):
    return sum(p.ybs[:5]), sum(p.nbs[:5])


def _imb(p):
    y, n = _sums(p)
    return (y - n) / (y + n) if p.yb and p.nb and y + n > 0 else None


def _slope(px, sz):
    """Price given up per contract of depth, from the touch to the last recorded level; needs two levels."""
    if len(px) < 2 or sum(sz) <= 0:
        return None
    return (px[0] - px[-1]) / sum(sz)


def f1_imb5(c):
    """(YES bid size - NO bid size) / total over the 5 recorded levels. Thin NO side gets lifted by YES buyers: positive buys YES."""
    return _imb(c.S)


def f2_imb1(c):
    """The same at the touch only."""
    p = c.S
    if not (p.yb and p.nb) or p.ybs[0] + p.nbs[0] <= 0:
        return None
    return (p.ybs[0] - p.nbs[0]) / (p.ybs[0] + p.nbs[0])


def f3_dwmid_minus_mid(c):
    """Size-weighted mid of the 5 levels minus the plain mid, YES price. Weighted YES bid B, weighted YES ask A = 1 - weighted NO bid."""
    p = c.S
    if not (p.yb and p.nb) or sum(p.ybs[:5]) <= 0 or sum(p.nbs[:5]) <= 0:
        return None
    b = sum(x * s for x, s in zip(p.yb[:5], p.ybs[:5])) / sum(p.ybs[:5])
    a = 1 - sum(x * s for x, s in zip(p.nb[:5], p.nbs[:5])) / sum(p.nbs[:5])
    return (b + a) / 2 - (p.yb[0] + 1 - p.nb[0]) / 2


def f4_d_imb30(c):
    """f1 now minus f1 about 30 s earlier: the book leaning more toward YES buys YES."""
    a, b = _imb(c.S), _imb(c.P30) if c.P30 is not None else None
    return None if a is None or b is None else a - b


def f5_d_imb60(c):
    """The same over about 60 s."""
    a, b = _imb(c.S), _imb(c.P60) if c.P60 is not None else None
    return None if a is None or b is None else a - b


def f6_thin_depletion(c):
    """The thinner side 60 s ago (5 level size): its relative loss of size by now. A thin NO side emptying buys YES (+), a thin YES side emptying buys NO (-)."""
    if c.P60 is None or not (c.S.yb and c.S.nb and c.P60.yb and c.P60.nb):
        return None
    y0, n0 = _sums(c.P60)
    y1, n1 = _sums(c.S)
    if y0 <= 0 or n0 <= 0:
        return None
    if y0 == n0:
        return 0.0
    return (n0 - n1) / n0 if n0 < y0 else -(y0 - y1) / y0


def f7_sweep_net(c):
    """Sweeps in the last 60 s: trades of one taker side in the same whole second at 2 or more prices. YES sweeps minus NO sweeps."""
    g = defaultdict(set)
    for t, px, n, side in c.tape:
        g[(math.floor(t), side)].add(round(px, 4))
    return float(sum((1 if k[1] == "yes" else -1) for k, v in g.items() if len(v) >= 2 and k[1] in ("yes", "no")))


def f8_hole_asymmetry(c):
    """Gap behind the touch on the NO side minus on the YES side (a missing second level counts as a gap down to 0). A hole behind the YES touch buys NO."""
    p = c.S
    if not (p.yb and p.nb):
        return None
    gy = p.yb[0] - (p.yb[1] if len(p.yb) > 1 else 0.0)
    gn = p.nb[0] - (p.nb[1] if len(p.nb) > 1 else 0.0)
    return gn - gy


def f9_book_slope(c):
    """Slope of the NO side minus the YES side (price given up per contract of depth). A steep, thin YES side buys NO."""
    sy, sn = _slope(c.S.yb[:5], c.S.ybs[:5]), _slope(c.S.nb[:5], c.S.nbs[:5])
    return None if sy is None or sn is None else sn - sy


def f10_imb_3c(c):
    """f1 counting only size within 0.03 of each side's touch."""
    p = c.S
    if not (p.yb and p.nb):
        return None
    y = sum(s for x, s in zip(p.yb[:5], p.ybs[:5]) if x >= p.yb[0] - 0.03 - EPS)
    n = sum(s for x, s in zip(p.nb[:5], p.nbs[:5]) if x >= p.nb[0] - 0.03 - EPS)
    return (y - n) / (y + n) if y + n > 0 else None


FEATURES = (f1_imb5, f2_imb1, f3_dwmid_minus_mid, f4_d_imb30, f5_d_imb60, f6_thin_depletion, f7_sweep_net, f8_hole_asymmetry,
            f9_book_slope, f10_imb_3c)
HELPERS = (_sums, _imb, _slope)
NAMES = tuple(f.__name__ for f in FEATURES)
assert len(FEATURES) == 10


def feature_hashes():
    out = {f.__name__: hashlib.sha256(inspect.getsource(f).encode()).hexdigest() for f in HELPERS + FEATURES}
    out["CONFIG"] = hashlib.sha256(json.dumps(CONFIG, sort_keys=True).encode()).hexdigest()
    return out


def feature_hash():
    """One sha256 over every helper and feature source and the fixed settings."""
    return hashlib.sha256(json.dumps(feature_hashes(), sort_keys=True).encode()).hexdigest()


class Ctx:
    __slots__ = ("S", "P30", "P60", "tape")

    def __init__(self, S, P30, P60, tape):
        self.S, self.P30, self.P60, self.tape = S, P30, P60, tape


# ---------------------------------------------------------------- freeze

def freeze():
    h, hs = feature_hash(), feature_hashes()
    if FROZEN_JSON.exists():
        old = json.loads(FROZEN_JSON.read_text())
        print("already frozen:", old["feature_hash"], "(current", h + ")")
        return 0 if old["feature_hash"] == h else 1
    doc = {"id": "DEPTH1", "frozen_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "feature_hash": h, "hashes": hs,
           "features": list(NAMES), "config": CONFIG}
    FROZEN_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    lines = ["# DEPTH1 frozen features (sha256, written before any R6 row was opened)", "",
             f"Frozen {doc['frozen_utc']} by `python -m scalper.depth1 freeze`. `tests/test_depth1.py` fails if any source below changes.", "",
             f"**Total sha256: `{h}`**", "", "| Name | sha256 of its source |", "|---|---|"]
    lines += [f"| {k} | `{v}` |" for k, v in hs.items()]
    lines += ["", "Fixed settings (CONFIG, hashed as one block):", "", "```json", json.dumps(CONFIG, indent=1, sort_keys=True), "```", ""]
    FROZEN_MD.write_text("\n".join(lines))
    print("DEPTH1 frozen sha256", h)
    for k, v in hs.items():
        print(f"  {k:24s} {v}")
    return 0


# ---------------------------------------------------------------- names on origin/quote-data (readiness; no file is opened)

def _names():
    """Every file path on the quote-data branch, names only. Falls back to the GitHub tree listing when the local clone has no tree."""
    R6._git("fetch", "-q", "origin", "+refs/heads/quote-data:refs/remotes/origin/quote-data")
    names = R6._git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    if not any(n.startswith(R6.PREFIX) for n in names):
        r = subprocess.run(["gh", "api", f"repos/{REPO_SLUG}/git/trees/quote-data?recursive=1", "--jq", '.tree[]|select(.type=="blob")|.path'],
                           capture_output=True, text=True)
        names = r.stdout.split()
    return [n for n in names if n.startswith(R6.PREFIX)]


def run_spans(names):
    """[(start, end)] UTC seconds of each recorder run seen by a coverage file name: a job records from its start to the next 4 hour boundary."""
    out = []
    for n in sorted({x.rsplit("/", 1)[0] for x in names if x.endswith("/coverage.csv.gz")}):
        d, hm = n[len(R6.PREFIX):].split("/")
        s = datetime.strptime(d + hm, "%Y-%m-%d%H%M").replace(tzinfo=timezone.utc)
        e = s.replace(minute=0, second=0) + timedelta(hours=4 - s.hour % 4)
        out.append((s.timestamp(), min(e.timestamp(), END_UTC)))
    return out


def gold_open(t):
    """Gold's 15 minute market is closed from Friday 17:00 to Sunday 18:00 US Central (the site's own silent-market rule); a daily break is not modelled."""
    c = datetime.fromtimestamp(t, CT)
    return not ((c.weekday() == 4 and c.hour >= 17) or c.weekday() == 5 or (c.weekday() == 6 and c.hour < 18))


def hours(a, b, only_gold=False, from_t=None):
    """Hours in [a, b) on a 15 minute grid, optionally gold's open hours and only from a time on."""
    a = max(a, from_t) if from_t else a
    t, n = a, 0
    while t < b - 1:
        n += 1 if (not only_gold or gold_open(t)) else 0
        t += 900
    return n / 4


def project(spans, now, usable_share=0.7):
    """Eligible windows (close on or after 2026-10-30 US Central) so far, and projected to the recorder's end at the observed coverage rate."""
    first = datetime(2026, 10, 30, tzinfo=CT).timestamp()
    out = {}
    if not spans:
        return out
    t0 = min(s for s, _ in spans)
    rate = sum(min(e, now) - s for s, e in spans if s < now) / max(1.0, now - t0)
    for name, g in (("gold", True), ("bitcoin", False)):
        have = sum(hours(s, min(e, now), g, first) for s, e in spans) * 4
        rest = hours(now, END_UTC, g) * 4 * rate
        out[name] = {"so_far": have, "projected": have + rest, "usable_projected": (have + rest) * usable_share,
                     "need_rate": max(0.0, (NEEDED / usable_share - have) / max(1e-9, hours(now, END_UTC, g) * 4))}
    out["rate"] = rate
    return out


def readiness(now=None):
    now = time.time() if now is None else now
    names = _names()
    spans = run_spans(names)
    p = project(spans, now)
    if not p:
        line = f"DEPTH1 readiness: {len(names)} R6 files on quote-data, no run yet"
        print(line)
        return line
    parts = []
    for k in ("gold", "bitcoin"):
        v = p[k]
        state = "on track" if v["usable_projected"] >= NEEDED else "OFF TRACK (NOT_ENOUGH_DATA expected)"
        parts.append(f"{k} ~{v['so_far']:.0f} windows so far (estimate), ~{v['projected']:.0f} by Nov 13, ~{v['usable_projected']:.0f} usable "
                     f"at 70%: {state}, 300 needs {100 * v['need_rate']:.0f}% recording coverage from now")
    line = (f"DEPTH1 readiness: {len(spans)} R6 runs from file names ({len(names)} files, none opened), recording coverage so far "
            f"{100 * p['rate']:.0f}%; " + "; ".join(parts) + f"; read on or after {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC")
    print(line)
    return line


# ---------------------------------------------------------------- one window (pure)

def window_record(polls, trades, close, result):
    """polls: [Poll] exchange time, sorted. trades: [(t, yes_px, n, "yes"|"no")] sorted. Returns the window's features and what each side would
    have paid, or None when there is no decision poll. No portfolio rule, no threshold: one decision at T-480 s."""
    S = R6.last_at(polls, close - CONFIG["decision_s_before_close"], CONFIG["decision_poll_max_early_s"])
    if S is None:
        return None
    e = CONFIG["lookback_poll_max_early_s"]
    P30, P60 = R6.last_at(polls, S.t - 30, e), R6.last_at(polls, S.t - 60, e)
    tape = [x for x in trades if S.t - CONFIG["tape_lookback_s"] < x[0] <= S.t]
    c = Ctx(S, P30, P60, tape)
    feat = {}
    for f in FEATURES:
        try:
            v = f(c)
        except Exception:
            v = None
        feat[f.__name__] = None if v is None or v != v else float(v)
    F = R6.first_at(polls, S.t + CONFIG["live_delay_s"], CONFIG["fill_poll_max_late_s"])
    lo, hi = CONFIG["ask_band"]
    fill = {}
    for side in ("yes", "no"):
        px = sz = None
        if F is not None:
            if side == "yes" and F.nb:
                px, sz = F.ask, F.nbs[0]
            if side == "no" and F.yb:
                px, sz = 1 - F.yb[0], F.ybs[0]
        ok = px is not None and lo - EPS <= px <= hi + EPS and sz >= CONFIG["min_ask_size"]
        if ok:
            fee = order_fee(0.07, 1, px)
            win = 1.0 if result == side else 0.0
            fill[side] = {"px": px, "pnl": win - px - fee, "pnl_stress": win - px - 1.2 * fee, "win": win}
        else:
            fill[side] = None
    S6 = R6.last_at(polls, close - R6.Q_SIGNAL, R6.Q_SIGNAL_GAP)
    l1 = None
    if S6 is not None:
        yi = S6.ask is not None and R6.BAND_LO - EPS <= S6.ask <= R6.BAND_HI + EPS
        ni = S6.bid is not None and R6.BAND_LO - EPS <= 1 - S6.bid <= R6.BAND_HI + EPS
        l1 = yi != ni
    return {"close": close, "feat": feat, "fill": fill, "result": result, "l1_signal": l1}


def trade_of(w, name):
    """(side, fill dict) for a window and feature, or None when no trade is made."""
    v = w["feat"].get(name)
    if v is None or v == 0:
        return None
    side = "yes" if v > 0 else "no"
    f = w["fill"].get(side)
    return (side, f) if f else None


# ---------------------------------------------------------------- scoring (pure)

def block_of(date):
    for i, (a, b) in enumerate(BLOCKS):
        if a <= date <= b:
            return i
    return None


def z_bar(n=CONFIG["bar"]["z_bar_N"]):
    return NormalDist().inv_cdf(1 - 0.05 / n)


def try_stats(ws, name):
    """ws: window records with "date" and "close". Statistics of one feature's trades on these windows."""
    tr = sorted(((w["close"], w["date"], *trade_of(w, name)) for w in ws if trade_of(w, name)), key=lambda x: x[0])
    pn = [t[3]["pnl"] for t in tr]
    st = [t[3]["pnl_stress"] for t in tr]
    n = len(tr)
    blocks = [[t[3]["pnl"] for t in tr if block_of(t[1]) == i] for i in range(3)]
    half = n // 2
    return {"n": n, "pf": pf(pn) if n else 0.0, "net_c": 100 * sum(pn) / n if n else 0.0, "pf_stress": pf(st) if n else 0.0,
            "net_stress_c": 100 * sum(st) / n if n else 0.0,
            "acc": sum(t[3]["win"] for t in tr) / n if n else 0.0, "mean_ask": sum(t[3]["px"] for t in tr) / n if n else 0.0,
            "blocks": [(len(b), pf(b) if b else 0.0) for b in blocks],
            "halves": [pf(pn[:half]) if half else 0.0, pf(pn[half:]) if n - half else 0.0],
            "z": clustered_z(pn, [t[1] for t in tr]) if n > 1 else 0.0, "pnl": pn}


def passes(s, ctrl_ok, zb):
    b = CONFIG["bar"]
    return (s["n"] >= b["n_trades"] and all(p >= b["pf_each_block"] and k > 0 for k, p in s["blocks"]) and s["pf"] >= b["pf_pooled"]
            and all(h > b["halves_pf_above"] for h in s["halves"]) and s["net_c"] > 0 and s["net_stress_c"] > 0
            and s["pf_stress"] > b["stress_pf_above"] and s["z"] >= zb and ctrl_ok)


def shuffle_control(by_market, n_shuffle=None, seed=None):
    """by_market {market: [window records]}. Shuffles each feature's values across the windows of its market (1,000 rounds), keeping each
    window's own prices and result. Returns (observed mean net per try, per round best-of-all-tries, threshold at the 99th percentile)."""
    import numpy as np
    n_shuffle = n_shuffle or CONFIG["control"]["shuffles"]
    rng = np.random.default_rng(seed if seed is not None else CONFIG["control"]["seed"])
    arr = {}
    for m, ws in by_market.items():
        py = np.array([w["fill"]["yes"]["pnl"] if w["fill"]["yes"] else np.nan for w in ws])
        pn = np.array([w["fill"]["no"]["pnl"] if w["fill"]["no"] else np.nan for w in ws])
        for name in NAMES:
            sg = np.array([0 if w["feat"][name] is None else (1 if w["feat"][name] > 0 else (-1 if w["feat"][name] < 0 else 0)) for w in ws])
            arr[(m, name)] = (sg, py, pn)

    def mean_net(sg, py, pn):
        v = np.where(sg > 0, py, np.where(sg < 0, pn, np.nan))
        v = v[~np.isnan(v)]
        return float(v.mean()) if len(v) >= 30 else -1e9

    obs = {k: mean_net(*a) for k, a in arr.items()}
    best = []
    for _ in range(n_shuffle):
        m_best = -1e9
        for (m, name), (sg, py, pn) in arr.items():
            m_best = max(m_best, mean_net(sg[rng.permutation(len(sg))], py, pn))
        best.append(m_best)
    return obs, best, float(np.percentile(best, 99))


# ---------------------------------------------------------------- the read

def _blob(path):
    raw = R6._git("show", f"origin/quote-data:{path}")
    if not raw:
        r = subprocess.run(["gh", "api", f"repos/{REPO_SLUG}/contents/{path}?ref=quote-data", "-H", "Accept: application/vnd.github.raw"],
                           capture_output=True)
        raw = r.stdout
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def _coverage():
    best = {}
    for r in sorted({n.rsplit("/", 1)[0] for n in _names() if n.endswith("/coverage.csv.gz")}):
        for row in _blob(f"{r}/coverage.csv.gz"):
            if not row.get("ticker") or row.get("series") not in UNIVERSE:
                continue
            k = (int(R6._ts(row["close_time"])), row["series"])
            if k not in best or int(row["ok_polls"] or 0) > int(best[k][1]["ok_polls"] or 0):
                best[k] = (r, row)
    return best


def usable(close, row):
    u = CONFIG["usable"]
    polls, ok = int(row.get("polls") or 0), int(row.get("ok_polls") or 0)
    first, last = int(row.get("first_recv_ms") or 0) / 1000, int(row.get("last_recv_ms") or 0) / 1000
    note = row.get("note") or ""
    return (bool(row.get("ticker")) and polls > 0 and ok / polls >= u["min_ok_polls"] and int(row.get("max_gap_ms") or 0) <= u["max_gap_ms"]
            and int(row.get("tape_pages") or 0) >= 1 and not any(b in note for b in u["bad_notes"]) and first > 0
            and first <= close - u["first_recv_at_or_before_s"] and last >= close - u["last_recv_at_or_after_s"]
            and row.get("result") in ("yes", "no") and close - 900 < END_UTC)


def _oicore_held(tickers):
    """{ticker: True / False} from data/fresh.sqlite candles by OICORE's published rule; a ticker with no candles is missing (unknown)."""
    import sqlite3
    from . import oifeed as O
    out = {}
    try:
        db = sqlite3.connect(f"file:{O.FRESH}?mode=ro", uri=True)
    except Exception:
        return out
    try:
        for tk, ct in db.execute("select ticker, close_ts from market where series=?", (BTC,)):
            if tk not in tickers:
                continue
            q = {e: (b, a, oi) for e, b, a, oi in db.execute("select end_ts, bid_c, ask_c, oi from candle where ticker=? and end_ts in (?, ?)",
                                                              (tk, ct - O.LOOK, ct - O.BACK))}
            s, p = q.get(ct - O.LOOK), q.get(ct - O.BACK)
            if not s or not p or s[0] is None or s[1] is None or s[2] is None or p[2] is None:
                continue
            cand = any(O.LO - 1e-9 <= a <= O.HI + 1e-9 for a in (s[1], round(1 - s[0], 4)))
            out[tk] = bool(cand and s[2] - p[2] > O.THRESH)
    finally:
        db.close()
    return out


def history_check():
    """WEAKER EVIDENCE, 1 look per market (not a try). Candles carry only the top of the book and volume, so nine of the ten features have no
    analogue (NOT_RUNNABLE on history). The one stand-in is short-term pressure: the sign of the YES mid change over the minute before the
    decision candle (T-540 s to T-480 s), bought at the NEXT candle's ask (T-420 s) when in the band, held to settlement, same fee. Windows
    closing before 2026-10-29 only, so the recorder days are not counted twice."""
    import sqlite3
    from . import oifeed as O
    out = {}
    cutoff = datetime(2026, 10, 29, tzinfo=timezone.utc).timestamp()
    db = sqlite3.connect(f"file:{O.FRESH}?mode=ro", uri=True)
    try:
        for ser in UNIVERSE:
            rows = []
            for tk, ct, res in db.execute("select ticker, close_ts, result from market where series=? and close_ts<? and result in ('yes','no')", (ser, cutoff)):
                q = {e: (b, a, v) for e, b, a, v in db.execute("select end_ts, bid_c, ask_c, volume from candle where ticker=? and end_ts in (?,?,?)",
                                                              (tk, ct - 540, ct - 480, ct - 420))}
                a, b, c = q.get(ct - 540), q.get(ct - 480), q.get(ct - 420)
                if not (a and b and c) or None in (a[0], a[1], b[0], b[1], c[0], c[1]):
                    continue
                d = (b[0] + b[1]) / 2 - (a[0] + a[1]) / 2
                if abs(d) < 1e-9:
                    continue
                side = "yes" if d > 0 else "no"
                px = c[1] if side == "yes" else 1 - c[0]
                lo, hi = CONFIG["ask_band"]
                if not lo - EPS <= px <= hi + EPS:
                    continue
                win = 1.0 if res == side else 0.0
                rows.append((ct, win - px - order_fee(0.07, 1, px), (b[2] or 0) > 0))
            rows.sort()
            k = len(rows) // 3
            thirds = [rows[:k], rows[k:2 * k], rows[2 * k:]] if k else [rows, [], []]
            out[ser] = {"n": len(rows), "pf": pf([r[1] for r in rows]) if rows else 0.0,
                        "net_c": 100 * sum(r[1] for r in rows) / len(rows) if rows else 0.0,
                        "thirds": [pf([r[1] for r in t]) if t else 0.0 for t in thirds],
                        "pf_volume_candle_only": pf([r[1] for r in rows if r[2]]) if any(r[2] for r in rows) else 0.0}
    finally:
        db.close()
    return out


def score(scored, per_market_windows, now_str="", shuffles=None):
    """scored: window records (with "series", "date", "held"). Returns (verdict, lines)."""
    zb = z_bar()
    L = []
    by = {m: [w for w in scored if w["series"] == m] for m in UNIVERSE}
    if min(len(v) for v in by.values()) < NEEDED:
        return "NOT_ENOUGH_DATA", [f"scored windows per market {{{', '.join(f'{m}: {len(v)}' for m, v in by.items())}}}, {NEEDED} needed in each; nothing scored."]
    obs, best, thr = shuffle_control(by, shuffles)
    L.append(f"z bar {zb:.2f} (N {CONFIG['bar']['z_bar_N']}); shuffled-book control: {len(best)} rounds, best-of-20 mean net 99th percentile {100 * thr:+.2f}c, "
             f"median {100 * sorted(best)[len(best) // 2]:+.2f}c")
    any_pass, second = False, []
    for m in UNIVERSE:
        L.append(f"-- {m}: {len(by[m])} scored windows")
        for name in NAMES:
            s = try_stats(by[m], name)
            ctrl_ok = obs[(m, name)] > thr
            p_marg = (1 + sum(1 for b in best if b >= obs[(m, name)])) / (1 + len(best))
            ok = passes(s, ctrl_ok, zb)
            clean = [w for w in by[m] if w.get("held") is False]
            sc = try_stats(clean, name)
            any_pass |= ok
            if s["n"] >= 300 and s["acc"] >= CONFIG["second_look"]["accuracy"]:
                second.append(f"{m} {name} accuracy {s['acc']:.3f} n {s['n']}")
            L.append(f"{name:22s} n {s['n']:4d} PF {s['pf']:.2f} blocks {' / '.join(f'{p:.2f} (n {k})' for k, p in s['blocks'])} halves "
                     f"{s['halves'][0]:.2f} / {s['halves'][1]:.2f} net {s['net_c']:+.2f}c stress PF {s['pf_stress']:.2f} acc {s['acc']:.3f} vs mean ask "
                     f"{s['mean_ask']:.3f} z {s['z']:+.2f} control p(best of 20) {p_marg:.3f} {'PASS' if ctrl_ok else 'fail'}; "
                     f"without windows L1 / OICORE holds: n {sc['n']} PF {sc['pf']:.2f} net {sc['net_c']:+.2f}c{' <- BAR MET' if ok else ''}")
    L.append("second look flags (accuracy >= 55% with n >= 300; not a verdict): " + ("; ".join(second) or "none"))
    return ("NOT_YET_FALSIFIED" if any_pass else "FALSIFIED"), L


def run(now=None):
    now = time.time() if now is None else now
    if RESULT_TXT.exists():
        print(f"Refusing to run again: {RESULT_TXT} exists.")
        return None
    if now < READ_NOT_BEFORE:
        print(f"Refusing: the read date is {datetime.fromtimestamp(READ_NOT_BEFORE, timezone.utc):%Y-%m-%d %H:%M} UTC.")
        return None
    if MARKER.exists():
        print(f"Refusing: {MARKER} exists without a result (a crashed run is never quietly read twice; the lead decides).")
        return None
    if json.loads(FROZEN_JSON.read_text())["feature_hash"] != feature_hash():
        print("NOT_RUNNABLE: the feature source or settings differ from the frozen hash")
        return None
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(f"started {datetime.now(timezone.utc).isoformat()}\n")
    cov = _coverage()
    use = {k: v for k, v in cov.items() if usable(k[0], v[1]) and (d := central_date(k[0])) >= FIRST_DATE and block_of(d) is not None}
    per = {m: sum(1 for k in use if k[1] == m) for m in UNIVERSE}
    head = f"usable windows {per} of {NEEDED} per market (dated {FIRST_DATE} to {BLOCKS[-1][1]} US Central)"
    if min(per.values()) < NEEDED:
        return _write("NOT_ENOUGH_DATA", [head + "; nothing scored."], now)
    byrun = defaultdict(list)
    for k, (r, row) in use.items():
        byrun[r].append((k, row))
    scored, no_clock, no_decision = [], 0, 0
    for r, ks in sorted(byrun.items()):
        book = _blob(f"{r}/book.csv.gz")
        if book and list(book[0]) != R6.BOOK_COLS:
            return _write("NOT_RUNNABLE", ["recorder schema changed"], now)
        off = R6._offset(book)
        if off is None:
            no_clock += len(ks)
            continue
        tick = {row["ticker"]: (k, row) for k, row in ks}
        polls, trades = defaultdict(list), defaultdict(list)
        for x in book:
            if x["ticker"] in tick:
                polls[x["ticker"]].append(R6._poll(x, off))
        del book
        for x in _blob(f"{r}/trades.csv.gz"):
            if x["ticker"] in tick:
                trades[x["ticker"]].append((R6._ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]), x["taker_outcome_side"]))
        for tk, ((close, ser), row) in tick.items():
            w = window_record(sorted(polls.get(tk, []), key=lambda p: p.t), sorted(trades.get(tk, [])), close, row["result"])
            if w is None:
                no_decision += 1
                continue
            w.update(series=ser, ticker=tk, date=central_date(close))
            scored.append(w)
    if no_clock > 0.2 * len(use):
        return _write("NOT_RUNNABLE", [f"{no_clock} of {len(use)} usable windows without a clock"], now)
    held = _oicore_held({w["ticker"] for w in scored if w["series"] == BTC})
    for w in scored:
        w["held"] = bool(w["l1_signal"]) if w["series"] == GOLD and w["l1_signal"] is not None else (held.get(w["ticker"]) if w["series"] == BTC else None)
    verdict, lines = score(scored, per)
    lines.insert(0, f"{head}; scored (with a decision poll) { {m: sum(1 for w in scored if w['series'] == m) for m in UNIVERSE} }, no decision poll {no_decision}, "
                    f"no clock {no_clock}; windows held by L1 (gold) or OICORE (Bitcoin): "
                    f"{ {m: sum(1 for w in scored if w['series'] == m and w.get('held')) for m in UNIVERSE} }, unknown {sum(1 for w in scored if w.get('held') is None)}")
    try:
        h = history_check()
        lines.append("HISTORY CHECK (weaker evidence; candles carry no depth, so only the price-pressure stand-in runs, 1 look per market): "
                     + "; ".join(f"{m} n {v['n']} PF {v['pf']:.2f} net {v['net_c']:+.2f}c thirds {' / '.join(f'{t:.2f}' for t in v['thirds'])} "
                                 f"(decision candle with volume only: PF {v['pf_volume_candle_only']:.2f})" for m, v in h.items()))
    except Exception as ex:
        lines.append(f"HISTORY CHECK NOT_RUNNABLE: {type(ex).__name__}: {str(ex)[:120]}")
    return _write(verdict, lines, now)


def _write(verdict, lines, now):
    head = f"DEPTH1 VERDICT {verdict} (20 tries; running count about {CONFIG['bar']['z_bar_N']:,}; feature hash {feature_hash()})"
    body = "\n".join([head] + lines) + "\n"
    RESULT_TXT.parent.mkdir(parents=True, exist_ok=True)
    RESULT_TXT.write_text(body)
    RESULT_MD.write_text(f"# DEPTH1 result (read once at {datetime.fromtimestamp(now, CT):%Y-%m-%d %H:%M} CT; research only)\n\n```\n{body}```\n")
    print(body)
    return verdict


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "freeze":
        return freeze()
    if cmd == "readiness":
        readiness()
    elif cmd == "read":
        run()
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
