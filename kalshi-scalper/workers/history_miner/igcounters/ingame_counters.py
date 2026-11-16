"""ingame_counters.py: counts only (History Miner, Nov 16, 2026). Hand case IGCOUNTERS_HAND_CASE_NOV16.md. No result, no outcome, no price figure is printed.
  python3 -I ingame_counters.py cadence <ingame folder> <date> [<date> ...]
  python3 -I ingame_counters.py fade2 <ingame folder>        (forward window only; prices are read)"""
import calendar, collections, csv, glob, gzip, hashlib, io, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
SIGNED_EVENTS_SHA256 = "4698bae08dca65bebcaac7bad551bad6611099ba71a082b58b0976835f817e0b"
if hashlib.sha256(open(os.path.join(HERE, "..", "igspecs", "ingame_events.py"), "rb").read()).hexdigest() != SIGNED_EVENTS_SHA256:
    raise SystemExit("REFUSED: ingame_events.py is not the signed file")
sys.path.insert(0, os.path.join(HERE, "..", "igspecs"))
import ingame_events as E
START, CUT = 1794873600, 1797292800
SERIES = ("KXNHLGAME", "KXNBATOTAL", "KXNFLTOTAL", "KXNHLTOTAL", "KXNBASPREAD", "KXNHLSPREAD")


def day_of(t):
    return time.strftime("%Y-%m-%d", time.gmtime(t))


def cadence_rows(rows):
    """rows: csv lists; ONLY index 0 (t_recv_ms) and index 4 (ticker) are read. -> {hour: [pairs, pairs <= 60 s, pairs <= 25 s]}"""
    last = {}; out = collections.defaultdict(lambda: [0, 0, 0])
    for r in rows:
        if not r or r[0] == "t_recv_ms":
            continue
        try:
            t = int(float(r[0])) / 1000
        except ValueError:
            continue
        tk = r[4]
        if tk in last:
            g = t - last[tk]; s = out[time.strftime("%Y-%m-%d %H", time.gmtime(t))]
            s[0] += 1; s[1] += g <= 60; s[2] += g <= 25
        last[tk] = t
    return {k: list(v) for k, v in out.items()}


def cadence_by_hour(folder, dates):
    allrows = []
    for d in dates:
        for f in sorted(glob.glob(os.path.join(folder, d, "*", "obs.csv.gz"))):
            allrows.extend(csv.reader(io.TextIOWrapper(gzip.open(f), newline="")))
    return cadence_rows(sorted(allrows, key=lambda r: float(r[0]) if r and r[0] != "t_recv_ms" else 0))


class Walled(dict):
    """a row outside the window: only the time column may be read"""
    def __getitem__(s, k):
        if k != "t_recv_ms":
            raise AssertionError("touched column %r of a row outside the window" % k)
        return super().__getitem__(k)


def signal_rows(dict_rows):
    """dict_rows: DictReader rows. Time first, then the ticker wall, then the prices. -> events {(league, game, kind): {"key", "league", "kind", "rows": {ticker: [(t, bid, ask)]}}}"""
    ev = {}
    for r in dict_rows:
        t = E_num(r["t_recv_ms"])
        if t is None or not START <= t / 1000 < CUT:
            continue
        tk = r["ticker"]
        if tk.split("-", 1)[0] not in SERIES:
            continue
        lg = tk.split("-", 1)[0][2:5]; key = (lg, r["event"].split("-", 1)[-1], r["kind"])
        e = ev.setdefault(key, {"key": "|".join(key), "league": lg, "kind": r["kind"], "rows": collections.defaultdict(list), "result": {}, "occ": {}, "close": {}})
        e["rows"][tk].append((int(t // 1000), E_num(r["yes_bid"]), E_num(r["yes_ask"])))
    for e in ev.values():
        e["rows"] = {tk: sorted(v) for tk, v in e["rows"].items()}
    return ev


def E_num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fade2_counts(events):
    out = collections.defaultdict(lambda: collections.Counter())
    for e in events.values():
        why, det = E.fade2(e)
        if why == "ok":
            out[day_of(det["t"])]["%s_%s" % (e["league"], e["kind"])] += 1
    days = sorted(out)
    return {"label": "decision counts only; " + ("provisional, fewer than 7 tip days, not the stored gate" if len(days) < 7 else "7 or more days: the gate's own counts come from the engine"),
            "by_day": {d: dict(out[d]) for d in days}, "decisions": sum(sum(c.values()) for c in out.values())}


def latedrift_counts(loader_events):
    out = collections.Counter()
    for e in loader_events:
        why, det = E.latedrift(e)
        if why == "ok":
            out[day_of(det["t"])] += 1
    return {"label": "decision counts only (the forward loader's events; spreads excluded)", "by_day": dict(sorted(out.items()))}


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "cadence":
        print(json.dumps(cadence_by_hour(a[1], a[2:]), indent=1, sort_keys=True))
    elif len(a) == 2 and a[0] == "fade2":
        rows = []
        for d in sorted(os.listdir(a[1])):
            if d >= "2026-11-17":
                for f in sorted(glob.glob(os.path.join(a[1], d, "*", "obs.csv.gz"))):
                    rows.extend(csv.DictReader(io.TextIOWrapper(gzip.open(f), newline="")))
        print(json.dumps(fade2_counts(signal_rows(rows)), indent=1, sort_keys=True))
    else:
        sys.exit(__doc__)
