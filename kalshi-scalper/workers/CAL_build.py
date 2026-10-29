"""CAL: build kalshi-scalper/studies/EVENT_CALENDAR_2026.csv (research only).
Dates below were transcribed on 2026-10-29 from the official pages named in each
row's source_url; Treasury rows and exchange maintenance rows come from the saved
JSON downloads (fiscaldata.treasury.gov API, Statuspage JSON of each status page).
Usage: python3 -I CAL_build.py <download_dir> <out_csv>
"""
import csv, json, sys, datetime as dt
from zoneinfo import ZoneInfo

ET, CT, UTC = ZoneInfo("America/New_York"), ZoneInfo("America/Chicago"), dt.timezone.utc
RET = "2026-10-29"
LO, HI = "2026-08-01", "2026-12-31"
rows = []

def add(event, detail, date, hhmm_et, src, status, note=""):
    if not (LO <= date <= HI):
        return
    y, m, d = map(int, date.split("-")); h, mi = map(int, hhmm_et.split(":"))
    t = dt.datetime(y, m, d, h, mi, tzinfo=ET)
    rows.append(dict(event=event, detail=detail, release_utc=t.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ"),
                     release_ct=t.astimezone(CT).strftime("%Y-%m-%d %H:%M %Z"), release_et=t.strftime("%Y-%m-%d %H:%M %Z"),
                     status=status, source_url=src, retrieved=RET, note=note))

BLS = "https://www.bls.gov/schedule/2026/home.htm"
for date, ref in [("2026-08-12","Jul 2026"),("2026-09-11","Aug 2026"),("2026-10-14","Sep 2026"),("2026-11-10","Oct 2026"),("2026-12-10","Nov 2026")]:
    add("CPI", "Consumer Price Index for " + ref, date, "08:30", BLS, "verified",
        "past dates also match https://www.bls.gov/bls/news-release/cpi.htm" if date < RET else "")
for date, ref in [("2026-08-13","Jul 2026"),("2026-09-10","Aug 2026"),("2026-10-15","Sep 2026"),("2026-11-13","Oct 2026"),("2026-12-15","Nov 2026")]:
    add("PPI", "Producer Price Index for " + ref, date, "08:30", BLS, "verified",
        "past dates also match https://www.bls.gov/bls/news-release/ppi.htm" if date < RET else "")
for date, ref in [("2026-08-07","Jul 2026"),("2026-09-04","Aug 2026"),("2026-10-02","Sep 2026"),("2026-11-06","Oct 2026"),("2026-12-04","Nov 2026")]:
    add("JOBS", "Employment Situation for " + ref, date, "08:30", BLS, "verified",
        "past dates also match https://www.bls.gov/bls/news-release/empsit.htm" if date < RET else "")

BEA = "https://www.bea.gov/news/schedule/full"
for date, det in [("2026-08-26","GDP (Second Estimate) 2nd Quarter 2026"),("2026-09-30","GDP (Third Estimate) 2nd Quarter 2026"),
                  ("2026-10-29","GDP (Advance Estimate) 3rd Quarter 2026"),("2026-11-25","GDP (Second Estimate) 3rd Quarter 2026"),
                  ("2026-12-23","GDP (Third Estimate) 3rd Quarter 2026")]:
    add("GDP", det, date, "08:30", BEA, "verified")
for date, det in [("2026-08-26","Personal Income and Outlays, July 2026"),("2026-09-30","Personal Income and Outlays, August 2026"),
                  ("2026-10-29","Personal Income and Outlays, September 2026"),("2026-11-25","Personal Income and Outlays, October 2026"),
                  ("2026-12-23","Personal Income and Outlays, November 2026")]:
    add("PCE", det, date, "08:30", BEA, "verified", "PCE price index is in this release")

CEN = "https://www.census.gov/retail/release_schedule.html"
for date, ref, src in [("2026-08-14","Jul 2026","https://www2.census.gov/retail/releases/historical/marts/adv2607.pdf"),
                       ("2026-09-16","Aug 2026","https://www2.census.gov/retail/releases/historical/marts/adv2608.pdf"),
                       ("2026-10-15","Sep 2026",CEN),("2026-11-17","Oct 2026",CEN),("2026-12-16","Nov 2026",CEN)]:
    add("RETAIL", "Advance Monthly Retail Sales for " + ref, date, "08:30", src, "verified")

FED = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
add("FOMC", "FOMC statement (Sep 15-16 meeting, SEP)", "2026-09-16", "14:00",
    "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm", "verified", "For release at 2:00 p.m. EDT")
add("FOMC", "FOMC statement (Oct 27-28 meeting)", "2026-10-28", "14:00",
    "https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm", "verified", "For release at 2:00 p.m. EDT")
add("FOMC", "FOMC statement (Dec 8-9 meeting, SEP)", "2026-12-09", "14:00", FED, "rule",
    "date from the FOMC calendar; the calendar states no time; 2:00 p.m. ET is the time of every 2026 statement checked (Jul, Sep, Oct)")

# Weekly claims: DOL pages (dol.gov) answered HTTP 403 to this session; rule only.
DOL = "https://www.dol.gov/ui/data.pdf"
d = dt.date(2026, 8, 6)
while d.isoformat() <= HI:
    iso = d.isoformat()
    if iso in ("2026-11-26", "2026-12-24", "2026-12-31"):
        st, nt = "unverified", "holiday week; DOL may move the release; not confirmed (dol.gov returned 403); left out of counts"
    else:
        st, nt = "rule", "Thursday 8:30 a.m. ET weekly rule (release embargo line); per-date page not retrievable (dol.gov 403); 2026-10-29 seen in the DOL release as indexed by search"
    add("CLAIMS", "Unemployment Insurance Weekly Claims", iso, "08:30", DOL, st, nt)
    d += dt.timedelta(days=7)

EIA = "https://www.eia.gov/petroleum/supply/weekly/schedule.php"
shift = {"2026-09-09": "2026-09-10", "2026-10-14": "2026-10-15", "2026-11-11": "2026-11-12"}
d = dt.date(2026, 8, 5)
while d.isoformat() <= HI:
    iso = d.isoformat()
    if iso in shift:
        add("EIA_WPSR", "Weekly Petroleum Status Report (holiday shift)", shift[iso], "12:00", EIA, "verified", "listed holiday change: Thursday 12:00 ET")
    else:
        add("EIA_WPSR", "Weekly Petroleum Status Report", iso, "10:30", EIA, "verified", "standard Wednesday 10:30 ET; not in the page's holiday-change list")
    d += dt.timedelta(days=7)

dl = sys.argv[1]
TSY = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
seen = set()
for x in json.load(open(dl + "/auctions.json"))["data"]:
    t = dt.datetime.strptime(x["closing_time_comp"], "%I:%M %p").strftime("%H:%M")
    kind = "TSY_BILL" if x["security_type"] in ("Bill", "CMB") else "TSY_COUPON"
    key = (x["auction_date"], x["security_type"], x["security_term"]); seen.add(key)
    add(kind, f'{x["security_term"]} {x["security_type"]} auction close (competitive), reopening={x["reopening"]}', x["auction_date"], t, TSY, "verified")
UPC = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/upcoming_auctions"
for x in json.load(open(dl + "/upcoming.json"))["data"]:
    key = (x["auction_date"], x["security_type"], x["security_term"])
    if key in seen or x["auction_date"] < LO:
        continue
    kind = "TSY_BILL" if x["security_type"] in ("Bill", "CMB") else "TSY_COUPON"
    add(kind, f'{x["security_term"]} {x["security_type"]} auction (announced {x["announcemt_date"]})', x["auction_date"],
        "11:30" if kind == "TSY_BILL" else "13:00", UPC, "rule",
        "date official (announced); this feed has no closing time; time is the closing time of every completed auction of that kind in the window")

TRADE = ("system maintenance", "order entry", "website and api", "infrastructure", "trading halt", "database")
for host in ("status.coinbase.com", "status.kraken.com", "status.bitstamp.net"):
    for m in json.load(open(f"{dl}/{host}.sched.json"))["scheduled_maintenances"]:
        s = dt.datetime.fromisoformat(m["scheduled_for"].replace("Z", "+00:00"))
        u = dt.datetime.fromisoformat(m["scheduled_until"].replace("Z", "+00:00"))
        if not (LO <= s.astimezone(UTC).date().isoformat() <= HI):
            continue
        name = m["name"].replace("\n", " ").strip()
        trading = any(k in name.lower() for k in TRADE)
        se = s.astimezone(ET)
        add("MAINT_" + host.split(".")[1].upper(), name[:120], se.date().isoformat(), se.strftime("%H:%M"), m["shortlink"], "verified",
            f'until {u.astimezone(UTC).strftime("%Y-%m-%dT%H:%MZ")}; status {m["status"]}; '
            + ("trading or API scope" if trading else "not trading scope (funding, banking, asset or product specific)"))

rows.sort(key=lambda r: (r["release_utc"], r["event"]))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
import collections
print(len(rows), collections.Counter((r["event"], r["status"]) for r in rows))
