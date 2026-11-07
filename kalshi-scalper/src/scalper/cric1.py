"""CRICT20 (workers/CRICT20_REGISTRATION.md): the CHEAP side (ask 3c to 30c) of Kalshi cricket match winners (KXT20MATCH, KXODIMATCH) against a
walk-forward player-and-team Elo from Cricsheet, using only what is known at the toss. Research only; nothing here places an order and nothing means trade.
Cheap side only: no favourite-side result is computed or printed.

    python3 -I src/scalper/cric1.py census   (listings and names: events, start times, Cricsheet matches; no candle, no outcome)
    python3 -I src/scalper/cric1.py fit      (Cricsheet matches only, 2024-01-01 to 2025-12-31: kt, w, b)
    python3 -I src/scalper/cric1.py fetch    (resumable; 1 minute candles of the registered universe, before the frozen cut; stops on repeated rate limits)
    python3 -I src/scalper/cric1.py run      (the one scored read; refused a second time)
Directory: CRIC1_DIR (default /tmp/cric1); Cricsheet files in CRIC1_DIR/all (unzipped all_json.zip).
"""
from __future__ import annotations

import collections
import glob
import json
import math
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

CUT = "2026-10-03T16:00"            # frozen last third: closes from here are never listed, fetched or joined
HIST_CUTOFF = "2026-09-07"         # markets closing before this live on the historical endpoint
SERIES = ("KXT20MATCH", "KXODIMATCH")
POOL = {"T20": "T20", "IT20": "T20", "ODI": "ODI", "ODM": "ODI"}
SERIES_POOL = {"KXT20MATCH": "T20", "KXODIMATCH": "ODI"}
ASK_LO, ASK_HI, RATIO, C = 0.03, 0.30, 3.0, 10
LOOK_S, STALE_S = 1800, 10800
BAR_PF, MIN_TRADES, Z_BAR = 1.5, 150, 5.3
MIN_PRIOR = 5
FIT_FROM, FIT_TO = "2024-01-01", "2025-12-31"
D = Path(os.environ.get("CRIC1_DIR", "/tmp/cric1"))
NY = ZoneInfo("America/New_York")
EVT = re.compile(r"-(\d{2}[A-Z]{3}\d{2})(\d{4})?")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\b(cricket|club|cc|and|athletic|sports|sc|the)\b", " ", s)
    return " ".join(s.split())


def fee(p, c=C):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


# ---------------------------------------------------------------- Cricsheet and the rating
def load_cricsheet(root=None):
    out = []
    for f in sorted(glob.glob(str((root or D / "all") / "*.json"))):
        d = json.load(open(f))
        i = d["info"]
        pool = POOL.get(i.get("match_type"))
        if not pool or len(i.get("teams", [])) != 2:
            continue
        reg = i.get("registry", {}).get("people", {})
        a, b = i["teams"]
        pl = i.get("players", {})
        win = (i.get("outcome") or {}).get("winner")
        out.append(dict(id=os.path.basename(f)[:-5], date=i["dates"][0], pool=pool, gender=i.get("gender", ""), teams=(a, b),
                        xi=([reg.get(n, n) for n in pl.get(a, [])], [reg.get(n, n) for n in pl.get(b, [])]),
                        toss=(i.get("toss") or {}).get("winner"), winner=win, ev=(i.get("event") or {}).get("name", "")))
    out.sort(key=lambda m: (m["date"], m["id"]))
    return out


class Engine:
    """Walk-forward team and player Elo. Ratings move only through update(); predict() reads them."""

    def __init__(self, kt=1.0, w=0.5, b=0.0):
        self.kt, self.w, self.b = kt, w, b
        self.rt, self.nt, self.rp, self.np = {}, collections.Counter(), {}, collections.Counter()

    def _tk(self, m, s):
        return (m["pool"], m["gender"], m["teams"][s])

    def strength(self, m, s):
        rt = self.rt.get(self._tk(m, s), 1500.0)
        xi = m["xi"][s]
        if xi and self.w > 0:
            rp = sum(self.rp.get((m["pool"], pid), rt) for pid in xi) / len(xi)
        else:
            rp = rt
        return (1 - self.w) * rt + self.w * rp

    def ready(self, m):
        return all(self.nt[self._tk(m, s)] >= MIN_PRIOR for s in (0, 1))

    def p0(self, m):
        return 1.0 / (1.0 + 10 ** ((self.strength(m, 1) - self.strength(m, 0)) / 400.0))

    def predict(self, m):
        """Probability that teams[0] wins, with the toss term (+1 if teams[0] won the toss, -1 if teams[1], else 0)."""
        p = min(max(self.p0(m), 1e-6), 1 - 1e-6)
        sign = 1 if m["toss"] == m["teams"][0] else -1 if m["toss"] == m["teams"][1] else 0
        z = math.log(p / (1 - p)) + self.b * sign
        return 1.0 / (1.0 + math.exp(-z))

    def update(self, m):
        if m["winner"] not in m["teams"]:
            return
        p0 = self.p0(m)
        res = (1.0 if m["winner"] == m["teams"][0] else 0.0, 1.0 if m["winner"] == m["teams"][1] else 0.0)
        pp = (p0, 1 - p0)
        for s in (0, 1):
            k = self._tk(m, s)
            rt = self.rt.get(k, 1500.0)
            for pid in m["xi"][s]:
                key = (m["pool"], pid)
                r0 = self.rp.get(key, rt)
                self.rp[key] = r0 + 20 * self.kt / (self.np[key] + 5) ** 0.4 * (res[s] - pp[s])
                self.np[key] += 1
        for s in (0, 1):
            k = self._tk(m, s)
            self.rt[k] = self.rt.get(k, 1500.0) + 250 * self.kt / (self.nt[k] + 5) ** 0.4 * (res[s] - pp[s])
            self.nt[k] += 1


def walk(matches, eng, want=None):
    """Advance date by date: every match of a date is predicted before any match of that date updates the ratings. want(m) -> bool picks matches to record."""
    rec = []
    i, n = 0, len(matches)
    while i < n:
        j = i
        while j < n and matches[j]["date"] == matches[i]["date"]:
            j += 1
        grp = matches[i:j]
        for m in grp:
            if want and want(m):
                rec.append((m, eng.ready(m), eng.p0(m), eng.predict(m)))
        for m in grp:
            eng.update(m)
        i = j
    return rec


def fit():
    cs = [m for m in load_cricsheet() if m["pool"] == "T20"]
    best, table = None, []
    for kt in (0.5, 1.0, 2.0):
        for w in (0.0, 0.5, 1.0):
            rec = walk(cs, Engine(kt, w, 0.0), lambda m: FIT_FROM <= m["date"] <= FIT_TO and m["winner"] in m["teams"])
            rec = [r for r in rec if r[1]]
            ll = 0.0
            for m, _, p0, _ in rec:
                y = 1.0 if m["winner"] == m["teams"][0] else 0.0
                p = min(max(p0, 1e-6), 1 - 1e-6)
                ll -= y * math.log(p) + (1 - y) * math.log(1 - p)
            table.append((kt, w, ll / len(rec), len(rec)))
            if best is None or ll / len(rec) < best[2]:
                best = (kt, w, ll / len(rec), len(rec))
    kt, w = best[0], best[1]
    rec = [r for r in walk(cs, Engine(kt, w, 0.0), lambda m: FIT_FROM <= m["date"] <= FIT_TO and m["winner"] in m["teams"]) if r[1]]
    # no-intercept logistic regression of the outcome on the toss sign with the model logit as offset (Newton steps)
    b = 0.0
    for _ in range(25):
        g = h = 0.0
        for m, _, p0, _ in rec:
            sign = 1 if m["toss"] == m["teams"][0] else -1 if m["toss"] == m["teams"][1] else 0
            if not sign:
                continue
            p0 = min(max(p0, 1e-6), 1 - 1e-6)
            p = 1 / (1 + math.exp(-(math.log(p0 / (1 - p0)) + b * sign)))
            y = 1.0 if m["winner"] == m["teams"][0] else 0.0
            g += (y - p) * sign
            h += p * (1 - p)
        if h == 0:
            break
        b += g / h
    b = max(-0.15, min(0.15, b))
    out = dict(kt=kt, w=w, b=b, n=best[3], logloss=best[2], grid=table, coin_logloss=math.log(2))
    (D / "params.json").parent.mkdir(parents=True, exist_ok=True)
    (D / "params.json").write_text(json.dumps(out))
    print(json.dumps(out, indent=1))
    return out


# ---------------------------------------------------------------- Kalshi listings and the universe
FIELDS = ("ticker", "event_ticker", "close_time", "open_time", "yes_sub_title")


def list_markets(with_result):
    from scalper import api
    out = {}
    for s in SERIES:
        for path, live in (("/historical/markets", False), ("/markets", True)):
            cur = None
            while True:
                p = {"series_ticker": s, "limit": 1000}
                if live:
                    p["status"] = "settled"
                if cur:
                    p["cursor"] = cur
                d = api._get(path, p)
                for m in d.get("markets", []):
                    if (m.get("close_time") or "") < CUT + ":00Z" and m.get("result") in ("yes", "no"):
                        row = {k: m.get(k) for k in FIELDS} | {"series": s, "src": "live" if live else "hist"}
                        if with_result:
                            row["result"] = m["result"]
                        out[m["ticker"]] = row
                cur = d.get("cursor")
                time.sleep(1.3)
                if not cur or not d.get("markets"):
                    break
    return out


def event_start(ev):
    m = EVT.search(ev)
    if not m:
        return None, None
    day = datetime.strptime(m.group(1), "%y%b%d").date()
    if not m.group(2):
        return day, None
    st = datetime.strptime(m.group(1) + m.group(2), "%y%b%d%H%M").replace(tzinfo=NY)
    return day, int(st.timestamp())


def build_universe(markets, cs, params, counts=None):
    """One row per Kalshi event matched to exactly one Cricsheet match, both teams ready: first market, start unix, p of each market."""
    counts = counts if counts is not None else collections.Counter()
    byev = collections.defaultdict(dict)
    for tk, m in markets.items():
        byev[m["event_ticker"]][tk] = m
    idx = collections.defaultdict(list)
    for m in cs:
        idx[(m["pool"], frozenset(norm(t) for t in m["teams"]))].append(m)
    eng = Engine(params["kt"], params["w"], params["b"])
    wanted = {}
    work = []
    for ev, mk in byev.items():
        counts["events"] += 1
        if len(mk) != 2:
            counts["not two markets"] += 1
            continue
        day, start = event_start(ev)
        if start is None:
            counts["no start time in ticker"] += 1
            continue
        first = sorted(mk)[0]
        names = {tk: norm(m["yes_sub_title"]) for tk, m in mk.items()}
        c = [m for m in idx.get((SERIES_POOL[mk[first]["series"]], frozenset(names.values())), [])]
        utc = datetime.fromtimestamp(start, timezone.utc).date()
        c = [(abs((datetime.strptime(m["date"], "%Y-%m-%d").date() - utc).days), m) for m in c]
        c = [x for x in c if x[0] <= 2]
        if not c:
            counts["no Cricsheet match"] += 1
            continue
        c.sort(key=lambda x: x[0])
        if len(c) > 1 and c[0][0] == c[1][0]:
            counts["ambiguous (dropped)"] += 1
            continue
        work.append((c[0][1], ev, mk, names, first, start))
        wanted[c[0][1]["id"]] = (ev, mk, names, first, start)
    uni = {}
    cs_by_id = {m["id"]: m for m in cs}
    rec = walk(cs, eng, lambda m: m["id"] in wanted)
    for m, ready, p0, p in rec:
        ev, mk, names, first, start = wanted[m["id"]]
        if not ready:
            counts["team not ready"] += 1
            continue
        t0 = norm(m["teams"][0])
        pf = p if names[first] == t0 else 1 - p
        if names[first] not in (t0, norm(m["teams"][1])):
            counts["name mismatch"] += 1
            continue
        other = [t for t in mk if t != first][0]
        uni[ev] = dict(event=ev, series=mk[first]["series"], src=mk[first]["src"], first=first, other=other, start=start,
                       startiso=datetime.fromtimestamp(start, timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), gender=m["gender"], cs=m["id"],
                       p={first: pf, other: 1 - pf}, p_no_toss={first: None})
        counts["rated"] += 1
    return uni


def census():
    D.mkdir(parents=True, exist_ok=True)
    mp = D / "markets.json"
    if not mp.exists():
        mp.write_text(json.dumps(list_markets(False)))
    markets = json.loads(mp.read_text())
    params = json.loads((D / "params.json").read_text())
    cnt = collections.Counter()
    uni = build_universe(markets, load_cricsheet(), params, cnt)
    (D / "universe.json").write_text(json.dumps(uni))
    print(dict(cnt))
    by = collections.Counter(u["series"] for u in uni.values())
    print("rated events by series", dict(by))


def fetch():
    from scalper import api
    from scalper.candlefield import quote_close
    uni = json.loads((D / "universe.json").read_text())
    cp = D / "candles.json"
    have = json.loads(cp.read_text()) if cp.exists() else {}
    todo = [e for e in sorted(uni, key=lambda e: uni[e]["start"]) if e not in have]
    print(len(uni), "events;", len(todo), "to fetch", flush=True)
    bad = 0
    for i, ev in enumerate(todo):
        u = uni[ev]
        path = f"/historical/markets/{u['first']}/candlesticks" if u["src"] == "hist" else f"/series/{u['series']}/markets/{u['first']}/candlesticks"
        try:
            d = api._get(path, {"start_ts": u["start"] - STALE_S - 120, "end_ts": u["start"] - LOOK_S + 60, "period_interval": 1})
            have[ev] = [(c["end_period_ts"], quote_close(c.get("yes_bid")), quote_close(c.get("yes_ask"))) for c in d.get("candlesticks", [])]
            bad = 0
        except Exception as e:  # noqa
            bad += 1
            print("fail", ev, str(e)[:80], flush=True)
            if bad >= 3:
                print("three failures in a row (rate limit): stopping, rerun later", flush=True)
                break
        if i % 25 == 0:
            cp.write_text(json.dumps(have))
        time.sleep(3.3)
    cp.write_text(json.dumps(have))
    print("have", len(have), "of", len(uni), flush=True)


def look(candles, start):
    """Last candle ending at or before start - 30 min and no earlier than start - 3 h with a valid two sided quote: (age_s, yes_bid, yes_ask) or None."""
    best = None
    for end, b, a in candles:
        if start - STALE_S <= end <= start - LOOK_S and b is not None and a is not None and 0 < b < a < 1:
            if best is None or end > best[0]:
                best = (end, b, a)
    return (start - best[0], best[1], best[2]) if best else None


def net_cents(ask, win):
    f = fee(ask)
    return ((C * (1 - ask) if win else -C * ask) - f) / C * 100, ((C * (1 - ask) if win else -C * ask) - 1.2 * f) / C * 100


def build_rows(uni, candles, results):
    """Cheap-side rows. results maps ticker -> 'yes'|'no' (None until the scored read)."""
    rows, c = [], collections.Counter()
    for ev, u in uni.items():
        q = look(candles[ev], u["start"]) if ev in candles else None
        if q is None:
            c["no quote at the look"] += 1
            continue
        c["quoted"] += 1
        _, b, a = q
        sides = [("yes", a, u["first"]), ("no", 1 - b, u["other"])]
        sides = [s for s in sides if ASK_LO <= s[1] <= ASK_HI]
        if not sides:
            c["no cheap side"] += 1
            continue
        side, ask, mk = min(sides, key=lambda s: s[1])
        p = u["p"][u["first"]] if side == "yes" else 1 - u["p"][u["first"]]
        win = None
        if results is not None:
            r = results[u["first"]]
            win = (r == "yes") == (side == "yes")
        rows.append(dict(event=ev, series=u["series"], start=u["start"], side=side, ask=ask, p=p, treated=p >= RATIO * ask and ask <= ASK_HI, win=win))
    return rows, c


def stats(rows):
    nets = [net_cents(r["ask"], r["win"]) for r in rows]
    n = len(nets)
    if n == 0:
        return dict(n=0)
    m = sum(x[0] for x in nets) / n
    sd = (sum((x[0] - m) ** 2 for x in nets) / (n - 1)) ** 0.5 if n > 1 else float("nan")
    def pf(idx):
        gain = loss = 0.0
        for r in rows:
            f = fee(r["ask"]) * (1.2 if idx else 1.0)
            pnl = (C * (1 - r["ask"]) if r["win"] else -C * r["ask"]) - f
            if pnl > 0:
                gain += pnl
            else:
                loss -= pnl
        return gain / loss if loss else float("inf")
    return dict(n=n, wins=sum(1 for r in rows if r["win"]), win=sum(1 for r in rows if r["win"]) / n, ask=sum(r["ask"] for r in rows) / n * 100,
                net=m, pf=pf(0), pf12=pf(1), z=(m / (sd / n ** 0.5)) if sd and sd == sd and sd > 0 else float("nan"))


def fmt(name, s):
    if not s.get("n"):
        return f"| {name} | 0 | | | | | | |"
    return f"| {name} | {s['n']} | {s['win']*100:.1f}% ({s['wins']}) | {s['ask']:.1f}c | {s['net']:.2f}c | {s['pf']:.2f} | {s['z']:.2f} | {s['pf12']:.2f} |"


def run():
    res = D / "cric1_result.txt"
    if res.exists() and "--force" not in sys.argv:
        raise SystemExit("already run once: " + str(res))
    uni = json.loads((D / "universe.json").read_text())
    candles = json.loads((D / "candles.json").read_text())
    markets = list_markets(True)
    results = {tk: m["result"] for tk, m in markets.items()}
    rows, c = build_rows({e: u for e, u in uni.items() if e in candles}, candles, results)
    tr = [r for r in rows if r["treated"]]
    starts = sorted(r["start"] for r in tr)
    med = starts[len(starts) // 2] if starts else 0
    d1 = [r for r in tr if r["start"] < med]
    d2 = [r for r in tr if r["start"] >= med]
    lines = ["| arm | n | win | mean ask | net per contract | PF | z | PF x1.2 |", "|---|---|---|---|---|---|---|---|"]
    lines += [fmt("CONTROL (all cheap-side rows)", stats(rows)), fmt("TREATED", stats(tr)), fmt("treated D1", stats(d1)), fmt("treated D2", stats(d2))]
    for s in SERIES:
        lines.append(fmt("info: treated " + s, stats([r for r in tr if r["series"] == s])))
        lines.append(fmt("info: control " + s, stats([r for r in rows if r["series"] == s])))
    lines.append(fmt("info: untreated cheap-side rows", stats([r for r in rows if not r["treated"]])))
    st = stats(tr)
    verdict = ("NOT_ENOUGH_DATA" if len(tr) < MIN_TRADES else
               "FALSIFIED" if not (stats(d1).get("net", -1) > 0 and stats(d2).get("net", -1) > 0 and st["pf"] >= BAR_PF) else
               "NOT_YET_FALSIFIED" if st["net"] >= 2 and st["z"] >= Z_BAR and st["pf12"] >= BAR_PF else "FALSIFIED")
    out = ["events in universe %d, with candles %d" % (len(uni), len(candles)), str(dict(c)), "treated %d, cheap-side rows %d" % (len(tr), len(rows))] + lines
    out.append("also under the kill rules if treated were 150: D1 net %s, D2 net %s, PF %s" % (stats(d1).get("net"), stats(d2).get("net"), st.get("pf")))
    out.append("VERDICT " + verdict)
    txt = "\n".join(out)
    res.write_text(txt)
    (D / "cric1_rows.json").write_text(json.dumps(rows))
    print(txt)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"census": census, "fit": fit, "fetch": fetch, "run": run}[cmd]()
