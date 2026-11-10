#!/usr/bin/env python3
"""DRAFT, NOT ACTIVE. Recorder OKLQ (Nov 10, 2026; the owner approved the research session's backlog row 55, kalshi-scalper/refine_tools/IDEA_BACKLOG.md; feasibility in
kalshi-scalper/refine_tools/ROW55_56_FEASIBILITY.md). Research data only: nothing here trades, signs or sends an order.

What it records. OKX's PUBLIC liquidation feed for the Bitcoin perpetual swaps (BTC-USDT-SWAP and BTC-USD-SWAP): for every filled liquidation its time (ts, ms), side, posSide,
size (sz, contracts), bankruptcy price (bkPx), bkLoss and the instrument id. It is for the research question "does a liquidation cascade move Bitcoin's 15 minute Kalshi
market"; nothing is scored here. OKX keeps only about 17 hours of this history (100 rows per call, newest first, `after=<ts>` pages to older rows), so the history cannot be
fetched later: this log is the only way to have it.
  - liquidations.csv: one row per liquidation, de-duplicated by (instId, ts, side, posSide, bkPx, sz) within a pass AND against what earlier passes already pushed (the workflow
                      checks the data branch out and passes its oklq/ folder with --seen, so overlapping passes add no duplicates; the analysis must still drop exact repeats);
  - coverage.csv:    one row per instrument per pass (requests, pages, rows read, new rows, oldest and newest ts read, whether the pass reached rows it already had or the
                      17 hour horizon, or ran out of pages = a possible hole), so a gap is counted, not silent.

Public data only, no key, no auth header, no order. One host (www.okx.com), GET only.
Politeness. One request stream, one call at a time, at least 1.0 s apart (OKX allows far more). Every request goes through Stream.get: a 429, a 5xx or a dropped connection
waits 2 s, doubling up to 30 s, tried at most 4 times, then the read is marked failed and the job goes on. A failed request never fails the job (the script always exits 0).

It stops by itself: nothing is recorded from END_UTC (2026-12-31 23:59 UTC). Stop it sooner by deleting the workflow.
Rows are written as OKX returns them (numbers as the exchange's own text, a missing value empty, never zero)."""
import argparse
import calendar
import csv
import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.request

OKX = "https://www.okx.com/api/v5/public/liquidation-orders"
UNDERLYINGS = ("BTC-USDT", "BTC-USD")       # the two Bitcoin swap families (linear and inverse)
END_UTC = "2026-12-31T23:59:00Z"            # nothing is recorded from here on
HORIZON_S = 16 * 3600                       # OKX keeps about 17 h; a pass never asks for rows older than 16 h (the 17 h edge is empty)
OVERLAP_MS = 5 * 60 * 1000                  # a pass reads this far back past the newest row it already has, to catch late arrivals
PAGE_LIMIT = 40                             # pages per instrument per pass (100 rows each; BTC-USDT runs about 200 rows an hour, so 16 h is about 32 pages); hitting it first is logged as a possible hole
GAP_S = 1.0
BACKOFF_S = 2.0
BACKOFF_MAX_S = 30.0
MAX_TRIES = 4
SEEN_DAYS = 3                               # how many data-branch day folders --seen reads for de-duplication
JOB_BUDGET_S = 10 * 60                      # a pass that is still running after this long stops asking for more

ROW_COLS = ["t_recv_ms", "inst_id", "uly", "ts_ms", "side", "pos_side", "sz", "bk_px", "bk_loss", "ccy"]
COVER_COLS = ["t_start_ms", "t_end_ms", "uly", "requests", "pages", "rows_read", "rows_new", "rows_dup", "oldest_ts_ms", "newest_ts_ms", "stop_reason", "n429", "n5xx",
              "n_other_fail", "seen_keys", "note"]


def epoch_of(iso_s):
    return calendar.timegm(time.strptime(iso_s, "%Y-%m-%dT%H:%M:%SZ"))


END_EPOCH = epoch_of(END_UTC)


def past_end(now):
    return now >= END_EPOCH


def user_agent():
    repo = os.environ.get("GITHUB_REPOSITORY", "shwoopnet")
    # An identification header, not a credential.
    return "shwoopnet-research-recorder (research only, no key; https://github.com/%s)" % repo


def rate_budget():
    """Requests from the constants: one stream, one call a second at most; a pass reads at most PAGE_LIMIT pages for each of the two underlyings."""
    return {"streams": 1, "peak_per_min": 60.0 / GAP_S, "max_per_pass": PAGE_LIMIT * len(UNDERLYINGS), "typical_per_pass": len(UNDERLYINGS)}


def http_get(url, headers):
    """(status, decoded json or None). Never raises: a failed read is a status, so one bad second cannot end the run."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


class Stream:
    """One request stream: one call at a time, at least `gap_s` between calls. EVERY request in this file goes through `get`. A 429, a 5xx or a failed connection (status 0)
    waits BACKOFF_S, doubling up to BACKOFF_MAX_S, and is asked again up to MAX_TRIES times in all; then the status is returned and the caller marks the read failed. `fetch` is
    the transport (url -> (status, body)); tests pass a fake one with a fake clock and sleep."""

    def __init__(self, gap_s, headers, fetch=None, clock=time.time, sleep=time.sleep):
        assert gap_s >= 1.0
        self.gap_s, self.headers, self.clock, self.sleep = gap_s, headers, clock, sleep
        self.fetch = fetch or (lambda url: http_get(url, headers))
        self.next_ok = 0.0
        self.requests = self.n429 = self.n5xx = self.n_other = 0

    def get(self, url):
        wait = BACKOFF_S
        st, body = 0, None
        for attempt in range(MAX_TRIES):
            gap = self.next_ok - self.clock()
            if gap > 0:
                self.sleep(gap)
            st, body = self.fetch(url)
            self.requests += 1
            self.next_ok = self.clock() + self.gap_s
            if st == 429 or st >= 500 or st == 0:
                if st == 429:
                    self.n429 += 1
                elif st >= 500:
                    self.n5xx += 1
                else:
                    self.n_other += 1
                if attempt + 1 < MAX_TRIES:
                    self.sleep(wait)
                    self.next_ok = max(self.next_ok, self.clock())
                    wait = min(BACKOFF_MAX_S, wait * 2)
                continue
            if st != 200:
                self.n_other += 1
            return st, body
        return st, None


def row_key(inst, d):
    """The de-duplication key of one liquidation: OKX has no row id, so it is the whole identity."""
    return "|".join(str(x) for x in (inst, d.get("ts"), d.get("side"), d.get("posSide"), d.get("bkPx"), d.get("sz")))


def parse_page(body):
    """(rows, ok): rows are (inst_id, uly, detail dict) from one OKX answer, newest first as OKX sends them. ok is False for a non-zero code or an unexpected shape."""
    if not isinstance(body, dict) or body.get("code") != "0" or not isinstance(body.get("data"), list):
        return [], False
    out = []
    for e in body["data"]:
        if not isinstance(e, dict):
            continue
        inst, uly = e.get("instId", ""), e.get("uly") or e.get("instFamily") or ""
        for d in e.get("details") or []:
            if isinstance(d, dict) and str(d.get("ts", "")).isdigit():
                out.append((inst, uly, d))
    return out, True


def load_seen(seen_dir, now):
    """(set of keys, newest ts per uly) from liquidations.csv(.gz) under the day folders of the last SEEN_DAYS days. Never raises."""
    keys, newest = set(), {}
    if not seen_dir or not os.path.isdir(seen_dir):
        return keys, newest
    days = {time.strftime("%Y-%m-%d", time.gmtime(now - i * 86400)) for i in range(SEEN_DAYS + 1)}
    try:
        for day in sorted(os.listdir(seen_dir)):
            if day not in days:
                continue
            for dp, _dn, fns in os.walk(os.path.join(seen_dir, day)):
                for fn in fns:
                    p = os.path.join(dp, fn)
                    opener = gzip.open if fn == "liquidations.csv.gz" else open if fn == "liquidations.csv" else None
                    if not opener:
                        continue
                    try:
                        with opener(p, "rt", newline="") as f:
                            for r in csv.DictReader(f):
                                keys.add(row_key(r.get("inst_id"), {"ts": r.get("ts_ms"), "side": r.get("side"), "posSide": r.get("pos_side"), "bkPx": r.get("bk_px"),
                                                                     "sz": r.get("sz")}))
                                try:
                                    ts = int(r.get("ts_ms"))
                                    newest[r.get("uly")] = max(newest.get(r.get("uly"), 0), ts)
                                except (TypeError, ValueError):
                                    pass
                    except Exception:
                        continue
    except Exception:
        pass
    return keys, newest


def read_underlying(stream, uly, seen, newest_seen_ms, now, deadline=None):
    """Page back from the newest liquidation of one underlying until the pass reaches rows it already has (minus an overlap), the horizon, or runs out of pages.
    Returns (new rows as lists, coverage dict). `seen` is updated with the keys added. Never raises."""
    t0 = int(time.time() * 1000)
    r0, a0, b0, c0 = stream.requests, stream.n429, stream.n5xx, stream.n_other
    horizon_ms = int((now - HORIZON_S) * 1000)
    stop_ms = max(horizon_ms, newest_seen_ms - OVERLAP_MS) if newest_seen_ms else horizon_ms
    new, read, dup, pages = [], 0, 0, 0
    oldest = newest = None
    reason, note, after = "", [], ""
    while True:
        if pages >= PAGE_LIMIT:
            reason = "page_limit"
            note.append("possible hole: page limit before the stop point")
            break
        if deadline is not None and time.time() > deadline:
            reason = "out_of_time"
            note.append("possible hole: out of time")
            break
        url = "%s?instType=SWAP&uly=%s&state=filled%s" % (OKX, uly, ("&after=" + after) if after else "")
        st, body = stream.get(url)
        rows, ok = parse_page(body) if st == 200 else ([], False)
        if not ok:
            reason = "read_failed"
            note.append("possible hole: http %s" % st)
            break
        pages += 1
        if not rows:
            reason = "history_end"
            break
        t_recv = int(time.time() * 1000)
        for inst, u, d in rows:
            ts = int(d["ts"])
            read += 1
            oldest = ts if oldest is None else min(oldest, ts)
            newest = ts if newest is None else max(newest, ts)
            k = row_key(inst, d)
            if k in seen:
                dup += 1
                continue
            seen.add(k)
            new.append([t_recv, inst, u or uly, d.get("ts"), d.get("side", ""), d.get("posSide", ""), d.get("sz", ""), d.get("bkPx", ""), d.get("bkLoss", ""), d.get("ccy", "")])
        page_oldest = min(int(d["ts"]) for _i, _u, d in rows)
        if page_oldest <= stop_ms:
            reason = "reached_seen_or_horizon"
            break
        if len(rows) < 100:
            reason = "history_end"
            break
        after = str(page_oldest)
    cov = [t0, int(time.time() * 1000), uly, stream.requests - r0, pages, read, len(new), dup, "" if oldest is None else oldest, "" if newest is None else newest, reason,
           stream.n429 - a0, stream.n5xx - b0, stream.n_other - c0, len(seen), ";".join(note)]
    return new, cov


class Out:
    def __init__(self, d):
        os.makedirs(d, exist_ok=True)
        self.files, self.w = [], {}
        for name, cols in (("liquidations", ROW_COLS), ("coverage", COVER_COLS)):
            f = open(os.path.join(d, name + ".csv"), "a", newline="")
            w = csv.writer(f)
            if f.tell() == 0:
                w.writerow(cols)
            self.files.append(f)
            self.w[name] = w

    def write(self, name, rows):
        self.w[name].writerows(rows)

    def close(self):
        for f in self.files:
            f.flush()
            f.close()


def run_pass(stream, out, seen_dir=None, now=None, deadline=None):
    """One pass over both underlyings. Never raises."""
    now = time.time() if now is None else now
    seen, newest = load_seen(seen_dir, now)
    totals = {}
    for uly in UNDERLYINGS:
        rows, cov = read_underlying(stream, uly, seen, newest.get(uly, 0), now, deadline)
        out.write("liquidations", rows)
        out.write("coverage", [cov])
        totals[uly] = {"new": cov[6], "pages": cov[4], "stop": cov[10]}
    return totals


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--seen", default="", help="the data branch's oklq folder, read to skip rows an earlier pass already pushed")
    args = ap.parse_args(argv)
    now = time.time()
    if past_end(now):
        print("past the end date (%s): nothing to record" % END_UTC)
        return 0
    out = Out(args.outdir)
    try:
        stream = Stream(GAP_S, {"User-Agent": user_agent()})
        print("pass: %s" % json.dumps(run_pass(stream, out, args.seen, now, deadline=time.time() + JOB_BUDGET_S)))
        print("requests: %d (429: %d, 5xx: %d, other: %d)" % (stream.requests, stream.n429, stream.n5xx, stream.n_other))
    except Exception as e:          # a recorder that fails loudly loses a day; this one writes what it has and exits 0
        print("recorder error (ignored): %s" % type(e).__name__)
    finally:
        out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
