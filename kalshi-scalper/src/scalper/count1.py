"""COUNT1: Truth Social post-count brackets against a pace model (see workers/COUNT1_REGISTRATION.md).
Usage: python -m scalper.count1 fetch | run   (cache outside the repo; holdout candles are never fetched)."""
from __future__ import annotations
import json, math, os, re, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from . import api
from .candlefield import quote_close

ET = ZoneInfo("America/New_York")
CACHE = Path(os.environ.get("COUNT1_CACHE", "/tmp/count1_cache")); CACHE.mkdir(parents=True, exist_ok=True)
SERIES = {"KXTRUTHSOCIAL": ("W", 84.0), "KXTRUTHSOCIALD": ("D", 12.0)}
R_DISP, RATIO, HARD, LOW, MAXPER = 10.0, 3.0, 0.30, 0.03, 2
ARCHIVE = "https://ix.cnn.io/data/truth-social/truth_archive.json"


def fee(p, C=10):
    return math.ceil(round(0.07 * C * p * (1 - p) * 100, 9)) / 100 / C


def nb_pmf(mu, r, kmax):
    """Negative binomial pmf 0..kmax with mean mu, variance mu + mu^2/r (Poisson-free: mu 0 gives a point mass)."""
    if mu <= 1e-12:
        return [1.0] + [0.0] * kmax
    p = r / (r + mu)
    out = []
    for k in range(kmax + 1):
        out.append(math.exp(math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1) + r * math.log(p) + k * math.log1p(-p)))
    return out


def bracket_prob(m, c, pmf):
    """P(total in bracket) with total = c + R; strike semantics fixed in the registration."""
    t = m["strike_type"]; lo = m.get("floor_strike"); hi = m.get("cap_strike")
    def ok(n):
        if t == "between": return lo <= n <= hi
        if t == "less": return n < hi
        if t == "greater": return n > lo
        if t == "greater_or_equal": return n >= lo
        return False
    return sum(q for k, q in enumerate(pmf) if ok(c + k))


def parse_period(m):
    s = (m.get("rules_primary") or "") + " " + (m.get("rules_secondary") or "")
    a = re.search(r"begins at ([\d:]+ [AP]M) ET on (\w+ \d+, \d{4}) and ends at ([\d:]+ [AP]M) ET on (\w+ \d+, \d{4})", s)
    if not a: return None
    d0 = datetime.strptime(a.group(2), "%b %d, %Y").replace(tzinfo=ET)
    d1 = datetime.strptime(a.group(4), "%b %d, %Y").replace(tzinfo=ET) + timedelta(days=1)
    return d0.astimezone(timezone.utc), d1.astimezone(timezone.utc)


def et_midnights(start, days):
    d = start.astimezone(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    return d


def profile(posts, start):
    """Mean posts per hour for ET hour 0..23 over the 28 full ET days before `start` (posts: sorted UTC datetimes)."""
    s0 = start.astimezone(ET).replace(hour=0, minute=0, second=0, microsecond=0)
    lo = (s0 - timedelta(days=28)).astimezone(timezone.utc); hi = s0.astimezone(timezone.utc)
    cnt = [0] * 24
    for t in posts:
        if lo <= t < hi: cnt[t.astimezone(ET).hour] += 1
    return [c / 28.0 for c in cnt]


def expected(prof, a, b):
    """Sum of profile over [a, b) UTC, pro rata for partial ET hours."""
    tot = 0.0; t = a
    while t < b:
        loc = t.astimezone(ET)
        nxt = min(b, (loc.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).astimezone(timezone.utc))
        if nxt <= t: nxt = t + timedelta(minutes=1)
        tot += prof[loc.hour] * (nxt - t).total_seconds() / 3600.0
        t = nxt
    return tot


def model(posts, start, end, look_h, r=R_DISP):
    look = start + timedelta(hours=look_h)
    c = sum(1 for t in posts if start <= t <= look - timedelta(minutes=10))
    prof = profile(posts, start)
    es, er = expected(prof, start, look), expected(prof, look, end)
    rho = min(2.0, max(0.5, (c + 10) / (es + 10)))
    mu = er * rho
    return look, c, mu, nb_pmf(mu, r, int(mu * 6 + 80))


def load_posts():
    p = CACHE / "truth.json"
    if not p.exists():
        os.system(f"curl -sS -m 120 -A Mozilla/5.0 -o {p} {ARCHIVE}")
    d = json.loads(p.read_text())
    return sorted(datetime.fromisoformat(x["created_at"].replace("Z", "+00:00")) for x in d)


def split_events(markets):
    ev = {}
    for m in markets:
        ev.setdefault(m["event_ticker"], []).append(m)
    keyed = []
    for e, L in ev.items():
        per = parse_period(L[0])
        if per: keyed.append((per[0], e, L, per))
    keyed.sort(key=lambda x: x[0])
    n = len(keyed); k = (2 * n) // 3
    return keyed[:k], keyed[k:]


def fetch():
    allm = json.loads((Path(os.environ.get("COUNT1_MARKETS", CACHE / "count_all.json"))).read_text())
    for t in SERIES:
        dev, hold = split_events(allm[t])
        print(t, "dev", len(dev), "holdout", len(hold), flush=True)
        cp = CACHE / f"candles_{t}.json"
        have = json.loads(cp.read_text()) if cp.exists() else {}
        for _, e, L, per in dev:
            look = per[0] + timedelta(hours=SERIES[t][1])
            for m in L:
                tk = m["ticker"]
                if tk in have: continue
                src = "/historical/markets/%s/candlesticks" % tk if m["close_time"] < "2026-09-04" else "/series/%s/markets/%s/candlesticks" % (t, tk)
                a, b = int((look - timedelta(minutes=60)).timestamp()), int((look + timedelta(minutes=15)).timestamp())
                try:
                    d = api._get(src, {"start_ts": a, "end_ts": b, "period_interval": 1})
                    have[tk] = [(c["end_period_ts"], quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
                except Exception as ex:
                    have[tk] = None
                time.sleep(0.4)
            cp.write_text(json.dumps(have))
    print("fetched", flush=True)


def fill_ask(cand, look):
    """(signal ask, fill ask) per the registration; None when no valid quote."""
    lt = int(look.timestamp())
    sig = [c for c in cand if c[0] <= lt and c[1] is not None and lt - c[0] <= 3600]
    fil = [c for c in cand if lt < c[0] <= lt + 900 and c[1] is not None]
    if not sig or not fil: return None
    return sig[-1][1], fil[0][1]


def select(rows):
    """rows: [(ticker, p_model, ask)] -> up to 2 by p/ask meeting the rule."""
    ok = [r for r in rows if LOW <= r[2] <= HARD and r[1] >= RATIO * r[2]]
    ok.sort(key=lambda r: -r[1] / r[2])
    return ok[:MAXPER]


def stats(ts):
    if not ts: return {"n": 0}
    wins = [x for x in ts if x > 0]; loss = [-x for x in ts if x <= 0]
    return {"n": len(ts), "mean": sum(ts) / len(ts), "win": len(wins) / len(ts), "pf": (sum(wins) / sum(loss)) if loss else float("inf")}


def run():
    out = CACHE / "count1_result.json"
    if out.exists() and not os.environ.get("COUNT1_RERUN"):
        print("Refusing to run again:", out); return
    allm = json.loads((CACHE / "count_all.json").read_text()); posts = load_posts()
    res = {}; lines = []
    for t, (kind, lh) in SERIES.items():
        cand = json.loads((CACHE / f"candles_{t}.json").read_text())
        dev, hold = split_events(allm[t])
        trades, ctrl, hit, skip, src = [], [], 0, 0, []
        for idx, (_, e, L, per) in enumerate(dev):
            look, c, mu, pmf = model(posts, per[0], per[1], lh)
            half = 0 if idx < len(dev) // 2 else 1
            rows = []
            for m in L:
                q = fill_ask(cand.get(m["ticker"]) or [], look)
                if not q: skip += 1; continue
                ask = q[1]
                pm = bracket_prob(m, c, pmf)
                pay = 1.0 if m["result"] == "yes" else 0.0
                rows.append((m["ticker"], pm, ask, pay))
                if LOW <= ask <= HARD: ctrl.append((half, pay - ask - fee(ask)))
            for tk, pm, ask, pay in select([(r[0], r[1], r[2]) for r in rows]):
                p = [r for r in rows if r[0] == tk][0][3]
                trades.append((half, p - ask - fee(ask), tk, pm, ask))
            # source check: archive full-period total vs winning bracket
            tot = sum(1 for x in posts if per[0] <= x < per[1])
            win = [m for m in L if m["result"] == "yes"]
            if win: src.append(bracket_prob(win[0], tot, [1.0]) > 0)
        s = {"kind": kind, "dev_events": len(dev), "holdout_events": len(hold), "skipped_markets": skip,
             "rule": stats([x[1] for x in trades]), "rule_h1": stats([x[1] for x in trades if x[0] == 0]), "rule_h2": stats([x[1] for x in trades if x[0] == 1]),
             "control": stats([x[1] for x in ctrl]), "source_ok": (sum(src) / len(src)) if src else None, "source_n": len(src),
             "trades": [(x[2], round(x[3], 3), x[4], round(x[1], 3)) for x in trades]}
        res[t] = s
        lines.append(f"{t}: {json.dumps({k: v for k, v in s.items() if k != 'trades'})}")
    out.write_text(json.dumps(res)); print("\n".join(lines))


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
