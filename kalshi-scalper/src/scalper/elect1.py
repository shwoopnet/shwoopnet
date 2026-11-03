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


def get(path, retries=8):
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(BASE + path, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            time.sleep(min(60, 5 * (i + 1)) if e.code == 429 else 2 * (i + 1))
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
    cols = ["series", "ticker", "event_ticker", "title", "yes_sub_title", "status", "yes_bid", "yes_ask", "last", "volume",
            "open_interest", "close_time", "quote_utc"]
    n = 0
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(cols)
        for s in sers:
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
        rows.setdefault(name, []).append(sum(ps) / len(ps) if ps else None)
    return {k: (v[0] if len(v) == 1 else None) for k, v in rows.items()}
