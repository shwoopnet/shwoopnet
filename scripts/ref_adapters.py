"""Reference-value adapters for the REFREC recorder (scripts/record_ref.py; workers/RECREF_NOTES.md). Research only.

One small adapter per source whose terms allow automated reads (Nov 11, 2026: the sources whose terms forbid or have not been checked were removed, see CLAUDE.md). Each has a URL builder and a parser:

    urls(params)  -> list of URLs to GET (usually one)
    parse(params, bodies) -> list of rows [rank, name, value, value2, note]

The parser works on text already downloaded, so a saved fixture tests it with no network. A parser never raises on a changed page: it returns an empty list, and the
recorder counts that as a parse failure in the run log (a source that quietly changes shape is the main way this kind of recorder rots). Public GET only, no key."""
import json
import re
from urllib.parse import quote

UA = "shwoopnet-research-recorder (public data, GET only)"


def _num(s):
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


# ---- Apple App Store top chart ------------------------------------------------------------------------------------------------------------------------------
def apple_urls(p):
    return [p["url"]]


def apple_parse(p, bodies):
    """Apple's marketing RSS (results[]) or the older iTunes RSS (feed.entry[]). Rank is the list position."""
    try:
        d = json.loads(bodies[0])
    except ValueError:
        return []
    feed = d.get("feed") or {}
    out = []
    if feed.get("results"):
        for i, r in enumerate(feed["results"][: p.get("top", 50)], 1):
            out.append([i, r.get("name", ""), None, None, str(r.get("id", ""))])
    elif feed.get("entry"):
        for i, e in enumerate(feed["entry"][: p.get("top", 50)], 1):
            nm = ((e.get("im:name") or {}).get("label")) or ""
            idv = (((e.get("id") or {}).get("attributes")) or {}).get("im:id", "")
            out.append([i, nm, None, None, idv])
    return out


# ---- Steam top sellers (the store's current list, a proxy for the weekly revenue chart) -------------------------------------------------------------------
def steam_urls(p):
    return [p["url"]]


def steam_parse(p, bodies):
    try:
        items = json.loads(bodies[0])["items"]
    except (ValueError, KeyError, TypeError):
        return []
    return [[i, (it.get("name") or "").strip(), None, None, "store_topsellers_current"] for i, it in enumerate(items[: p.get("top", 25)], 1)]


# ---- Yahoo Finance 1-minute chart (forex, WTI, natural gas, silver: the reference the Kalshi hourly and daily ladders settle near) ------------------------------
YH_HOSTS = ("query2.finance.yahoo.com", "query1.finance.yahoo.com")   # the same public chart service on two hosts: one is sometimes answered 429 when the other is not (seen Nov 4, 2026)


def yahoo1m_url(symbol, rng, host=None):
    """Yahoo's public chart endpoint, 1 minute bars. It keeps only about 7 days of 1 minute data, so a first run asks for 7d (the backfill) and later runs ask for 1d."""
    return "https://%s/v8/finance/chart/%s?interval=1m&range=%s&includePrePost=false" % (host or YH_HOSTS[0], quote(symbol), rng)


def yahoo1m_parse(p, bodies):
    """One row per 1 minute bar with a close: [unix second, symbol, close, volume, 'o=..;h=..;l=..']. Bars at or before p['after_ts'] are dropped (already on file), so a re-read adds only
    new minutes. A body that is not a chart with timestamps returns [] (counted as a parse failure by the recorder), never a made-up value."""
    try:
        res = json.loads(bodies[0])["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        sym = res["meta"]["symbol"]
    except (ValueError, KeyError, IndexError, TypeError):
        return []
    after = p.get("after_ts") or 0
    out = []
    for i, t in enumerate(ts):
        try:
            c = q["close"][i]
            if c is None or t <= after:
                continue
            ohl = ";".join("%s=%s" % (k, q[n][i]) for k, n in (("o", "open"), ("h", "high"), ("l", "low")))
            v = q["volume"][i] if q.get("volume") else None
            out.append([int(t), sym, c, v if v is not None else "", ohl])
        except (IndexError, KeyError, TypeError):
            continue
    return out


def slugify(title, sep):
    """'Wild Horse Nine' -> wild_horse_nine (or wild-horse-nine). Only letters and digits survive; an odd title gives a wrong URL, which is a counted failed read, not a value."""
    s = re.sub(r"[^a-z0-9]+", sep, title.lower().replace("&", " and ").replace("'", "")).strip(sep)
    return s


ADAPTERS = {
    "apple": (apple_urls, apple_parse),
    "steam": (steam_urls, steam_parse),
    "yahoo1m": (None, yahoo1m_parse),            # the URL comes from the symbol and the range (see record_ref.run_standalone)
}
