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


def slugify(title, sep):
    """'Wild Horse Nine' -> wild_horse_nine (or wild-horse-nine). Only letters and digits survive; an odd title gives a wrong URL, which is a counted failed read, not a value."""
    s = re.sub(r"[^a-z0-9]+", sep, title.lower().replace("&", " and ").replace("'", "")).strip(sep)
    return s


ADAPTERS = {
    "apple": (apple_urls, apple_parse),
    "steam": (steam_urls, steam_parse),
}
