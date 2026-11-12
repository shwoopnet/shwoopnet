#!/usr/bin/env python3
"""Family census: one day of settled markets (the CENSUS_LISTING pull, Nov 10, 2026 UTC) by family.

Reads series_day.csv written by read_listing.py and groups series into families by ticker
pattern. Counts and sums only: series, events, markets, contracts traded, contracts a market.
Hours of the pull that hit the page cap make every figure a LOWER BOUND.

Usage: python3 family_day.py <series_day.csv> <out dir>
"""
import csv, os, re, sys
from first_cut import RULES as OLD

NEW = [
    ("m15_all", r"15M$"),
    ("virtual_sports", r"^KX(ESOCCER|EBASKETBALL|LIGAPRO)"),
    ("tennis_itf", r"^KXITF"),
    ("tennis_sets_exact", r"^KX(ATP|WTA)(SETWINNER|EXACTMATCH)"),
    ("esports", r"^KX(CS2|LOL|R6|DOTA2|VALORANT)"),
    ("darts_chess_other", r"^KX(DARTS|TITLEDTUES|PBA)"),
    ("overtime_markets", r"^KX(NBA|NHL|NCAAMB|NCAAF)OT$"),
    ("nba_periods", r"^KXNBA([1-4]Q|[12]H)(SPREAD|TOTAL|TEAMTOTAL)?$"),
    ("nba_props", r"^KXNBA(PTS|REB|AST|3PT|BLK|STL|PRA|2D|3D|ESCALATOR|STOCK|PTSLEADER)"),
    ("nba_game_extras", r"^KXNBA(RACE|WINMARGIN|TEAMTOTAL)$"),
    ("us_spread_total", r"^KX(NBA|NHL|NFL|MLB)(SPREAD|TOTAL|TEAMTOTAL|TOTALPRECISE)$"),
    ("college_basketball", r"^KXNCAA(MB|WB)"),
    ("nhl_props", r"^KXNHL(AST|F10G|FIRSTGOAL|GOAL|PTS|SAVE)"),
    ("nfl_periods", r"^KXNFL([1-4E]Q|[12]H)(SPREAD|TOTAL|FT|BTTS|TEAMTOTAL)?$"),
    ("nfl_props", r"^KXNFL(FF|FG|FIRSTTD|LONG|MOST|PASS|REC|RSH|SFTY|TDPROT|TEAMFIRSTTD|WEEK|RACE|NEXTTEAM|SEASON|TRADE|WINS)"),
    ("ncaaf_other", r"^KXNCAAF"),
    ("cricket", r"^KX(T20|WT20|ODI|TEST)MATCH"),
    ("soccer_btts", r"BTTS$"),
    ("intl_basketball", r"^KX(EUROCUP|FIBA|ARGLNB|JBLEAGUE|KBL|NBB|SESBL|VTB|LIGMAG|SKL|MLBB|NBL|BBL|BSL|ABA)"),
    ("hockey_other", r"^KX(AHL|KHL|EUCHL)GAME"),
    ("golf", r"^KXPGA"),
    ("wx_hourly_temp", r"^KXTEMP"),
    ("rates_hourly_event", r"^KX\d+YR(RATE|DIR)"),
    ("rates_daily", r"^KX(UST\d+AD?|SOFRD)$"),
    ("index_intraday", r"^KX(INX|NASDAQ100|NDQ|NASDAQ)(U|HUD|DUD)$"),
    ("index_ladder", r"^KX(INX|NASDAQ100|DJI)$"),
    ("crypto_hourly_daily", r"^KX(BTC|ETH|XRP|SOL|DOGE|HYPE|BNB|SHIBA|ZEC|NEAR)(D|E|MINMON|MAXMON)?$"),
    ("commodity_hourly", r"^KX(GOLD|SILVER|WTI|PALLADIUM|PLATINUM|COPPER|BRENT|NATGAS)H$"),
    ("commodity_ladder", r"^KX(NATGAS|COPPER|GOLD|SILVER|BRENT|WTI)[DW]?$"),
    ("fx_ladder", r"^KX[A-Z]{6}(AD|AW|EVENT)?$"),
    ("macro_release", r"^KX(CPI|ECONSTAT|UE$|AIRFARE|SHELTER|USEDCAR|USGAS|OER|EGGS|AUTODELQ|POWERKWH|AAAGASMINM)"),
    ("earnings_mentions", r"^KXEARNINGSMENTION"),
    ("mentions", r"MENTION$|^KXTRUMPSAY"),
    ("official_counts", r"^KX(HORMUZ|PANAMA|SUEZ|MAXSHIPS|TSAD|TRUMPACTD)"),
    ("music_video_charts", r"^KX(YT|ARTISTSTREAMS|WEEKSNUM1)"),
    ("streaming_charts", r"^KXNETFLIX"),
    ("steam", r"^KXSTEAM"),
]
RULES = NEW + OLD

def family(t):
    for k, rx in RULES:
        if re.search(rx, t):
            return k
    return "unmapped"

def main(src, out):
    fam, un = {}, []
    for r in csv.DictReader(open(src)):
        ev = int(float(r["settled_events_day"]))
        if not ev:
            continue
        k = family(r["series"])
        if k == "unmapped":
            k = "other:" + (r["category"] or "no category")
            un.append((r["series"], r["category"], ev, round(float(r["volume_day"]))))
        a = fam.setdefault(k, dict(family=k, series=0, events=0, markets=0, volume=0.0, tie=0, never=0, new=0))
        a["series"] += 1; a["events"] += ev; a["markets"] += int(float(r["settled_markets_day"]))
        a["volume"] += float(r["volume_day"]); a["tie"] += int(float(r["tie_markets"]))
        a["never"] += r["sweep_status"].startswith("eligible"); a["new"] += r["sweep_status"].startswith("not in")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "family_day.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family", "series_settling", "events_day", "markets_day", "contracts_day", "contracts_a_market",
                    "tie_markets", "series_never_read_by_sweeps", "series_not_in_sweep_files"])
        for a in sorted(fam.values(), key=lambda a: -a["events"]):
            row = [a["family"], a["series"], a["events"], a["markets"], round(a["volume"]), round(a["volume"] / max(1, a["markets"])),
                   a["tie"], a["never"], a["new"]]
            w.writerow(row); print(" | ".join(str(x) for x in row))
    print("unmapped series:", len(un))
    for u in sorted(un, key=lambda u: -u[3])[:60]:
        print("  ", u)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
