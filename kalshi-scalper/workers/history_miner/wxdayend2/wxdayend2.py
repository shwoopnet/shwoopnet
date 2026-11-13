"""WXDAYEND second count (History Miner, Nov 13, 2026), from the registration text only; the Testing Desk's scorer was not read. Rule and made-up
expectations in EXPECTED_BY_HAND.md (63e662da), committed first. An existence count, no new try. Reads two landed kalshi-pull runs (the lists bundle with
the wx_c* candle requests and the wx_l* Nov 10 lists, and the run holding the wxb_c* Nov 10 candles). Prints counts only.
Usage: python3 -I wxdayend2.py <TESTING_LISTS_BUNDLE run folder> <TIE3_CANDLES run folder>"""
import gzip, hashlib, json, os, re, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hm_guard  # noqa: E402

TOL = 1e-9
LINE = 0.96
STD_OFFSET = {"KXHIGHTDAL": -6, "KXHIGHDEN": -7, "KXHIGHNY": -5, "KXHIGHLAX": -8}
TOTAL = 40
KILL_AT = 3
MONTHS = {"NOV": 11}


class Stop(Exception):
    pass


def iso(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def load(folder):
    hm_guard.refuse_all([folder])
    m = json.load(open(os.path.join(folder, "manifest.json")))
    if m.get("status") != "complete":
        raise Stop("run not complete: %s" % folder)
    root = os.path.realpath(folder)
    reqs = {q["id"]: q for q in m["job"]["requests"]}
    out = {}
    for r in m["rows"]:
        if r.get("status") != 200 or r.get("truncated") or not r.get("file") or "sha256" not in r or "bytes" not in r:
            raise Stop("row %s is not a whole 200 answer with sha256 and bytes" % r.get("id"))
        p = os.path.realpath(os.path.join(folder, r["file"]))
        if os.path.commonpath([root, p]) != root:
            raise Stop("file outside run: %s" % r["file"])
        hm_guard.refuse_all([p])
        raw = gzip.open(p, "rb").read()
        if hashlib.sha256(raw).hexdigest() != r["sha256"] or len(raw) != r["bytes"]:
            raise Stop("sha256 or bytes mismatch %s" % r["file"])
        out.setdefault(r["id"], []).append((reqs.get(r["id"]), json.loads(raw)))
    return out


def std_close(event):
    """close = local standard midnight after the event date + 3600 s, from an event ticker like KXHIGHTDAL-26NOV01."""
    series, code = event.split("-")[0], event.split("-")[1]
    mt = re.fullmatch(r"(\d\d)([A-Z]{3})(\d\d)", code)
    day = datetime(2000 + int(mt.group(1)), MONTHS[mt.group(2)], int(mt.group(3)), tzinfo=timezone.utc) + timedelta(days=1)
    return int(day.timestamp()) - STD_OFFSET[series] * 3600 + 3600


def judge(cands, day_end):
    post = [c for c in cands if int(c["end_period_ts"]) > day_end]

    def px(c, k):
        o = c.get("yes_ask") or {}
        v = o.get(k + "_dollars")
        return float(v) if v not in (None, "") else None
    sc = any(px(c, "close") is not None and px(c, "close") <= LINE + TOL for c in post)
    sl = any(px(c, "low") is not None and px(c, "low") <= LINE + TOL for c in post)
    return sc, sl, not post


def count(lists_dir, candles_dir):
    A, B = load(lists_dir), load(candles_dir)
    days, unresolved = {}, []
    for rid, pages in A.items():
        if rid.startswith("wx_c"):
            q = pages[0][0]
            t = q["params"]["market_tickers"]
            ev = t.rsplit("-", 1)[0]
            close = int(q["params"]["end_ts"])
            if close != std_close(ev):
                raise Stop("%s window end %d is not standard midnight + 1 h (%d)" % (ev, close, std_close(ev)))
            cs = [c for _, b in pages for mk in b.get("markets") or [] if mk.get("market_ticker") == t for c in mk.get("candlesticks") or []]
            days[ev] = {"winner": t, "confirmed": False, "day_end": close - 3600, "candles": cs}
        elif rid.startswith("wx_l"):
            ms = [mk for _, b in pages for mk in b.get("markets") or []]
            yes = [mk for mk in ms if mk.get("result") == "yes"]
            ev = ms[0]["event_ticker"] if ms else rid
            if len(yes) != 1:
                unresolved.append(ev)
                continue
            days[ev] = {"winner": yes[0]["ticker"], "confirmed": True, "day_end": iso(yes[0]["close_time"]) - 3600, "candles": None}
    for rid, pages in B.items():
        if not rid.startswith("wxb_c"):
            continue
        t = pages[0][0]["params"]["market_tickers"]
        ev = t.rsplit("-", 1)[0]
        if ev in unresolved:                                                    # zero or two winners: reported, stays unread
            continue
        if ev not in days or days[ev]["winner"] != t:
            raise Stop("Nov 10 candle ticker %s is not the list winner" % t)
        days[ev]["candles"] = [c for _, b in pages for mk in b.get("markets") or [] if mk.get("market_ticker") == t for c in mk.get("candlesticks") or []]
    res = {"covered": 0, "shows_close": 0, "shows_low": 0, "no_post_day_candle": 0, "winner_unconfirmed": 0, "unresolved": unresolved}
    for ev, d in sorted(days.items()):
        if d["candles"] is None:
            continue
        sc, sl, none = judge(d["candles"], d["day_end"])
        res["covered"] += 1
        res["shows_close"] += sc
        res["shows_low"] += sl
        res["no_post_day_candle"] += none
        res["winner_unconfirmed"] += not d["confirmed"]
    res["not_recounted"] = TOTAL - res["covered"]
    res["verdict"] = ("incomplete: %d city-days not recounted" % res["not_recounted"]) if res["not_recounted"] else \
        ("FAIL" if res["shows_close"] < KILL_AT else "kill rule not hit")
    return res


if __name__ == "__main__":
    try:
        print(json.dumps(count(sys.argv[1], sys.argv[2])))
    except Stop as e:
        raise SystemExit("STOP: %s" % e)
