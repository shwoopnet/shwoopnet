#!/usr/bin/env python3
"""FOMCTEXT stage 1 reader (History Miner, Nov 13, 2026): Idea Desk C's card (claude/idea-desk-c 8851d822, kalshi-scalper/workers/idea_desk_c/FOMCTEXT_CARD.md) and its dated clarifications.
Zero tries: a count. Reads kalshi-pull run folders only; sends nothing. Development decision dates only; every list row whose meeting is held out (decision date on or after 2026-06-17 00:00 UTC) or is not a
development decision date is dropped BEFORE any field other than its ticker is read (its result is never read). A HELDOUT_ folder (any case) is refused.
Commands:
  build-candles <table.csv> <lists folder>...   -> the stage 2 candle job (JSON) for every strike of the table's development events
  count <table.csv> --lists <folder>... --candles <folder>...   -> the stage 1 count and the CLOSE lines
The hand-matched statement-word table is Desk C's (decision_date,event_ticker,market_ticker,strike_word,statement_word; card Clarification 1, 28a2d63d); this reader never matches words."""
import calendar, csv, gzip, json, os, re, sys

SERIES = ("KXFEDMENTION", "KXPOWELLMENTION", "KXJPOWMENTION", "KXWARSHMENTION")
DEV_DATES = ("2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10", "2026-01-28", "2026-03-18", "2026-04-29")
HELDOUT_FROM = calendar.timegm((2026, 6, 17, 0, 0, 0))     # decision dates at or after this are held out (the card); refused
TOL = 1e-9
ASK_MAX, GAP_MIN = 0.87, 0.10                                # the card: YES ask at 87c or less, 10c or more under settlement
CLOSE_MIN_STRIKES, CLOSE_MIN_MEETINGS = 15, 5                # (a), (b); (c) under half two-sided
MON = {m: i for i, m in enumerate(("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"), 1)}


def refuse_heldout(path):
    for p in (os.path.abspath(path), os.path.realpath(path)):
        if any(c.upper().startswith("HELDOUT") for c in p.split(os.sep)):
            raise SystemExit("refused: %s is a held-out folder" % path)


def eastern_offset(y, mo, d, h):
    def nth_sunday(y, mo, n):
        return 1 + (6 - calendar.weekday(y, mo, 1)) % 7 + 7 * (n - 1)
    a = (mo, d, h) >= (3, nth_sunday(y, 3, 2), 2)
    b = (mo, d, h) < (11, nth_sunday(y, 11, 1), 2)
    return -4 * 3600 if (a and b) else -5 * 3600


def et_epoch(date, h, mi):
    y, mo, d = (int(x) for x in date.split("-"))
    return calendar.timegm((y, mo, d, h, mi, 0)) - eastern_offset(y, mo, d, h)


def date_of_event(event):
    """The decision date read from the event ticker's date part (YYMMMDD), e.g. KXFEDMENTION-25JAN29 -> 2025-01-29; None if absent."""
    m = re.match(r"^[A-Z0-9]+-(\d\d)([A-Z]{3})(\d\d)", event or "")
    if not m or m.group(2) not in MON:
        return None
    return "%04d-%02d-%02d" % (2000 + int(m.group(1)), MON[m.group(2)], int(m.group(3)))


def held_out(date):
    return date is None or calendar.timegm(tuple(int(x) for x in date.split("-")) + (0, 0, 0)) >= HELDOUT_FROM


def answers(folder):
    refuse_heldout(folder)
    m = json.load(open(os.path.join(folder, "manifest.json")))
    for row in m["rows"]:
        if row.get("status") != 200 or not row.get("file") or row.get("truncated"):
            raise SystemExit("refused: %s has a row that is not a whole 200 answer (%s); a partial pull is not read" % (folder, row.get("id")))
        yield row, json.load(gzip.open(os.path.join(folder, row["file"]), "rt"))


def load_lists(folders):
    """{ticker: dict(ticker, event, date, result, source)} for development rows only, and the drop counts. A held-out or non-development row is dropped on its event ticker alone."""
    keep, drop = {}, {"held_out": 0, "not_a_development_decision_date": 0, "not_fed_series": 0}
    for f in folders:
        for row, body in answers(f):
            src = "historical" if row.get("path", "").startswith("/historical") else "live"
            for mk in (body.get("markets") or []) if isinstance(body, dict) else []:
                t = mk.get("ticker") if isinstance(mk, dict) else None
                if not t:
                    continue
                if t.split("-")[0] not in SERIES:
                    drop["not_fed_series"] += 1; continue
                ev = mk.get("event_ticker") or t.rsplit("-", 1)[0]
                d = date_of_event(ev)
                if held_out(d):
                    drop["held_out"] += 1; continue
                if d not in DEV_DATES:
                    drop["not_a_development_decision_date"] += 1; continue
                keep[t] = {"ticker": t, "event": ev, "date": d, "result": mk.get("result"), "source": src}
    return keep, drop


def load_table(path):
    rows = list(csv.DictReader(open(path)))
    out = {}
    for r in rows:
        if held_out(r["decision_date"]):
            raise SystemExit("refused: the table names a held-out meeting (%s)" % r["decision_date"])
        if r["decision_date"] not in DEV_DATES:
            raise SystemExit("refused: the table names a date that is not a development decision date (%s)" % r["decision_date"])
        if r["statement_word"].strip().lower() not in ("yes", "no"):
            raise SystemExit("refused: statement_word must be yes or no (%s)" % r["market_ticker"])
        out[r["market_ticker"]] = {"date": r["decision_date"], "event": r["event_ticker"], "word": r["strike_word"], "sw": r["statement_word"].strip().lower() == "yes"}
    return out


def universe(table, lists):
    """Every strike of every event the table names must be in the table, and every table strike must be in the lists."""
    events = {v["event"] for v in table.values()}
    missing_from_table = sorted(t for t, m in lists.items() if m["event"] in events and t not in table)
    missing_from_lists = sorted(t for t in table if t not in lists)
    if missing_from_table or missing_from_lists:
        raise SystemExit("refused: table and lists disagree: %d strikes of named events missing from the table %s; %d table strikes not in the lists %s"
                         % (len(missing_from_table), missing_from_table[:5], len(missing_from_lists), missing_from_lists[:5]))
    for t, v in table.items():
        if lists[t]["date"] != v["date"] or lists[t]["event"] != v["event"]:
            raise SystemExit("refused: %s date or event differs between table and lists" % t)
    return events


def build_candles(table_path, list_folders):
    table = load_table(table_path); lists, drop = load_lists(list_folders); universe(table, lists)
    reqs, live = [], {}
    for t in sorted(table):
        d = table[t]["date"]; a, b = et_epoch(d, 13, 55), et_epoch(d, 14, 45)
        if lists[t]["source"] == "historical":
            reqs.append({"id": "h_" + t, "path": "/historical/markets/%s/candlesticks" % t, "params": {"start_ts": a, "end_ts": b, "period_interval": 1}})
        else:
            live.setdefault((a, b), []).append(t)
    for (a, b), ts in sorted(live.items()):
        per = max(1, min(100, 9000 // ((b - a) // 60)))
        for i in range(0, len(ts), per):
            reqs.append({"id": "b_%d_%d" % (a, i // per), "path": "/markets/candlesticks", "params": {"market_tickers": ",".join(ts[i:i + per]), "start_ts": a, "end_ts": b, "period_interval": 1}})
    return reqs, drop


def candles(folders):
    out = {}
    for f in folders:
        for row, body in answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list):
                    continue
                t = n.get("market_ticker") or n.get("ticker") or (row["id"][2:] if row["id"].startswith("h_") else None)
                for c in n["candlesticks"]:
                    out.setdefault(t, {})[int(c["end_period_ts"])] = c
    return out


def px(node):
    """A candle close in dollars: '<close>_dollars' string (verified on batched answers). The /historical answer's shape is unverified: a plain 'close' above 1.0 is read as cents."""
    if not isinstance(node, dict):
        return None
    for k in ("close_dollars", "close"):
        try:
            v = float(node[k])
        except (KeyError, TypeError, ValueError):
            continue
        return v / 100.0 if (k == "close" and v > 1.0) else v
    return None


def count(table_path, list_folders, candle_folders):
    table = load_table(table_path); lists, drop = load_lists(list_folders); universe(table, lists); cd = candles(candle_folders)
    sw = tally({t: v for t, v in table.items() if v["sw"]}, lists, cd)
    placebo = tally({t: v for t, v in table.items() if not v["sw"]}, lists, cd)   # Clarification 1 point 5: printed beside, never part of the kill line
    n_sw, n_two, qual, meetings = sw["strikes"], sw["two_sided_at_1405"], sw["qualifying"], set(sw["qualifying_meetings"])
    close = []
    if qual < CLOSE_MIN_STRIKES: close.append("(a) fewer than 15 qualifying strikes (%d)" % qual)
    if len(meetings) < CLOSE_MIN_MEETINGS: close.append("(b) from fewer than 5 meetings (%d)" % len(meetings))
    if n_sw == 0 or 2 * n_two < n_sw: close.append("(c) fewer than half of statement-word strikes two-sided at 2:05 pm (%d of %d)" % (n_two, n_sw))
    met = {v["date"] for v in table.values()}
    return {"development_meetings_in_table": len(met), "no_market_dates": sorted(d for d in DEV_DATES if d not in met), "strikes_in_table": len(table),
            "statement_word_strikes": n_sw, "two_sided_at_1405": n_two, "qualifying": qual, "qualifying_meetings": sorted(meetings), "excluded": sw["excluded"],
            "placebo_non_statement_words": placebo, "list_rows_dropped_unread": drop,
            "verdict": ("CLOSED, efficient, move on: " + "; ".join(close)) if close else "survives stage 1: register 1 try separately (slow-family paper screen)",
            "label": "zero tries; development only; reads settlements by design (see FOMCTEXT_READER_NOTE.md); the placebo is not part of the kill line"}


def tally(group, lists, cd):
    """For one group of strikes: how many, how many two-sided at 14:05 ET, how many settled yes with a two-sided ask at or under 87c and 10c or more under settlement, and from which meetings."""
    n_two, qual, meetings, excl = 0, 0, set(), {"no_candle_at_1405": 0, "result_not_yes_or_no": 0}
    for t, v in sorted(group.items()):
        c = cd.get(t, {}).get(et_epoch(v["date"], 14, 5))
        bid = px(c.get("yes_bid")) if c else None; ask = px(c.get("yes_ask")) if c else None
        two = bid is not None and ask is not None and bid > TOL and bid < ask - TOL and ask < 1 - TOL   # 0 < bid < ask < 1; a 0.00 or 1.00 placeholder is not two-sided
        if c is None:
            excl["no_candle_at_1405"] += 1
        n_two += two
        res = lists[t]["result"]
        if res not in ("yes", "no"):
            excl["result_not_yes_or_no"] += 1; continue
        settle = 1.0 if res == "yes" else 0.0
        q = two and ask <= ASK_MAX + TOL and (settle - ask) >= GAP_MIN - TOL
        if q:
            qual += 1; meetings.add(v["date"])
    return {"strikes": len(group), "two_sided_at_1405": n_two, "qualifying": qual, "qualifying_meetings": sorted(meetings), "excluded": excl}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "build-candles":
        reqs, drop = build_candles(a[1], a[2:])
        print(json.dumps({"requests": reqs, "count": len(reqs), "list_rows_dropped_unread": drop}, indent=1))
    elif a[0] == "count":
        i, j = a.index("--lists"), a.index("--candles")
        print(json.dumps(count(a[1], a[i + 1:j], a[j + 1:]), indent=1))
    else:
        sys.exit("unknown command")
