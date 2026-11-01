"""SPORTS-PRE (workers/SPORTSPRE_REGISTRATION.md, incl. Amendment 1 / commit 300112c; README "Pre-registration: SPORTS-PRE"): Kalshi pre-game
moneylines (KXNFLGAME, KXNCAAFGAME, KXNBAGAME, KXMLBGAME) against ESPN's pre-game win probability. Research only. Nothing here means trade.
Verdict words: FALSIFIED, NOT_ENOUGH_DATA, NOT_YET_FALSIFIED (earns only a registered forward test, never a live rule).

    python -m scalper.sportspre count   games, looks and qualifying rows and dates ONLY. results.csv and every outcome field are never
                                        opened, no Brier, no PF, no PnL is computed (an information look allowed before the read date)
    python -m scalper.sportspre read    THE ONE READ. Refuses before 2027-01-01 12:00 UTC and a second time. Prints the registered verdict.

Data: the recorder's files on origin/quote-data under sportspre/<date>/<hhmm>/ (games, quotes, predictor, results, coverage .csv.gz).
Every threshold below is the registration's; none was chosen after seeing a row.
"""
from __future__ import annotations

import csv
import gzip
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

from .mm1 import clustered_z, order_fee, pf
from .paths import DATA_DIR

CT = ZoneInfo("America/Chicago")
ROOT = DATA_DIR.parent
WORKERS = ROOT / "workers"
RESULT_TXT = DATA_DIR / "sportspre_result.txt"
RESULT_MD = WORKERS / "SPORTSPRE_RESULT.md"
MARKER = DATA_DIR / "sportspre_started"
REPO = "/home/user/shwoopnet"
REPO_SLUG = "shwoopnet/shwoopnet"
PREFIX = "sportspre/"

def _utc(y, m, d, h=0):
    return datetime(y, m, d, h, tzinfo=timezone.utc).timestamp()

READ_NOT_BEFORE = _utc(2027, 1, 1, 12)      # "Read date: 2027-01-01, once, after 12:00 UTC"
FIRST_START = _utc(2026, 11, 1)             # games starting before this were looked at (disclosure) and are excluded
STOP_START = _utc(2026, 12, 31)             # the recorder tracks nothing starting at or after this
HALF_SPLIT = _utc(2026, 12, 1)              # first 30 days (Nov 1 to Nov 30) and second 30 days (Dec 1 to Dec 30), by start date, whole UTC days
SERIES = ("KXNFLGAME", "KXNCAAFGAME", "KXNBAGAME", "KXMLBGAME")

LOOK_S, LOOK_EARLIEST_S = 3600, 4500        # T-60 minutes, no earlier than T-75
PAIR_S = 300                                # ESPN response received within 5 minutes of the Kalshi read
MAX_SPREAD, MIN_ASK_SIZE, C = 0.02, 10.0, 10
GAP = 0.06
FEE, FEE_STRESS = 0.07, 0.07 * 1.2
MIN_TRADES, PF_HALF, Z_MIN = 200, 1.2, 3.0
N_COUNT = 728696                            # running count including these 2 tries
Z_BAR = NormalDist().inv_cdf(1 - 0.05 / N_COUNT)    # one-sided, about 5.27 as registered
NBA_DROP_RATE = 0.05                        # NBA is dropped from the verdict if the post-game predictor differs in more than 5% of games
AUDIT_MEAN_C = 3.0                          # a mean above +3c per contract is an audit trigger first
EPS = 1e-9
TRIES = ("A", "B")


# ---------------------------------------------------------------- helpers

def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def parse_iso(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def utc_day(t):
    return datetime.fromtimestamp(t, timezone.utc).date().isoformat()


def fee(ask, rate=FEE):
    """Kalshi's rate x C x p x (1-p), rounded UP to the cent per order, C = 10 (dollars)."""
    return order_fee(rate, C, ask)


def net_per_contract(ask, payout, rate=FEE):
    """(payout - ask) - fee / C, dollars per contract."""
    return payout - ask - fee(ask, rate) / C


# ---------------------------------------------------------------- loading (the only place that touches git)

def _git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True).stdout


def _names():
    _git("fetch", "-q", "origin", "+refs/heads/quote-data:refs/remotes/origin/quote-data")
    names = _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    return [n for n in names if n.startswith(PREFIX)]


def _blob(path):
    raw = _git("show", f"origin/quote-data:{path}")
    if not raw:
        r = subprocess.run(["gh", "api", f"repos/{REPO_SLUG}/contents/{path}?ref=quote-data", "-H", "Accept: application/vnd.github.raw"], capture_output=True)
        raw = r.stdout
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(io.BytesIO(raw))))) if raw else []


def load(kind):
    """All rows of one recorder file kind ('games', 'quotes', 'predictor', 'results') over every job. Tests replace this function."""
    rows = []
    for n in sorted(x for x in _names() if x.endswith("/" + kind + ".csv.gz")):
        rows += _blob(n)
    return rows


# ---------------------------------------------------------------- the look (no outcome field is used here)

def build_games(games, quotes, pred):
    """One record per tracked game with the look, the ESPN probability and the universe filters. Reads games, quotes and predictor rows only.
    Returns (records, drops) where drops counts why games fell out; every game is counted once, at the first rule it fails."""
    g_by = {}
    for r in games:
        if r.get("event_ticker") and r.get("match", "ok") == "ok":
            g_by[(r["league"], r["espn_id"])] = r
    q_by = defaultdict(lambda: defaultdict(dict))
    for r in quotes:
        q_by[(r["league"], r["espn_id"])][r["poll_ts_ms"]][r["side"]] = r
    p_by = defaultdict(list)
    for r in pred:
        if r.get("kind") == "core_predictor":
            p_by[(r["league"], r["espn_id"])].append(r)
    drops = defaultdict(int)
    recs = []
    for key, g in sorted(g_by.items()):
        start = parse_iso(g["start_iso"])
        if start is None or start < FIRST_START or start >= STOP_START or key[0] not in SERIES:
            drops["outside_dates"] += 1
            continue
        look = None
        for ms in sorted(q_by[key], key=lambda m: -float(m)):
            t = float(ms) / 1000.0
            both = q_by[key][ms]
            if start - LOOK_EARLIEST_S <= t <= start - LOOK_S and "home" in both and "away" in both:
                look = (t, both)
                break
        if look is None:
            drops["no_poll"] += 1
            continue
        t, both = look
        best = None
        for r in p_by[key]:
            rt = num(r.get("recv_ms"))
            hg, ag = num(r.get("home_gp")), num(r.get("away_gp"))
            if rt is None or r.get("http") != "200" or hg is None or ag is None:
                continue
            rt /= 1000.0
            if abs(rt - t) <= PAIR_S and rt < start and (best is None or abs(rt - t) < abs(best[0] - t)):
                best = (rt, hg, ag, r)
        if best is None:
            drops["no_espn_probability"] += 1       # Amendment 1: no pre-game figure at the look, dropped and counted
            continue
        rt, hg, ag, prow = best
        q = {}
        for side in ("home", "away"):
            r = both[side]
            q[side] = {"ticker": r["ticker"], "bid": num(r["yes_bid"]), "ask": num(r["yes_ask"]), "ask_size": num(r["yes_ask_size"])}
        ok = True
        for side in ("home", "away"):
            b, a = q[side]["bid"], q[side]["ask"]
            if b is None or a is None or b < 0.01 - EPS or a > 0.99 + EPS or a < b - EPS or a - b > MAX_SPREAD + EPS:
                ok = False
        if not ok:
            drops["not_two_sided_or_spread"] += 1
            continue
        q["home"]["pE"], q["away"]["pE"] = hg / 100.0, ag / 100.0
        recs.append({"league": key[0], "id": key[1], "start": start, "day": utc_day(start), "look_t": t, "espn_recv": rt, "espn_recv_after_t60": rt > start - LOOK_S + EPS,
                     "espn_last_modified": prow.get("last_modified", ""), "home_gp": hg, "away_gp": ag, "q": q, "event": g["event_ticker"],
                     "home_ticker": g["home_ticker"], "away_ticker": g["away_ticker"]})
    return recs, dict(drops)


def signals(rec):
    """{'A': side or None, 'B': side or None}: the side to buy in each try, from the quote and pE only (never an outcome).
    A: the cheaper side (lower ask; a tie goes to the larger gap), if pE - ask >= 0.06 and its ask size >= 10. B: either side, the larger gap."""
    q = rec["q"]
    gap = {s: q[s]["pE"] - q[s]["ask"] for s in ("home", "away")}
    ok = {s: q[s]["ask_size"] is not None and q[s]["ask_size"] >= MIN_ASK_SIZE - EPS for s in ("home", "away")}
    ha, aa = q["home"]["ask"], q["away"]["ask"]
    if abs(ha - aa) <= EPS:
        cheap = "home" if gap["home"] >= gap["away"] else "away"
    else:
        cheap = "home" if ha < aa else "away"
    out = {"A": None, "B": None}
    if ok[cheap] and gap[cheap] >= GAP - EPS:
        out["A"] = cheap
    cand = [s for s in ("home", "away") if ok[s] and gap[s] >= GAP - EPS]
    if cand:
        out["B"] = max(cand, key=lambda s: gap[s])
    return out


# ---------------------------------------------------------------- count (no outcome, anywhere)

def count_report(games, quotes, pred):
    recs, drops = build_games(games, quotes, pred)
    tracked = len({(r["league"], r["espn_id"]) for r in games if r.get("event_ticker")})
    by = defaultdict(lambda: defaultdict(int))
    days, sig = defaultdict(set), {t: 0 for t in TRIES}
    for r in recs:
        by[r["league"]]["universe"] += 1
        days[r["league"]].add(r["day"])
        s = signals(r)
        for t in TRIES:
            if s[t]:
                sig[t] += 1
                by[r["league"]]["signal_" + t] += 1
    lines = [f"tracked and matched games {tracked}; with a look and an ESPN probability in the universe {len(recs)}; dropped {drops}",
             f"qualifying signals (quote and ESPN figure only): Try A {sig['A']}, Try B {sig['B']}; the registered minimum is {MIN_TRADES} per try"]
    for lg in sorted(by):
        d = sorted(days[lg])
        lines.append(f"  {lg}: universe {by[lg]['universe']}, signals A {by[lg]['signal_A']} B {by[lg]['signal_B']}, dates {d[0]} to {d[-1]} ({len(d)} days)")
    return lines


def count():
    # results.csv is deliberately never loaded here
    print("\n".join(count_report(load("games"), load("quotes"), load("predictor"))))
    return 0


# ---------------------------------------------------------------- outcomes (read only)

def outcomes(results):
    """{(league, id): home payout in {1, 0, 0.5}} for games Kalshi settled and ESPN's final agrees with; plus a dict of counts of what was left out."""
    last = {}
    for r in results:
        last[(r["league"], r["espn_id"])] = r        # a later row (a settled one) replaces an earlier give-up row
    out, left = {}, defaultdict(int)
    for k, r in last.items():
        if str(r.get("resolved")) != "1":
            left["not_settled"] += 1
            continue
        hr, ar = (r.get("home_result") or "").lower(), (r.get("away_result") or "").lower()
        hs, as_ = num(r.get("home_score")), num(r.get("away_score"))
        done = str(r.get("espn_completed")).lower() == "true"
        if (hr, ar) == ("yes", "no"):
            pay = 1.0
        elif (hr, ar) == ("no", "yes"):
            pay = 0.0
        elif hr and ar and hr != "yes" and ar != "yes" and hs is not None and hs == as_:
            pay = 0.5                                  # a tie (NFL): each team pays $0.50
        else:
            left["void_or_disagree"] += 1
            continue
        if not done or hs is None or as_ is None or (pay == 1.0 and not hs > as_) or (pay == 0.0 and not hs < as_) or (pay == 0.5 and hs != as_):
            left["espn_disagrees_or_not_final"] += 1
            continue
        out[k] = pay
    return out, dict(left)


def audit_c(pred, recs):
    """(c): per league, games whose core predictor read after the game differs from the look value (more than 0.01 points), and the rate."""
    post = {}
    for r in pred:
        if r.get("kind") == "core_predictor_post" and r.get("http") == "200":
            post[(r["league"], r["espn_id"])] = (num(r.get("home_gp")), num(r.get("away_gp")))
    res = defaultdict(lambda: [0, 0])
    for rec in recs:
        p = post.get((rec["league"], rec["id"]))
        if p is None or p[0] is None or p[1] is None:
            continue
        res[rec["league"]][1] += 1
        if abs(p[0] - rec["home_gp"]) > 0.01 or abs(p[1] - rec["away_gp"]) > 0.01:
            res[rec["league"]][0] += 1
    return {lg: (d, n, d / n if n else 0.0) for lg, (d, n) in res.items()}


def brier(recs, pay):
    """(market, ESPN) mean squared error on the home team, both normalised to sum to 1 over the two teams. Market = quote midpoint."""
    m = e = 0.0
    for r in recs:
        q = r["q"]
        mh, ma = (q["home"]["bid"] + q["home"]["ask"]) / 2, (q["away"]["bid"] + q["away"]["ask"]) / 2
        mh /= (mh + ma)
        eh = q["home"]["pE"] / (q["home"]["pE"] + q["away"]["pE"])
        y = pay[(r["league"], r["id"])]
        m += (mh - y) ** 2
        e += (eh - y) ** 2
    n = len(recs)
    return m / n, e / n


def trades_of(recs, pay, try_):
    """[(start, day, net per contract at 1.0x fees, net at 1.2x fees)] for a try."""
    out = []
    for r in recs:
        side = signals(r)[try_]
        if not side:
            continue
        ask = r["q"][side]["ask"]
        win = pay[(r["league"], r["id"])]
        w = win if side == "home" else 1.0 - win       # tie 0.5 is 0.5 for either side
        out.append((r["start"], r["day"], net_per_contract(ask, w), net_per_contract(ask, w, FEE_STRESS)))
    return out


def try_stats(tr):
    v = [x[2] for x in tr]
    h1, h2 = [x[2] for x in tr if x[0] < HALF_SPLIT], [x[2] for x in tr if x[0] >= HALF_SPLIT]
    return {"n": len(tr), "net_c": 100 * sum(v) / len(v) if v else 0.0, "pf": pf(v), "pf_h1": pf(h1), "pf_h2": pf(h2), "n_h1": len(h1), "n_h2": len(h2),
            "pf_stress": pf([x[3] for x in tr]), "z": clustered_z(v, [x[1] for x in tr])}


def try_verdict(s, brier_fail):
    """The registered kill rules, in the registration's order. Returns (word, [reasons])."""
    if brier_fail:
        return "FALSIFIED", ["rule 1: market Brier at or below ESPN's"]
    if s["n"] < MIN_TRADES:
        return "NOT_ENOUGH_DATA", [f"rule 3: {s['n']} trades, fewer than {MIN_TRADES}"]
    why = []
    if s["pf_h1"] < PF_HALF:
        why.append(f"rule 2: PF {s['pf_h1']:.2f} under {PF_HALF} in the first 30 days")
    if s["pf_h2"] < PF_HALF:
        why.append(f"rule 2: PF {s['pf_h2']:.2f} under {PF_HALF} in the second 30 days")
    if s["z"] < Z_MIN:
        why.append(f"rule 4: day-clustered z {s['z']:.2f} under {Z_MIN}")
    if s["z"] < Z_BAR:
        why.append(f"rule 5: z {s['z']:.2f} under the deflated bar {Z_BAR:.2f}")
    if not s["pf_stress"] > 1.0:
        why.append(f"rule 6: PF {s['pf_stress']:.2f} not above 1 at fees x 1.2")
    return ("FALSIFIED", why) if why else ("NOT_YET_FALSIFIED", ["all of rules 1 to 6 passed; earns only a registered forward test"])


def score(games, quotes, pred, results):
    recs, drops = build_games(games, quotes, pred)
    pay, left = outcomes(results)
    lines = [f"games in the universe with a look and an ESPN probability {len(recs)}; dropped {drops}; settlement left out {left}"]
    lines.append(f"audit (a): looks whose ESPN response arrived after T-60 (still before the start): {sum(1 for r in recs if r['espn_recv_after_t60'])} of {len(recs)}")
    fb = [r for r in recs if r["league"] != "KXNBAGAME" and r["espn_last_modified"]]
    late = sum(1 for r in fb if (parse_iso(r["espn_last_modified"]) or 0) >= r["start"])
    lines.append(f"audit (b): football/MLB looks with lastModified at or after the start: {late} of {len(fb)}")
    ac = audit_c(pred, recs)
    lines.append("audit (c): core predictor re-read after the game differs from the look: " + ("; ".join(f"{lg} {d} of {n} ({100 * x:.1f}%)" for lg, (d, n, x) in sorted(ac.items())) or "no post-game reads"))
    dropped_lg = [lg for lg, (d, n, x) in ac.items() if lg == "KXNBAGAME" and x > NBA_DROP_RATE]
    if dropped_lg:
        recs = [r for r in recs if r["league"] != "KXNBAGAME"]
        lines.append(f"NBA DROPPED from the verdict: post-game predictor differs in more than {int(100 * NBA_DROP_RATE)}% of games")
    recs = [r for r in recs if (r["league"], r["id"]) in pay]
    lines.append(f"games scored (settled, ESPN agrees): {len(recs)}")
    if not recs:
        return "NOT_ENOUGH_DATA", lines + ["nothing to score"]
    bm, be = brier(recs, pay)
    brier_fail = bm <= be + 1e-12
    lines.append(f"Brier (home team, both normalised to sum 1): market {bm:.5f}, ESPN {be:.5f}; rule 1 {'FAILS (market at or below ESPN)' if brier_fail else 'passes'}")
    words = {}
    for t in TRIES:
        s = try_stats(trades_of(recs, pay, t))
        w, why = try_verdict(s, brier_fail)
        words[t] = w
        lines.append(f"Try {t}: {w}. n {s['n']} (halves {s['n_h1']} / {s['n_h2']}), net {s['net_c']:+.2f}c per contract, PF {s['pf']:.2f}, halves PF {s['pf_h1']:.2f} / {s['pf_h2']:.2f}, "
                     f"PF at fees x1.2 {s['pf_stress']:.2f}, day-clustered z {s['z']:.2f} (bars 3 and {Z_BAR:.2f}); " + "; ".join(why))
        if s["net_c"] > AUDIT_MEAN_C:
            lines.append(f"  AUDIT FIRST: Try {t} mean above +{AUDIT_MEAN_C:.0f}c per contract; check the look, the receive times and the outcome source before believing it")
    ws = list(words.values())
    verdict = "NOT_YET_FALSIFIED" if "NOT_YET_FALSIFIED" in ws else ("NOT_ENOUGH_DATA" if "NOT_ENOUGH_DATA" in ws and "FALSIFIED" not in ws else "FALSIFIED")
    return verdict, lines


# ---------------------------------------------------------------- the read

def _write(verdict, lines, now):
    head = f"SPORTSPRE VERDICT {verdict} (2 tries; running count about {N_COUNT:,}; z bar {Z_BAR:.2f})"
    body = "\n".join([head] + lines) + "\n"
    RESULT_TXT.parent.mkdir(parents=True, exist_ok=True)
    RESULT_TXT.write_text(body)
    RESULT_MD.write_text(f"# SPORTS-PRE result (read once at {datetime.fromtimestamp(now, CT):%Y-%m-%d %H:%M} CT; research only)\n\n```\n{body}```\n")
    print(body)
    return verdict


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
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(f"started {datetime.now(timezone.utc).isoformat()}\n")
    verdict, lines = score(load("games"), load("quotes"), load("predictor"), load("results"))
    return _write(verdict, lines, now)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "count":
        return count()
    if cmd == "read":
        run()
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
