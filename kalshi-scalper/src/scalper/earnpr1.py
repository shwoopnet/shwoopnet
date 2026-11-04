"""EARNPR1 (README, Registration: EARNPR1): earnings press release text (SEC EDGAR 8-K Item 2.02 Ex-99.1) against Kalshi
earnings-call word markets (KXEARNINGSMENTION*). Discovery lane, research only. Verdict words: FALSIFIED, NOT_YET_FALSIFIED,
NOT_ENOUGH_DATA, NOT_RUNNABLE. Nothing here means trade; there is no order code in this file.

This file holds the fixed rules (matching, look, model, scoring) as pure functions so they can be tested on synthetic data.
Fetching lives in the worker scripts that write to a cache outside the repo (EARNPR1_CACHE, default ~/.cache/earnpr1).
The frozen last third (events closing from CUT) is never fetched or joined.
"""
from __future__ import annotations

import html
import re
from collections import defaultdict
from datetime import datetime

CUT = "2026-10-03T16:00:00Z"
MATCH_BEFORE_H, MATCH_AFTER_MIN = 72, 60   # a filing belongs to a call if accepted within 72h before to 60 minutes after the call start
LOOK_AFTER_FILING_MIN, LOOK_BEFORE_CALL_MIN = 10, 10
ASK_LO, ASK_HI = 0.03, 0.30
B_YES_BID_MIN = 0.70          # Arm B: NO ask = 1 - YES bid, so a NO ask of 30c or less means a YES bid of 70c or more
MODEL_MULT = 3.0
MAX_PER_EVENT = 2
CONTRACTS = 10
MIN_CELL = 5                   # FIT markets needed in a word's cell before the word's own rate is used
PRIOR_W = 2.0                  # shrinkage weight toward the pooled all-words rate of that cell
BAR_PF, MIN_TREATED, MIN_EVENTS = 1.5, 150, 60
MIN_LEAD_MEDIAN_MIN, MIN_QUOTE_SHARE = 20.0, 0.40


def ts(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def fee(p: float, m: float = 1.0) -> float:
    return m * 0.07 * p * (1 - p)


# ---------------------------------------------------------------- text matching (fixed rule)
def clean_text(raw: str) -> str:
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = html.unescape(t).lower().replace("’", "'").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t)


def word_alts(word: str) -> list[str]:
    """Alternatives of a Kalshi word: split on '/', lowercase, curly quote to straight, punctuation to a single space."""
    out = []
    for a in (word or "").lower().replace("’", "'").split("/"):
        a = re.sub(r"[^a-z0-9% ]+", " ", a)
        a = re.sub(r"\s+", " ", a).strip()
        if a:
            out.append(a)
    return out


def stem_of(word: str) -> str:
    """Pooling key: the first alternative, lowercased, one trailing 's' dropped when the word is longer than 3 letters."""
    a = word_alts(word)
    if not a:
        return ""
    s = a[0]
    return s[:-1] if len(s) > 3 and s.endswith("s") and not s.endswith("ss") else s


def in_release(word: str, text: str) -> bool:
    """True if any alternative occurs as a whole word or phrase (plural s/es or possessive 's allowed) in the cleaned text."""
    t = re.sub(r"[^a-z0-9% ]+", " ", text)
    t = re.sub(r"\s+", " ", t)
    for a in word_alts(word):
        base = a[:-1] if len(a) > 3 and a.endswith("s") and not a.endswith("ss") else a
        if re.search(r"(?<![a-z0-9])" + re.escape(base) + r"(?:s|es)?(?![a-z0-9])", t) or re.search(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])", t):
            return True
    return False


# ---------------------------------------------------------------- call time, filing match and look
def call_time(occ, earliest_close):
    """Call start used for the look. Kalshi's scheduled `occurrence_datetime` when the market carries one, taken as the earlier of
    it and the earliest market close (a word's market closes when it is said, so a close before the scheduled time means the
    schedule was wrong or the call began early); when no scheduled time is listed, the earliest market close in the event (the
    first word said, normally in the first minutes of the call). Returns (unix seconds, 'sched' | 'proxy')."""
    if occ is not None:
        return min(occ, earliest_close), "sched"
    return earliest_close, "proxy"


def match_filing(occ_ts: int, filings: list[tuple[str, str]]):
    """filings: (accession, acceptance 'YYYY-MM-DDTHH:MM:SS(.000)Z'). Latest acceptance within the window; None if none."""
    best = None
    for acc, at in filings:
        a = ts(at if at.endswith("Z") else at + "Z")
        if occ_ts - MATCH_BEFORE_H * 3600 <= a <= occ_ts + MATCH_AFTER_MIN * 60 and (best is None or a > best[1]):
            best = (acc, a)
    return best


def look_quote(candles, accept_ts: int, occ_ts: int):
    """candles: (end_ts, bid, ask) in dollars. The last two-sided quote whose end is at least 10 minutes after the filing and at
    least 10 minutes before the call. Returns (end_ts, bid, ask) or None."""
    lo, hi = accept_ts + LOOK_AFTER_FILING_MIN * 60, occ_ts - LOOK_BEFORE_CALL_MIN * 60
    ok = [c for c in candles if lo <= c[0] <= hi and c[1] is not None and c[2] is not None and 0 < c[1] < c[2] < 1]
    return ok[-1] if ok else None


# ---------------------------------------------------------------- model (FIT only)
def fit_model(fit_rows):
    """fit_rows: (stem, in_release_bool, yes_bool). Returns a function rate(stem, in_rel) = P(yes | cell), shrunk toward the
    pooled all-words rate of the same in_release cell with weight PRIOR_W; the pooled rate alone if the word's cell has fewer
    than MIN_CELL markets."""
    n = defaultdict(int); k = defaultdict(int); gn = defaultdict(int); gk = defaultdict(int)
    for s, r, y in fit_rows:
        n[(s, r)] += 1; k[(s, r)] += bool(y); gn[r] += 1; gk[r] += bool(y)

    def rate(stem, in_rel):
        g = (gk[in_rel] + 0.5) / (gn[in_rel] + 1.0)
        c = n.get((stem, in_rel), 0)
        if c < MIN_CELL:
            return g
        return (k[(stem, in_rel)] + PRIOR_W * g) / (c + PRIOR_W)
    return rate


# ---------------------------------------------------------------- scoring
def pf(xs):
    w = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return w / l if l else float("inf")


def trade_net(price: float, win: bool, m: float = 1.0) -> float:
    """Net per contract of buying one side at `price` (its ask) and holding to settlement, taker fee included."""
    return (1.0 if win else 0.0) - price - fee(price, m)


def cluster_z(rows):
    """rows: (cluster, value). Mean, z (clusters as units, one-sample against 0), number of clusters."""
    g = defaultdict(list)
    for c, v in rows:
        g[c].append(v)
    if len(g) < 2:
        return (sum(v for _, v in rows) / len(rows) if rows else 0.0), 0.0, len(g)
    n = len(rows); mean = sum(v for _, v in rows) / n
    s = sum((sum(vs) - mean * len(vs)) ** 2 for vs in g.values())
    se = (len(g) / (len(g) - 1) * s) ** 0.5 / n
    return mean, (mean / se if se else 0.0), len(g)


def verdict(treated, control, lead_median_min, quote_share, events):
    """treated/control: lists of dict(ev, net, st, half). Fixed kill rules from the registration."""
    if lead_median_min < MIN_LEAD_MEDIAN_MIN or quote_share < MIN_QUOTE_SHARE:
        return "NOT_RUNNABLE"
    if len(treated) < MIN_TREATED or events < MIN_EVENTS:
        return "NOT_ENOUGH_DATA"
    nets = [t["net"] for t in treated]
    h1 = [t["net"] for t in treated if t["half"] == 1]; h2 = [t["net"] for t in treated if t["half"] == 2]
    cm = sum(c["net"] for c in control) / len(control) if control else 0.0
    if pf(nets) < BAR_PF or sum(h1) <= 0 or sum(h2) <= 0 or sum(nets) / len(nets) <= cm:
        return "FALSIFIED"
    return "NOT_YET_FALSIFIED"
