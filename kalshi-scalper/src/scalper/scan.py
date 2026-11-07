"""FAST SCAN HARNESS (Strategy Research V2, owner mandate Nov 7, 2026): one shared, vectorised rule scanner.
Research only: no order, no key, no network, no trading code.

    python3 -I src/scalper/scan.py selftest            reproduce a registered README figure (MKTTIME1 gold windows A and B) and check the engine
    python3 -I src/scalper/scan.py bench               rules per second on a synthetic table of Kalshi size (no real rule is scored)
    python3 -I src/scalper/scan.py unseen [--adapter]  how much data each adapter leaves unread (counts only)
    python3 -I src/scalper/scan.py ledger              N read back from the ledgers and the Bonferroni bar
    python3 -I src/scalper/scan.py run --adapter kalshi_fresh --n 5000     one RUN: ledger first, then score, survivors to data/scan/
    python3 -I src/scalper/scan.py freeze --run <file> --id <ID>           write workers/SCAN_FROZEN_<ID>.json (+ .sha256) for a holdout
    python3 -I src/scalper/scan.py audit --frozen <file>                   audit hooks on a frozen list (dev data only)
    python3 -I src/scalper/scan.py holdout --frozen <file>                 the ONE holdout read (guard file, sha256, read-once record)

Workers import it: `from scalper import scan` (see workers/SCAN_HARNESS.md). Everything is documented there; the exact fee
function is `kalshi_fee_cents`, N is `n_total()`, the bar is `z_bar(N)`."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import NormalDist

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))                # kalshi-scalper/
DATA = os.path.join(ROOT, "data")
SCAN_DATA = os.path.join(DATA, "scan")                                 # git-ignored: guard file, run outputs
LEDGER_DIR = os.path.join(ROOT, "workers", "scan_ledger")              # committed, append-only
PERPGEN_LEDGER_DIR = os.path.join(ROOT, "workers", "perpgen_ledger")   # read back for N
PRIOR_FILE = os.path.join(LEDGER_DIR, "PRIOR_N.json")
GUARD = os.path.join(SCAN_DATA, "holdout_guard.json")
WORKERS = os.path.join(ROOT, "workers")

# ------------------------------------------------------------------ the bar and the grammar (fixed here, printed by every scan)
QS = (0.10, 0.25, 0.50, 0.75, 0.90)                  # quantile cut points, estimated on WINDOW 1 (W1) rows only
P_ATOMS = (0.2, 0.4, 0.4)                            # probability of 1, 2, 3 atoms
BAR = dict(pf=1.5,                                   # the owner's bar: profit factor 1.5 in EACH of W1, W2, W3 after fees. Never raised here.
           min_trades_window=40, min_trades_total=150, min_days_window=3,   # floors (README: 150 treated trades for any read)
           alpha=0.05)                               # one-sided Bonferroni z at alpha / N
HOLD_BAR = dict(pf=1.5, min_trades=50, min_days=5)   # the held-out third, read once
PF_CAP = 99.0
FEE_RATE = 0.07
LEFTS = tuple(range(840, 179, -60))                  # Kalshi look times, seconds before the close
HOLD_FROM_TS = int(datetime(2026, 10, 28, tzinfo=timezone.utc).timestamp())   # F2: closes on or after this are the frozen holdout of fresh.sqlite
PERP_FEE_BPS = 12.0                                  # per side, PERPGEN placeholder (not confirmed against Kalshi's fee page)
PERP_HOLDS = (900, 1800, 3600, 7200, 14400, 28800, 86400)


class Blocked(PermissionError):
    pass


# ------------------------------------------------------------------ fees, stats, N
def kalshi_fee_cents(p, c=1, mult=1.0):
    """The live bot's fee per ORDER of c contracts at price p (dollars): ceil(0.07 x c x p x (1-p) in cents), taker at the ask.
    The 1e-9 keeps an exact whole-cent product (for example 0.5 x 0.5 x 0.07 x 100 x 4) from rounding up on float noise; it is the same
    guard gen1.py, gen2.py and l1studies.py use. Returns cents per ORDER (integers as floats); divide by c for per contract."""
    p = np.asarray(p, dtype=np.float64)
    return np.ceil(mult * FEE_RATE * c * p * (1.0 - p) * 100.0 - 1e-9)


def kalshi_net_cents(won, ask, c=1, mult=1.0):
    """Net cents per contract of a buy at the ask held to settlement: (payoff - ask) x 100 minus the rounded order fee over c."""
    return (np.asarray(won, dtype=np.float64) - np.asarray(ask, dtype=np.float64)) * 100.0 - kalshi_fee_cents(ask, c, mult) / c


def pf_of(v):
    v = np.asarray(v, dtype=np.float64)
    w = float(v[v > 0].sum()); l = float(-v[v < 0].sum())
    return min(PF_CAP, w / l) if l > 0 else (PF_CAP if w > 0 else 0.0)


def cell_z(win, date, net):
    """Day-clustered z: mean of the per-cell mean nets over (their sample sd over sqrt(cells)); a cell is (window, UTC date)."""
    if len(net) == 0:
        return 0.0
    key = win.astype(np.int64) * (1 << 20) + date.astype(np.int64)
    u, inv = np.unique(key, return_inverse=True)
    s = np.bincount(inv, weights=net.astype(np.float64)); n = np.bincount(inv)
    mu = s / n
    if len(mu) < 2 or mu.std(ddof=1) == 0:
        return 0.0
    return float(mu.mean() / (mu.std(ddof=1) / math.sqrt(len(mu))))


def stats_from_rows(win, date, net, windows=(0, 1, 2)):
    """Plain float64 stats of a trade list: per window and pooled. The reference the batch engine is tested against."""
    win = np.asarray(win); date = np.asarray(date); net = np.asarray(net, dtype=np.float64)
    out = {"win": []}
    for w in windows:
        m = win == w
        v = net[m]
        out["win"].append(dict(n=int(m.sum()), days=int(len(np.unique(date[m]))), wr=float((v > 0).mean()) if len(v) else 0.0,
                               mean=float(v.mean()) if len(v) else 0.0, pf=pf_of(v), z=cell_z(win[m], date[m], v),
                               pos=float(v[v > 0].sum()), neg=float(-v[v < 0].sum())))
    out["all"] = dict(n=int(len(net)), days=int(len(np.unique(win.astype(np.int64) * (1 << 20) + date))), mean=float(net.mean()) if len(net) else 0.0,
                      pf=pf_of(net), z=cell_z(win, date, net), wr=float((net > 0).mean()) if len(net) else 0.0)
    return out


def _count_lines(dirpath):
    n = 0
    if not os.path.isdir(dirpath):
        return 0
    for f in sorted(os.listdir(dirpath)):
        if f.endswith(".ids.gz"):
            with gzip.open(os.path.join(dirpath, f), "rt") as fh:
                n += sum(1 for _ in fh)
    return n


def prior_n():
    return int(json.load(open(PRIOR_FILE))["prior_n"])


def n_total(ledger_dir=None, perpgen_dir=None, prior=None):
    """N for the deflation = the running prior (PRIOR_N.json, the lead's tally before the PERPGEN ledgers) + every line of every PERPGEN ledger
    + every line of every scan ledger, all read back from disk now. One line is one distinct (dataset, group, rule) pair scored."""
    return (prior_n() if prior is None else prior) + _count_lines(PERPGEN_LEDGER_DIR if perpgen_dir is None else perpgen_dir) + \
        _count_lines(LEDGER_DIR if ledger_dir is None else ledger_dir)


def z_bar(n, alpha=None):
    """One-sided Bonferroni: inverse normal CDF of 1 - alpha / N."""
    alpha = BAR["alpha"] if alpha is None else alpha
    return NormalDist().inv_cdf(1.0 - alpha / max(1, n))


# ------------------------------------------------------------------ table, atoms
class Table:
    """Decision rows of one dataset and stage. Features are columns; `outcome(dir, variant, group)` gives the rows a rule with that
    direction and look/hold time can trade and its net per trade (NaN rows are void and are dropped)."""

    def __init__(self, name, groups, fnames, X, cats, ts, date, win, scope, scope_names, dirs, variants, outcome_fn, unit, thin_fn=None, meta=None):
        self.name, self.groups, self.fnames = name, list(groups), list(fnames)
        self.X = X                                   # (F, n) float32, NaN = missing, an atom on a NaN is false
        self.cats = cats                             # {name: int16 array, -1 missing}
        self.ts, self.date, self.win, self.scope = ts, date, win, scope
        self.scope_names, self.dirs, self.variants = list(scope_names), tuple(dirs), tuple(variants)
        self.outcome, self.unit, self.thin, self.meta = outcome_fn, unit, thin_fn, meta or {}
        self.n = int(len(ts))

    def fingerprint(self):
        h = hashlib.sha256()
        h.update(np.ascontiguousarray(self.ts).tobytes()); h.update(np.ascontiguousarray(self.X).tobytes())
        for k in sorted(self.cats):
            h.update(np.ascontiguousarray(self.cats[k]).tobytes())
        return h.hexdigest()


def make_cuts(tab):
    """Quantile cut points per scope (a scope is one ticker for perps, one pool for Kalshi) from W1 rows ONLY. Never re-estimated."""
    cuts = {}
    for sc, nm in enumerate(tab.scope_names):
        sel = (tab.win == 0) & (tab.scope == sc)
        d = {}
        for fi, f in enumerate(tab.fnames):
            v = tab.X[fi][sel]
            v = v[~np.isnan(v)]
            d[f] = [float(x) for x in np.quantile(v, QS)] if len(v) >= 20 else [float("nan")] * len(QS)
        cuts[nm] = d
    return cuts


def cuts_sha(cuts):
    return hashlib.sha256(json.dumps(cuts, sort_keys=True, allow_nan=True).encode()).hexdigest()


class AtomSet:
    """All atoms as one boolean matrix A (n_atoms + 1, n); the last row is all True (padding for 1 and 2 atom rules)."""

    def __init__(self, tab, cuts, cat_values=None):
        self.names, self.specs, rows = [], [], []
        self.cuts = cuts                                    # kept so the plain-loop audit can evaluate every atom without the matrix
        nsc = len(tab.scope_names)
        for fi, f in enumerate(tab.fnames):
            cv = np.array([[cuts[tab.scope_names[s]][f][qi] for qi in range(len(QS))] for s in range(nsc)], dtype=np.float32)   # (scopes, q)
            per_row = cv[tab.scope]                                                                                         # (n, q)
            for op in ("ge", "le"):
                for qi, q in enumerate(QS):
                    col = per_row[:, qi]
                    with np.errstate(invalid="ignore"):
                        m = (tab.X[fi] >= col) if op == "ge" else (tab.X[fi] <= col)
                    rows.append(m); self.names.append("%s:%s:%.2f" % (f, op, q)); self.specs.append(dict(kind="num", feat=f, op=op, q=q))
        for cname, arr in tab.cats.items():
            vals = sorted(set(int(v) for v in np.unique(arr[tab.win == 0]) if v >= 0)) if cat_values is None else cat_values[cname]
            for v in vals:
                rows.append(arr == v); self.names.append("%s:eq:%d" % (cname, v)); self.specs.append(dict(kind="cat", feat=cname, val=int(v)))
        self.n_real = len(rows)
        rows.append(np.ones(tab.n, dtype=bool))
        self.A = np.array(rows, dtype=bool)
        self.feat_of = [s["feat"] for s in self.specs]
        self.by_feat = {}
        for i, f in enumerate(self.feat_of):
            self.by_feat.setdefault(f, []).append(i)
        self.pad = self.n_real

    def add_custom(self, name, mask):
        """Add an atom that is not a quantile cut (used by the self-test for the plain 88c to 97c band)."""
        self.A = np.vstack([self.A[:-1], np.asarray(mask, dtype=bool)[None, :], self.A[-1:]])
        self.names.append(name); self.specs.append(dict(kind="custom", feat=name)); self.feat_of.append(name)
        self.by_feat.setdefault(name, []).append(self.n_real)
        self.n_real += 1; self.pad = self.n_real
        return self.n_real - 1


@dataclass(frozen=True)
class Rule:
    atoms: tuple            # atom ids, sorted
    dir: str
    variant: object         # look time (Kalshi, seconds before close) or hold seconds (perps)


def rule_id(tab, ats, group, r):
    return "%s|%s|%s|%s|%s" % (tab.name, group, "&".join(sorted(ats.names[a] for a in r.atoms)), r.dir, r.variant)


def draw_rule(rng, ats, tab):
    k = rng.choices((1, 2, 3), P_ATOMS)[0]
    feats = rng.sample(sorted(ats.by_feat), min(k, len(ats.by_feat)))
    atoms = tuple(sorted(rng.choice(ats.by_feat[f]) for f in feats))
    return Rule(atoms, rng.choice(tab.dirs), rng.choice(tab.variants))


# ------------------------------------------------------------------ the vectorised engine
SCREEN_SLACK = 1e-3          # the float32 screen may undercount a PF by rounding; survivors are re-scored in float64, so the screen is slightly loose


def _prep(tab, group, dir_, variant):
    """The rows a (direction, variant) rule can trade (void rows dropped) with their net, stress net and window."""
    rows, net, nets = tab.outcome(dir_, variant, group)
    ok = ~np.isnan(net)
    return rows[ok], net[ok].astype(np.float32), nets[ok].astype(np.float32)


def _window_matrix(win, net, nwin=3):
    """Q (m, 4 x nwin): per window the columns [is in window, positive net, losing net (absolute), win flag], so ONE matrix product gives
    trades, gross wins, gross losses and winners of every rule in every window."""
    Q = np.zeros((len(net), 4 * nwin), dtype=np.float32)
    pos, neg, won = np.maximum(net, 0), np.maximum(-net, 0), (net > 0)
    for w in range(nwin):
        m = win == w
        Q[m, 4 * w] = 1.0; Q[m, 4 * w + 1] = pos[m]; Q[m, 4 * w + 2] = neg[m]; Q[m, 4 * w + 3] = won[m]
    return Q


def batch_stats(M, Q, nwin=3):
    """Screen stats of B rules at once: M (B, m) bool trade masks, Q from _window_matrix. One float32 matrix product, no Python loop over rules or
    trades. Days per window and the day-clustered z are NOT computed here (they need per-day cells); the exact stage computes them for survivors."""
    S = (M.astype(np.float32) @ Q).astype(np.float64).reshape(M.shape[0], nwin, 4)
    n, pos, neg, wins = S[:, :, 0], S[:, :, 1], S[:, :, 2], S[:, :, 3]
    pf = np.where(neg > 0, np.minimum(PF_CAP, pos / np.where(neg > 0, neg, 1)), np.where(pos > 0, PF_CAP, 0.0))
    return dict(n=n, pos=pos, neg=neg, wins=wins, pf=pf, mean=(pos - neg) / np.maximum(n, 1), wr=wins / np.maximum(n, 1),
                tot_n=n.sum(1), tot_pf=np.where(neg.sum(1) > 0, np.minimum(PF_CAP, pos.sum(1) / np.where(neg.sum(1) > 0, neg.sum(1), 1)), 0.0),
                tot_mean=(pos.sum(1) - neg.sum(1)) / np.maximum(n.sum(1), 1))


def survivor_mask(R, bar=None):
    b = BAR if bar is None else bar
    return ((R["pf"] >= b["pf"] - SCREEN_SLACK).all(1) & (R["n"] >= b["min_trades_window"]).all(1) & (R["tot_n"] >= b["min_trades_total"]))


def score_rules(tab, ats, group, rules, batch_cells=24_000_000, bar=None):
    """Score rules (any mix of directions and variants). Returns a list of dicts in input order. Rules are grouped by (direction,
    variant), each group's rows prepared once, then masks built B at a time with A[a0] & A[a1] & A[a2]."""
    out = [None] * len(rules)
    groups = {}
    for i, r in enumerate(rules):
        groups.setdefault((r.dir, r.variant), []).append(i)
    for (d, v), ids in groups.items():
        rows, net, nets = _prep(tab, group, d, v)
        m = len(rows)
        if m == 0:
            for i in ids:
                out[i] = dict(n=[0, 0, 0], pf=[0, 0, 0], mean=[0, 0, 0], wr=[0, 0, 0], pos=[0, 0, 0], neg=[0, 0, 0], tot_n=0, tot_pf=0.0, tot_mean=0.0, surv=False)
            continue
        Asub = np.ascontiguousarray(ats.A[:, rows])      # C order: a column gather can come back transposed, which makes every row gather slow
        Q = _window_matrix(tab.win[rows], net)
        B = max(8, min(2048, batch_cells // m))
        for s in range(0, len(ids), B):
            chunk = ids[s:s + B]
            at = np.full((len(chunk), 3), ats.pad, dtype=np.int64)
            for j, i in enumerate(chunk):
                a = rules[i].atoms
                at[j, :len(a)] = a
            M = Asub[at[:, 0]] & Asub[at[:, 1]] & Asub[at[:, 2]]
            R = batch_stats(M, Q)
            sv = survivor_mask(R, bar)
            for j, i in enumerate(chunk):
                out[i] = {k: (R[k][j].tolist() if R[k].ndim == 2 else float(R[k][j])) for k in R}
                out[i]["surv"] = bool(sv[j])
    return out


def exact_rule(tab, ats, group, rule, stress=False):
    """One rule, plain float64, with the adapter's exact overlap rule applied (perps: one position per ticker). The final word on a
    survivor: the batch screen ignores overlap and uses float32 sums."""
    rows, net, nets = _prep(tab, group, rule.dir, rule.variant)
    m = ats.A[list(rule.atoms)][:, rows].all(axis=0) if rule.atoms else np.ones(len(rows), bool)
    sel = rows[m]
    v = (nets if stress else net)[m].astype(np.float64)
    if tab.thin is not None and len(sel):
        keep = tab.thin(sel, rule.variant)
        sel, v = sel[keep], v[keep]
    st = stats_from_rows(tab.win[sel], tab.date[sel], v)
    st["rows"] = sel
    return st


def passes_bar(st, bar=None):
    b = BAR if bar is None else bar
    return all(w["pf"] >= b["pf"] and w["n"] >= b["min_trades_window"] and w["days"] >= b["min_days_window"] for w in st["win"]) \
        and st["all"]["n"] >= b["min_trades_total"]


# ------------------------------------------------------------------ ledger, guard, freeze
def seen_ids(prefix):
    s = set()
    if os.path.isdir(LEDGER_DIR):
        for f in sorted(os.listdir(LEDGER_DIR)):
            if f.endswith(".ids.gz"):
                with gzip.open(os.path.join(LEDGER_DIR, f), "rt") as fh:
                    for line in fh:
                        if line.startswith(prefix):
                            s.add(line.rstrip("\n"))
    return s


def ledger_append(path, ids):
    """Append and CLOSE (so the bytes are on disk) BEFORE the batch is scored: a crash cannot lose a count."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "at") as f:
        f.write("".join(i + "\n" for i in ids))


def _sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _guard_load():
    return json.load(open(GUARD)) if os.path.exists(GUARD) else None


def guard_check(frozen_id, dataset, guard_path=None):
    """The holdout opens only if data/scan/holdout_guard.json (written BY HAND, after the frozen list is committed) names this frozen id
    and dataset, and only once. Returns the guard dict; raises Blocked otherwise."""
    gp = guard_path or GUARD
    if not os.path.exists(gp):
        raise Blocked("holdout guard file missing: holdout is locked (%s)" % gp)
    g = json.load(open(gp))
    u = (g.get("unlock") or {}).get(frozen_id)
    if not u or dataset not in u.get("datasets", []):
        raise Blocked("holdout not unlocked for %s / %s" % (frozen_id, dataset))
    if "%s|%s" % (frozen_id, dataset) in g.get("used", {}):
        raise Blocked("holdout already read once for %s / %s" % (frozen_id, dataset))
    return g


def guard_record(frozen_id, dataset, guard_path=None):
    gp = guard_path or GUARD
    g = json.load(open(gp))
    g.setdefault("used", {})["%s|%s" % (frozen_id, dataset)] = datetime.now(timezone.utc).isoformat()
    json.dump(g, open(gp, "w"), indent=1)


def load_frozen(path, require_committed=True):
    """A frozen survivor list is valid only with its sha256 sidecar matching, and (by default) committed unchanged in git."""
    sc = path + ".sha256"
    if not os.path.exists(sc):
        raise Blocked("no sha256 sidecar for the frozen list")
    want = open(sc).read().split()[0]
    got = _sha_file(path)
    if want != got:
        raise Blocked("frozen list does not match its sha256 (%s vs %s)" % (got[:12], want[:12]))
    if require_committed:
        rel = os.path.relpath(path, ROOT)
        try:
            tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, capture_output=True).returncode == 0
            clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=ROOT, capture_output=True).returncode == 0
        except OSError:
            tracked = clean = False
        if not (tracked and clean):
            raise Blocked("the frozen list must be committed (and pushed) unchanged before the holdout is read")
    return json.load(open(path))


def spec_of(ats, a):
    s = dict(ats.specs[a]); return s


# ------------------------------------------------------------------ adapters
class Adapter:
    """A dataset adapter: rows with decision time, side (direction), entry price or forward return, series (scope), date, features as columns.
    Subclasses implement build_dev (never the holdout), build_holdout (guarded), unseen (counts only), truncation_test (look-ahead check)."""
    name = "adapter"
    groups = ("ALL",)

    def build_dev(self) -> Table:
        raise NotImplementedError

    def build_holdout(self, frozen_id, cuts) -> Table:
        raise NotImplementedError

    def unseen(self) -> dict:
        raise NotImplementedError

    def truncation_test(self, tab, n=200, seed=0) -> dict:
        raise NotImplementedError

    def reverse_dir(self, d):
        return None


# ---- Kalshi 15 minute windows
@dataclass
class KalshiSpec:
    name: str
    files: tuple
    series: tuple | None = None
    dev_hi: int | None = None                # dev rows: close_ts < dev_hi
    hold_lo: int | None = None               # holdout rows: close_ts >= hold_lo (guarded); None = no holdout exists for this spec
    dev_lo: int | None = None
    win_cuts: tuple | None = None            # two close_ts cuts; None = thirds of the dev UTC dates
    contracts: int = 1
    looks: tuple = LEFTS


FRESH = KalshiSpec("kalshi15_fresh", ("fresh",), None, dev_hi=HOLD_FROM_TS, hold_lo=HOLD_FROM_TS)
SELFTEST_GOLD = KalshiSpec("kalshi15_selftest_gold", ("alts2", "alts3", "alts4", "book", "l1b", "e3b"), ("KXGOLD15M",),
                           dev_hi=1791248400, hold_lo=None, win_cuts=(1788634800, 1791248400), looks=(360,))
FEATS_K = ["ask", "bid", "spread", "d1", "d2", "d3", "d5", "rng5", "vol", "doi", "nprev", "hour"]
CATS_K = ["series", "hod4", "dow"]


def _valid_quote(b, a):
    """analyze.valid_quote: a usable two sided quote (an empty fresh market shows 0.1c / $1.00)."""
    return b is not None and a is not None and b >= 0.001 and a <= 0.999 and a >= b and a - b <= 0.10


def kalshi_row(cs, close_ts, L, side):
    """Features of one (market, look, side) from candles with end_ts <= close_ts - L ONLY (`cs`: end_ts -> (bid_c, ask_c, volume, oi)).
    Returns None if there is no usable quote or the side's ask is outside 2c to 98c, else (ask, feature list, hour). The truncation test
    calls this with every later candle deleted and demands the same answer, so this function is the whole look-ahead surface."""
    t = close_ts - L
    q = cs.get(t)
    if q is None or not _valid_quote(q[0], q[1]):
        return None
    sq = (lambda x: (x[0], x[1])) if side else (lambda x: (round(1 - x[1], 4), round(1 - x[0], 4)))
    bid, ask = sq(q)
    if not 0.02 <= ask <= 0.98:
        return None
    d = []
    for lag in (60, 120, 180, 300):
        p = cs.get(t - lag)
        d.append(bid - sq(p)[0] if p is not None and p[0] is not None and p[1] is not None else float("nan"))
    path = [sq(cs[t - 60 * j])[0] for j in range(6) if (t - 60 * j) in cs and cs[t - 60 * j][0] is not None and cs[t - 60 * j][1] is not None]
    rng5 = (max(path) - min(path)) if len(path) >= 2 else float("nan")
    vol = q[2] if q[2] is not None else float("nan")
    p3 = cs.get(t - 180)
    doi = (q[3] - p3[3]) if (p3 is not None and q[3] is not None and p3[3] is not None) else float("nan")
    nprev = float(sum(1 for k in cs if k <= t))
    hour = float((t % 86400) // 3600)
    return ask, [ask, bid, ask - bid, d[0], d[1], d[2], d[3], rng5, vol, doi, nprev, hour], t


class KalshiAdapter(Adapter):
    groups = ("ALL",)

    def __init__(self, spec: KalshiSpec = FRESH, db_dir=None, fee_mult_stress=1.2):
        self.spec, self.name = spec, spec.name
        self.db_dir = db_dir or DATA
        self.stress = fee_mult_stress
        self.markets = []

    # -- loading: the SQL carries the cut as a bind parameter; a dev load can never ask for the holdout
    def _read(self, lo, hi):
        sp = self.spec
        if hi is not None and sp.hold_lo is not None and hi > sp.hold_lo:
            raise Blocked("dev load would cross the frozen holdout cut")
        seen, mk = set(), []
        for f in sp.files:
            p = os.path.join(self.db_dir, f + ".sqlite")
            if not os.path.exists(p):
                continue
            db = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
            cond, par = "m.result IN ('yes','no')", []
            if lo is not None:
                cond += " AND m.close_ts >= ?"; par.append(lo)
            if hi is not None:
                cond += " AND m.close_ts < ?"; par.append(hi)
            if sp.series:
                cond += " AND m.series IN (%s)" % ",".join("?" * len(sp.series)); par += list(sp.series)
            cur = None
            q = ("SELECT m.ticker, m.series, m.close_ts, m.result, c.end_ts, c.bid_c, c.ask_c, c.volume, c.oi FROM market m "
                 "JOIN candle c ON c.ticker = m.ticker WHERE " + cond + " ORDER BY m.ticker, c.end_ts")
            for tk, series, close_ts, res, end, b, a, vol, oi in db.execute(q, par):
                if cur is None or cur[0] != tk:
                    if cur is not None and cur[0] not in seen:
                        mk.append(cur); seen.add(cur[0])
                    cur = (tk, series, close_ts, res, {})
                if tk in seen:
                    continue
                cur[4][end] = (b, a, vol, oi)
            if cur is not None and cur[0] not in seen:
                mk.append(cur); seen.add(cur[0])
            db.close()
        return mk

    def _table(self, mk, stage, cuts=None):
        sp = self.spec
        series_names = sorted({m[1] for m in mk}) if cuts is None else cuts["_series"]
        sid = {s: i for i, s in enumerate(series_names)}
        rows, cols, meta = [], [], []
        self.markets = mk if stage == "dev" else self.markets
        for mi, (tk, series, close_ts, res, cs) in enumerate(mk):
            for L in sp.looks:
                for side in (1, 0):
                    r = kalshi_row(cs, close_ts, L, side)
                    if r is None:
                        continue
                    ask, f, t = r
                    won = (res == "yes") == bool(side)
                    cols.append(f)
                    meta.append((mi, close_ts, L, side, sid.get(series, -1), won, ask, t))
        n = len(meta)
        X = np.array(cols, dtype=np.float32).reshape(n, len(FEATS_K)).T.copy()
        M = np.array(meta, dtype=np.float64).reshape(n, 8)
        mi_, close, look, side, ser, won, ask, t = (M[:, i] for i in range(8))
        close = close.astype(np.int64); t = t.astype(np.int64)
        date = (close // 86400).astype(np.int32)
        if stage == "dev":
            if sp.win_cuts:
                win = np.where(close < sp.win_cuts[0], 0, np.where(close < sp.win_cuts[1], 1, 2)).astype(np.int8)
            else:
                ud = np.unique(date); parts = np.array_split(ud, 3)
                wmap = {int(d): w for w, p in enumerate(parts) for d in p}
                win = np.array([wmap[int(d)] for d in date], dtype=np.int8)
        else:
            win = np.full(n, 3, dtype=np.int8)
        net = kalshi_net_cents(won, ask, sp.contracts).astype(np.float32)
        nets = kalshi_net_cents(won, ask, sp.contracts, self.stress).astype(np.float32)
        hod4 = ((t % 86400) // 14400).astype(np.int16)
        dow = (((t // 86400) + 3) % 7).astype(np.int16)                     # 1970-01-01 was a Thursday (weekday 3)
        cats = {"series": ser.astype(np.int16), "hod4": hod4, "dow": dow}
        sidea, looka = side.astype(np.int8), look.astype(np.int32)

        def outcome(dir_, variant, group):
            rows_ = np.flatnonzero((sidea == (1 if dir_ == "yes" else 0)) & (looka == variant))
            return rows_, net[rows_], nets[rows_]

        tab = Table(sp.name + ("" if stage == "dev" else ":holdout"), ["ALL"], FEATS_K, X, cats, t, date, win, np.zeros(n, dtype=np.int16), ["ALL"],
                    ("yes", "no"), sp.looks, outcome, mi_.astype(np.int64),
                    meta=dict(series_names=series_names, market_index=mi_.astype(np.int64), look=looka, side=sidea, close=close, won=won, ask=ask))
        return tab

    def build_dev(self):
        sp = self.spec
        mk = self._read(sp.dev_lo, sp.dev_hi)
        tab = self._table(mk, "dev")
        return tab

    def build_holdout(self, frozen_id, cuts):
        sp = self.spec
        if sp.hold_lo is None:
            raise Blocked("this spec has no holdout")
        guard_check(frozen_id, self.name)
        guard_record(frozen_id, self.name)               # recorded BEFORE the read: a crash cannot allow a second one
        mk = self._read(sp.hold_lo, None)
        return self._table(mk, "holdout", cuts={"_series": cuts["_series"]})

    def unseen(self):
        sp = self.spec
        out = dict(adapter=self.name, holdout_from=None, holdout_markets=0, note="")
        if sp.hold_lo is None:
            out["note"] = "no holdout defined for this spec"
            return out
        n = lo = hi = 0
        for f in sp.files:
            p = os.path.join(self.db_dir, f + ".sqlite")
            if os.path.exists(p):
                db = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
                r = db.execute("SELECT COUNT(*), MIN(close_ts), MAX(close_ts) FROM market WHERE close_ts >= ? AND result IN ('yes','no')", (sp.hold_lo,)).fetchone()
                n += r[0]; lo = r[1] or lo; hi = r[2] or hi
                db.close()
        out.update(holdout_from=datetime.fromtimestamp(sp.hold_lo, timezone.utc).strftime("%Y-%m-%d"), holdout_markets=n,
                   holdout_decision_rows_est=n * len(sp.looks) * 2,
                   holdout_to=datetime.fromtimestamp(hi, timezone.utc).strftime("%Y-%m-%d") if hi else None,
                   note="settled windows closing on or after the cut; counted only, never read. GEN1 and OICOREX1 hold the same 10-28 cut (do not unlock before "
                        "2026-11-08 and coordinate); F11: windows closing after 2026-10-30 are also read by the GEN5 candidate file, not by hand")
        return out

    def truncation_test(self, tab, n=200, seed=0):
        rng = random.Random(seed)
        idx = rng.sample(range(tab.n), min(n, tab.n))
        bad = 0
        for i in idx:
            mi = int(tab.meta["market_index"][i]); L = int(tab.meta["look"][i]); side = int(tab.meta["side"][i])
            tk, series, close_ts, res, cs = self.markets[mi]
            t = close_ts - L
            r = kalshi_row(cs, close_ts, L, side)
            r2 = kalshi_row({k: v for k, v in cs.items() if k <= t}, close_ts, L, side)
            same = r is not None and r2 is not None and r[0] == r2[0] and np.allclose(np.array(r[1], dtype=np.float32), np.array(r2[1], dtype=np.float32), equal_nan=True) \
                and np.allclose(np.array(r[1], dtype=np.float32), tab.X[:, i], equal_nan=True)
            bad += 0 if same else 1
        return dict(name="truncation", checked=len(idx), mismatches=bad, passed=bad == 0)


# ---- Perps candles (data/perpgen through perpdata)
FEATS_P = ["r5", "r15", "r60", "r240", "r1440", "vol60", "vol240", "rng60", "rng240", "sp", "spr", "vlr15", "vlr60", "doi60", "doi240",
           "dhi240", "dlo240", "dhi1440", "dlo1440", "pir1440", "tvm", "fr_last", "fr_chg", "fr_avg3"]
CATS_P = ["hod4", "dow", "wkend"]


def _win_gather(arr, idx, w, chunk=2000):
    """Yield (slice, window matrix (len, w)) of arr over the w minutes ending at each idx (inclusive); idx >= w - 1 required."""
    from numpy.lib.stride_tricks import sliding_window_view
    sw = sliding_window_view(arr, w)
    for s in range(0, len(idx), chunk):
        sl = slice(s, s + chunk)
        yield sl, sw[idx[sl] - w + 1]


def perp_features(g, idx, fund_ts, fund_rate):
    """Features at decision minutes `idx` of one ticker's minute grid g (dict of arrays, NaN = missing minute). Uses only minutes <= idx.
    Returns {name: float32 array}. A window needs at least 90 percent of its minutes present, else NaN (protocol)."""
    mid, spr_bp, vol_usd, oi, px = g["mid"], g["sp"], g["vol"], g["oi"], g["px"]
    n = len(idx)
    out = {k: np.full(n, np.nan, dtype=np.float32) for k in FEATS_P}
    lm = np.log(mid)
    ret1 = np.full(len(mid), np.nan); ret1[1:] = lm[1:] - lm[:-1]
    for name, w in (("r5", 5), ("r15", 15), ("r60", 60), ("r240", 240), ("r1440", 1440)):
        ok = idx >= w
        j = np.where(ok, idx - w, 0)
        out[name][ok] = ((lm[idx[ok]] - lm[j[ok]]) * 1e4).astype(np.float32)
    for name, w in (("vol60", 60), ("vol240", 240)):
        c = np.where(np.isnan(ret1), 0.0, ret1); c2 = c * c; k = (~np.isnan(ret1)).astype(np.float64)
        cs, cs2, ck = np.r_[0, np.cumsum(c)], np.r_[0, np.cumsum(c2)], np.r_[0, np.cumsum(k)]
        ok = idx >= w
        i1 = idx[ok] + 1; i0 = idx[ok] + 1 - w
        kk = ck[i1] - ck[i0]
        mean = (cs[i1] - cs[i0]) / np.maximum(kk, 1); var = (cs2[i1] - cs2[i0]) / np.maximum(kk, 1) - mean ** 2
        v = np.sqrt(np.maximum(var, 0)) * 1e4
        v[kk < 0.9 * w] = np.nan
        out[name][ok] = v.astype(np.float32)
    for name, w, hi, lo in (("rng60", 60, None, None), ("rng240", 240, None, None)):
        ok = idx >= w
        sel = np.flatnonzero(ok)
        for sl, W in _win_gather(mid, idx[sel], w):
            cnt = (~np.isnan(W)).sum(1)
            with np.errstate(all="ignore"):
                r = (np.nanmax(W, 1) - np.nanmin(W, 1)) / W[:, -1] * 1e4
            r[cnt < 0.9 * w] = np.nan
            out[name][sel[sl]] = r.astype(np.float32)
    out["sp"] = spr_bp[idx].astype(np.float32)
    ok = idx >= 1440
    sel = np.flatnonzero(ok)
    for sl, W in _win_gather(spr_bp, idx[sel], 1440):
        with np.errstate(all="ignore"):
            med = np.nanmedian(W, 1)
        cnt = (~np.isnan(W)).sum(1)
        r = spr_bp[idx[sel][sl]] / med; r[cnt < 0.9 * 1440] = np.nan
        out["spr"][sel[sl]] = r.astype(np.float32)
    for name, w, kind in (("dhi240", 240, "hi"), ("dlo240", 240, "lo"), ("dhi1440", 1440, "hi"), ("dlo1440", 1440, "lo")):
        sel = np.flatnonzero(idx >= w)
        for sl, W in _win_gather(mid, idx[sel], w):
            cnt = (~np.isnan(W)).sum(1)
            with np.errstate(all="ignore"):
                ext = np.nanmax(W, 1) if kind == "hi" else np.nanmin(W, 1)
            r = (W[:, -1] / ext - 1.0) * 1e4; r[cnt < 0.9 * w] = np.nan
            out[name][sel[sl]] = r.astype(np.float32)
    sel = np.flatnonzero(idx >= 1440)
    for sl, W in _win_gather(mid, idx[sel], 1440):
        cnt = (~np.isnan(W)).sum(1)
        with np.errstate(all="ignore"):
            hi, lo = np.nanmax(W, 1), np.nanmin(W, 1)
        r = (W[:, -1] - lo) / np.where(hi > lo, hi - lo, np.nan); r[cnt < 0.9 * 1440] = np.nan
        out["pir1440"][sel[sl]] = r.astype(np.float32)
    v0 = np.where(np.isnan(vol_usd), 0.0, vol_usd); cv = np.r_[0, np.cumsum(v0)]
    for name, w in (("vlr15", 15), ("vlr60", 60)):
        ok = idx >= 1440
        i1 = idx[ok] + 1
        cur = cv[i1] - cv[i1 - w]; base = (cv[i1] - cv[i1 - 1440]) / (1440.0 / w)
        out[name][ok] = np.log((cur + 1.0) / (base + 1.0)).astype(np.float32)
    for name, w in (("doi60", 60), ("doi240", 240)):
        ok = idx >= w
        a, b = oi[idx[ok]], oi[idx[ok] - w]
        with np.errstate(all="ignore"):
            out[name][ok] = np.log(a / b).astype(np.float32)
    # trade price over mid: the last non-missing trade close within the last 5 minutes
    last = np.full(n, np.nan)
    for k in range(5):
        pk = px[np.maximum(idx - k, 0)]
        last = np.where(np.isnan(last), pk, last)
    out["tvm"] = ((last / mid[idx] - 1.0) * 1e4).astype(np.float32)
    # funding: the last rate published at or before t (never earlier than its funding_time)
    t_idx = g["t0"] + idx.astype(np.int64) * 60
    if len(fund_ts):
        j = np.searchsorted(fund_ts, t_idx, side="right") - 1
        ok = j >= 0
        out["fr_last"][ok] = (fund_rate[j[ok]] * 1e4).astype(np.float32)
        ok2 = j >= 1
        out["fr_chg"][ok2] = ((fund_rate[j[ok2]] - fund_rate[j[ok2] - 1]) * 1e4).astype(np.float32)
        ok3 = j >= 2
        out["fr_avg3"][ok3] = (np.mean([fund_rate[j[ok3]], fund_rate[j[ok3] - 1], fund_rate[j[ok3] - 2]], axis=0) * 1e4).astype(np.float32)
    return out


class PerpAdapter(Adapter):
    """Perps 1 minute candles through perpdata.load_stage. With frozen_id=None only the DISCOVERY third is read (validation is locked by
    perpdata until a PERPGEN_FROZEN_<id>.json exists); with an existing id, discovery + validation (the development region) is read and cut
    into W1, W2, W3 per ticker by UTC calendar days. The holdout comes only from perpdata.load_holdout and its own guard file."""

    def __init__(self, group="CRYPTO", frozen_id=None, tickers=None, fee_bps=PERP_FEE_BPS, extra=False):
        self.group, self.groups, self.frozen_id, self.fee = group, (group,), frozen_id, fee_bps
        self.extra = bool(extra)                         # HARNESS v1.1: leader returns (BTC, ETH) and minutes-to-next-funding; off keeps v1 atoms and ids exactly
        self.opts = dict(extra=self.extra)
        self.name = "perps_%s" % group.lower()
        self._tickers = tickers
        self.cuts_cache = {}

    def _pd(self):
        sys.path.insert(0, HERE)
        import perpdata  # noqa: E402
        return perpdata

    def tickers(self):
        return list(self._tickers) if self._tickers else self._pd().universe_frozen()[self.group]

    def _grid(self, rows, t0, t1):
        N = int((t1 - t0) // 60) + 1
        g = {k: np.full(N, np.nan) for k in ("bid", "ask", "mid", "sp", "vol", "oi", "px")}
        ts = np.array([r["ts"] for r in rows], dtype=np.int64)
        ix = ((ts - t0) // 60).astype(np.int64)
        good = (ix >= 0) & (ix < N)
        def col(k):
            return np.array([np.nan if r.get(k) is None else r[k] for r in rows], dtype=np.float64)
        bid, ask = col("bid_c"), col("ask_c")
        ok = np.array([r.get("ok") == 1 for r in rows]) & good
        g["bid"][ix[ok]], g["ask"][ix[ok]] = bid[ok], ask[ok]
        g["mid"][ix[ok]] = (bid[ok] + ask[ok]) / 2
        g["sp"][ix[ok]] = (ask[ok] - bid[ok]) / ((ask[ok] + bid[ok]) / 2) * 1e4
        gg = good
        g["vol"][ix[gg]] = col("vol_usd")[gg]; g["oi"][ix[gg]] = col("oi_usd")[gg]; g["px"][ix[gg]] = col("px_c")[gg]
        g["t0"] = t0
        return g

    def _ticker_rows(self, pd, tk, frozen_id, holdout=False):
        if holdout:
            m1 = pd.load_holdout(tk, frozen_id, "1m"); fu = pd.load_holdout(tk, frozen_id, "funding")
            return m1, fu
        m1 = pd.load_stage(tk, "discovery", "1m")
        fu = pd.load_stage(tk, "discovery", "funding") if True else []
        if frozen_id:
            m1 += pd.load_stage(tk, "validation", "1m", frozen_id=frozen_id)
            fu += pd.load_stage(tk, "validation", "funding", frozen_id=frozen_id)
        return m1, fu

    def _one(self, tk, m1, fu, stage, win_cuts=None):
        """Rows of one ticker: decision times are quarter hours with a usable quote; returns arrays and the grid for the truncation test."""
        ts = np.array(sorted(r["ts"] for r in m1), dtype=np.int64)
        t0, t1 = int(ts[0]), int(ts[-1])
        g = self._grid(sorted(m1, key=lambda r: r["ts"]), t0, t1)
        f_ts = np.array([r["ts"] for r in fu if r.get("funding_rate") is not None], dtype=np.int64) if fu else np.array([], dtype=np.int64)
        f_rt = np.array([r["funding_rate"] for r in fu if r.get("funding_rate") is not None], dtype=np.float64) if fu else np.array([])
        o = np.argsort(f_ts); f_ts, f_rt = f_ts[o], f_rt[o]
        first_q = ((t0 + 899) // 900) * 900
        dts = np.arange(first_q, t1 - 60 + 1, 900)
        idx = ((dts - t0) // 60).astype(np.int64)
        ok = ~np.isnan(g["mid"][idx]) & (idx + 1 < len(g["mid"]))
        idx, dts = idx[ok], dts[ok]
        feats = perp_features(g, idx, f_ts, f_rt)
        # fills: close quote of the bar ending at t + 60 s (long at ask, short at bid), exit at the first usable bar within 5 minutes of t + 60 + h
        N = len(g["mid"])
        spread_med = np.nanmedian(g["sp"][: max(1, int(len(g["sp"]) / 3))]) if stage == "dev" else np.nan
        cum = np.r_[0.0, np.cumsum(f_rt)] if len(f_rt) else np.array([0.0])
        ent = idx + 1
        ent_ok = ~np.isnan(g["ask"][ent]) & ~np.isnan(g["bid"][ent])
        defect = (g["sp"][ent] > 100.0)
        if stage == "dev" and not np.isnan(spread_med):
            defect |= g["sp"][ent] > 10 * spread_med
        H = len(PERP_HOLDS)
        netL, netS, nsL, nsS = (np.full((len(idx), H), np.nan, dtype=np.float32) for _ in range(4))
        exit_ts = np.full((len(idx), H), np.nan, dtype=np.float64)      # float64: unix seconds in float32 round by up to 64 s and corrupted the one-position rule (found by the v1.1 plain-loop audit)
        for hi, h in enumerate(PERP_HOLDS):
            base = idx + 1 + h // 60
            ex = np.full(len(idx), -1, dtype=np.int64)
            for k in range(0, 6):                           # first usable bar within the next 5 minutes
                cand = base + k
                inr = cand < N
                u = np.zeros(len(idx), bool)
                u[inr] = ~np.isnan(g["bid"][cand[inr]]) & ~np.isnan(g["ask"][cand[inr]])
                take = (ex < 0) & u
                ex[take] = cand[take]
            valid = ent_ok & ~defect & (ex >= 0)
            e = np.where(valid, ex, 0)
            ask_in, bid_in = g["ask"][ent], g["bid"][ent]
            bid_out, ask_out = g["bid"][e], g["ask"][e]
            t_in, t_out = g["t0"] + ent.astype(np.int64) * 60, g["t0"] + e.astype(np.int64) * 60
            pay = cum[np.searchsorted(f_ts, t_out, side="right")] - cum[np.searchsorted(f_ts, t_in, side="right")] if len(f_ts) else np.zeros(len(idx))
            fund_bps = pay * 1e4
            gl = (bid_out / ask_in - 1.0) * 1e4 - fund_bps               # long pays a positive rate (ASSUMED sign)
            gs = -(ask_out / bid_in - 1.0) * 1e4 + fund_bps
            for arr, v, fee in ((netL, gl, self.fee), (netS, gs, self.fee), (nsL, gl, 2 * self.fee), (nsS, gs, 2 * self.fee)):
                arr[valid, hi] = (v - 2 * fee)[valid]
            exit_ts[valid, hi] = t_out[valid]
        return dict(ts=dts, idx=idx, feats=feats, netL=netL, netS=netS, nsL=nsL, nsS=nsS, exit_ts=exit_ts, grid=g, f_ts=f_ts, f_rt=f_rt)

    def build_dev(self):
        pd = self._pd()
        return self._assemble(pd, self.frozen_id, holdout=False)

    def _assemble(self, pd, frozen_id, holdout, cuts=None):
        tks = self.tickers()
        parts = []
        self.grids = {}
        for si, tk in enumerate(tks):
            m1, fu = self._ticker_rows(pd, tk, frozen_id, holdout)
            if len(m1) < 3000:
                continue
            P = self._one(tk, m1, fu, "hold" if holdout else "dev")
            self.grids[tk] = P
            parts.append((si, tk, P))
        ts = np.concatenate([p[2]["ts"] for p in parts])
        n = len(ts)
        X = np.concatenate([np.stack([p[2]["feats"][f] for f in FEATS_P]) for p in parts], axis=1)
        scope = np.concatenate([np.full(len(p[2]["ts"]), i, dtype=np.int16) for i, p in enumerate(parts)])
        names = [p[1] for p in parts]
        date = (ts // 86400).astype(np.int32)
        win = np.zeros(n, dtype=np.int8)
        off = 0
        for i, p in enumerate(parts):
            m = len(p[2]["ts"]); d = date[off:off + m]
            if holdout:
                win[off:off + m] = 3
            else:
                ud = np.unique(d); wmap = {int(x): w for w, q in enumerate(np.array_split(ud, 3)) for x in q}
                win[off:off + m] = [wmap[int(x)] for x in d]
            off += m
        hod4 = ((ts % 86400) // 14400).astype(np.int16)
        dow = (((ts // 86400) + 3) % 7).astype(np.int16)
        wk = (dow >= 5).astype(np.int16)
        cats = {"hod4": hod4, "dow": dow, "wkend": wk}
        cat = lambda k: np.concatenate([p[2][k] for p in parts])
        NL, NS_, SL, SS_, EX = cat("netL"), cat("netS"), cat("nsL"), cat("nsS"), cat("exit_ts")
        hidx = {h: i for i, h in enumerate(PERP_HOLDS)}

        def outcome(dir_, variant, group):
            hi = hidx[variant]
            rows = np.arange(n)
            return rows, (NL if dir_ == "long" else NS_)[:, hi], (SL if dir_ == "long" else SS_)[:, hi]

        def thin(sel, variant):
            """One position per ticker: a signal while that ticker's position is open (until its actual exit) is ignored."""
            hi = hidx[variant]
            keep = np.zeros(len(sel), bool)
            o = np.lexsort((ts[sel], scope[sel]))
            last_sc, free = -1, -1
            for j in o:
                r = sel[j]
                if scope[r] != last_sc:
                    last_sc, free = scope[r], -1
                if ts[r] + 60 >= free:
                    keep[j] = True; free = EX[r, hi]
            return keep

        fnames = FEATS_P
        self.offsets, off = {}, 0
        for p in parts:
            self.offsets[p[1]] = (off, len(p[2]["ts"])); off += len(p[2]["ts"])
        if self.extra:
            X, cats, fnames = self._add_extra(pd, parts, X, cats, frozen_id, holdout)
        tab = Table(self.name + (":holdout" if holdout else ""), [self.group], fnames, X, cats, ts, date, win, scope, names, ("long", "short"), PERP_HOLDS,
                    outcome, scope.astype(np.int64), thin_fn=thin, meta=dict(parts=names))
        return tab

    def build_holdout(self, frozen_id, cuts):
        guard_check(frozen_id, self.name)
        guard_record(frozen_id, self.name)
        return self._assemble(self._pd(), frozen_id, holdout=True)

    def reverse_dir(self, d):
        return "short" if d == "long" else "long"

    def unseen(self):
        pd = self._pd()
        cuts = pd.cuts()
        out = dict(adapter=self.name, group=self.group, tickers=[], holdout_days=0)
        for tk in self.tickers():
            c = cuts[tk]
            last = datetime.fromisoformat(c["last_day"]); hs = datetime.fromisoformat(c["holdout_start"])
            d = (last - hs).days + 1
            out["tickers"].append((tk, c["holdout_start"], d)); out["holdout_days"] += d
        out["holdout_decision_rows_est"] = out["holdout_days"] * 96
        out["validation_locked"] = self.frozen_id is None
        out["note"] = ("holdout = each ticker's last third (calendar days from workers/PERPGEN_CUTS.json, never opened); the whole universe has "
                       "1,244,096 holdout 1 minute rows (DATA_INVENTORY G02, counted there by lines). Validation is read only with an existing "
                       "PERPGEN_FROZEN_<id>.json (frozen_id), and was already read by earlier PERPGEN runs.")
        return out

    def truncation_test(self, tab, n=200, seed=0):
        rng = random.Random(seed)
        bad = 0; tested = 0
        names = list(self.grids)
        for _ in range(n):
            tk = rng.choice(names); P = self.grids[tk]
            k = rng.randrange(len(P["idx"])); i = int(P["idx"][k])
            g = P["grid"]
            gt = {kk: (vv.copy() if isinstance(vv, np.ndarray) else vv) for kk, vv in g.items()}
            for kk in ("bid", "ask", "mid", "sp", "vol", "oi", "px"):
                gt[kk][i + 1:] = np.nan
            t = g["t0"] + i * 60
            ft = np.searchsorted(P["f_ts"], t, side="right")
            a = perp_features(g, np.array([i]), P["f_ts"], P["f_rt"])
            b = perp_features(gt, np.array([i]), P["f_ts"][:ft], P["f_rt"][:ft])
            same = all(np.allclose(a[f], b[f], equal_nan=True) and np.allclose(a[f], P["feats"][f][k:k + 1], equal_nan=True) for f in FEATS_P)
            if same and self.extra:
                same = self._extra_truncation_ok(tk, P, k, rng)
            bad += 0 if same else 1; tested += 1
        return dict(name="truncation", checked=tested, mismatches=bad, passed=bad == 0)


# ---- synthetic (tests, benchmark)
class SyntheticAdapter(Adapter):
    """Random features, a planted effect (optional), and an optional LEAKY feature that reads the future, to test the engine and the audit."""
    name = "synthetic"
    groups = ("ALL",)

    def __init__(self, days=30, per_day=400, nfeat=8, plant=False, leak=False, seed=1, looks=(360, 600)):
        self.days, self.per_day, self.nfeat, self.plant, self.leak, self.seed, self.looks = days, per_day, nfeat, plant, leak, seed, looks

    def build_dev(self):
        rng = np.random.default_rng(self.seed)
        n = self.days * self.per_day
        ts = (np.arange(n) // self.per_day) * 86400 + (np.arange(n) % self.per_day) * 60 + 1_790_000_000
        ts = ts.astype(np.int64)
        px = np.cumsum(rng.normal(size=n + 20))                      # a price path per row index
        X = rng.normal(size=(self.nfeat, n)).astype(np.float32)
        self.px = px
        X[0] = (px[np.arange(n)] - px[np.arange(n) - 5]).astype(np.float32)           # past only
        if self.leak:
            X[1] = (px[np.arange(n) + 5] - px[np.arange(n)]).astype(np.float32)       # reads the future
        self.X0 = X.copy()
        date = (ts // 86400).astype(np.int32)
        ud = np.unique(date); wmap = {int(d): w for w, q in enumerate(np.array_split(ud, 3)) for d in q}
        win = np.array([wmap[int(d)] for d in date], dtype=np.int8)
        base = -2.0 + rng.normal(size=n) * 20
        net_y = base.copy(); net_n = rng.normal(size=n) * 20 - 2.0
        if self.plant:
            m = (X[2] > 0.8) & (X[3] < 0.0)
            net_y = np.where(m, rng.normal(size=n) * 18 + 16.0, net_y)
        look = np.array([self.looks[i % len(self.looks)] for i in range(n)], dtype=np.int32)
        side = (np.arange(n) // len(self.looks)) % 2
        net = {"yes": net_y.astype(np.float32), "no": net_n.astype(np.float32)}

        def outcome(dir_, variant, group):
            rows = np.flatnonzero(look == variant)
            return rows, net[dir_][rows], net[dir_][rows] - 1.0

        return Table("synthetic", ["ALL"], ["f%d" % i for i in range(self.nfeat)], X, {"hod4": (ts // 14400 % 6).astype(np.int16)}, ts, date, win,
                     np.zeros(n, dtype=np.int16), ["ALL"], ("yes", "no"), self.looks, outcome, np.arange(n))

    def unseen(self):
        return dict(adapter=self.name, holdout_markets=0, note="synthetic")

    def truncation_test(self, tab, n=200, seed=0):
        rng = random.Random(seed); bad = 0
        for _ in range(n):
            i = rng.randrange(10, tab.n - 10)
            px = self.px.copy(); px[i + 1:] = np.nan                    # delete everything after the decision
            f0 = px[i] - px[i - 5]
            f1 = (px[i + 5] - px[i]) if self.leak else float(self.X0[1][i])
            ok0 = np.isclose(f0, self.X0[0][i], atol=1e-5)
            ok1 = (not self.leak) or (not np.isnan(f1) and np.isclose(f1, self.X0[1][i], atol=1e-5))
            bad += 0 if (ok0 and ok1) else 1
        return dict(name="truncation", checked=n, mismatches=bad, passed=bad == 0)


ADAPTERS = {"kalshi_fresh": lambda **k: KalshiAdapter(FRESH),
            "perps_crypto": lambda frozen_id=None, extra=False, **k: PerpAdapter("CRYPTO", frozen_id, extra=extra),
            "perps_noncrypto": lambda frozen_id=None, extra=False, **k: PerpAdapter("NONCRYPTO", frozen_id, extra=extra)}


# ------------------------------------------------------------------ HARNESS v1.1: perps cross-asset leaders and minutes to the next funding
# Opt-in (PerpAdapter(extra=True), CLI --perp-extra) so a v1 run, its atoms and its ledger ids are untouched. Protocol: PERPGEN_PROTOCOL.md (cross-asset
# leads, mtf). A leader's return is used at a timestamp ONLY if the leader's own loaded region (the same stage this adapter reads for it: discovery,
# plus validation with a frozen id; at a holdout read only leaders that are themselves in the guarded read) has both end minutes there; otherwise NaN and
# the atom is false. BTC does not lead BTC, ETH does not lead ETH. xgold60 and xus500_60 of the protocol are NOT built (BTC and ETH only).
FEATS_PX = ["xbtc15", "xbtc60", "xbtc240", "xeth60", "xeth240", "rel_btc60", "rel_btc240"]
LEADER_TICKERS = (("xbtc", "KXBTCPERP", (15, 60, 240)), ("xeth", "KXETHPERP", (60, 240)))
MTF_EDGES = (30, 120, 240)                             # minutes to the next funding: under 30, 30 to 120, 120 to 240, 240 and over (codes 0 to 3, -1 missing)


def leader_ret(gl, t, w):
    """Leader log mid return (bps) over the w minutes ending at the leader's minute t (both end minutes present in its grid), else NaN. Reads grid minutes <= t only."""
    t = np.asarray(t, dtype=np.int64)
    off = t - gl["t0"]; i = off // 60; N = len(gl["mid"])
    ok = (off >= 0) & (off % 60 == 0) & (i >= w) & (i < N)
    j = np.where(ok, i, 0); jw = np.where(ok, i - w, 0)
    with np.errstate(all="ignore"):
        r = (np.log(gl["mid"][j]) - np.log(gl["mid"][jw])) * 1e4
    r[~ok] = np.nan
    return r.astype(np.float32)


def mtf_codes(t, f_ts):
    """Minutes to the next funding as a bucket code. The calendar is read from funding rows published at or before t only (the distinct seconds of
    day of the last 6 settlements, so a clock change moves it one settlement late rather than looking ahead); next = the nearest such slot strictly after t."""
    t = np.asarray(t, dtype=np.int64); out = np.full(len(t), -1, dtype=np.int16)
    if len(f_ts) == 0:
        return out
    j = np.searchsorted(f_ts, t, side="right")
    for k in range(len(t)):
        if j[k] == 0:
            continue
        slots = {int(x) % 86400 for x in f_ts[max(0, j[k] - 6):j[k]]}
        d = min(((s_ - int(t[k])) % 86400) or 86400 for s_ in slots) / 60.0
        out[k] = 0 if d < MTF_EDGES[0] else 1 if d < MTF_EDGES[1] else 2 if d < MTF_EDGES[2] else 3
    return out


def _px_features(leaders, tk, t, own):
    """(7, len(t)) float32 in FEATS_PX order for ticker tk at decision seconds t; own = its r60 and r240."""
    nan = np.full(len(t), np.nan, dtype=np.float32)
    f = {k: nan.copy() for k in FEATS_PX}
    for pref, lt, ws in LEADER_TICKERS:
        gl = leaders.get(lt)
        if gl is None or tk == lt:
            continue
        for w in ws:
            f["%s%d" % (pref, w)] = leader_ret(gl, t, w)
    for w in (60, 240):
        f["rel_btc%d" % w] = (own["r%d" % w] - f["xbtc%d" % w]).astype(np.float32)
    return np.stack([f[k] for k in FEATS_PX])


def _perp_add_extra(self, pd, parts, X, cats, frozen_id, holdout):
    self.leaders = {}
    have = {p[1]: p[2]["grid"] for p in parts}
    for _, lt, _ in LEADER_TICKERS:
        if lt in have:
            self.leaders[lt] = have[lt]
        elif not holdout:                                            # a dev read of a leader outside the table; never at a holdout (that read is guarded)
            try:
                m1, fu = self._ticker_rows(pd, lt, frozen_id, False)
                if len(m1) >= 3000:
                    ts_ = np.array(sorted(r["ts"] for r in m1), dtype=np.int64)
                    self.leaders[lt] = self._grid(sorted(m1, key=lambda r: r["ts"]), int(ts_[0]), int(ts_[-1]))
            except (OSError, KeyError, ValueError):
                pass
    xs, ms = [], []
    for si, tk, P in parts:
        P["xf"] = _px_features(self.leaders, tk, P["ts"], P["feats"])
        P["mtf"] = mtf_codes(P["ts"], P["f_ts"])
        xs.append(P["xf"]); ms.append(P["mtf"])
    X = np.concatenate([X, np.concatenate(xs, axis=1)], axis=0)
    cats = dict(cats); cats["mtf"] = np.concatenate(ms)
    return X, cats, list(FEATS_P) + FEATS_PX


def _perp_extra_truncation_ok(self, tk, P, k, rng):
    """Delete every leader minute after t and every funding row after t; the extras at row k must be unchanged."""
    t = np.array([P["ts"][k]], dtype=np.int64)
    cut = {}
    for lt, gl in self.leaders.items():
        i = int((t[0] - gl["t0"]) // 60)
        gt = {kk: (vv.copy() if isinstance(vv, np.ndarray) else vv) for kk, vv in gl.items()}
        for kk in ("bid", "ask", "mid", "sp", "vol", "oi", "px"):
            gt[kk][max(i + 1, 0):] = np.nan
        cut[lt] = gt
    own = {"r%d" % w_: P["feats"]["r%d" % w_][k:k + 1] for w_ in (60, 240)}
    a = _px_features(cut, tk, t, own)
    ft = np.searchsorted(P["f_ts"], t[0], side="right")
    m = mtf_codes(t, P["f_ts"][:ft])
    return bool(np.allclose(a[:, 0], P["xf"][:, k], equal_nan=True) and m[0] == P["mtf"][k])


PerpAdapter._add_extra = _perp_add_extra
PerpAdapter._extra_truncation_ok = _perp_extra_truncation_ok


# ------------------------------------------------------------------ audit hooks (dev data only)
AUDIT_HOOKS = []


def audit_hook(fn):
    AUDIT_HOOKS.append(fn)
    return fn


@audit_hook
def audit_truncation(adapter, tab, ats, group, rules):
    """A1: delete every bar after the decision time and recompute the features of 200 random rows: nothing may change."""
    return adapter.truncation_test(tab, 200, 0)


@audit_hook
def audit_reverse_control(adapter, tab, ats, group, rules):
    """A2: the same entries in the opposite direction must have PF under 1.0 (the edge is directional, not a cost artefact). Perps only."""
    res = []
    for r in rules:
        rd = adapter.reverse_dir(r.dir)
        if rd is None:
            return dict(name="reverse_control", passed=None, note="not defined for this adapter")
        e = exact_rule(tab, ats, group, Rule(r.atoms, rd, r.variant))
        res.append(e["all"]["pf"])
    return dict(name="reverse_control", pfs=res, passed=all(p < 1.0 for p in res))


@audit_hook
def audit_fee_stress(adapter, tab, ats, group, rules):
    """A3: PF at the stress cost (Kalshi fees x1.2, perps 24 bps a side) must stay at least 1.0 pooled."""
    res = [exact_rule(tab, ats, group, r, stress=True)["all"]["pf"] for r in rules]
    return dict(name="fee_stress", pfs=res, passed=all(p >= 1.0 for p in res))


# ------------------------------------------------------------------ HARNESS v1.1 audit hooks: plain-python reference, placebo, latency, clusters
# The plain loop below is written from the fee function and the settlement definition, NOT from the vectorised engine: python floats, math.ceil, one
# trade at a time. It shares only the feature definitions (kalshi_row, perp feature arrays), which the truncation hook audits on their own.
PLACEBO_PERMS = 1000
PLACEBO_SEED = 20261107
PLACEBO_ALPHA = 0.05
LATENCY_SHIFTS = (1, 2)
CLUSTER_JACCARD = 0.7
PLAIN_REL_TOL = 1e-4          # the engine's nets are float32 (then summed in float64); the plain loop is float64 throughout


class AuditMismatch(AssertionError):
    """The plain-loop recompute disagrees with the engine: a defect in one of the two, never to be averaged away."""


def _thirds_of(dates):
    """date -> window 0, 1, 2 by thirds of the distinct dates (the first r windows get one extra date, as numpy array_split does); written out, not np.array_split."""
    ud = sorted(set(int(d) for d in dates)); q, r = divmod(len(ud), 3); out, i = {}, 0
    for w in range(3):
        k = q + (1 if w < r else 0)
        for d in ud[i:i + k]:
            out[d] = w
        i += k
    return out


def _py_cut_ok(x, c, op):
    """One numeric atom the way the engine defines it: a missing value or a missing cut is false; compared in float32 as the table stores them."""
    if x != x or c != c:
        return False
    x32, c32 = np.float32(x), np.float32(c)
    return bool(x32 >= c32) if op == "ge" else bool(x32 <= c32)


def _atoms_ok(specs, cuts, scope_name, getnum, getcat):
    for sp in specs:
        if sp["kind"] == "cat":
            if getcat(sp["feat"]) != sp["val"]:
                return False
        elif sp["kind"] == "num":
            if not _py_cut_ok(getnum(sp["feat"]), cuts[scope_name][sp["feat"]][QS.index(sp["q"])], sp["op"]):
                return False
        else:
            raise NotImplementedError("custom atoms are not part of a frozen survivor")
    return True


def _k_net(won, ask, c, mult):
    fee_cents = math.ceil(mult * 0.07 * c * ask * (1.0 - ask) * 100.0 - 1e-9)       # per ORDER of c contracts, rounded up
    return ((1.0 if won else 0.0) - ask) * 100.0 - fee_cents / c


def _kalshi_plain_state(self, tab):
    st = getattr(self, "_plain_state", None)
    if st is not None and st["tab"] is tab:
        return st
    sp = self.spec
    dates = set()
    for tk, series, close_ts, res, cs in self.markets:           # a window's date counts if ANY look and side gave a usable row
        hit = False
        for L in sp.looks:
            for side in (1, 0):
                q = cs.get(close_ts - L)
                if q is None or not _valid_quote(q[0], q[1]):
                    continue
                ask = q[1] if side else round(1 - q[0], 4)
                if 0.02 <= ask <= 0.98:
                    hit = True
                    break
            if hit:
                break
        if hit:
            dates.add(close_ts // 86400)
    st = dict(tab=tab, wmap=None if sp.win_cuts else _thirds_of(dates), rows={})
    self._plain_state = st
    return st


def _kalshi_plain_trades(self, tab, ats, group, rule, shift=0, stress=False):
    """Trades of one rule recomputed one at a time. shift = bars (minutes) of latency: the rule is decided at its own look from that look's features and
    filled at the ask of the look `shift` minutes later; a market with no usable quote there is a MISSED fill (counted, not traded)."""
    sp = self.spec
    st = _kalshi_plain_state(self, tab)
    L = rule.variant
    want = 1 if rule.dir == "yes" else 0
    specs = [ats.specs[a] for a in rule.atoms]
    cuts = ats.cuts
    mult = self.stress if stress else 1.0
    snames = tab.meta["series_names"]
    if L not in st["rows"]:
        lst = []
        for mi, (tk, series, close_ts, res, cs) in enumerate(self.markets):
            for side in (1, 0):
                r = kalshi_row(cs, close_ts, L, side)
                if r is not None:
                    lst.append((mi, side, r[0], r[1], r[2], close_ts, series, (res == "yes") == bool(side)))
        st["rows"][L] = lst
    keys, win, date, net, missed = [], [], [], [], 0
    for mi, side, ask, feats, t, close_ts, series, won in st["rows"][L]:
        if side != want:
            continue
        getnum = lambda f, feats=feats: feats[FEATS_K.index(f)]
        getcat = lambda f, t=t, series=series: {"series": snames.index(series), "hod4": (t % 86400) // 14400, "dow": ((t // 86400) + 3) % 7}[f]
        if not _atoms_ok(specs, cuts, "ALL", getnum, getcat):
            continue
        if shift:
            r2 = kalshi_row(self.markets[mi][4], close_ts, L - 60 * shift, side)
            if r2 is None:
                missed += 1
                continue
            ask = r2[0]
        d = close_ts // 86400
        if sp.win_cuts:
            w = 0 if close_ts < sp.win_cuts[0] else 1 if close_ts < sp.win_cuts[1] else 2
        else:
            w = st["wmap"][d]
        keys.append((mi, side)); win.append(w); date.append(d); net.append(_k_net(won, ask, sp.contracts, mult))
    return dict(keys=keys, win=win, date=date, net=net, missed=missed)


def _perp_one_trade(g, P, i, hold, dirn, shift, fee, smed):
    """One perps trade at decision minute i: entry at the bar after (plus shift), exit at the first usable bar within 5 minutes of the hold; None if void."""
    N = len(g["mid"])
    ent = i + 1 + shift
    if ent >= N:
        return None
    ask_in, bid_in = g["ask"][ent], g["bid"][ent]
    if ask_in != ask_in or bid_in != bid_in:
        return None
    spr = g["sp"][ent]
    if spr > 100.0 or (smed == smed and spr > 10 * smed):
        return None
    base = ent + hold // 60
    ex = -1
    for k in range(6):
        c = base + k
        if c < N and g["bid"][c] == g["bid"][c] and g["ask"][c] == g["ask"][c]:
            ex = c
            break
    if ex < 0:
        return None
    t_in, t_out = int(g["t0"]) + ent * 60, int(g["t0"]) + ex * 60
    pay = 0.0
    for ft, fr in zip(P["f_ts"], P["f_rt"]):                      # funding settled in (entry, exit]
        if t_in < ft <= t_out:
            pay += float(fr)
    fund = pay * 1e4
    bid_out, ask_out = g["bid"][ex], g["ask"][ex]
    gross = ((bid_out / ask_in - 1.0) * 1e4 - fund) if dirn == "long" else (-(ask_out / bid_in - 1.0) * 1e4 + fund)
    return float(gross) - 2 * fee, t_out


def _perp_plain_trades(self, tab, ats, group, rule, shift=0, stress=False):
    specs = [ats.specs[a] for a in rule.atoms]
    cuts = ats.cuts
    fee = self.fee * (2 if stress else 1)
    keys, win, date, net, missed = [], [], [], [], 0
    fi = {f: i for i, f in enumerate(tab.fnames)}
    for tk, P in self.grids.items():
        off, m = self.offsets[tk]
        g = P["grid"]
        ts = [int(x) for x in P["ts"]]
        wmap = _thirds_of(t // 86400 for t in ts)
        sp_ = sorted(float(x) for x in g["sp"][:max(1, int(len(g["sp"]) / 3))] if x == x)
        smed = (sp_[len(sp_) // 2] if len(sp_) % 2 else 0.5 * (sp_[len(sp_) // 2 - 1] + sp_[len(sp_) // 2])) if sp_ else float("nan")
        taken = []
        for k in range(m):
            t = ts[k]

            def getcat(f, t=t, k=k):
                if f == "hod4":
                    return (t % 86400) // 14400
                if f == "dow":
                    return ((t // 86400) + 3) % 7
                if f == "wkend":
                    return 1 if ((t // 86400) + 3) % 7 >= 5 else 0
                return int(tab.cats[f][off + k])
            if not _atoms_ok(specs, cuts, tk, lambda f, k=k: float(tab.X[fi[f], off + k]), getcat):
                continue
            r = _perp_one_trade(g, P, int(P["idx"][k]), rule.variant, rule.dir, shift, fee, smed)
            if r is None:
                missed += 1
                continue
            taken.append((t, r[0], r[1]))
        free = -1                                                   # one position per ticker, until its exit
        for t, v, ex_t in sorted(taken):
            if t + 60 + 60 * shift >= free:
                keys.append((tk, t)); win.append(wmap[t // 86400]); date.append(t // 86400); net.append(v); free = ex_t
    return dict(keys=keys, win=win, date=date, net=net, missed=missed)


def _generic_plain_trades(self, tab, ats, group, rule, shift=0, stress=False):
    """Fallback for table-only adapters (synthetic): the selection, windows and PF are redone in python from the table's own columns."""
    if tab.thin is not None:
        raise NotImplementedError
    shift_fn = getattr(self, "shift_net", None)
    if shift and shift_fn is None:
        raise NotImplementedError
    rows, net, nets = tab.outcome(rule.dir, rule.variant, group)
    src = nets if stress else net
    specs = [ats.specs[a] for a in rule.atoms]
    fi = {f: i for i, f in enumerate(tab.fnames)}
    keys, win, date, out = [], [], [], []
    for pos in range(len(rows)):
        v = float(src[pos])
        i = int(rows[pos])
        if v != v:
            continue
        if not _atoms_ok(specs, ats.cuts, tab.scope_names[int(tab.scope[i])], lambda f, i=i: float(tab.X[fi[f], i]), lambda f, i=i: int(tab.cats[f][i])):
            continue
        keys.append(i); win.append(int(tab.win[i])); date.append(int(tab.date[i])); out.append(shift_fn(v, shift) if shift else v)
    return dict(keys=keys, win=win, date=date, net=out, missed=0)


Adapter.plain_trades = _generic_plain_trades
KalshiAdapter.plain_trades = _kalshi_plain_trades
PerpAdapter.plain_trades = _perp_plain_trades
SyntheticAdapter.shift_net = lambda self, v, shift: v - 1.5 * shift       # a fixed slippage per bar of delay (planted edges survive it)
Adapter.trade_keys = lambda self, tab, rows: [int(r) for r in rows]
Adapter.window_keys = lambda self, tab, rows: [int(r) for r in rows]
KalshiAdapter.trade_keys = lambda self, tab, rows: [(int(tab.meta["market_index"][r]), int(tab.meta["side"][r])) for r in rows]
KalshiAdapter.window_keys = lambda self, tab, rows: [int(tab.meta["market_index"][r]) for r in rows]
PerpAdapter.trade_keys = lambda self, tab, rows: [(tab.scope_names[int(tab.scope[r])], int(tab.ts[r])) for r in rows]
PerpAdapter.window_keys = PerpAdapter.trade_keys


def plain_recompute(adapter, tab, ats, group, rule, strict=True):
    """Hook 2 for one rule: the plain loop's trade set, windows and PF against exact_rule. strict=True raises AuditMismatch on any difference."""
    ex = exact_rule(tab, ats, group, rule)
    pl = adapter.plain_trades(tab, ats, group, rule)
    bad = []
    ek, pk = adapter.trade_keys(tab, ex["rows"]), pl["keys"]
    if set(ek) != set(pk) or len(ek) != len(pk):
        bad.append("trade sets differ: engine %d, plain %d, only-engine %d, only-plain %d" % (len(ek), len(pk), len(set(ek) - set(pk)), len(set(pk) - set(ek))))
    ps = stats_from_rows(np.array(pl["win"]), np.array(pl["date"]), np.array(pl["net"], dtype=np.float64))
    for w in range(3):
        a, b = ex["win"][w], ps["win"][w]
        if a["n"] != b["n"] or a["days"] != b["days"]:
            bad.append("W%d n/days engine %d/%d plain %d/%d" % (w + 1, a["n"], a["days"], b["n"], b["days"]))
        if abs(a["pf"] - b["pf"]) > PLAIN_REL_TOL * max(1.0, abs(a["pf"])) or abs(a["mean"] - b["mean"]) > PLAIN_REL_TOL * max(1.0, abs(a["mean"])) * 10:
            bad.append("W%d PF engine %.6f plain %.6f (mean %.5f vs %.5f)" % (w + 1, a["pf"], b["pf"], a["mean"], b["mean"]))
    if strict and bad:
        raise AuditMismatch("; ".join(bad))
    return dict(passed=not bad, mismatches=bad, n=[w["n"] for w in ps["win"]], pf=[round(w["pf"], 4) for w in ps["win"]], engine_pf=[round(w["pf"], 4) for w in ex["win"]])


def placebo_shuffle(tab, ats, group, rule, perms=None, seed=None, chunk=64):
    """Hook 1 for one rule: keep the rule's trade selection, shuffle the OUTCOME column (the per-row net of the rows this direction and variant can trade)
    within blocks of (ticker, UTC date), and rescore. share = fraction of permutations whose pooled PF reaches the observed one; p_plus = (1 + hits) / (1 + perms).
    It asks whether the rule's picks beat random picks of the same date's outcomes; it is NOT corrected for the many rules the survivor was chosen from."""
    perms = PLACEBO_PERMS if perms is None else perms
    seed = PLACEBO_SEED if seed is None else seed
    rows, net, _ = _prep(tab, group, rule.dir, rule.variant)
    ex = exact_rule(tab, ats, group, rule)
    sel_rows = ex["rows"]
    if len(sel_rows) == 0:
        return dict(n=0, observed_pf=0.0, share=1.0, p_plus=1.0, perms=perms, passed=False)
    pos = np.searchsorted(rows, sel_rows)
    block = tab.scope[rows].astype(np.int64) * (1 << 20) + tab.date[rows]
    keep_blocks = np.unique(block[pos])
    sub = np.flatnonzero(np.isin(block, keep_blocks))                       # only blocks that hold a selected row can matter
    order0 = sub[np.argsort(block[sub], kind="stable")]
    _, bidx = np.unique(block[order0], return_inverse=True)
    net_s = net[order0].astype(np.float64)
    where = np.full(len(rows), -1, dtype=np.int64)
    where[order0] = np.arange(len(order0))
    sel_s = where[pos]
    wsel = tab.win[sel_rows]
    obs_v = net[pos].astype(np.float64)
    obs_pf = pf_of(obs_v)
    obs_min = min(pf_of(obs_v[wsel == w]) for w in range(3))
    rng = np.random.default_rng(seed)
    hit = hit_min = done = 0
    masks = [wsel == w for w in range(3)]

    def pf_cols(V):
        p_ = np.where(V > 0, V, 0).sum(1)
        n_ = np.where(V < 0, -V, 0).sum(1)
        return np.where(n_ > 0, np.minimum(PF_CAP, p_ / np.where(n_ > 0, n_, 1)), np.where(p_ > 0, PF_CAP, 0.0))
    while done < perms:
        c = min(chunk, perms - done)
        K = rng.random((c, len(order0))) + bidx[None, :]
        order = np.argsort(K, axis=1)
        V = net_s[order[:, sel_s]]                                          # a random row of the same block at every selected position
        hit += int((pf_cols(V) >= obs_pf - 1e-12).sum())
        mins = np.full(c, PF_CAP)
        for m_ in masks:
            if m_.any():
                mins = np.minimum(mins, pf_cols(V[:, m_]))
        hit_min += int((mins >= obs_min - 1e-12).sum())
        done += c
    p_plus = (1 + hit) / (1 + perms)
    return dict(n=int(len(sel_rows)), observed_pf=round(obs_pf, 4), observed_min_window_pf=round(obs_min, 4), share=hit / perms,
                share_min_window=hit_min / perms, p_plus=p_plus, perms=perms, seed=seed, passed=p_plus < PLACEBO_ALPHA)


def latency_stress(adapter, tab, ats, group, rule, shifts=LATENCY_SHIFTS):
    """Hook 3 for one rule: the rule is still DECIDED at its own row; the fill is `shift` bars later (Kalshi: look 6 min becomes 5 and 4, a missing quote there is
    a missed fill; perps: entry and exit one and two minutes later; the one-position rule uses the later exits). PF per window and pooled; passes at pooled PF >= 1.0."""
    out = {}
    for j in shifts:
        pl = adapter.plain_trades(tab, ats, group, rule, shift=j)
        st = stats_from_rows(np.array(pl["win"]), np.array(pl["date"]), np.array(pl["net"], dtype=np.float64))
        out["shift_%d" % j] = dict(pf_windows=[round(w["pf"], 3) for w in st["win"]], n_windows=[w["n"] for w in st["win"]], pf_pooled=round(st["all"]["pf"], 3),
                                   mean_pooled=round(st["all"]["mean"], 3), missed=pl["missed"], passed=st["all"]["pf"] >= 1.0)
    return out


def cluster_dedupe(adapter, tab, ats, group, rules, thr=None):
    """Hook 4: greedy clusters on the Jaccard overlap of the SET OF TRADED WINDOW IDS (Kalshi: market; perps: ticker and decision time). Survivors are taken in
    order of their weakest window PF (best first); a survivor joins the first representative whose Jaccard exceeds thr, else starts a cluster. Clusters are
    not transitive: this counts independent bets conservatively as K, never as N survivors."""
    thr = CLUSTER_JACCARD if thr is None else thr
    sets, quality = [], []
    for r in rules:
        ex = exact_rule(tab, ats, group, r)
        sets.append(set(adapter.window_keys(tab, ex["rows"])))
        quality.append(min(w["pf"] for w in ex["win"]))
    order = sorted(range(len(rules)), key=lambda i: -quality[i])
    reps, members = [], []
    for i in order:
        for ci, rp in enumerate(reps):
            u = len(sets[i] | sets[rp])
            if u and len(sets[i] & sets[rp]) / u > thr:
                members[ci].append(i)
                break
        else:
            reps.append(i)
            members.append([i])
    return dict(survivors=len(rules), independent=len(reps), threshold=thr,
                clusters=[dict(representative=rp, size=len(m), members=sorted(m), trades=len(sets[rp])) for rp, m in zip(reps, members)])


@audit_hook
def audit_placebo(adapter, tab, ats, group, rules):
    """A4: placebo shuffle of the outcome within date blocks, per survivor (see placebo_shuffle). Passes at p_plus under 0.05 for every survivor."""
    res = [placebo_shuffle(tab, ats, group, r) for r in rules]
    return dict(name="placebo_shuffle", per_rule=res, passed=all(x["passed"] for x in res), max_p_plus=max([x["p_plus"] for x in res] or [0]))


@audit_hook
def audit_plain_loop(adapter, tab, ats, group, rules):
    """A5: independent plain-python recompute of every survivor's trades and per-window PF; any mismatch fails."""
    res = []
    for r in rules:
        try:
            res.append(plain_recompute(adapter, tab, ats, group, r, strict=True))
        except AuditMismatch as e:
            res.append(dict(passed=False, mismatches=[str(e)]))
    return dict(name="plain_loop_recompute", per_rule=res, passed=all(x["passed"] for x in res))


@audit_hook
def audit_latency(adapter, tab, ats, group, rules):
    """A6: latency stress, one and two bars (see latency_stress)."""
    try:
        res = [latency_stress(adapter, tab, ats, group, r) for r in rules]
    except NotImplementedError:
        return dict(name="latency_stress", passed=None, note="not defined for this adapter")
    return dict(name="latency_stress", per_rule=res, passed=all(v["passed"] for x in res for v in x.values()))


@audit_hook
def audit_cluster(adapter, tab, ats, group, rules):
    """A7: cluster dedupe (informational: reports independent survivors and a representative per cluster; no pass or fail)."""
    d = cluster_dedupe(adapter, tab, ats, group, rules)
    d.update(name="cluster_dedupe", passed=None)
    return d


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if o != o else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def audit_summary_text(rep):
    L = ["SCAN AUDIT %s (%s, group %s): %d survivors, development data only, cuts match frozen: %s"
         % (rep["frozen_id"], rep["adapter"], rep["group"], rep["survivors"], rep["cuts_match"])]
    for h in rep["hooks"]:
        extra = ""
        if h["name"] == "cluster_dedupe":
            extra = " independent survivors %d of %d (Jaccard > %.1f), representatives %s" % (h["independent"], h["survivors"], h["threshold"], [c["representative"] for c in h["clusters"]])
        elif h["name"] == "placebo_shuffle":
            extra = " max p %.4f" % h["max_p_plus"]
        L.append("  %-22s %s%s" % (h["name"], {True: "PASS", False: "FAIL", None: "n/a "}[h.get("passed")], extra))
    L.append("overall: %s" % ("FAIL: " + ", ".join(rep["failed"]) if rep["failed"] else "no hook failed"))
    return "\n".join(L)


def audit_frozen(adapter, doc, tab=None, out_dir=None, frozen_id=None, perms=None):
    """Run every hook on a frozen survivor list (development rows only: build_dev), write workers/SCAN_AUDIT_<id>.json and .txt (out_dir=False writes nothing)."""
    global PLACEBO_PERMS
    tab = tab or adapter.build_dev()
    cuts = {k: v for k, v in doc["cuts"].items() if not k.startswith("_")}
    own = make_cuts(tab)
    if tab.meta.get("series_names") is not None:
        own["_series"] = tab.meta["series_names"]
    cuts_match = cuts_sha(own) == doc.get("cuts_sha256")
    ats = AtomSet(tab, cuts)
    rules = []
    for sv in doc["survivors"]:
        ids = [ats.names.index(_name_of(sp)) for sp in sv["atoms"]]
        rules.append(Rule(tuple(sorted(ids)), sv["dir"], sv["variant"]))
    old = PLACEBO_PERMS
    if perms is not None:
        PLACEBO_PERMS = perms
    try:
        hooks = run_audit(adapter, tab, ats, doc["group"], rules)
    finally:
        PLACEBO_PERMS = old
    failed = [h["name"] for h in hooks if h.get("passed") is False] + ([] if cuts_match else ["cuts_sha256_mismatch"])
    fid = frozen_id or doc.get("frozen_id", "X")
    rep = _jsonable(dict(frozen_id=fid, adapter=doc["adapter"], group=doc["group"], survivors=len(rules), cuts_match=cuts_match,
                         table_match=tab.fingerprint() == doc.get("table_sha256"), rules=[describe(tab, ats, r) for r in rules], hooks=hooks, failed=failed,
                         created=datetime.now(timezone.utc).isoformat()))
    text = audit_summary_text(rep)
    if out_dir is not False:
        od = out_dir or WORKERS
        json.dump(rep, open(os.path.join(od, "SCAN_AUDIT_%s.json" % fid), "w"), indent=1)
        open(os.path.join(od, "SCAN_AUDIT_%s.txt" % fid), "w").write(text + "\n")
    rep["text"] = text
    return rep


def run_audit(adapter, tab, ats, group, rules):
    return [h(adapter, tab, ats, group, rules) for h in AUDIT_HOOKS]


# ------------------------------------------------------------------ run / freeze / holdout
def describe(tab, ats, r):
    return " & ".join(sorted(ats.names[a] for a in r.atoms)) + " | " + r.dir + " | " + str(r.variant)


def banner(adapter, N, bar_z):
    u = adapter.unseen()
    lines = ["BAR: PF >= %.2f in each of W1, W2, W3 after fees; floors: %d trades per window, %d total, %d days per window; N so far %d -> one-sided "
             "Bonferroni z >= %.3f (alpha %.2f / N); the 1.5 is not raised for N" % (BAR["pf"], BAR["min_trades_window"], BAR["min_trades_total"],
                                                                                   BAR["min_days_window"], N, bar_z, BAR["alpha"]),
             "UNSEEN: " + json.dumps({k: v for k, v in u.items() if k != "tickers"}, default=str)]
    return "\n".join(lines)


def run(adapter, n_rules, seed, group=None, batch=2000, ledger_dir=None, out_dir=None, tab=None, verbose=True):
    """One RUN for one (adapter, group): at least n_rules DISTINCT new rules, ledger written before every batch is scored."""
    global LEDGER_DIR
    old = LEDGER_DIR
    if ledger_dir:
        LEDGER_DIR = ledger_dir
    try:
        t_build = time.time()
        tab = tab or adapter.build_dev()
        cuts = make_cuts(tab)
        if hasattr(adapter, "spec") and tab.meta.get("series_names") is not None:
            cuts["_series"] = tab.meta["series_names"]
        csha = cuts_sha(cuts)
        ats = AtomSet(tab, {k: v for k, v in cuts.items() if not k.startswith("_")})
        group = group or tab.groups[0]
        prefix = "%s|%s|" % (tab.name, group)
        seen = seen_ids(prefix)
        rng = random.Random(seed)
        path = os.path.join(LEDGER_DIR, "%s_%s_RUN%d.ids.gz" % (tab.name.replace(":", "_"), group, seed))
        N0 = n_total(ledger_dir=LEDGER_DIR)
        if verbose:
            print(banner(adapter, N0, z_bar(N0)))
            print("table: %d rows, atoms %d, build %.1fs, cuts sha256 %s" % (tab.n, ats.n_real, time.time() - t_build, csha[:16]))
        done, tried, surv, top = 0, 0, [], []
        t0 = time.time()
        while done < n_rules and tried < 50 * n_rules:
            want = min(batch, n_rules - done)
            cand, ids = [], []
            while len(cand) < want and tried < 50 * n_rules:
                r = draw_rule(rng, ats, tab); tried += 1
                rid = rule_id(tab, ats, group, r)
                if rid in seen:
                    continue
                seen.add(rid); cand.append(r); ids.append(rid)
            if not cand:
                break
            ledger_append(path, ids)                              # BEFORE scoring
            res = score_rules(tab, ats, group, cand)
            for r, rid, s in zip(cand, ids, res):
                if s["surv"]:
                    surv.append((r, rid, s))
                if min(s["pf"]) > 0 and all(x >= BAR["min_trades_window"] for x in s["n"]):
                    top.append((min(s["pf"]), rid))
            done += len(cand)
            top = sorted(top, reverse=True)[:10]
        dt = time.time() - t0
        N1 = n_total(ledger_dir=LEDGER_DIR); zb = z_bar(N1)
        final = []
        for r, rid, s in surv:                                    # exact re-score: plain float64 and the adapter's overlap rule
            ex = exact_rule(tab, ats, group, r)
            if passes_bar(ex):
                final.append(dict(id=rid, atoms=[ats.specs[a] for a in r.atoms], dir=r.dir, variant=r.variant, batch=s,
                                  exact={k: ex[k] for k in ("win", "all")}, deflated=bool(ex["all"]["z"] >= zb)))
        summary = dict(adapter=tab.name, group=group, seed=seed, rules_scored=done, seconds=round(dt, 2), rules_per_sec=round(done / max(dt, 1e-9), 1),
                       N_before=N0, N_after=N1, z_bar=round(zb, 4), screen_survivors=len(surv), exact_survivors=len(final),
                       deflated=sum(1 for f in final if f["deflated"]), cuts_sha256=csha, table_sha256=tab.fingerprint(), survivors=final, adapter_opts=getattr(adapter, "opts", {}),
                       top_by_min_window_pf=top, cuts={k: v for k, v in cuts.items()})
        if out_dir is not False:
            od = out_dir or os.path.join(SCAN_DATA, "runs"); os.makedirs(od, exist_ok=True)
            fn = os.path.join(od, "%s_%s_RUN%d.json" % (tab.name.replace(":", "_"), group, seed))
            json.dump(summary, open(fn, "w"), indent=1, default=str)
            summary["file"] = fn
        if verbose:
            print("scored %d distinct new rules in %.1fs (%.0f rules/s); N now %d, bar z %.3f; screen survivors %d, exact survivors %d, deflated %d"
                  % (done, dt, done / max(dt, 1e-9), N1, zb, len(surv), len(final), summary["deflated"]))
            for s_, rid in top[:5]:
                print("  best min-window PF %.3f  %s" % (s_, rid))
        return summary
    finally:
        LEDGER_DIR = old


def freeze(run_files, frozen_id, out_dir=None):
    """Write workers/SCAN_FROZEN_<id>.json (the survivor list, the cut points, N and the bar) and its .sha256. Commit and push BEFORE the guard
    file is written and the holdout is read."""
    runs = [json.load(open(f)) for f in run_files]
    surv = [dict(s, adapter=r["adapter"], group=r["group"]) for r in runs for s in r["survivors"]]
    doc = dict(frozen_id=frozen_id, created=datetime.now(timezone.utc).isoformat(), adapter=runs[0]["adapter"], group=runs[0]["group"],
               N_total=max(r["N_after"] for r in runs), z_bar=max(r["z_bar"] for r in runs), bar=BAR, hold_bar=HOLD_BAR,
               cuts_sha256=runs[0]["cuts_sha256"], cuts=runs[0]["cuts"], table_sha256=runs[0]["table_sha256"], survivors=surv,
               adapter_opts=runs[0].get("adapter_opts", {}))
    od = out_dir or WORKERS
    p = os.path.join(od, "SCAN_FROZEN_%s.json" % frozen_id)
    if os.path.exists(p):
        raise Blocked("a frozen list with this id already exists; ids are never reused")
    json.dump(doc, open(p, "w"), indent=1, default=str)
    open(p + ".sha256", "w").write(_sha_file(p) + "  " + os.path.basename(p) + "\n")
    return p


def _atom_mask(tab, spec, cuts):
    if spec["kind"] == "cat":
        return tab.cats[spec["feat"]] == spec["val"]
    fi = tab.fnames.index(spec["feat"]); qi = QS.index(spec["q"])
    cv = np.array([cuts[nm][spec["feat"]][qi] for nm in tab.scope_names], dtype=np.float32)[tab.scope]
    with np.errstate(invalid="ignore"):
        return (tab.X[fi] >= cv) if spec["op"] == "ge" else (tab.X[fi] <= cv)


def holdout(adapter, frozen_path, require_committed=True, verbose=True):
    """THE one read. Order: frozen list valid (sha256, committed) -> guard names this id and dataset and it is unused -> the use is
    recorded -> the holdout rows are built -> frozen rules scored with the frozen cut points. Never re-run for a rule: a failed read is final."""
    doc = load_frozen(frozen_path, require_committed)
    fid = doc["frozen_id"]
    if doc["adapter"].split(":")[0] != adapter.name:
        raise Blocked("frozen list is for %s, adapter is %s" % (doc["adapter"], adapter.name))
    tab = adapter.build_holdout(fid, doc["cuts"])
    cuts = {k: v for k, v in doc["cuts"].items() if not k.startswith("_")}
    out = []
    for s in doc["survivors"]:
        m = np.ones(tab.n, bool)
        for sp in s["atoms"]:
            m &= _atom_mask(tab, sp, cuts)
        rows, net, nets = tab.outcome(s["dir"], s["variant"], doc["group"])
        ok = ~np.isnan(net)
        rows, net, nets = rows[ok], net[ok].astype(np.float64), nets[ok].astype(np.float64)
        sel = m[rows]
        r2, v = rows[sel], net[sel]
        if tab.thin is not None and len(r2):
            k = tab.thin(r2, s["variant"]); r2, v = r2[k], v[k]
        st = stats_from_rows(np.zeros(len(r2), dtype=int), tab.date[r2], v, windows=(0,))
        w = st["win"][0]
        half = np.argsort(tab.ts[r2], kind="stable"); h = len(half) // 2
        pf1 = pf_of(v[half[:h]]) if h else 0.0; pf2 = pf_of(v[half[h:]]) if h else 0.0
        if w["n"] < HOLD_BAR["min_trades"] or w["days"] < HOLD_BAR["min_days"]:
            label = "NOT_ENOUGH_DATA"
        elif w["pf"] >= HOLD_BAR["pf"]:
            label = "CANDIDATE" if s["deflated"] else "LEAD"
        else:
            label = "FALSIFIED"
        out.append(dict(id=s["id"], label=label, n=w["n"], days=w["days"], pf=w["pf"], mean=w["mean"], wr=w["wr"], z=w["z"], pf_half1=pf1, pf_half2=pf2,
                        dev_deflated=s["deflated"]))
    res = dict(frozen_id=fid, read_at=datetime.now(timezone.utc).isoformat(), frozen_sha256=_sha_file(frozen_path), holdout_rows=int(tab.n), results=out)
    rp = os.path.join(os.path.dirname(frozen_path), "SCAN_HOLDOUT_%s_RESULT.json" % fid)
    json.dump(res, open(rp, "w"), indent=1)
    if verbose:
        for o in out:
            print("  %-16s n=%d days=%d PF %.2f  %s" % (o["label"], o["n"], o["days"], o["pf"], o["id"]))
    return res


# ------------------------------------------------------------------ self-test and benchmark
# Registered figure (README, MKTTIME1 result of 2026-10-29, data/mkttime1_ab_result.txt): gold, L1's rule (6 minute look, side priced 88c to 97c,
# held to settlement, 1 contract, fee rounded up per order), baseline in close-date thirds: A: PF 1.439, net +1100c; B: PF 1.026, net +83c (n 666 and 607 here).
# Window C was read once by MKTTIME1 and is never loaded here: the SELFTEST_GOLD spec has no rows at or after C's first close.
# A rerun of the legacy code (tstop1.load on the same files, Nov 7) gives A PF 1.410 / +1137.7c and B PF 1.022 / +77.6c, so the files changed slightly
# after Oct 29: both the README numbers (tolerance) and the current rerun (exact, pinned below) are checked.
README_AB = {"A": dict(pf=1.439, net=1100.0), "B": dict(pf=1.026, net=83.0)}
PINNED_AB = {"A": dict(n=666, pf=1.4100, net=1137.7), "B": dict(n=607, pf=1.0220, net=77.6)}


def selftest(verbose=True):
    ad = KalshiAdapter(SELFTEST_GOLD)
    tab = ad.build_dev()
    # (1) plain loop in float64, independent of the engine's array code: L1 favourite 88c to 97c at 360 s, either side
    m = tab.meta
    plain = {0: [], 1: []}
    for i in range(tab.n):
        if m["look"][i] == 360 and 0.88 <= m["ask"][i] <= 0.97:
            fee = math.ceil(0.07 * 1 * m["ask"][i] * (1 - m["ask"][i]) * 100 - 1e-9)
            plain[int(tab.win[i])].append((1.0 if m["won"][i] else 0.0) * 100 - m["ask"][i] * 100 - fee)
    # (2) the engine: two custom band atoms scored through score_rules (yes and no separately, combined by sums)
    cuts = make_cuts(tab)
    ats = AtomSet(tab, cuts)
    lo = ats.add_custom("ask>=0.88", m["ask"] >= 0.88)           # float64 asks: a float32 0.97 would sit above 0.97
    hi = ats.add_custom("ask<=0.97", m["ask"] <= 0.97)
    rs = [Rule((lo, hi), "yes", 360), Rule((lo, hi), "no", 360)]
    sc = score_rules(tab, ats, "ALL", rs)
    ok = True
    rep = []
    for w, name in ((0, "A"), (1, "B")):
        v = np.array(plain[w])
        n_p, pf_p, net_p = len(v), pf_of(v), float(v.sum())
        n_e = sc[0]["n"][w] + sc[1]["n"][w]
        pos = sc[0]["pos"][w] + sc[1]["pos"][w]; neg = sc[0]["neg"][w] + sc[1]["neg"][w]
        pf_e = pos / neg; net_e = pos - neg
        pin = PINNED_AB[name]; rd = README_AB[name]
        checks = dict(
            engine_vs_plain=(n_e == n_p and abs(pf_e - pf_p) < 1e-3 and abs(net_e - net_p) < 0.5),
            pinned_exact=(n_p == pin["n"] and abs(pf_p - pin["pf"]) < 0.002 and abs(net_p - pin["net"]) < 0.5),
            readme_tolerance=(abs(pf_p - rd["pf"]) <= 0.05 and abs(net_p - rd["net"]) <= 60.0))
        ok &= all(checks.values())
        rep.append((name, n_p, pf_p, net_p, rd, checks))
    # (3) fee function checks, vectorised against a scalar loop
    ps = np.linspace(0.02, 0.98, 97)
    for c in (1, 3, 10, 50):
        v = kalshi_fee_cents(ps, c)
        s = np.array([math.ceil(0.07 * c * p * (1 - p) * 100 - 1e-9) for p in ps])
        ok &= bool(np.array_equal(v, s))
    ok &= float(kalshi_fee_cents(0.5, 1)) == 2.0 and float(kalshi_fee_cents(0.9, 1)) == 1.0 and float(kalshi_fee_cents(0.5, 10)) == 18.0
    tr = ad.truncation_test(tab, 200, 0)
    ok &= tr["passed"]
    ok &= tab.win.max() == 1 or tab.win.max() == 2
    # no row at or after window C's first close was loaded
    ok &= int(tab.meta["close"].max()) < SELFTEST_GOLD.dev_hi
    if verbose:
        for name, n_p, pf_p, net_p, rd, checks in rep:
            print("selftest gold window %s: n=%d PF %.3f net %+.1fc | README PF %.3f net %+.0fc | %s" % (name, n_p, pf_p, net_p, rd["pf"], rd["net"], checks))
        print("selftest truncation: %s" % tr)
        print("SELFTEST:", "PASS" if ok else "FAIL")
    return bool(ok)


def bench(per_key=20_000, n_looks=12, n_feat=12, n_rules=40_000, seed=3, verbose=True):
    """Rules per second on a synthetic table shaped like the Kalshi fresh dev table (about 20,000 tradable rows per direction and look time,
    12 look times). Scores random rules on random outcomes: no real rule is scored and nothing is written to a ledger."""
    ad = SyntheticAdapter(days=17, per_day=per_key * n_looks // 17, nfeat=n_feat, looks=tuple(range(n_looks)))
    t0 = time.time(); tab = ad.build_dev(); t1 = time.time()
    cuts = make_cuts(tab); ats = AtomSet(tab, cuts); t2 = time.time()
    rng = random.Random(seed)
    rules = [draw_rule(rng, ats, tab) for _ in range(n_rules)]
    t3 = time.time()
    res = score_rules(tab, ats, "ALL", rules)
    t4 = time.time()
    rps = n_rules / (t4 - t3)
    if verbose:
        print("bench: table %d rows x %d features built in %.1fs, atoms %d in %.1fs; scored %d rules in %.1fs = %.0f rules/s (survivors on noise %d)"
              % (tab.n, n_feat, t1 - t0, ats.n_real, t2 - t1, n_rules, t4 - t3, rps, sum(r["surv"] for r in res)))
    return rps


# ------------------------------------------------------------------ CLI
def _adapter(name, frozen_id=None, extra=False):
    if name not in ADAPTERS:
        raise SystemExit("unknown adapter %s (have %s)" % (name, ", ".join(ADAPTERS)))
    return ADAPTERS[name](frozen_id=frozen_id, extra=extra)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scan")
    ap.add_argument("cmd", choices=["selftest", "bench", "unseen", "ledger", "run", "freeze", "audit", "holdout"])
    ap.add_argument("--adapter", default="kalshi_fresh"); ap.add_argument("--n", type=int, default=5000); ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--run", nargs="*"); ap.add_argument("--id"); ap.add_argument("--frozen"); ap.add_argument("--perp-frozen-id", default=None)
    ap.add_argument("--allow-uncommitted", action="store_true")
    ap.add_argument("--perp-extra", action="store_true", help="perps: add leader returns (BTC, ETH) and minutes-to-funding features (v1.1)")
    ap.add_argument("--perms", type=int, default=None, help="audit: placebo permutations (default %d)" % PLACEBO_PERMS)
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        sys.exit(0 if selftest() else 1)
    if a.cmd == "bench":
        bench(); return
    if a.cmd == "ledger":
        N = n_total(); print("N = prior %d + perpgen ledger %d + scan ledger %d = %d; one-sided Bonferroni z bar %.3f at alpha %.2f"
                             % (prior_n(), _count_lines(PERPGEN_LEDGER_DIR), _count_lines(LEDGER_DIR), N, z_bar(N), BAR["alpha"])); return
    if a.cmd == "unseen":
        for nm in ([a.adapter] if a.adapter != "all" else list(ADAPTERS)):
            u = _adapter(nm, a.perp_frozen_id).unseen()
            print(json.dumps({k: v for k, v in u.items() if k != "tickers"}, indent=1, default=str))
        return
    if a.cmd == "run":
        ad = _adapter(a.adapter, a.perp_frozen_id, extra=a.perp_extra)
        seed = a.seed if a.seed is not None else 7000 + len([f for f in os.listdir(LEDGER_DIR) if f.endswith(".ids.gz")]) if os.path.isdir(LEDGER_DIR) else 7000
        run(ad, a.n, seed); return
    if a.cmd == "freeze":
        print(freeze(a.run, a.id)); return
    if a.cmd == "holdout":
        ad = _adapter(a.adapter, a.perp_frozen_id, extra=bool(a.perp_extra or json.load(open(a.frozen)).get("adapter_opts", {}).get("extra")))
        holdout(ad, a.frozen, require_committed=not a.allow_uncommitted); return
    if a.cmd == "audit":
        p = a.frozen
        doc = load_frozen(p, require_committed=False) if os.path.exists(p + ".sha256") else json.load(open(p))
        opts = doc.get("adapter_opts", {})
        ad = _adapter(a.adapter, a.perp_frozen_id, extra=bool(a.perp_extra or opts.get("extra")))
        rep = audit_frozen(ad, doc, perms=a.perms)
        print(rep["text"])
        sys.exit(2 if rep["failed"] else 0)


def _name_of(sp):
    return "%s:eq:%d" % (sp["feat"], sp["val"]) if sp["kind"] == "cat" else "%s:%s:%.2f" % (sp["feat"], sp["op"], sp["q"])


if __name__ == "__main__":
    main()
