"""Independent REMATCH counts (History Miner), written separately from Desk B's count_listing.py. Times and tickers only:
no price field and no result field is read. Usage: python3 -I rematch_count.py <list folder>...
Per UTC day of S: matches, distinct pairs, next meetings of a pair, of those with B's S 20 to 60 and 20 to 120 minutes after A's,
A settled at least 12 minutes before B's S, and B's market open before A's S (strict, and 3 minutes before)."""
import calendar, collections, gzip, json, os, sys, time
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}

def iso(s):
    if not s: return None
    s = s.split(".")[0].rstrip("Z")
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))

def et_off(y, mo, d, hh, mi):
    def nsun(yr, m, n):
        return 1 + (6 - calendar.weekday(yr, m, 1)) % 7 + 7 * (n - 1)
    return 4 * 3600 if (3, nsun(y, 3, 2), 2, 0) <= (mo, d, hh, mi) < (11, nsun(y, 11, 1), 2, 0) else 5 * 3600

def S_of(ev):
    k = ev.split("-")[1]
    y, mo, d, hh, mi = 2000 + int(k[:2]), MON[k[2:5]], int(k[5:7]), int(k[7:9]), int(k[9:11])
    return calendar.timegm((y, mo, d, hh, mi, 0)) + et_off(y, mo, d, hh, mi)

ev = collections.defaultdict(dict)
for folder in sys.argv[1:]:
    # standing rule (h): counting is reading; a HELDOUT_ folder (by its typed or resolved path) is refused
    if any(part.startswith("HELDOUT_") for p in (os.path.abspath(folder), os.path.realpath(folder)) for part in p.split(os.sep)):
        sys.exit("refused: %s is a HELDOUT_ folder (rule (h))" % folder)
    m = json.load(open(os.path.join(folder, "manifest.json")))
    for r in m["rows"]:
        if r.get("status") != 200 or not r.get("file"): continue
        try: body = json.load(gzip.open(os.path.join(folder, r["file"])))
        except Exception: continue
        for x in body.get("markets", []) if isinstance(body, dict) else []:
            e = x.get("event_ticker", "")
            if not e.startswith("KXESOCCERGAME-"): continue
            ev[e][x["ticker"].rsplit("-", 1)[1]] = (iso(x.get("settlement_ts")), iso(x.get("open_time")))
recs = []
for e, mk in ev.items():
    teams = tuple(sorted(k for k in mk if k != "TIE"))
    if len(teams) != 2 or "TIE" not in mk: continue
    try: S = S_of(e)
    except Exception: continue
    recs.append((teams, S, max(v[0] or 0 for v in mk.values()), min(v[1] or 9e18 for v in mk.values())))
day = lambda t: time.strftime("%Y-%m-%d", time.gmtime(t))
per = collections.defaultdict(lambda: collections.Counter())
pairs_day = collections.defaultdict(set)
by = collections.defaultdict(list)
for r in recs:
    by[r[0]].append(r); per[day(r[1])]["matches"] += 1; pairs_day[day(r[1])].add(r[0])
for rs in by.values():
    rs.sort(key=lambda r: r[1])
    for a, b in zip(rs, rs[1:]):
        c = per[day(b[1])]; c["next"] += 1
        g = (b[1] - a[1]) / 60
        for lo, hi, tag in ((20, 60, "60"), (20, 120, "120")):
            if lo <= g <= hi:
                c["gap" + tag] += 1
                if a[2] and a[2] <= b[1] - 720:
                    c["settled" + tag] += 1
                    if b[3] < a[1]: c["open" + tag] += 1
                    if b[3] <= a[1] - 180: c["open3m" + tag] += 1
days = sorted(per)
cols = ["matches", "next", "gap60", "settled60", "open60", "open3m60", "gap120", "settled120", "open120", "open3m120"]
print("day,pairs," + ",".join(cols))
for d in days: print(d + "," + str(len(pairs_day[d])) + "," + ",".join(str(per[d][c]) for c in cols))
tot = collections.Counter(); [tot.update(per[d]) for d in days]
n = len(days)
print("TOTAL days %d, distinct pairs %d, " % (n, len(by)) + ", ".join("%s %d (per day %.0f)" % (c, tot[c], tot[c] / max(n, 1)) for c in cols))
