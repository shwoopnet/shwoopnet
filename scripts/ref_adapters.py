"""Reference-value adapters for the REFREC recorder (scripts/record_ref.py; workers/RECREF_NOTES.md). Research only.

One small adapter per public source. Each has a URL builder and a parser:

    urls(params)  -> list of URLs to GET (usually one)
    parse(params, bodies) -> list of rows [rank, name, value, value2, note]

The parser works on text already downloaded, so a saved fixture tests it with no network. A parser never raises on a changed page: it returns an empty list, and the
recorder counts that as a parse failure in the run log (a source that quietly changes shape is the main way this kind of recorder rots). Public GET only, no key."""
import html
import json
import re
from urllib.parse import quote

UA = "shwoopnet-research-recorder (public data, GET only)"


def _num(s):
    try:
        return float(str(s).replace(",", "").replace("%", "").strip())
    except ValueError:
        return None


# ---- kworb Spotify chart (daily or weekly, any country page) -------------------------------------------------------------------------------------------------
def kworb_urls(p):
    return [p["url"]]


def kworb_parse(p, bodies):
    """Top `top` rows of a kworb chart table: rank, 'Artist - Title', streams, total. Streams are the chart's own figure (the day or week ending on the page's date)."""
    h = bodies[0]
    i = h.find("<tbody>")
    if i < 0:
        return []
    out = []
    for tr in re.findall(r"<tr>(.*?)</tr>", h[i:], re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) < 7:
            continue
        rank = _num(tds[0])
        name = html.unescape(re.sub(r"<[^>]+>", "", tds[2])).strip()
        streams = _num(tds[6])
        total = _num(tds[-1])
        if rank is None or not name:
            continue
        out.append([int(rank), name, streams, total, ""])
        if len(out) >= p.get("top", 20):
            break
    return out


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


# ---- Rotten Tomatoes title page -------------------------------------------------------------------------------------------------------------------------------
def rt_urls(p):
    return [p["url"]]


def rt_parse(p, bodies):
    """Tomatometer (critics, percent, with its review count) and Popcornmeter (audience, percent) from the page's own embedded data. None when the page has no score yet."""
    h = bodies[0]
    out = []
    m = re.search(r'"@type"\s*:\s*"AggregateRating"[^{}]*?"name"\s*:\s*"Tomatometer"[^{}]*?"ratingValue"\s*:\s*"?([0-9.]+)"?[^{}]*?"reviewCount"\s*:\s*([0-9]+)', h, re.S)
    if m:
        out.append([1, "tomatometer", _num(m.group(1)), _num(m.group(2)), "percent;critic_reviews"])
    a = re.search(r'"scorePercent"\s*:\s*"([0-9]+)%"[^{}]*?"title"\s*:\s*"Popcornmeter"', h, re.S)
    if a:
        out.append([2, "popcornmeter", _num(a.group(1)), None, "percent"])
    if not out and "media-hero-json" in h and "Tomatometer" in h:
        # Nov 4, 2026 (RECPATCH1): a real title page whose critics have not published a score yet (embargo or too few reviews) has no AggregateRating at all. That is a
        # normal state, not a parser failure (it was counted as one on every run: 3 of 3 films on 11-04). Marked so a later read can tell "no score yet" from "page unreadable".
        out.append([1, "tomatometer", None, None, "no_score_yet"])
    return out


# ---- Metacritic title page ------------------------------------------------------------------------------------------------------------------------------------
def mc_urls(p):
    return [p["url"]]


def mc_parse(p, bodies):
    """Metascore and its review count from the page's AggregateRating."""
    m = re.search(r'"@type"\s*:\s*"AggregateRating"[^{}]*?"ratingValue"\s*:\s*"?([0-9.]+)"?[^{}]*?"reviewCount"\s*:\s*"?([0-9]+)', bodies[0], re.S)
    return [[1, "metascore", _num(m.group(1)), _num(m.group(2)), "critic_reviews"]] if m else []


# ---- Polymarket xtracker post counts (a window of one account's posts) --------------------------------------------------------------------------------
XT = "https://xtracker.polymarket.com/api"


def xtracker_url(handle, start_iso, end_iso):
    return "%s/users/%s/posts?startDate=%s&endDate=%s" % (XT, quote(handle), quote(start_iso), quote(end_iso))


def xtracker_parse(p, bodies):
    """The number of posts in the window (one row). A count at the API's page size would be a cut-off, so it is marked."""
    try:
        posts = json.loads(bodies[0])["data"]
    except (ValueError, KeyError, TypeError):
        return []
    if not isinstance(posts, list):
        return []
    last = max([x.get("createdAt") or "" for x in posts] or [""])
    return [[1, "posts_in_window", len(posts), None, "last_post=%s%s" % (last, ";maybe_truncated" if len(posts) >= 1000 else "")]]


# ---- Billboard chart page (Hot 100 or Billboard 200: the chart as last published) ----------------------------------------------------------------------
def billboard_urls(p):
    return [p["url"]]


def billboard_parse(p, bodies):
    """Rank, title and artist of each row, plus the chart date in `note`. Billboard's page is large (3 to 5 MB) and its markup is not an API, so a changed layout returns []."""
    h = bodies[0]
    d = re.search(r'data-date="([0-9]{4}-[0-9]{2}-[0-9]{2})"', h)
    date = d.group(1) if d else ""
    out = []
    for blk in re.split(r'<ul class="o-chart-results-list-row ', h)[1:]:
        blk = blk[:6000]
        r = re.search(r'<span class="c-label[^>]*>\s*([0-9]+)\s*</span>', blk)
        ti = re.search(r'<h3 id="title-of-a-story"[^>]*>\s*(.*?)\s*</h3>\s*<span[^>]*>\s*(.*?)\s*</span>', blk, re.S)
        if not (r and ti):
            continue
        name = html.unescape(re.sub(r"<[^>]+>", "", ti.group(1))).strip()
        artist = html.unescape(re.sub(r"<[^>]+>", "", ti.group(2))).strip()
        out.append([int(r.group(1)), name + " - " + artist, None, None, "chart_date=" + date])
        if len(out) >= p.get("top", 25):
            break
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
    "kworb": (kworb_urls, kworb_parse),
    "apple": (apple_urls, apple_parse),
    "rt": (rt_urls, rt_parse),
    "mc": (mc_urls, mc_parse),
    "xtracker": (None, xtracker_parse),          # the URL comes from the market's own close time (see record_ref.targets_for)
    "billboard": (billboard_urls, billboard_parse),
    "steam": (steam_urls, steam_parse),
}
