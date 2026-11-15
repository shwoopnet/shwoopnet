"""CALIB3 per-bucket statistics (Desk A, Nov 15 2026), built to CALIB3_HAND_CASE_NOV15.md (committed first at 82aa1d014) and CALIB3_CARD_NOV15.md. PURE functions on invented or extracted rows; no file, network or clock. The loader (waits for Forensics' extract and the Head's go) is not here.
rows = [(event, ask, won)] for one bucket (one look, one side's 5c range) and one third."""
import math, collections
NB = 20; EPS = 1e-9; MIN_EVENTS = 60
def bucket(p): return min(NB - 1, int(math.floor(p * 20 + EPS)))
def fee1(p): return math.ceil(round(100 * 0.07 * p * (1 - p), 9)) / 100
def Phi(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def bucket_stats(rows):
    n = len(rows)
    if n == 0: return {"n": 0, "events": 0}
    wins = sum(1 for _, _, w in rows if w); mean_ask = sum(a for _, a, _ in rows) / n; w = wins / n
    by = collections.defaultdict(list)
    for e, a, won in rows: by[e].append((a, 1.0 if won else 0.0))
    s = [sum(won - a for a, won in v) for v in by.values()]; E = len(s)
    z = None
    if E >= 2:
        m = sum(s) / E; sd = math.sqrt(sum((x - m) ** 2 for x in s) / (E - 1))
        z = None if sd == 0 else m / (sd / math.sqrt(E))
    sd_null = math.sqrt(sum(ae * (1 - ae) for ae in (sum(a for a, _ in v) / len(v) for v in by.values()))) / E
    fee = sum(fee1(a) for _, a, _ in rows) / n
    return {"n": n, "wins": wins, "w": w, "mean_ask": mean_ask, "gap": w - mean_ask, "fee": fee, "events": E, "event_z": z, "sd_null": sd_null,
            "p_pass_third": 1 - Phi((fee + 0.02) / sd_null) if sd_null > 0 else None, "evidence": "ok" if E >= MIN_EVENTS else "no evidence (under %d events)" % MIN_EVENTS}
