"""ingame_events.py: scorer plugin for IGFADE2, IGLATEDRIFT1, IGDOG1 (History Miner, Nov 16, 2026). Hand case IGFWD_HAND_CASE_NOV16.md. Pure functions, no I/O.
event = ingame_fwd_load event. Upper bound, not fill-checked. Fee and PF match engine1_core's formulas (per-order rounded fee)."""
import calendar, collections, math, statistics, time
CONTRACTS = 10; HAIRCUTS = (0.01, 0.02); EPS = 1e-9
OK_MIN = ("00", "30", "05"); OK_MIN_NFL = OK_MIN + ("15", "20", "25")


def fee(p, c=CONTRACTS):
    return math.ceil(round(100 * 0.07 * c * p * (1 - p), 9)) / 100


def pf(xs):
    g = sum(x for x in xs if x > 0); l = -sum(x for x in xs if x < 0)
    return float("inf") if l == 0 else g / l


def day_z(pairs):
    d = collections.defaultdict(float)
    for k, x in pairs:
        d[k] += x
    v = list(d.values())
    if len(v) < 3:
        return None
    sd = statistics.stdev(v)
    return statistics.mean(v) / (sd / math.sqrt(len(v))) if sd else None


def two(b, a):
    return b is not None and a is not None and 0 < b < a < 1


def tip_of(ev):
    vals = set(ev["occ"].values())
    if len(vals) != 1:
        return None
    v = next(iter(vals))
    if not v or v[17:19] != "00" or v[14:16] not in (OK_MIN_NFL if ev["league"] == "NFL" else OK_MIN):
        return None
    return calendar.timegm(time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S")) - 3 * 3600


def quote_at(rows, mark, win=300):
    q = None
    for t, b, a in rows:
        if t > mark:
            break
        if t > mark - win:
            q = (b, a)
    return q if q and two(*q) else None


def fade2(ev):
    best = None
    for tk, rows in sorted(ev["rows"].items()):
        for (t1, b1, a1), (t2, b2, a2) in zip(rows, rows[1:]):
            if t2 - t1 > 60 or not two(b1, a1) or not two(b2, a2):
                continue
            d = (b2 + a2) / 2 - (b1 + a1) / 2
            if abs(d) < 0.10 - EPS:
                continue
            side, ask = ("no", round(1 - b2, 6)) if d > 0 else ("yes", a2)
            if 0.15 - EPS <= ask <= 0.60 + EPS and (best is None or t2 < best[3]):
                best = (tk, side, ask, t2)
    return ("ok", {"ticker": best[0], "side": best[1], "ask": best[2], "t": best[3]}) if best else ("no signal", None)


def latedrift(ev):
    if ev["kind"] == "spread":
        return "not in wall", None
    tip = tip_of(ev)
    if tip is None:
        return "schedule test failed", None
    tks = sorted(ev["rows"])[:1] if ev["kind"] == "ml" else sorted(ev["rows"])
    for tk in tks:
        q1, q2 = quote_at(ev["rows"][tk], tip + 5400), quote_at(ev["rows"][tk], tip + 7200)
        if not q1 or not q2:
            continue
        d = (q2[0] + q2[1]) / 2 - (q1[0] + q1[1]) / 2
        if abs(d) < 0.08 - EPS:
            return "no signal", None
        side, ask = ("yes", q2[1]) if d > 0 else ("no", round(1 - q2[0], 6))
        if 0.20 - EPS <= ask <= 0.80 + EPS:
            return "ok", {"ticker": tk, "side": side, "ask": ask, "t": tip + 7200}
        return "ask out of range", None
    return "no quote at a mark", None


def dog(ev):
    if ev["kind"] != "ml" or ev["league"] != "NHL":
        return "not in wall", None
    tip = tip_of(ev)
    if tip is None:
        return "schedule test failed", None
    hits = []
    for tk, rows in sorted(ev["rows"].items()):
        q = quote_at(rows, tip + 4500)
        if q and 0.15 - EPS <= q[1] <= 0.35 + EPS:
            hits.append((tk, q[1]))
    if len(hits) != 1:
        return "no single underdog", None
    return "ok", {"ticker": hits[0][0], "side": "yes", "ask": hits[0][1], "t": tip + 4500}


RULES = {"IGFADE2": fade2, "IGLATEDRIFT1": latedrift, "IGDOG1": dog}


def cash(ev, det, h):
    paid = min(det["ask"] + h, 0.99); f = fee(paid); r = ev["result"][det["ticker"]]
    if r == "void":
        return round(-f, 9)
    return round(CONTRACTS * (1 - paid) - f, 9) if r == det["side"] else round(-CONTRACTS * paid - f, 9)


def run(events, spec):
    skips = collections.Counter(); rows = {h: [] for h in HAIRCUTS}
    for ev in events:
        why, det = RULES[spec](ev)
        if why != "ok":
            skips[why] += 1; continue
        for h in HAIRCUTS:
            rows[h].append((det["t"], cash(ev, det, h)))
    out = {"spec": spec, "skips": dict(skips)}
    for h in HAIRCUTS:
        rs = sorted(rows[h]); xs = [x for _, x in rs]; half = len(xs) // 2
        out["h%d" % round(h * 100)] = {"n": len(xs), "pf": pf(xs) if xs else None, "half1": pf(xs[:half]) if half else None, "half2": pf(xs[half:]) if xs else None,
            "net": sum(xs), "day_z": day_z([(time.strftime("%Y-%m-%d", time.gmtime(t)), x) for t, x in rs]),
            "evidence": "ok" if len(xs) >= 100 else "no evidence at n = %d" % len(xs)}
    p2 = out["h2"]["pf"]
    out["kill_fast"] = p2 is not None and p2 < 1.0
    return out
