#!/usr/bin/env python3
"""FOMCTEXT count, BUILD 2 (Testing Desk, Nov 14, 2026). Research only: reads the files it is given, sends nothing, writes NO file.
Built from Idea Desk C's FOMCTEXT_CARD.md (20196129 on claude/idea-desk-c: the card, Clarifications 1 to 7 and the candle rule C7 to C10) ONLY; not from Desk C's code, not from the History Miner's reader.
Hand case: FOMCTEXT_SECOND_HAND_CASE.md (committed first). Test: test_fomctext_second.py (INVENTED data only). Run only after Auditor B's structure check of the landed run is CLEAN and the Head says go; ONCE.
Universe = the rows of the committed table STATEMENT_WORD_TABLE.csv. A row whose decision_date is on or after 2026-06-17 is dropped by a date constant before any other field is read (held out). Sets (Clarification 7):
KILL ARM = statement-type strikes with feature (statement_word) yes; PLACEBO = statement-type strikes with feature no; NOT STATEMENT-TYPE strikes are printed on their own line, outside both.
The 2:05 pm candle = the candle whose end_period_ts is 14:05:00 US Eastern on the decision date (zoneinfo America/New_York); YES ask / bid = the candle's yes_ask / yes_bid close; a missing candle is not carried forward (not two-sided).
Two-sided: 0 < bid < ask < 1 (1e-9). Result from the lists run, by market ticker: yes counts; void and any other result are excluded and counted. A counted strike: settled YES, two-sided, entry price at or under 0.87.
Printed per set: RAW (the card's wording: the 2:05 pm ask at or under 0.87), 1c (ask + 0.01) and 2c (ask + 0.02), per C7; the count and its distinct decision dates. Kill line (card): (a) fewer than 15 counted strikes, (b) from fewer than 5 distinct decision dates,
(c) fewer than half of ALL kill-arm strikes two-sided at 2:05 pm (those with no candle included). RAW decides the verdict (the Head's ruling A, 02:33Z); 1c and 2c are printed beside it and decide only whether a pass could count toward the 20 to 30 ("does not count: fails the haircut"); CLOSED is never called from a haircut line. Every result line says "upper bound, not fill-checked".
STOPs: a table ticker repeated; a table strike missing from the lists or from the candle answers (the universe check); a market_ticker in more than one candle answer. Prints aggregates only, no strike line.
Usage: fomctext_second.py <STATEMENT_WORD_TABLE.csv> --lists <lists run>... --candles <candle run>...
"""
import calendar, csv, datetime, hashlib, math, os, re, sys, zoneinfo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scorekit as k

ET = zoneinfo.ZoneInfo("America/New_York")
HELDOUT_FROM = "2026-06-17"          # decision dates on or after this are held out (a date constant)
CAP = 0.87
TOL = 1e-9
SLIPS = (("raw", 0.0), ("1c", 0.01), ("2c", 0.02))
MIN_COUNT, MIN_MEETINGS = 15, 5
STATEMENT_TYPE, NOT_STATEMENT = "statement-type", "NOT STATEMENT-TYPE"
AUDITED = {"scorekit.py": "f219b43c755b4b87"}
BOUND = "upper bound, not fill-checked"
AMBIGUITIES = [
    "Entry price at 1c and 2c = ask + 0.01 / + 0.02, and the 0.87 cap applies to that entry price; RAW is the card's literal wording (the ask itself at or under 0.87). RAW decides the verdict (Head's ruling A); 1c and 2c only label whether a pass could count toward the 20 to 30.",
    "Counted = settled YES, two-sided at 2:05 pm, entry price at or under 0.87; the settlement gap is then at least 0.13 (the card's 10c line is implied).",
    "(c) is judged on ALL kill-arm strikes including those with no candle, and does not depend on the haircut.",
    "A market's result is read from the lists answers by ticker (a later answer overwrites an earlier one); a result other than yes, no or void is counted as 'other'.",
    "A table strike with no answer in the candle run (the universe check) or no market in the lists STOPs the run; a strike whose candles lack the 14:05 minute is simply not two-sided.",
    "The unit rule (Head, 02:28Z): close_dollars as before; a `close` must be a string [01].dddd (read as its float) or the run STOPs; applied to the 14:05 candle of a scored strike only; 0.0000 and 1.0000 are read and are not two-sided (the Head's ruling, 02:31Z).",
    "A candle node's ticker is market_ticker, else ticker, else the request id without a leading 'h_'.",
]


def check_hashes(want=None):
    for name, pre in (want or AUDITED).items():
        got = hashlib.sha256(open(os.path.join(HERE, name), "rb").read()).hexdigest()[:16]
        if got != pre:
            raise SystemExit("refused: %s is not the audited build (%s, wanted %s)" % (name, got, pre))


def candle_end(date):
    y, m, d = (int(x) for x in date.split("-"))
    return int(datetime.datetime(y, m, d, 14, 5, tzinfo=ET).timestamp())


def two_sided(bid, ask):
    return bid is not None and ask is not None and bid > TOL and ask < 1.0 - TOL and ask - bid > TOL


def counted(result, ask, slip):
    return result == "yes" and ask is not None and ask + slip <= CAP + TOL


_CLOSE = re.compile(r"[01]\.\d{4}")


def side_price(node, ticker):
    """One side of the 14:05 candle (the Head's unit rule, Amendment 4; ruling 02:31Z): close_dollars is read as before; otherwise `close` must be a STRING full-matching [01].dddd, read as its float ("0.0000" and "1.0000" are READ, and
    rule 18 then marks the strike not two-sided); a value of any other shape STOPs; an absent, null or non-object node, or one with neither key, is no price."""
    if not isinstance(node, dict):
        return None
    if "close_dollars" in node:
        return k.price(node, "close")
    if "close" in node:
        v = node["close"]
        if not (isinstance(v, str) and _CLOSE.fullmatch(v)):
            raise SystemExit("STOP: yes_bid/yes_ask close of %s is %s, not a string [01].dddd (the unit rule)" % (ticker, type(v).__name__ + " " + repr(v)))
        return float(v)
    return None


def quote(raw, ticker):
    """(bid, ask) from the raw (yes_bid node, yes_ask node) pair of the 14:05 candle."""
    return side_price(raw[0], ticker), side_price(raw[1], ticker)


def load_table(path):
    """-> (development rows [dict], heldout rows dropped, table rows). Only decision_date is read before the held-out cut."""
    dev, dropped, total, seen = [], 0, 0, set()
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            total += 1
            if (r.get("decision_date") or "") >= HELDOUT_FROM:
                dropped += 1; continue
            t = r["market_ticker"]
            if t in seen:
                raise SystemExit("STOP: market ticker %s is repeated in the table" % t)
            seen.add(t)
            dev.append({"date": r["decision_date"], "ticker": t, "feature": r["statement_word"], "type": r["type"]})
    return dev, dropped, total


def read_results(lists, wanted):
    """{ticker: result} for the wanted tickers only (no other market's result is read)."""
    out = {}
    for f in lists:
        for row, body in k.iter_answers(f):
            for m in body.get("markets", []) if isinstance(body, dict) else []:
                if isinstance(m, dict) and m.get("ticker") in wanted:
                    out[m["ticker"]] = m.get("result")
    return out


def read_candles(candle_runs, wanted):
    """{ticker: {end_ts: (bid, ask)}} for the wanted tickers; STOPs if a ticker is in more than one candle answer (any ticker, a repeat inside one answer too)."""
    out, seen = {}, {}
    for f in candle_runs:
        for row, body in k.iter_answers(f):
            nodes = body.get("markets") if isinstance(body, dict) and isinstance(body.get("markets"), list) else [body]
            for n in nodes:
                if not isinstance(n, dict) or not isinstance(n.get("candlesticks"), list):
                    continue
                rid = row["id"]
                t = n.get("market_ticker") or n.get("ticker") or (rid[2:] if rid.startswith("h_") else rid)
                where = "%s/%s" % (os.path.basename(str(f).rstrip("/")), row.get("file"))
                if t in seen:
                    raise SystemExit("STOP: market_ticker %s appears in more than one candle answer (%s and %s)" % (t, seen[t], where))
                seen[t] = where
                if t not in wanted:
                    continue
                cs = {}
                for c in n["candlesticks"]:
                    try:
                        ts = int(c["end_period_ts"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    cs[ts] = (c.get("yes_bid"), c.get("yes_ask"))          # raw nodes: the unit rule is applied to the 14:05 candle only
                out[t] = cs
    return out


def figures(rows, cs, res):
    """The counts of one set (a list of table rows)."""
    n = len(rows)
    results = {"yes": 0, "no": 0, "void": 0, "other": 0}
    two = 0
    quotes = []
    for r in rows:
        raw = cs.get(r["ticker"], {}).get(candle_end(r["date"]))
        bid, ask = quote(raw, r["ticker"]) if raw is not None else (None, None)
        ok = two_sided(bid, ask)
        two += ok
        rv = res.get(r["ticker"])
        results[rv if rv in ("yes", "no", "void") else "other"] += 1
        quotes.append((r, ask if ok else None, rv))
    out = {"n": n, "two_sided": two, "two_sided_share": (two / n if n else None), "results": results}
    for name, slip in SLIPS:
        hit = [r for r, ask, rv in quotes if counted(rv, ask, slip)]
        out[name] = {"count": len(hit), "meetings": len({r["date"] for r in hit})}
    return out


def kill(fig):
    out = {}
    for name, _ in SLIPS:
        c = fig[name]
        out[name] = {"a": c["count"] < MIN_COUNT, "b": c["meetings"] < MIN_MEETINGS, "c": (fig["two_sided"] < fig["n"] / 2.0 - 1e-12) if fig["n"] else True}
    return out


def measure(dev, dropped, total, cs, res):
    kill_rows = [r for r in dev if r["type"] == STATEMENT_TYPE and r["feature"] == "yes"]
    placebo_rows = [r for r in dev if r["type"] == STATEMENT_TYPE and r["feature"] != "yes"]
    other = [r for r in dev if r["type"] != STATEMENT_TYPE]
    ka, pl = figures(kill_rows, cs, res), figures(placebo_rows, cs, res)
    ka["kill"] = kill(ka)
    held = [x for x, v in ka["kill"]["raw"].items() if v]
    verdict = ("CLOSED: efficient, move on (the card's kill line holds on the plain count: (%s))" % ", ".join(held)) if held else "NOT CLOSED (no kill condition holds on the plain count)"
    haircut = {name: ("does not count: fails the haircut" if any(ka["kill"][name].values()) else "passes the haircut") for name in ("1c", "2c")}
    could = (not held) and all(v == "passes the haircut" for v in haircut.values())
    return {"table_rows": total, "heldout_rows_dropped": dropped, "development_rows": len(dev), "kill_arm": ka, "placebo": pl, "not_statement_type_n": len(other),
            "VERDICT": verdict + "; " + BOUND, "haircut": haircut, "could_count_toward_20_to_30": could, "ambiguities": AMBIGUITIES}


def run(table, lists, candle_runs, hash_check=True):
    if hash_check:
        check_hashes()
    for f in list(lists) + list(candle_runs):
        k.guard(f)
    dev, dropped, total = load_table(table)
    wanted = {r["ticker"] for r in dev}
    res = read_results(lists, wanted)
    miss = [t for t in wanted if t not in res]
    if miss:
        raise SystemExit("STOP: %d table strikes have no market in the lists run (the universe is not whole)" % len(miss))
    cs = read_candles(candle_runs, wanted)
    miss = [t for t in wanted if t not in cs]
    if miss:
        raise SystemExit("STOP: %d table strikes have no answer in the candle run (the universe is not whole)" % len(miss))
    out = measure(dev, dropped, total, cs, res)
    out["python"] = "%s at %s" % (sys.version.split()[0], sys.executable)
    return out


def _line(name, fig):
    c = lambda key: "%s: %d strikes from %d decision dates" % (key, fig[key]["count"], fig[key]["meetings"])
    return ["%s (n = %d): two-sided at 2:05 pm %d of %d (%s); results yes %d, no %d, void %d, other %d" % (name, fig["n"], fig["two_sided"], fig["n"], ("%.1f%%" % (100.0 * fig["two_sided_share"])) if fig["n"] else "n/a", *[fig["results"][x] for x in ("yes", "no", "void", "other")]),
            "  counted (settled YES, entry at or under 0.87, %s): RAW (ask) %s; 1c %s; 2c %s" % (BOUND, c("raw"), c("1c"), c("2c"))]


def render(r):
    lines = ["python %s" % r["python"], "table rows %d, held-out rows dropped %d, development rows %d" % (r["table_rows"], r["heldout_rows_dropped"], r["development_rows"])]
    lines += _line("kill arm (statement-type, feature yes)", r["kill_arm"])
    kl = r["kill_arm"]["kill"]
    for name in ("raw", "1c", "2c"):
        lines.append("  kill line at %s: (a) fewer than %d counted: %s; (b) fewer than %d decision dates: %s; (c) fewer than half two-sided: %s" % (name, MIN_COUNT, kl[name]["a"], MIN_MEETINGS, kl[name]["b"], kl[name]["c"]))
    lines += _line("placebo (statement-type, feature no)", r["placebo"])
    lines.append("not statement-type, n = %d (outside the kill line and the placebo)" % r["not_statement_type_n"])
    lines.append("VERDICT (decided on the plain count): " + r["VERDICT"])
    lines.append("haircut lines (decide only whether a pass could count toward the 20 to 30; %s): 1c %s; 2c %s" % (BOUND, r["haircut"]["1c"], r["haircut"]["2c"]))
    lines.append("could count toward the 20 to 30: %s" % ("yes" if r["could_count_toward_20_to_30"] else "no"))
    return "\n".join(lines)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 5 and "--lists" in a and "--candles" in a:
        i, j = a.index("--lists"), a.index("--candles")
        print(render(run(a[0], a[i + 1:j], a[j + 1:])))
    else:
        print(__doc__)
