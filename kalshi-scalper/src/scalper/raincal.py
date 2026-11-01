"""RAINCAL (workers/RAINCAL_REGISTRATION.md): Kalshi's daily KXRAIN markets against the NWS probability of precipitation (PoP). Research only.
Verdict words: FALSIFIED, NOT_YET_FALSIFIED, NOT_ENOUGH_DATA. Nothing here means trade.

    python -m scalper.raincal count [--dir D]   qualifying city-days, dates, universe and trade-signal counts. Reads quotes.csv.gz and pop.csv.gz ONLY: it
                                                never opens results.csv.gz and prints no outcome, no PnL, no profit factor, no Brier.
    python -m scalper.raincal read [--dir D]    THE ONE READ. Refuses before 2027-01-01 18:00 UTC and a second time; prints the registered verdict.

Data: gzipped CSVs the recorder (scripts/record_rain.py) pushes to branch quote-data as raincal/<YYYY-MM-DD>/<HHMM>/{quotes,pop,obs,coverage,results}.csv.gz.
Without --dir the files are exported from origin/quote-data into a temp folder (count exports only quotes and pop).

Every price comparison is done in whole cents and whole percent, so a threshold tie (exactly 8 cents) is decided by integers, not float luck."""
from __future__ import annotations

import calendar
import csv
import gzip
import io
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist

from .mm1 import clustered_z, order_fee, pf
from .paths import DATA_DIR

ROOT = DATA_DIR.parent
WORKERS = ROOT / "workers"
RESULT_TXT = DATA_DIR / "raincal_result.txt"
RESULT_MD = WORKERS / "RAINCAL_RESULT.md"
MARKER = DATA_DIR / "raincal_started"

READ_NOT_BEFORE = datetime(2027, 1, 1, 18, 0, tzinfo=timezone.utc).timestamp()   # the registration: 2027-01-01 after 18:00 UTC
LOOK_BEFORE_CLOSE_S = 17 * 3600          # 7:00 AM local standard time
LAST_BEFORE_CLOSE_S = 16 * 3600          # a look poll later than 8:00 AM is no trade
DAY_S = 24 * 3600
POP_MATCH_S = 30 * 60                    # a poll's forecast is the first fetch of its own pass (the recorder's pass is capped at 20 minutes)
SPREAD_DAYS = 14                         # the first 14 recorded UTC days choose the universe
SPREAD_MAX_C = 3                         # median spread at most 3 cents ...
SPREAD_MIN_DAYS = 7                      # ... with at least 7 two-sided days
EDGE_C = 8                               # buy when PoP and the price differ by at least 8 cents
C = 10                                   # contracts per order, for the fee rounding
FEE_RATE = 0.07
NEEDED = 150
PF_HALF_MIN = 1.2
Z_MIN = 3.0
N_TRIED = 728698                         # running count after the 2 tries; recomputed at the read from this constant
SMALL_ASK = 10


def z_bar(n=N_TRIED):
    return NormalDist().inv_cdf(1 - 0.05 / n)


# ---------------------------------------------------------------- loading
def _epoch(s):
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))


def _fnum(x):
    try:
        return None if x in ("", None) else float(x)
    except ValueError:
        return None


def read_table(root, name, opened=None):
    """All rows of raincal/*/*/<name>.csv.gz under root as dicts, oldest folder first. `opened` (a list) records each file name actually opened."""
    rows = []
    for p in sorted(Path(root).glob(f"raincal/*/*/{name}.csv.gz")):
        if opened is not None:
            opened.append(name)
        with gzip.open(p, "rt", newline="") as f:
            rows.extend(csv.DictReader(f))
    return rows


def export_branch(dest, names):
    """Export raincal/ from origin/quote-data into dest, only the named tables (count never exports results)."""
    subprocess.run(["git", "fetch", "-q", "origin", "+refs/heads/quote-data:refs/remotes/origin/quote-data"], check=True, cwd=ROOT)
    arch = subprocess.Popen(["git", "archive", "origin/quote-data", "raincal"], stdout=subprocess.PIPE, cwd=ROOT)
    pats = [f"raincal/*/*/{n}.csv.gz" for n in names]
    subprocess.run(["tar", "-x", "-C", str(dest), "--wildcards", *pats], stdin=arch.stdout, check=True)
    arch.stdout.close()
    arch.wait()


# ---------------------------------------------------------------- the look: one decision per city and day
def city_of(ticker):
    parts = (ticker or "").split("-")
    return parts[2] if len(parts) == 3 and parts[0] == "KXRAIN" else None


def utc_date(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%d")


def build_looks(quotes, pops):
    """One look per ticker (= city and day): the FIRST recorded poll at or after close - 17 h that has an active quote and a PoP series, and only if it is no later than
    close - 16 h. Returns {ticker: look dict}. Uses no outcome. PoP_day = max of the periods still running at the look (valid_end after the look), in whole percent."""
    groups = defaultdict(lambda: defaultdict(list))          # ticker -> t_fetch_ms -> rows
    for r in pops:
        groups[r["ticker"]][r["t_fetch_ms"]].append(r)
    polls = {}
    for r in quotes:                                         # duplicates of one poll collapse
        polls[(r["ticker"], r["t_recv_ms"])] = r
    by_ticker = defaultdict(list)
    for (tk, ms), r in polls.items():
        by_ticker[tk].append((float(ms) / 1000.0, r))
    looks = {}
    for tk, lst in by_ticker.items():
        city = city_of(tk)
        if city is None or not lst[0][1].get("close_time"):
            continue
        close = _epoch(lst[0][1]["close_time"])
        look = close - LOOK_BEFORE_CLOSE_S
        for t, r in sorted(lst, key=lambda x: x[0]):
            if t < look:
                continue
            if t > close - LAST_BEFORE_CLOSE_S:
                break                                        # the first poll in line is too late: no trade for this city and day
            if r.get("status") != "active":
                continue
            g = None
            for ms in sorted(groups.get(tk, {}), key=float):
                if t <= float(ms) / 1000.0 <= t + POP_MATCH_S:
                    g = groups[tk][ms]
                    break
            if g is None:
                continue
            vals = []
            for p in g:
                v = _fnum(p.get("pop_percent"))
                if v is not None and _epoch(p["valid_end"]) > look and _epoch(p["valid_start"]) < close:
                    vals.append(v)
            if not vals:
                continue
            bid, ask = _fnum(r.get("yes_bid")), _fnum(r.get("yes_ask"))
            looks[tk] = {
                "ticker": tk, "city": city, "t": t, "close": close, "day": utc_date(look),
                "bid_c": None if bid is None else round(bid * 100), "ask_c": None if ask is None else round(ask * 100),
                "bid_sz": _fnum(r.get("yes_bid_size")), "ask_sz": _fnum(r.get("yes_ask_size")),
                "pop": int(round(max(vals))), "pop_union": 1 - math.prod(1 - v / 100.0 for v in vals),
            }
            break
    return looks


def two_sided(lk):
    """Spread counts only when both sides are quoted: bid at least 1 cent and ask at most 99 cents."""
    return lk["bid_c"] is not None and lk["ask_c"] is not None and lk["bid_c"] >= 1 and lk["ask_c"] <= 99


def universe(looks):
    """Cities whose median two-sided spread over the first 14 recorded UTC days is at most 3 cents, with at least 7 such days. Cost only; no outcome.
    Returns (set of cities, {city: (days, median spread in cents or None)}, the 14 days used, whether 14 days exist yet)."""
    days = sorted({lk["day"] for lk in looks.values()})[:SPREAD_DAYS]
    sp = defaultdict(list)
    for lk in looks.values():
        if lk["day"] in days and two_sided(lk):
            sp[lk["city"]].append(lk["ask_c"] - lk["bid_c"])
    info = {c: (len(v), statistics.median(v)) for c, v in sp.items()}
    uni = {c for c, (n, m) in info.items() if n >= SPREAD_MIN_DAYS and m <= SPREAD_MAX_C}
    return uni, info, days, len(days) >= SPREAD_DAYS


def signal(lk):
    """The registered rule on one look. Returns ('yes'|'no', price in cents, size) or None. Whole-cent integer arithmetic: a gap of exactly 8 cents trades.
    YES at the ask when PoP - ask >= 8 (ask 1..99); NO at the NO ask (100 - bid) when bid - PoP >= 8 (bid 1..99). If both fire (crossed quotes) there is no trade."""
    a, b, p = lk["ask_c"], lk["bid_c"], lk["pop"]
    y = a is not None and 1 <= a <= 99 and p - a >= EDGE_C
    n = b is not None and 1 <= b <= 99 and b - p >= EDGE_C
    if y == n:
        return None
    return ("yes", a, lk["ask_sz"]) if y else ("no", 100 - b, lk["bid_sz"])


def net_per_contract(side, price_c, result, rate=FEE_RATE):
    """Payout minus price paid minus the fee per contract: fee = rate x C x p x (1-p) rounded up to the cent per order at C = 10, divided by 10."""
    win = (side == result)
    return (1.0 if win else 0.0) - price_c / 100.0 - order_fee(rate, C, price_c / 100.0) / C


# ---------------------------------------------------------------- count: no outcome anywhere
def count(root, opened=None):
    """Counts of what qualifies. Reads quotes and pop only. Returns the lines to print."""
    looks = build_looks(read_table(root, "quotes", opened), read_table(root, "pop", opened))
    uni, info, days, full = universe(looks)
    L = [f"RAINCAL count (no outcome is read; results.csv.gz is never opened)"]
    if not looks:
        return L + ["city-days with a look: 0"]
    alld = sorted({lk["day"] for lk in looks.values()})
    L.append(f"city-days with a look: {len(looks)} on {len(alld)} UTC days ({alld[0]} to {alld[-1]})")
    L.append(f"universe: {len(uni)} cities" + ("" if full else f" (PROVISIONAL: only {len(days)} of {SPREAD_DAYS} spread days recorded yet)") + ": " + ", ".join(sorted(uni)))
    inu = [lk for lk in looks.values() if lk["city"] in uni]
    sig = [(lk, signal(lk)) for lk in inu]
    sig = [(lk, s) for lk, s in sig if s]
    L.append(f"city-days with a look in the universe: {len(inu)}; trade signals: {len(sig)} (need {NEEDED} settled at the read); trade days: {len({lk['day'] for lk, _ in sig})}")
    return L


# ---------------------------------------------------------------- read
def brier(pairs):
    return sum((f - o) ** 2 for f, o in pairs) / len(pairs) if pairs else None


def half_of(day, d0, d1):
    """First half = dates strictly before the midpoint of the first and last look date; a date exactly on the midpoint goes to the second half."""
    o, o0, o1 = datetime.strptime(day, "%Y-%m-%d").toordinal(), datetime.strptime(d0, "%Y-%m-%d").toordinal(), datetime.strptime(d1, "%Y-%m-%d").toordinal()
    return 0 if o < o0 + (o1 - o0) / 2 else 1


def score(looks, results, n_tried=N_TRIED):
    """The registered verdict. looks: from build_looks; results: {ticker: 'yes'|'no'}. Returns (verdict, lines)."""
    uni, info, days, full = universe(looks)
    inu = [lk for lk in looks.values() if lk["city"] in uni]
    settled = [lk for lk in inu if results.get(lk["ticker"]) in ("yes", "no")]
    unsettled = [lk["ticker"] for lk in inu if lk["ticker"] not in results or results[lk["ticker"]] not in ("yes", "no")]
    trades = []
    for lk in settled:
        s = signal(lk)
        if s:
            side, px, sz = s
            trades.append({"day": lk["day"], "city": lk["city"], "side": side, "px": px, "sz": sz, "t": lk["t"],
                           "net": net_per_contract(side, px, results[lk["ticker"]]), "net12": net_per_contract(side, px, results[lk["ticker"]], FEE_RATE * 1.2)})
    L = [f"universe {len(uni)} cities ({'full' if full else 'only %d of %d' % (len(days), SPREAD_DAYS)} spread days); city-days with a look {len(inu)}, settled {len(settled)}, "
         f"unsettled and excluded {len(unsettled)}" + (": " + ", ".join(sorted(unsettled)[:20]) + (" ..." if len(unsettled) > 20 else "") if unsettled else ""),
         f"settled trades {len(trades)} (the bar: at least {NEEDED})"]
    if len(trades) < NEEDED:
        return "NOT_ENOUGH_DATA", L + ["NOT_ENOUGH_DATA: fewer than %d trades; nothing else is scored." % NEEDED]
    nets = [t["net"] for t in trades]
    all_days = sorted({lk["day"] for lk in inu})
    d0, d1 = all_days[0], all_days[-1]
    halves = [[t["net"] for t in trades if half_of(t["day"], d0, d1) == h] for h in (0, 1)]
    pfs = [pf(h) for h in halves]
    pf_all = pf(nets)
    z = clustered_z(nets, [t["day"] for t in trades])
    bar = z_bar(n_tried)
    pairs = [(lk, results[lk["ticker"]]) for lk in settled if two_sided(lk)]
    b_pop = brier([(lk["pop"] / 100.0, 1.0 if r == "yes" else 0.0) for lk, r in pairs])
    b_mid = brier([((lk["bid_c"] + lk["ask_c"]) / 200.0, 1.0 if r == "yes" else 0.0) for lk, r in pairs])
    fails = []
    for h, v, n in ((1, pfs[0], len(halves[0])), (2, pfs[1], len(halves[1]))):
        L.append(f"half {h}: {n} trades, profit factor {v:.3f} (falsified if under {PF_HALF_MIN})")
        if v < PF_HALF_MIN:
            fails.append(f"profit factor {v:.3f} under {PF_HALF_MIN} in half {h}")
    L.append(f"halves split at the date midpoint of {d0} and {d1}; a date on the midpoint is in the second half")
    L.append(f"Brier over {len(pairs)} two-sided city-days: PoP {b_pop:.5f}, Kalshi mid {b_mid:.5f} (falsified if mid is at or below PoP)")
    if b_mid <= b_pop:
        fails.append("Kalshi's mid Brier at or below the PoP Brier")
    L.append(f"day-clustered z {z:.2f} over {len({t['day'] for t in trades})} UTC days (falsified under {Z_MIN}); deflated bar {bar:.2f} at N {n_tried}")
    if z < Z_MIN:
        fails.append(f"day-clustered z {z:.2f} under {Z_MIN}")
    if z < bar:
        fails.append(f"z {z:.2f} under the deflated bar {bar:.2f}")
    L.append(f"pooled profit factor {pf_all:.3f}, mean net {sum(nets) / len(nets) * 100:+.2f}c per contract after the fee; fees x1.2: PF {pf([t['net12'] for t in trades]):.3f}")
    # information, not part of the verdict
    L.append("INFORMATION (not part of the verdict)")
    bycity = defaultdict(int)
    for t in trades:
        bycity[t["city"]] += 1
    L.append("spread by city (days, median cents): " + ", ".join(f"{c} {info[c][0]}d {info[c][1]:g}c" for c in sorted(info)))
    L.append("trades by city: " + ", ".join(f"{c} {n}" for c, n in sorted(bycity.items())))
    L.append(f"mean price paid {sum(t['px'] for t in trades) / len(trades):.1f}c; trades with ask size under {SMALL_ASK}: {sum(1 for t in trades if t['sz'] is not None and t['sz'] < SMALL_ASK)}"
             f"; PF without them {pf([t['net'] for t in trades if t['sz'] is None or t['sz'] >= SMALL_ASK]):.3f}")
    dec = defaultdict(list)
    for lk, r in pairs:
        dec[min(lk["pop"] // 10, 9)].append(1.0 if r == "yes" else 0.0)
    L.append("PoP reliability (decile: n, share rained): " + ", ".join(f"{d * 10}s {len(v)}, {sum(v) / len(v):.2f}" for d, v in sorted(dec.items())))
    L.append(f"Brier with the independence-union PoP: {brier([(lk['pop_union'], 1.0 if r == 'yes' else 0.0) for lk, r in pairs]):.5f}")
    if fails:
        return "FALSIFIED", L + ["FALSIFIED: " + "; ".join(fails)]
    return "NOT_YET_FALSIFIED", L + ["NOT_YET_FALSIFIED: every bar holds. A pass permits considering a small capped slot, nothing more."]


def settled_results(rows):
    """{ticker: 'yes'|'no'} from results.csv rows; the last copy of a ticker wins."""
    out = {}
    for r in rows:
        if r.get("result") in ("yes", "no"):
            out[r["ticker"]] = r["result"]
    return out


def run(now=None, root=None):
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
    tmp = None
    if root is None:
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        export_branch(root, ["quotes", "pop", "results"])
    looks = build_looks(read_table(root, "quotes"), read_table(root, "pop"))
    v, L = score(looks, settled_results(read_table(root, "results")))
    body = "\n".join(L) + "\n"
    print(f"RAINCAL verdict: {v}\n{body}")
    RESULT_TXT.parent.mkdir(parents=True, exist_ok=True)
    RESULT_TXT.write_text(f"{v}\n{body}")
    WORKERS.mkdir(parents=True, exist_ok=True)
    RESULT_MD.write_text(f"# RAINCAL result (read once at {datetime.fromtimestamp(now, timezone.utc):%Y-%m-%d %H:%M} UTC; research only)\n\n{v}\n\n```\n{body}```\n")
    return v


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    root = a[a.index("--dir") + 1] if "--dir" in a else None
    if not a or a[0] not in ("count", "read"):
        print(__doc__)
        return 2
    if a[0] == "read":
        run(root=root)
        return 0
    tmp = None
    if root is None:
        tmp = tempfile.TemporaryDirectory()
        root = tmp.name
        export_branch(root, ["quotes", "pop"])
    print("\n".join(count(root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
