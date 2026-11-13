#!/usr/bin/env python3
"""First cut of the family census from V2's three universe sweeps (no new read).

Input: USWEEP1_SERIES.json, USWEEP2_SERIES.json, USWEEP3_SERIES.json as committed on
branch claude/epic-ptolemy-0amjd9 under kalshi-scalper/workers/ (public market
counts taken on 2026-11-03: settled markets and close dates in 60 days, median
volume of a settled market). Output: first_cut_series.csv (one row per series)
and first_cut_families.csv (one row per family). Counts only; no price, no result.

Usage: python3 first_cut.py <dir with the three json files> <out dir>
"""
import csv, json, os, re, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
from deskb_guard import refuse_all as _refuse_all
_refuse_all()   # standing rule (h): refuse any HELDOUT_ folder before the first open or glob

# (family key, regex on the series ticker). First match wins.
RULES = [
    ("wx_daily_temp", r"^KX(HIGH|LOWT)"),
    ("wx_rain", r"^KXRAIN"),
    ("wx_hazard", r"^KXBIGGESTQUAKE"),
    ("gas_price", r"^KX(AAAGAS|DIESEL)"),
    ("commodity_ladder", r"^KX(NATGAS|COPPER|GOLD|SILVER|BRENT|WTI)[DW]?$"),
    ("crypto_ladder", r"^KXSHIBA"),
    ("index_ladder", r"^KX(INX|NASDAQ100|DJI)"),
    ("fx_ladder", r"^KX(GBPUSD|NZDUSD|AUDUSD|EURUSD|USDJPY|USDSEK|USDMXN|USDBRL|USDCAD)"),
    ("rates_daily", r"^KX(UST\d+A|SOFRD|30YMORTW)"),
    ("macro_release", r"^KXUE$"),
    ("power_demand", r"^KXTXERCOT"),
    ("truflation", r"^KXTRUEV"),
    ("approval_ballot", r"^KX(TRUMPAPPROVE|VHGCB)"),
    ("post_counts", r"^KXTRUTHSOCIAL"),
    ("mentions", r"^KX(TRUMPMENTION|TRUMPSAY)"),
    ("music_video_charts", r"^KX(YTTOPVIDEO|TOPSONG|BILLBOARD|ALBUMEQUIV|PUREALBUMS)"),
    ("streaming_charts", r"^KXNETFLIX"),
    ("ai_share", r"^KXOPENSOURCESHARE"),
    ("nfl_periods", r"^KXNFL([1-4]Q|[12]H)(SPREAD|TOTAL|FT)?$"),
    ("ncaaf_periods", r"^KXNCAAF([1-4]Q|[12]H|OT)$"),
    ("nhl_periods", r"^KXNHL[1-3]P(SPREAD|TOTAL)?$"),
    ("nba_mls_periods", r"^KX(NBA|MLS)[12]H(SPREAD|TOTAL)?$"),
    ("nfl_props", r"^KXNFL(FG|RSHATT|PASS|RRYDS|FFPTS|ESCALATOR|LADDER|LONG|TEAM|FIRSTTD|WINMARGIN|BOTH)"),
    ("ncaaf_props", r"^KXNCAAF(TEAMRECTD|FIRSTTDTEAM)"),
    ("nhl_props", r"^KXNHLSAVE"),
    ("mlb_props", r"^KXMLBHA"),
    ("us_game_winner", r"^KX(MLB|NBA|NHL|NFL|NCAAF|MLS)GAME$"),
    ("minor_hockey", r"^KX(AHL|KHL)GAME$"),
    ("tennis", r"^KX(ATP|WTA)"),
    ("esports", r"^KX(DOTA2|VALORANT)"),
    ("cricket", r"^KXT20"),
    ("nascar", r"^KXNASCAR"),
    ("volleyball", r"^KXNCAAWV"),
    ("intl_basketball", r"^KX(NBL|BBL|BSL|ABA|VTB)(TOTAL|SPREAD)$"),
    ("soccer_extras", r"(CORNERS|TEAMTOTAL|BTTS)$"),
    ("soccer_major", r"^KX(EPL|LALIGA|SERIEA|BUNDESLIGA|LIGUE1|MLS|LIGAMX)(TOTAL|SPREAD|GAME)$"),
    ("soccer_minor", r"(TOTAL|SPREAD|GAME|1H|1HTOTAL)$"),
]

def family(t):
    for k, rx in RULES:
        if re.search(rx, t):
            return k
    return "unmapped"

def main(src, out):
    rows = {}
    for f, tag in (("USWEEP1_SERIES.json", "U1"), ("USWEEP2_SERIES.json", "U2"), ("USWEEP3_SERIES.json", "U3")):
        d = json.load(open(os.path.join(src, f)))
        for r in d["series"]:
            rows[r["ticker"]] = dict(series=r["ticker"], category=r["cat"], frequency=r["freq"], title=r["title"],
                                     settled_60d=r["n"], close_dates_60d=r["dates"], capped=r.get("capped", False),
                                     median_volume=round(r["median_volume"]), sweep=tag, sweep_status="tail rule read")
        for t in d.get("budget_skipped") or []:
            rows.setdefault(t, dict(series=t, category="Sports?", frequency="", title="", settled_60d="300+",
                                    close_dates_60d="20+", capped="", median_volume="100+", sweep=tag,
                                    sweep_status="eligible, never read"))
    for r in rows.values():
        r["family"] = family(r["series"])
    os.makedirs(out, exist_ok=True)
    cols = ["family", "series", "category", "frequency", "title", "settled_60d", "close_dates_60d", "capped",
            "median_volume", "sweep", "sweep_status"]
    with open(os.path.join(out, "first_cut_series.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, cols); w.writeheader()
        for r in sorted(rows.values(), key=lambda r: (r["family"], r["series"])):
            w.writerow(r)
    fam = {}
    for r in rows.values():
        a = fam.setdefault(r["family"], dict(family=r["family"], series=0, read=0, never_read=0, max_dates_60d=0,
                                             settled_60d=0, vols=[]))
        a["series"] += 1
        if r["sweep_status"] == "tail rule read":
            a["read"] += 1
            a["max_dates_60d"] = max(a["max_dates_60d"], r["close_dates_60d"])
            a["settled_60d"] += r["settled_60d"]
            a["vols"].append(r["median_volume"])
        else:
            a["never_read"] += 1
    with open(os.path.join(out, "first_cut_families.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "series", "read_by_sweep", "eligible_never_read", "max_close_dates_60d",
                    "settled_markets_60d_of_read", "median_of_series_median_volume"])
        for a in sorted(fam.values(), key=lambda a: a["family"]):
            v = sorted(a["vols"]); med = v[len(v) // 2] if v else ""
            w.writerow([a["family"], a["series"], a["read"], a["never_read"], a["max_dates_60d"], a["settled_60d"], med])
            print(f'{a["family"]:20} series {a["series"]:3} read {a["read"]:3} never {a["never_read"]:3} '
                  f'dates {a["max_dates_60d"]:3} settled {a["settled_60d"]:6} medvol {med}')
    print("series", len(rows), "unmapped", [r["series"] for r in rows.values() if r["family"] == "unmapped"])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
