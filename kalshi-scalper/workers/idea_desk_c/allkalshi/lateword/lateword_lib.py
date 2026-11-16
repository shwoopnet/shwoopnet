#!/usr/bin/env python3
"""LATEWORD shared code (Idea Desk C, Nov 16, 2026). Standard library only, no network. Card: LATEWORD_CARD.md.
A Trump mention word that Kalshi lists hours after the rest of the event's words was added for a reason (a topic in the news).
At D = O - 60 min, buy YES on each such word whose YES ask is 0.30 to 0.70; hold to settlement."""
import calendar, gzip, json, math, os, time

SERIES = ("KXTRUMPMENTION", "KXTRUMPMENTIONB")
DEV = ("2026-04-17T00:00:00", "2026-08-06T00:00:00")     # event occurrence window (own occurrence of each market)
LATE_H = 6                                               # opened at least 6 h after the event's first market
D_MIN = 60
BAND = (0.30, 0.70)
LOOKBACK_S = 180
EPS = 1e-9
LIST_JOB = "MENTDRIFT_LISTS_A"


def iso(s):
    s = (s or "").split(".")[0].rstrip("Z")
    try:
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def _bodies(root, job):
    base = os.path.join(root, "pull", job)
    for run in sorted(os.listdir(base)):
        with open(os.path.join(base, run, "manifest.json")) as fh:
            man = json.load(fh)
        for r in man["rows"]:
            fn = r.get("file")
            if not fn or os.path.basename(fn) != fn:
                continue
            with gzip.open(os.path.join(base, run, fn), "rt") as fh:
                b = json.load(fh)
            if isinstance(b, dict):
                yield r, b


def truncated(root):
    last = {}
    for r, b in _bodies(root, LIST_JOB):
        if "markets" in b:
            last[r.get("id")] = b.get("cursor") or ""
    return sorted(k for k, v in last.items() if v)


def list_rows(root):
    """(ticker, event, open, occurrence, close) for dev markets. The market's OWN occurrence is tested first; then open and close;
    then the word title for the 'Event does not qualify' drop. No price, volume or result."""
    lo, hi = iso(DEV[0]), iso(DEV[1])
    out = []
    for _r, b in _bodies(root, LIST_JOB):
        for m in b.get("markets") or []:
            o = iso(m.get("occurrence_datetime"))
            if o is None or not (lo <= o < hi):
                continue
            t = m.get("ticker") or ""
            if t.split("-")[0] not in SERIES:
                continue
            op, c = iso(m.get("open_time")), iso(m.get("close_time"))
            if op is None or c is None:
                continue
            if "does not qualify" in ((m.get("yes_sub_title") or "") + " " + (m.get("title") or "")).lower():
                continue
            out.append((t, m.get("event_ticker") or "", op, o, c))
    return out


def late_words(rows):
    """ticker -> dict(D, event, close). A word is late if opened >= LATE_H after the event's first market and before D."""
    ev = {}
    for x in rows:
        ev.setdefault(x[1], []).append(x)
    out = {}
    for e, L in sorted(ev.items()):
        first = min(x[2] for x in L)
        O = min(x[3] for x in L)
        D = O - D_MIN * 60
        for t, _e, op, _o, c in L:
            if op - first >= LATE_H * 3600 and op < D and c > D:
                out[t] = {"D": D, "event": e, "close": c}
    return out


def fee(p):
    return math.ceil(0.07 * p * (1 - p) * 100 - EPS) / 100
