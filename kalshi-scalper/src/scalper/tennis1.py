"""TENNIS1 (workers/TENNIS1_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi ATP and WTA tour-level match-winner markets against a walk-forward
Elo built only from ESPN's completed tour-level results. Research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA, NOT_RUNNABLE.
Nothing here means trade; no promote verb. Cheap side only: no favourite-side result is computed or printed anywhere in this file.

    python -m scalper.tennis1 census   (listings and names only: how many Kalshi matches match an ESPN match with Elo ready; no candle, no outcome)
    python -m scalper.tennis1 fetch    (resumable; candles of the registered universe only, before the frozen cut)
    python -m scalper.tennis1 run      (the one scored read; refused a second time)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone

CUT = datetime(2026, 10, 3, 16, 0, tzinfo=timezone.utc)   # frozen last third: matches from here are never fetched or joined
K0, K_EXP, K_OFF, SCALE, INIT, MIN_PRIOR = 250.0, 0.4, 5.0, 400.0, 1500.0, 10
ASK_LO, ASK_HI, RATIO, HARD_LIMIT = 0.03, 0.30, 3.0, 0.30
C, LEAD_S = 10, 600
BAR_PF, MIN_TRADES = 1.5, 150
SUFFIX = {"jr": 1, "sr": 1, "ii": 1, "iii": 1}


def norm(name: str) -> str:
    """Lower case, accents removed, punctuation to spaces, suffixes dropped; the same function is applied to Kalshi's and ESPN's names."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return " ".join(w for w in s.split() if w not in SUFFIX)


def elo_p(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rb - ra) / SCALE))


class Elo:
    """Per-tour walk-forward Elo. K = K0 / (n + K_OFF) ** K_EXP, n = the player's earlier matches (a new player moves fast)."""

    def __init__(self):
        self.r = defaultdict(lambda: INIT)
        self.n = defaultdict(int)

    def prob(self, a: str, b: str) -> float:
        return elo_p(self.r[a], self.r[b])

    def ready(self, a: str, b: str) -> bool:
        return self.n[a] >= MIN_PRIOR and self.n[b] >= MIN_PRIOR

    def update(self, winner: str, loser: str) -> None:
        pw = elo_p(self.r[winner], self.r[loser])
        kw = K0 / (self.n[winner] + K_OFF) ** K_EXP
        kl = K0 / (self.n[loser] + K_OFF) ** K_EXP
        self.r[winner] += kw * (1 - pw)
        self.r[loser] -= kl * (1 - pw)
        self.n[winner] += 1
        self.n[loser] += 1


def fee(price: float, contracts: int = C) -> float:
    """Kalshi taker fee: 7% x C x p x (1-p), rounded UP to the cent, in dollars for the order."""
    return math.ceil(round(0.07 * contracts * price * (1 - price) * 100, 6)) / 100


def cheap_side(yes_bid: float, yes_ask: float):
    """The side with ask 3c to 30c, or None. Returns ('yes'|'no', ask). NO ask is 1 - YES bid. Needs a two-sided quote."""
    if yes_bid is None or yes_ask is None or not (0 < yes_bid < yes_ask < 1):
        return None
    if ASK_LO <= yes_ask <= ASK_HI:
        return "yes", yes_ask
    no_ask = 1 - yes_bid
    if ASK_LO <= no_ask <= ASK_HI:
        return "no", no_ask
    return None


def net_cents(ask: float, won: bool, contracts: int = C) -> float:
    """Net per contract, in cents, after the fee on the order (buy at the ask, hold to settlement)."""
    gross = (1.0 - ask) if won else -ask
    return (gross * contracts - fee(ask, contracts)) / contracts * 100


def treated(p_side: float, ask: float) -> bool:
    return ask <= HARD_LIMIT and p_side >= RATIO * ask - 1e-9


def profit_factor(xs):
    g = sum(x for x in xs if x > 0)
    l = -sum(x for x in xs if x < 0)
    return g / l if l > 0 else float("inf") if g > 0 else 0.0


def summary(rows):
    """rows: (cluster, net_cents, won, ask). Returns n, mean, win rate, mean ask, PF."""
    if not rows:
        return dict(n=0, mean=None, win=None, ask=None, pf=None)
    n = len(rows)
    return dict(n=n, mean=sum(r[1] for r in rows) / n, win=sum(1 for r in rows if r[2]) / n,
                ask=sum(r[3] for r in rows) / n, pf=profit_factor([r[1] for r in rows]))


def verdict(treated_rows, midpoint):
    """FALSIFIED unless mean net > 0 in BOTH halves (split by match start at midpoint) and PF >= 1.5; NOT_ENOUGH_DATA under 150 trades."""
    n = len(treated_rows)
    if n < MIN_TRADES:
        return "NOT_ENOUGH_DATA"
    h1 = [r[1] for r in treated_rows if r[4] < midpoint]
    h2 = [r[1] for r in treated_rows if r[4] >= midpoint]
    m1 = sum(h1) / len(h1) if h1 else 0.0
    m2 = sum(h2) / len(h2) if h2 else 0.0
    pf = profit_factor([r[1] for r in treated_rows])
    return "NOT_YET_FALSIFIED" if (m1 > 0 and m2 > 0 and pf >= BAR_PF) else "FALSIFIED"


def build_matches(espn_rows):
    """ESPN completed singles rows -> list sorted by start time of (start_iso, name_a, name_b, winner_index). Retirements and walkovers are kept
    out of the Elo only if ESPN marks them not final; every STATUS_FINAL result updates the ratings."""
    out = []
    for r in espn_rows:
        if r.get("status") != "STATUS_FINAL" or "Singles" not in (r.get("grp") or ""):
            continue
        if r["win"].count(True) != 1:
            continue
        a, b = r["names"]
        out.append((r["date"], norm(a), norm(b), 0 if r["win"][0] else 1, r["id"]))
    out.sort()
    return out


def elo_before(matches, t_iso):
    """Yield-style helper: returns a function advancing the Elo to just before t_iso (ISO strings compare lexically in this format)."""
    elo = Elo()
    i = [0]

    def advance(t):
        while i[0] < len(matches) and matches[i[0]][0] < t:
            _, a, b, w, _id = matches[i[0]]
            elo.update(a if w == 0 else b, b if w == 0 else a)
            i[0] += 1
        return elo
    return advance


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
