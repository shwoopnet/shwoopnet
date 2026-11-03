"""STRADDLE1 earnings event list from keyless SEC EDGAR. Infrastructure only: no returns, no option prices, scores nothing.

Universe rule (metadata only, fixed before any return is looked at): the current S&P 500 constituents from Wikipedia's
public table (deduplicated by CIK, so GOOG/GOOGL is one company), each required to appear in SEC's
company_tickers_exchange.json with a Nasdaq or NYSE listing. A size proxy chosen without any price or return.
Known bias, stated: current members, so names that left the index (often after falling) are absent. Metadata only.

Events: every 8-K (not 8-K/A) whose Items include 2.02, acceptanceDateTime >= 2023-06-01 minus a lookback, then the
EARLIEST 2.02 filing in each cluster (filings of one CIK less than 45 days apart are one quarter). Dates follow
workers/STRADDLE1_REGISTRATION.md via straddle1.exit_day / entry_day with a hard-coded NYSE calendar.
Split by event (announcement) date only: first two thirds -> halves A and B, final third FROZEN.
Usage: python3 -I -B src/scalper/straddle1_events.py <cache_dir> <out_csv> <universe_csv>
"""
import csv, datetime as dt, io, json, os, sys, time, urllib.request
from collections import Counter
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import straddle1 as s1

UA = "ShwoopnetResearch research-contact@shwoopnet.com"
START = dt.date(2023, 6, 1)
LAST_DATA_DAY = dt.date(2026, 10, 30)  # ThetaData free tier is delayed one day; exits after this are not scoreable yet
NY, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")

HOLIDAYS = """2023-01-02 2023-01-16 2023-02-20 2023-04-07 2023-05-29 2023-06-19 2023-07-04 2023-09-04 2023-11-23 2023-12-25
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26 2026-12-25""".split()
HOLIDAYS = {dt.date.fromisoformat(x) for x in HOLIDAYS}


def trading_days(a=dt.date(2023, 1, 1), b=dt.date(2026, 12, 31)):
    out, d = [], a
    while d <= b:
        if d.weekday() < 5 and d not in HOLIDAYS:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def classify(accept_et):
    """BMO before 09:30 ET, AMC at or after 16:00 ET, INTRADAY between (weekend/holiday acceptances count as BMO)."""
    if accept_et.date().weekday() >= 5 or accept_et.date() in HOLIDAYS:
        return "BMO"
    t = accept_et.time()
    if t < dt.time(9, 30):
        return "BMO"
    if t >= dt.time(16, 0):
        return "AMC"
    return "INTRADAY"


def parse_accept(s):
    u = dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    return u, u.astimezone(NY)


def cluster_earliest(rows, gap_days=45):
    """rows sorted by time for ONE cik -> list of (row, n_in_cluster). Earliest 2.02 of each quarter is the event."""
    out = []
    for r in rows:
        if out and (r["et"] - out[-1][0]["et"]).days < gap_days:
            out[-1][1] += 1
        else:
            out.append([r, 1])
    return out


def build_events(filings_by_cik, meta, tdays):
    """filings_by_cik: cik -> list of dicts(form, items, filing_date, accept_utc, accept_et, acc). Pure function (tested)."""
    drops = Counter()
    events = []
    for cik, fl in filings_by_cik.items():
        keep = []
        for f in fl:
            if f["form"] != "8-K":
                if "2.02" in f["items"].split(","):
                    drops["8-K/A or other form with 2.02"] += 1
                continue
            if "2.02" not in f["items"].split(","):
                continue
            if not f.get("accept_utc"):
                drops["missing acceptance time"] += 1
                continue
            keep.append(f)
        keep.sort(key=lambda r: r["utc"])
        for r, n in cluster_earliest(keep):
            et = r["et"]
            kind = classify(et)
            if kind == "INTRADAY":
                drops["intraday (09:30-16:00 ET), excluded"] += 1
                continue
            exit_d = s1.exit_day(et.replace(tzinfo=None), tdays)
            try:
                entry_d = s1.entry_day(exit_d, tdays)
            except Exception:
                drops["no calendar"] += 1
                continue
            if entry_d < START:
                drops["entry before 2023-06-01"] += 1
                continue
            if exit_d > LAST_DATA_DAY:
                drops["exit after last scoreable day"] += 1
                continue
            ann = exit_d if kind == "AMC" else min(x for x in tdays if x >= et.date())
            events.append(dict(ticker=meta[cik]["ticker"], cik=cik, accession=r["acc"], filing_date=r["filing_date"],
                               accept_utc=r["utc"].strftime("%Y-%m-%dT%H:%M:%SZ"), accept_et=et.strftime("%Y-%m-%d %H:%M:%S"),
                               timing=kind, announce_day=ann.isoformat(), entry_close=entry_d.isoformat(),
                               exit_close=exit_d.isoformat(), cluster_n=n, flag_multi202=int(n > 1)))
    events.sort(key=lambda e: (e["announce_day"], e["ticker"]))
    return events, drops


def assign_split(events):
    """By announcement date only. Cut points are nudged forward to a date change so one day is never split.
    First two thirds -> A (first half) / B (second half); final third -> FROZEN."""
    n = len(events)

    def snap(i):
        while 0 < i < n and events[i]["announce_day"] == events[i - 1]["announce_day"]:
            i += 1
        return i
    cut2 = snap((2 * n) // 3)
    cutA = snap(cut2 // 2)
    for i, e in enumerate(events):
        e["split"] = "A" if i < cutA else ("B" if i < cut2 else "FROZEN")
    return events


def get(url, cache, name):
    p = os.path.join(cache, name)
    if os.path.exists(p):
        return open(p, "rb").read()
    time.sleep(0.25)  # <= 4 requests a second, under SEC's 10/s limit and the 5/s asked for
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    data = urllib.request.urlopen(req, timeout=40).read()
    open(p, "wb").write(data)
    return data


def universe(cache):
    import pandas as pd
    html = get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", cache, "sp500.html").decode()
    t = pd.read_html(io.StringIO(html), match="Symbol")[0]
    cte = json.loads(get("https://www.sec.gov/files/company_tickers_exchange.json", cache, "cte.json"))
    listed = {int(r[0]): r for r in cte["data"] if r[3] in ("Nasdaq", "NYSE")}
    meta, dropped = {}, 0
    for sym, cik in zip(t["Symbol"], t["CIK"]):
        cik = int(cik)
        if cik in meta:
            continue
        if cik not in listed:
            dropped += 1
            continue
        meta[cik] = dict(ticker=str(sym), exchange=listed[cik][3])
    return meta, len(t), dropped


def fetch_filings(meta, cache):
    out = {}
    for cik in meta:
        j = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", cache, f"sub{cik}.json"))
        blocks = [j["filings"]["recent"]]
        if j["filings"]["recent"]["filingDate"] and j["filings"]["recent"]["filingDate"][-1] > "2023-05-01":
            for fl in j["filings"]["files"]:
                if fl["filingTo"] >= "2023-05-01":
                    blocks.append(json.loads(get("https://data.sec.gov/submissions/" + fl["name"], cache, f"{cik}_{fl['name']}")))
        rows = []
        for b in blocks:
            for i in range(len(b["form"])):
                if b["filingDate"][i] < "2023-05-01":
                    continue
                if "2.02" not in (b["items"][i] or "").split(","):
                    continue
                a = b["acceptanceDateTime"][i]
                row = dict(form=b["form"][i], items=b["items"][i], filing_date=b["filingDate"][i], acc=b["accessionNumber"][i], accept_utc=a)
                if a:
                    u, e = parse_accept(a)
                    row["utc"], row["et"] = u, e
                rows.append(row)
        out[cik] = rows
    return out


FIELDS = ["ticker", "cik", "accession", "filing_date", "accept_utc", "accept_et", "timing", "announce_day", "entry_close",
          "exit_close", "cluster_n", "flag_multi202", "split"]


def main(cache, out_csv, uni_csv):
    os.makedirs(cache, exist_ok=True)
    meta, n_rows, n_unlisted = universe(cache)
    with open(uni_csv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["cik", "ticker", "exchange"])
        for c, m in meta.items():
            w.writerow([c, m["ticker"], m["exchange"]])
    ev, drops = build_events(fetch_filings(meta, cache), meta, trading_days())
    ev = assign_split(ev)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(ev)
    print("universe rows", n_rows, "unique listed", len(meta), "unlisted/no-match dropped", n_unlisted)
    print("events", len(ev), "drops", dict(drops))
    return ev, meta, drops


if __name__ == "__main__":
    main(*sys.argv[1:4])
