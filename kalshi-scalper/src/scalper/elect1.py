"""ELECT1: election night cheap-side snapshot and scorer (public data only, no orders).

snapshot: python3 -I src/scalper/elect1.py snapshot OUT.csv
score:    python3 -I src/scalper/elect1.py score SNAPSHOT.csv
"""
from __future__ import annotations
import csv, json, math, re, sys, time, urllib.request, urllib.error, datetime

BASE = "https://api.elections.kalshi.com/trade-api/v2"
ST = "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()
S2 = "|".join(ST)
UNIVERSE_RE = re.compile(
    r"^(KX)?SENATE(%s)$|^SENATEPARTY(-)?(%s)S?$|^KXAKSENATE$|^GOVPARTY(-)?(%s)$|^KXGOV(%s)$|"
    r"^(KX)?HOUSE(%s)\d+S?$|^HOUSEPARTY-.*$|^HOUSEAKAL$|^(HOUSE|SENATE|KXHOUSE|KXSENATE|CONTROLH|CONTROLS)$|^HOUSE(%s)\d+$"
    % (S2, S2, S2, S2, S2, S2))
NOT_RE = re.compile(r"NOM|PRIMARY|MARGIN|MOV|COMBO|SEATS")


def series_in_universe(tickers):
    return sorted(t for t in tickers if UNIVERSE_RE.match(t) and not NOT_RE.search(t))


def get(path, retries=20):
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(BASE + path, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(min(10, 2 * (i + 1)) if e.code == 429 else 2 * (i + 1))
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise last


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def fee(p, c=10):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def snapshot(out):
    allser = [s["ticker"] for s in get("/series?category=Elections")["series"]]
    allser += [s["ticker"] for s in get("/series?category=Politics")["series"]]
    sers = series_in_universe(set(allser))
    pri = lambda t: (0 if 'SENATE' in t and 'HOUSE' not in t else 1 if 'GOV' in t else 2 if t in ('HOUSE','CONTROLH','CONTROLS','KXHOUSE') else 3, t)
    sers.sort(key=pri)
    print('universe series', len(sers), flush=True)
    cols = ["series", "ticker", "event_ticker", "title", "yes_sub_title", "status", "yes_bid", "yes_ask", "last", "volume",
            "open_interest", "close_time", "quote_utc"]
    n = 0
    import os
    done = set()
    if os.path.exists(out):
        done = {r["series"] for r in csv.DictReader(open(out))}
    with open(out, "a", newline="") as fh:
        w = csv.writer(fh)
        if not done:
            w.writerow(cols)
        for s in sers:
            if s in done:
                continue
            try:
                d = get("/markets?series_ticker=%s&limit=200" % s)
            except Exception as e:  # noqa
                sys.stderr.write("MISSING %s %s\n" % (s, e)); continue
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            for m in d.get("markets", []):
                w.writerow([s, m["ticker"], m.get("event_ticker"), m.get("title"), m.get("yes_sub_title"), m.get("status"),
                            m.get("yes_bid_dollars"), m.get("yes_ask_dollars"), m.get("last_price_dollars"),
                            m.get("volume_fp"), m.get("open_interest_fp"), m.get("close_time"), now]); n += 1
            fh.flush(); time.sleep(0.4)
    print("series", len(sers), "markets", n)


if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        snapshot(sys.argv[2])


# ---- reference: Wikipedia ratings (Cook, Sabato, Inside Elections), mapping fixed in the registration
RATING_P = {"solid": 0.97, "safe": 0.97, "likely": 0.88, "lean": 0.72, "tilt": 0.60, "toss-up": 0.50, "tossup": 0.50}
RATERS = ("Cook", "Sabato", "IE")
ROW_RE = re.compile(r"^! ?\[\[(?:2026 United States (?:Senate|House of Representatives) elections? in [^|\]]+|2026 [^|\]]+ gubernatorial election)\|([^\]]+)\]\]", re.M)
RATE_RE = re.compile(r"<!--(Cook|Sabato|IE)-->\s*\|\s*\{\{USRaceRating\|([A-Za-z-]+)\|?([A-Za-z]*)")


def parse_ratings(text):
    """state -> list of (rater, favoured_prob_for_R, ...) -> returns state -> P(R wins) averaged, or None if duplicated rows."""
    rows = {}
    ms = list(ROW_RE.finditer(text))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        block = text[m.end():end]
        ps = []
        for r in RATE_RE.finditer(block):
            lvl, party = r.group(2).lower(), r.group(3).upper()
            if lvl in ("toss-up", "tossup", "tilt") and party not in ("R", "D"):
                p_r = 0.5
            elif lvl not in RATING_P or party not in ("R", "D"):
                continue
            else:
                p = RATING_P[lvl]
                p_r = p if party == "R" else 1 - p
            ps.append(p_r)
        name = m.group(1).strip()
        if ps:
            rows.setdefault(name, []).append(sum(ps) / len(ps))
        else:
            rows.setdefault(name, [])
    return {k: (v[0] if len(v) == 1 else None) for k, v in rows.items()}


# ---- races, trades, scoring (pure functions, tested on synthetic data)
def race_key(series, ticker):
    """(type, state-or-id) for a market; None if unknown."""
    m = re.match(r"^(?:KX)?(SENATE|GOV)(?:PARTY)?(?:-)?(%s)S?$" % S2, series)
    if m:
        return (m.group(1), m.group(2))
    m = re.match(r"^(?:KX)?HOUSE(%s)(\d+)S?$" % S2, series)
    if m:
        return ("HOUSE", m.group(1) + m.group(2))
    return (series, ticker.split("-")[1] if "-" in ticker else ticker)


def party_of(ticker):
    t = ticker.rsplit("-", 1)[-1]
    return t if t in ("R", "D") else None


def eligible(row):
    b, a = f(row["yes_bid"]), f(row["yes_ask"])
    if row["status"] != "active" or b <= 0 or a <= 0:
        return False
    return f(row["volume"]) >= 100 or f(row["open_interest"]) >= 100


def sides(row):
    """Both sides: (side, ask). NO ask is 1 - yes bid."""
    return [("yes", f(row["yes_ask"])), ("no", round(1 - f(row["yes_bid"]), 4))]


def build_trades(rows, ref=None, lo=0.03, hi=0.30, mult=3.0):
    """Return (control_trades, ref_trades). One per race: lowest-ask cheap side.
    ref: dict (type,state)->P(R wins) or None. A trade is a dict with race, ticker, side, ask, ref_p, party."""
    by_race = {}
    for r in rows:
        if not eligible(r):
            continue
        k = race_key(r["series"], r["ticker"])
        for side, ask in sides(r):
            if lo - 1e-9 <= ask <= hi + 1e-9:
                pr = party_of(r["ticker"])
                if side == "yes":
                    bought = pr
                else:
                    bought = {"R": "D", "D": "R"}.get(pr)
                rp = None
                if ref is not None and bought and ref.get(k) is not None:
                    p_r = ref[k]
                    rp = p_r if bought == "R" else 1 - p_r
                by_race.setdefault(k, []).append(dict(race=k, ticker=r["ticker"], side=side, ask=ask, party=bought, ref_p=rp))
    control, refl = [], []
    for k, c in by_race.items():
        c.sort(key=lambda t: (t["ask"], t["ticker"]))
        control.append(c[0])
        ok = [t for t in c if t["ref_p"] is not None and t["ref_p"] >= mult * t["ask"]]
        if ok:
            refl.append(ok[0])
    return control, refl


def fee(p, c=10):
    return math.ceil(round(0.07 * c * p * (1 - p) * 100, 9)) / 100


def trade_pnl(t, won, c=10):
    p = t["ask"]
    return c * ((1 - p) if won else -p) - fee(p, c)


def stats(trades, results):
    """results: ticker -> 'yes'/'no'. Unsettled trades are skipped."""
    pnl, wins, price = [], 0, []
    gw = gl = 0.0
    for t in trades:
        r = results.get(t["ticker"])
        if r not in ("yes", "no"):
            continue
        won = (r == t["side"])
        x = trade_pnl(t, won)
        pnl.append(x); price.append(t["ask"]); wins += won
        if x > 0: gw += x
        else: gl += -x
    n = len(pnl)
    return dict(n=n, win_rate=wins / n if n else None, mean_ask=sum(price) / n if n else None,
                net=sum(pnl), net_per_trade=sum(pnl) / n if n else None, pf=gw / gl if gl else None)


def cluster_boot(trades, results, key, reps=2000, seed=1):
    import random
    rnd = random.Random(seed)
    groups = {}
    for t in trades:
        r = results.get(t["ticker"])
        if r in ("yes", "no"):
            groups.setdefault(key(t), []).append(trade_pnl(t, r == t["side"]))
    keys = list(groups)
    if len(keys) < 2:
        return None
    means = []
    for _ in range(reps):
        tot = n = 0
        for _ in keys:
            g = groups[rnd.choice(keys)]
            tot += sum(g); n += len(g)
        means.append(tot / n)
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)], len(keys)


NAMES = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT",
 "Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS",
 "Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS",
 "Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY",
 "North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI",
 "South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA",
 "West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
WIKI = (("SENATE", "2026_United_States_Senate_elections"), ("GOV", "2026_United_States_gubernatorial_elections"))


def fetch_reference():
    """(type, state code) -> P(R wins), from Wikipedia raw wikitext (keyless)."""
    ref = {}
    for typ, page in WIKI:
        url = "https://en.wikipedia.org/w/index.php?title=%s&action=raw" % page
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-bot/1.0 (election ratings read)"}), timeout=40) as r:
            text = r.read().decode("utf8")
        for name, p in parse_ratings(text).items():
            if name in NAMES and p is not None:
                ref[(typ, NAMES[name])] = p
    return ref


def read_results(tickers, out):
    """Resumable: re-reads only tickers not yet settled in out."""
    done = {}
    try:
        for r in csv.DictReader(open(out)):
            done[r["ticker"]] = r["result"]
    except FileNotFoundError:
        pass
    for t in tickers:
        if done.get(t) in ("yes", "no"):
            continue
        try:
            m = get("/markets/%s" % t)["market"]
            done[t] = m.get("result", "") or ""
        except Exception:  # noqa
            done[t] = ""
        time.sleep(0.4)
        with open(out, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["ticker", "result"])
            for k, v in done.items(): w.writerow([k, v])
    return done


def score(snapshot_path):
    rows = list(csv.DictReader(open(snapshot_path)))
    ref = fetch_reference()
    control, refl = build_trades(rows, ref)
    tickers = sorted({t["ticker"] for t in control + refl})
    res = read_results(tickers, snapshot_path.replace("SNAPSHOT_2026-11-03", "RESULTS_RAW"))
    out = {}
    for name, tr in (("control", control), ("ref", refl)):
        o = dict(trades=len(tr), **stats(tr, res))
        o["by_party"] = {p: stats([t for t in tr if t["party"] == p], res) for p in ("R", "D")}
        o["by_type"] = {ty: stats([t for t in tr if t["race"][0] == ty], res) for ty in sorted({t["race"][0] for t in tr})}
        o["boot_by_state"] = cluster_boot(tr, res, key=lambda t: t["race"][1][:2])
        out[name] = o
    out["unsettled"] = [t for t in tickers if res.get(t) not in ("yes", "no")]
    print(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__" and sys.argv[1] == "score":
    score(sys.argv[2])
