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


# ---------------------------------------------------------------- the one scored read (run once, after the registration push)
def score(cache, markets_path, candle_files, result_path):
    import glob, json, os
    if os.path.exists(result_path):
        raise SystemExit(f"Refusing to run again: {result_path} exists.")
    ev = json.load(open(os.path.join(cache, "events.json")))
    rows = json.load(open(os.path.join(cache, "census_rows.json")))
    texts = json.load(open(os.path.join(cache, "texts.json")))
    res = {m["t"]: m["res"] for m in json.load(open(markets_path)).values()}
    cd = {}
    for f in sorted(glob.glob(candle_files)):
        cd.update(json.load(open(f)))
    ok = sorted((r for r in rows if r.get("has_text") and r["close"] < CUT), key=lambda r: r["occ"])
    k = len(ok) * 2 // 3
    fit, test = ok[:k], ok[k:]
    fit_rows = []
    for r in fit:
        for m in ev[r["ev"]]:
            if m["word"] and m["t"] in res:
                fit_rows.append((stem_of(m["word"]), in_release(m["word"], texts[r["acc"]]), res[m["t"]] == "yes"))
    rate = fit_model(fit_rows)

    def side_rows(rs):
        out = []  # per market: dict(ev, t, stem, inrel, bid, ask, yes, kind)
        for r in rs:
            for m in ev[r["ev"]]:
                if not m["word"] or m["t"] not in res:
                    continue
                q = look_quote(cd.get(m["t"]) or [], r["acc_ts"], r["occ"])
                if not q:
                    continue
                out.append(dict(ev=r["ev"], t=m["t"], stem=stem_of(m["word"]), inrel=in_release(m["word"], texts[r["acc"]]), bid=q[1], ask=q[2], yes=res[m["t"]] == "yes", kind=r["kind"], occ=r["occ"]))
        return out

    def trades(rows_, arm=None):
        """arm 'A'/'B' treated; arm 'cA'/'cB' control (cheap side, no text condition)."""
        out = []
        by = defaultdict(list)
        for x in rows_:
            if arm in ("A", "cA") and ASK_LO <= x["ask"] <= ASK_HI:
                price, win, mod = x["ask"], x["yes"], rate(x["stem"], True)
                if arm == "A" and (not x["inrel"] or mod < MODEL_MULT * price):
                    continue
            elif arm in ("B", "cB") and ASK_LO <= 1 - x["bid"] <= ASK_HI and x["bid"] >= B_YES_BID_MIN:
                price, win, mod = 1 - x["bid"], not x["yes"], 1 - rate(x["stem"], False)
                if arm == "B" and (x["inrel"] or mod < MODEL_MULT * price):
                    continue
            else:
                continue
            by[x["ev"]].append((mod / price, dict(ev=x["ev"], t=x["t"], net=trade_net(price, win), st=trade_net(price, win, 1.2), price=price, win=win, kind=x["kind"], occ=x["occ"])))
        for lst in by.values():
            lst.sort(key=lambda z: -z[0])
            out += [z[1] for z in (lst[:MAX_PER_EVENT] if arm in ("A", "B") else lst)]
        return out

    T = side_rows(test)
    F = side_rows(fit)
    med = sorted(r["occ"] for r in test)[len(test) // 2]
    lead = sorted(r["lead_min"] for r in ok)[len(ok) // 2]
    qshare = sum(1 for r in ok if any(look_quote(cd.get(m["t"]) or [], r["acc_ts"], r["occ"]) for m in ev[r["ev"]])) / len(ok)
    lines = [f"EARNPR1 scored once. FIT events {len(fit)}, TEST events {len(test)}, TEST markets with a look quote {len(T)}, events with any look quote {qshare:.3f} (all text-matched), lead median {lead:.1f} min"]
    summary = {}
    for arm, ctl in (("A", "cA"), ("B", "cB")):
        for tag, rows_ in (("TEST", T), ("FIT_in_sample", F)):
            tr = trades(rows_, arm); cn = trades(rows_, ctl)
            for t_ in tr + cn:
                t_["half"] = 1 if t_["occ"] < med else 2
            nets = [t_["net"] for t_ in tr]
            if not tr:
                lines.append(f"Arm {arm} {tag}: 0 treated, control {len(cn)}"); summary[(arm, tag)] = None; continue
            m_, z, ncl = cluster_z([(t_["ev"], t_["net"]) for t_ in tr])
            cm_, cz, cncl = cluster_z([(t_["ev"], t_["net"]) for t_ in cn]) if cn else (0.0, 0.0, 0)
            h = {i: [t_["net"] for t_ in tr if t_["half"] == i] for i in (1, 2)}
            win = sum(t_["win"] for t_ in tr) / len(tr); ap = sum(t_["price"] for t_ in tr) / len(tr)
            cw = sum(t_["win"] for t_ in cn) / len(cn) if cn else 0; cp = sum(t_["price"] for t_ in cn) / len(cn) if cn else 0
            sch = [t_["net"] for t_ in tr if t_["kind"] == "sched"]; prx = [t_["net"] for t_ in tr if t_["kind"] == "proxy"]
            v = verdict(tr, cn, lead, qshare, len({t_["ev"] for t_ in tr}) if tag == "TEST" else 0) if tag == "TEST" else "info only"
            lines.append(f"Arm {arm} {tag}: treated {len(tr)} on {ncl} events, win {win:.3f} at mean price {ap:.3f}, mean net {m_*100:+.2f}c (z {z:+.2f}), PF {pf(nets):.2f}, PF x1.2 fees {pf([t_['st'] for t_ in tr]):.2f}, halves D1 {sum(h[1])*10:+.2f}$ ({len(h[1])}) D2 {sum(h[2])*10:+.2f}$ ({len(h[2])}), sched {len(sch)} PF {pf(sch) if sch else 0:.2f} proxy {len(prx)} PF {pf(prx) if prx else 0:.2f} | control {len(cn)} on {cncl} events, win {cw:.3f} at {cp:.3f}, mean {cm_*100:+.2f}c, PF {pf([t_['net'] for t_ in cn]) if cn else 0:.2f} | treated minus control {100*(m_-cm_):+.2f}c | verdict {v}")
            summary[(arm, tag)] = v
    open(result_path, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    import os
    from .paths import DATA_DIR
    score(os.environ.get("EARNPR1_CACHE", os.path.expanduser("~/.cache/earnpr1")), str(DATA_DIR / "ment1" / "markets.json"), str(DATA_DIR / "ment1" / "candles_*.json"), str(DATA_DIR / "earnpr1_result.txt"))
