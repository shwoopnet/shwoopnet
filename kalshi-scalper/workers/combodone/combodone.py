#!/usr/bin/env python3
"""COMBODONE stage 1: a zero-try COUNT (go or no-go). Built from Idea Desk C's card
kalshi-scalper/workers/idea_desk_c/COMBODONE_CARD.md with its Amendments 1 and 2 (commit 593597e6 on claude/idea-desk-c),
before any combo-data file was opened for it. Nothing is scored against an outcome. It reads leg RESULTS only to
classify a snapshot (a leg decided for the combo, against it, or neither), so it is not blind to leg outcomes.

  week     <combo dir>                 runs per UTC day and the first full week, or "no full week yet". Coverage files only.
  legs-job <combo dir> <out dir>       the leg pull for that week: /markets with a tickers parameter, 100 a request.
  count    <combo dir> <legs run>      the count and the one line.

<combo dir> is the `combo` folder of the combo-data branch: <YYYY-MM-DD>/<run folder>/{coverage,quotes,books}.csv.gz
Standard library only. Every command refuses a path in a HELDOUT_ folder.
"""
import csv
import gzip
import io
import json
import math
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from deskb_guard import refuse_all, refuse_heldout  # noqa: E402

EPS = 1e-9
RUNS_A_DAY = 48                       # cron 11,41
WEEK_MIN_RUNS = 269                   # 80% of 336, Amendment 1.1
DAY_MIN_RUNS = 24
SETTLED_LEAD_S = 60                   # (b): a leg decided for the combo at least this long before t
ASK_MAX = 0.87
SIZE_MIN = 1.0
KILL_BELOW = 30
CUT_MARK = "|..."
BATCH = 100
MAX_REQUESTS = 100
TAG = " [a count, zero tries, nothing scored]"
CARD = "kalshi-scalper/workers/idea_desk_c/COMBODONE_CARD.md"
DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
TICKER_RE = re.compile(r"[A-Z0-9][A-Z0-9._-]{1,118}")


def inside(root, *parts):
    """A path under root. Refused if it lies in or resolves into a HELDOUT_ folder, or outside root."""
    path = os.path.join(root, *[str(p) for p in parts])
    refuse_heldout(path)
    if not (os.path.realpath(path) + os.sep).startswith(os.path.realpath(root) + os.sep):
        sys.exit("REFUSED: %s is not inside %s" % (path, root))
    return path


def read_csv(root, *parts):
    """Rows of a gzipped (or plain) CSV as dicts; None if the file is not there."""
    for name in (parts[-1] + ".gz", parts[-1]):
        path = inside(root, *(parts[:-1] + (name,)))
        if os.path.isfile(path):
            with (gzip.open(path, "rt", newline="") if name.endswith(".gz") else open(path, newline="")) as f:
                return list(csv.DictReader(io.StringIO(f.read())))
    return None


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def epoch(x):
    """Seconds since 1970 from an ISO time or a number of seconds or milliseconds; None if unreadable or empty."""
    if x in (None, ""):
        return None
    v = num(x)
    if v is not None:
        return v / 1000.0 if v > 1e11 else v
    try:
        d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()


def day_of(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def runs(combo):
    """Every run folder: (day folder, run folder, completed, list_complete or None). Amendment 1.1: a run is completed
    when its folder has a coverage row with stopped_early = 0 and a quotes file."""
    refuse_heldout(combo)
    out = []
    for d in sorted(os.listdir(combo)):
        if not DAY_RE.fullmatch(d) or not os.path.isdir(inside(combo, d)):
            continue
        for r in sorted(os.listdir(inside(combo, d))):
            if not os.path.isdir(inside(combo, d, r)):
                continue
            cov = read_csv(combo, d, r, "coverage.csv")
            has_quotes = any(os.path.isfile(inside(combo, d, r, n)) for n in ("quotes.csv.gz", "quotes.csv"))
            ok = bool(cov) and str(cov[0].get("stopped_early", "")).strip() == "0" and has_quotes
            out.append((d, r, ok, (str(cov[0].get("list_complete", "")).strip() == "1") if cov else None))
    return out


def find_week(all_runs):
    """(per-day completed counts, the seven days of the earliest full week or None). A day counts only once it is over:
    a run folder exists on a later UTC day."""
    per = {}
    for d, _, ok, _ in all_runs:
        per[d] = per.get(d, 0) + (1 if ok else 0)
    if not per:
        return per, None
    last = max(per)
    d0 = date.fromisoformat(min(per))
    while True:
        days = [(d0 + timedelta(days=i)).isoformat() for i in range(7)]
        if days[-1] >= last:
            return per, None
        if sum(per.get(d, 0) for d in days) >= WEEK_MIN_RUNS and min(per.get(d, 0) for d in days) >= DAY_MIN_RUNS:
            return per, days
        d0 += timedelta(days=1)


def print_week(all_runs, per, days):
    for d in sorted(per):
        print("%s: completed runs %d of %d scheduled%s" % (d, per[d], RUNS_A_DAY, TAG))
    if days is None:
        print("NO FULL WEEK YET: seven UTC days in a row, each over, with %d or more completed runs in all and no day under %d. The count waits; nothing is read on a partial week.%s" % (WEEK_MIN_RUNS, DAY_MIN_RUNS, TAG))
        return
    inw = [x for x in all_runs if x[0] in days]
    done = [x for x in inw if x[2]]
    print("THE WEEK: %s to %s | completed runs %d of %d scheduled (%.1f%%) | run folders not completed %d | completed runs whose combo list was whole %d of %d%s"
          % (days[0], days[-1], len(done), 7 * RUNS_A_DAY, 100.0 * len(done) / (7 * RUNS_A_DAY) + 1e-7, len(inw) - len(done), sum(1 for x in done if x[3]), len(done), TAG))


def parse_legs(s, n_legs):
    """('empty' | 'cut' | 'ok', legs). A leg is (ticker, side); side is 'yes', 'no' or '' when the string has none.
    If the row's leg count is readable and differs from the number of legs in the string, a (None, '') leg is added:
    a leg the recorder could not name is a leg unknown."""
    s = (s or "").strip()
    if not s:
        return "empty", []
    if s.endswith(CUT_MARK):
        return "cut", []
    legs = []
    for part in s.split("|"):
        t, _, side = part.partition(":")
        legs.append((t, side if side in ("yes", "no") else ""))
    n = num(n_legs)
    if n is not None and int(n) != len(legs):
        legs.append((None, ""))
    return "ok", legs


def week_rows(combo, all_runs, days):
    """Every quotes row whose receive time falls on one of the seven days, in time order, with its run folder."""
    wanted = set(days)
    near = wanted | {(date.fromisoformat(days[0]) - timedelta(days=1)).isoformat(), (date.fromisoformat(days[-1]) + timedelta(days=1)).isoformat()}
    out, unreadable = [], 0
    for d, r, _, _ in all_runs:
        if d not in near:
            continue
        for row in read_csv(combo, d, r, "quotes.csv") or []:
            t = epoch(row.get("t_recv_ms"))
            if t is None or not row.get("ticker"):
                unreadable += 1
                continue
            if day_of(t) in wanted:
                out.append((t, d, r, row))
    out.sort(key=lambda x: (x[0], x[1], x[2], x[3]["ticker"]))
    return out, unreadable


def needed_legs(rows):
    need = set()
    for _, _, _, row in rows:
        kind, legs = parse_legs(row.get("leg_tickers"), row.get("legs"))
        if kind == "ok":
            need |= {t for t, _ in legs if t}
    return need


def cmd_week(combo):
    all_runs = runs(combo)
    per, days = find_week(all_runs)
    print_week(all_runs, per, days)


def cmd_legs_job(combo, out):
    all_runs = runs(combo)
    per, days = find_week(all_runs)
    print_week(all_runs, per, days)
    if days is None:
        return
    rows, unreadable = week_rows(combo, all_runs, days)
    need = sorted(needed_legs(rows))
    bad = [t for t in need if not TICKER_RE.fullmatch(t)]
    n_req = (len(need) + BATCH - 1) // BATCH
    print("quote rows in the week %d (unreadable rows left out %d) | distinct legs named in whole leg strings %d | requests %d (cap %d)%s" % (len(rows), unreadable, len(need), n_req, MAX_REQUESTS, TAG))
    if bad:
        print("%d LEG NAMES ARE NOT TICKERS (first: %r): no job written; this goes to the Head of R&D." % (len(bad), bad[0]))
        return
    if not need or n_req > MAX_REQUESTS:
        print("%s: no job written. No leg is dropped to fit; the count goes to the Head of R&D." % ("NO LEG TO ASK FOR" if not need else "OVER THE CAP"))
        return
    reqs = [{"id": "legs%03d" % (i + 1), "path": "/markets", "params": {"tickers": ",".join(need[i * BATCH:(i + 1) * BATCH]), "limit": 1000}} for i in range(n_req)]
    job = {"job_id": "COMBODONE_LEGS", "owner": "DESK_B", "registration": CARD,
           "purpose": "COMBODONE stage 1, a zero-try count: status, result and settlement time of every leg named by the combo recorder in the week %s to %s." % (days[0], days[-1]),
           "heldout": "none (a count; nothing is scored; leg results are read only to classify a snapshot)",
           "allowed_endpoints": [{"name": "markets_list", "method": "GET", "path_pattern": "/markets", "params_allowed": ["tickers", "limit"]}],
           "ticker_allowlist": need, "max_requests": n_req, "requests": reqs,
           "notes": "Built by workers/combodone/combodone.py legs-job from the combo-data files of the week; no leg is dropped.",
           "status": "active", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2", "pacing_seconds": 1.0,
           "stop_rules": {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3,
                          "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}}
    os.makedirs(out, exist_ok=True)
    json.dump(job, open(os.path.join(out, "COMBODONE_LEGS.json"), "w"), indent=1)
    print("written: COMBODONE_LEGS.json in %s" % out)


def read_legs_run(run):
    """(leg facts by ticker, whole, tickers the job asked for). A leg fact is (result, settlement time or None)."""
    refuse_heldout(run)
    man = json.load(open(inside(run, "manifest.json")))
    reqs = (man.get("job") or {}).get("requests")
    if not isinstance(reqs, list) or not reqs:
        sys.exit("REFUSED: the leg run's manifest does not carry its job, so it cannot be tied to the week")
    asked_ids = {r.get("id") for r in reqs}
    asked = {t for r in reqs for t in str((r.get("params") or {}).get("tickers", "")).split(",") if t}
    rows = man.get("rows", [])
    bad = {r.get("id") for r in rows if r.get("status") != 200 or r.get("truncated")}
    good = {r.get("id") for r in rows if r.get("status") == 200 and not r.get("truncated")}
    facts, cursor_left = {}, False
    for r in rows:
        if r.get("status") != 200 or not r.get("file"):
            continue
        body = json.load(gzip.open(inside(run, r["file"]), "rt"))
        if not isinstance(body, dict):
            bad.add(r.get("id"))
            continue
        cursor_left = cursor_left or bool(body.get("cursor"))
        for m in body.get("markets") or []:
            if isinstance(m, dict) and m.get("ticker"):
                facts[m["ticker"]] = (str(m.get("result") or "").strip().lower(), epoch(m.get("settlement_ts")))
    whole = man.get("status") == "complete" and not bad and asked_ids <= good and not cursor_left
    return facts, whole, asked


def classify(legs, facts, t):
    """One of: 'leg unknown', 'other result', 'a leg lost', 'no leg decided', 'every leg settled', or ('ok', open legs).
    Amendment 1, readings 2 to 4, tested in this order."""
    state = []
    for tk, side in legs:
        f = facts.get(tk) if tk else None
        if f is None or not side or (f[1] is None and f[0]):
            return "leg unknown"
        res, s = f
        if s is None or s > t + EPS:
            state.append("open")
        elif res not in ("yes", "no"):
            state.append("other")
        elif res == side:
            state.append("won early" if s <= t - SETTLED_LEAD_S + EPS else "won late")
        else:
            state.append("lost")
    if "other" in state:
        return "other result"
    if "lost" in state:
        return "a leg lost"
    if "won early" not in state:
        return "no leg decided"
    if "open" not in state:
        return "every leg settled"
    return ("ok", tuple(sorted("%s:%s" % (tk, side) for (tk, side), st in zip(legs, state) if st == "open")))


def resting(px, size):
    """Amendment 1.5: the ask rounded UP to the whole cent, then at most 87c; above zero; a size of 1 or more."""
    a, z = num(px), num(size)
    if a is None or z is None or a <= EPS or z < SIZE_MIN - EPS:
        return None
    return a if math.ceil(a * 100 - 1e-7) <= ASK_MAX * 100 + 1e-7 else None


def med(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def cmd_count(combo, legs_run):
    all_runs = runs(combo)
    per, days = find_week(all_runs)
    print("COMBODONE stage 1 count | quotes are list copies (delayed) | only the first 100 quote rows of a run carry legs, so a combo with a wide spread is invisible and the count is conservative%s" % TAG)
    print_week(all_runs, per, days)
    if days is None:
        return
    rows, unreadable = week_rows(combo, all_runs, days)
    facts, whole, asked = read_legs_run(legs_run)
    need = needed_legs(rows)
    if not need <= asked:
        sys.exit("REFUSED: the leg run did not ask for %d of the %d legs this week names; it is not this week's leg pull" % (len(need - asked), len(need)))
    kinds = {"ok": 0, "empty": 0, "cut": 0}
    why = {"leg unknown": 0, "other result": 0, "a leg lost": 0, "no leg decided": 0, "every leg settled": 0, "combo closed": 0}
    books = {}
    elig = asks = book_seen = book_ask = 0
    combos, book_combos = {}, set()                       # (open set, day) -> first list ask or None
    for t, d, r, row in rows:
        kind, legs = parse_legs(row.get("leg_tickers"), row.get("legs"))
        kinds[kind] += 1
        if kind != "ok":
            continue
        c = classify(legs, facts, t)
        if not isinstance(c, tuple):
            why[c] += 1
            continue
        close = epoch(row.get("close_time"))
        if close is None or close <= t + EPS:
            why["combo closed"] += 1
            continue
        elig += 1
        key = (c[1], day_of(t))
        a = resting(row.get("yes_ask"), row.get("yes_ask_size"))
        asks += a is not None
        if combos.get(key) is None:
            combos[key] = a
        if (d, r) not in books:
            books[(d, r)] = {b.get("ticker"): b for b in (read_csv(combo, d, r, "books.csv") or [])}
        b = books[(d, r)].get(row["ticker"])
        if b is not None:
            book_seen += 1
            nb = num(b.get("no_bid_px_1"))
            if nb is not None and resting(1 - nb, b.get("no_bid_sz_1")) is not None:
                book_ask += 1
                book_combos.add(key)
    n_rows = len(rows)
    print("quote rows in the week %d (unreadable rows left out %d) | leg string whole %d (%.1f%%) | empty %d | cut %d%s" % (n_rows, unreadable, kinds["ok"], (100.0 * kinds["ok"] / n_rows + 1e-7) if n_rows else 0.0, kinds["empty"], kinds["cut"], TAG))
    print("rows with a whole leg string that are NOT eligible: leg unknown %d | a leg settled with a result other than yes or no %d | a leg already settled against the combo %d | no leg settled for the combo 60 seconds or more before %d | every leg settled %d | combo closed %d%s"
          % (why["leg unknown"], why["other result"], why["a leg lost"], why["no leg decided"], why["every leg settled"], why["combo closed"], TAG))
    with_ask = {k: a for k, a in combos.items() if a is not None}
    print("eligible snapshots %d | with a resting ask %d | with none %d%s" % (elig, asks, elig - asks, TAG))
    print("independent combos (a still-open leg set on a UTC day) %d | WITH A RESTING ASK %d | with none %d | distinct still-open leg sets over the week %d, with a resting ask %d%s"
          % (len(combos), len(with_ask), len(combos) - len(with_ask), len({k[0] for k in combos}), len({k[0] for k in with_ask}), TAG))
    for d in days:
        print("%s: independent combos %d, with a resting ask %d%s" % (d, sum(1 for k in combos if k[1] == d), sum(1 for k in with_ask if k[1] == d), TAG))
    m = med(list(with_ask.values()))
    print("median ask, each independent combo at its first eligible snapshot with a resting ask: %s%s" % ("n/a" if m is None else "%.2fc" % (100 * m + 1e-7), TAG))
    print("book figure (information; the line reads the list figure): eligible snapshots also in that run's books file %d | with 1 minus the best NO bid at 87c or less and a size of 1 or more %d | independent combos by that test %d%s" % (book_seen, book_ask, len(book_combos), TAG))
    if not whole:
        verdict = "the leg pull is not whole: not decided"
    elif len(with_ask) < KILL_BELOW:
        verdict = "CLOSED, nothing to buy: %d independent combos with a resting ask in the week, fewer than %d" % (len(with_ask), KILL_BELOW)
    else:
        verdict = "SURVIVES THE COUNT: %d independent combos with a resting ask in the week, %d or more. Nothing is approved; stage 2 needs its own registration, its own held-out date and one try" % (len(with_ask), KILL_BELOW)
    print("VERDICT: %s%s" % (verdict, TAG))


def main():
    refuse_all()
    cmds = {"week": (cmd_week, 1), "legs-job": (cmd_legs_job, 2), "count": (cmd_count, 2)}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds or len(sys.argv) - 2 != cmds[sys.argv[1]][1]:
        sys.exit(__doc__)
    cmds[sys.argv[1]][0](*sys.argv[2:])


if __name__ == "__main__":
    main()
