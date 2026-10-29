"""FWDLEDGER: an automatic forward ledger for strategy candidates (workers/candidates/*.json, see workers/candidates/README.md).
Research only. It adds no hypothesis, places no order, reads no key, and NEVER promotes anything: it only reports. A candidate with
forward PF 1.5+ (at 1 AND 10 contracts) on 30+ trades over 10+ trade days is marked READY FOR THE FALSIFIER, nothing more.

    python -m scalper.fwdledger run [--candidates DIR] [--out FILE]
        evaluates every candidate on every window closing AFTER its freeze time that has data, writes workers/FORWARD_LEDGER.md
        (or FILE). Run by `scalper.autoscore check` once per AUTO pass.

Data sources a candidate may name:
  candles  1 minute candles in data/fresh.sqlite (refreshed by `python -m scalper.fresh_update`); settlement from its market table
  quotes   the quote recorder on origin/quote-data, quotes/*/ (last ~150 s of each window, about two polls a second)
  r6       recorder R6 on origin/quote-data, book15r6/*/ (5 levels a side every few seconds, plus the public tape)
Fees: 7% x C x p x (1-p), rounded UP to the cent per order, at C = 1 and C = 10 (and x1.2 as a stress column); a position held to
settlement pays the entry fee only. Robustness: a bad candidate file, a missing evaluator or a crashing evaluator is reported on its
own row and never stops the others.
"""
from __future__ import annotations

import importlib
import json
import math
import sqlite3
import sys
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .fwdeval import NoData
from .paths import DATA_DIR

ROOT = DATA_DIR.parent
CAND_DIR = ROOT / "workers" / "candidates"
OUT = ROOT / "workers" / "FORWARD_LEDGER.md"
TRADES_OUT = DATA_DIR / "fwdledger_trades.json"
FRESH = DATA_DIR / "fresh.sqlite"
BASE_SERIES = ("KXBTC15M", "KXETH15M", "KXGOLD15M")   # always loaded for "candles", so cross-market features have their peers
SOURCES = ("candles", "quotes", "r6")
STAGES = ("discovery", "validation", "reference")
REQUIRED = ("id", "market", "stage", "freeze_utc", "source", "evaluator", "params")
READY_PF, READY_TRADES, READY_DAYS = 1.5, 30, 10
SIZES = (1, 10)


def order_fee(p: float, c: int, m: float = 1.0) -> float:
    """Dollars for one taker order of c contracts at price p, rounded up to the cent."""
    if not 0.0 < p < 1.0:
        return 0.0
    return math.ceil(m * 0.07 * c * p * (1 - p) * 100 - 1e-9) / 100


def net_per_contract(tr: dict, result: str, c: int, m: float = 1.0) -> float:
    e = tr["entry"]
    if tr.get("exit") is None:
        payout, fees = (1.0 if tr["side"] == result else 0.0), order_fee(e, c, m)
    else:
        payout, fees = tr["exit"], order_fee(e, c, m) + order_fee(tr["exit"], c, m)
    return payout - e - fees / c


def pf(v) -> float:
    w = sum(x for x in v if x > 0); l = -sum(x for x in v if x < 0)
    return w / l if l > 0 else (float("inf") if w > 0 else 0.0)


def parse_ts(x: str) -> int:
    return int(datetime.fromisoformat(x.replace("Z", "+00:00")).timestamp())


def day(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- data sources

def load_candles(series: set, min_close: int) -> list:
    """Settled windows in data/fresh.sqlite closing after min_close; each window carries its peers (same close, other series)."""
    db = sqlite3.connect(FRESH)
    want = sorted(set(series) | set(BASE_SERIES))
    q = ",".join("?" * len(want))
    mk = db.execute(f"select ticker, series, strike, close_ts, result from market where series in ({q}) and close_ts > ?", (*want, min_close)).fetchall()
    cs = defaultdict(dict)
    for tk, e, b, a, v, oi in db.execute(
            f"select ticker, end_ts, bid_c, ask_c, volume, oi from candle where series in ({q}) and end_ts > ? and bid_c is not null and ask_c is not null",
            (*want, min_close - 900)):
        cs[tk][e] = (b, a, v or 0.0, oi or 0.0)
    byclose = defaultdict(dict)
    wins = []
    for tk, se, strike, close_ts, res in mk:
        if not cs.get(tk):
            continue
        byclose[close_ts][se] = cs[tk]
        if se in series:
            wins.append({"source": "candles", "ticker": tk, "series": se, "strike": strike, "close_ts": close_ts,
                         "result": res if res in ("yes", "no") else None, "candles": cs[tk]})
    for w in wins:
        w["peers"] = {se: c for se, c in byclose[w["close_ts"]].items() if se != w["series"]}
    return wins


def _fresh_results() -> dict:
    try:
        return dict(sqlite3.connect(FRESH).execute("select ticker, result from market where result in ('yes','no')").fetchall())
    except Exception:
        return {}


def load_quotes(series: set, min_close: int) -> list:
    """Quote recorder windows: polls [(t_recv_s, yes_bid, yes_ask, bid_size, ask_size)], the coverage row, and the result."""
    from .mm1 import _csv, _git
    _git("fetch", "-q", "origin", "quote-data")
    files = _git("ls-tree", "-r", "--name-only", "origin/quote-data").decode().split()
    lo_day = day(min_close - 86400)
    runs = sorted({f.rsplit("/", 1)[0] for f in files if f.startswith("quotes/") and f.endswith("quotes.csv.gz") and f.split("/")[1] >= lo_day})
    results, best = _fresh_results(), {}
    for r in runs:
        for row in _csv(f"{r}/results.csv.gz"):
            if row.get("result") in ("yes", "no"):
                results[row["ticker"]] = row["result"]
        cov = {}
        for row in _csv(f"{r}/coverage.csv.gz"):
            tk = row.get("ticker", "")
            se = tk.split("-", 1)[0]
            close = parse_ts(row["window_close_utc"])
            if se in series and close > min_close and (tk not in best or int(row["ok_polls"] or 0) > int(best[tk][1]["ok_polls"] or 0)):
                cov[tk] = (close, row)
        if not cov:
            continue
        polls = defaultdict(list)
        for x in _csv(f"{r}/quotes.csv.gz"):
            if x["ticker"] in cov and x.get("yes_bid") not in (None, "") and x.get("yes_ask") not in (None, ""):
                polls[x["ticker"]].append((int(x["t_recv_ms"]) / 1000, float(x["yes_bid"]), float(x["yes_ask"]),
                                           float(x["bid_size"] or 0), float(x["ask_size"] or 0)))
        for tk, (close, row) in cov.items():
            best[tk] = (close, row, sorted(polls.get(tk, [])))
    return [{"source": "quotes", "ticker": tk, "series": tk.split("-", 1)[0], "close_ts": close, "result": results.get(tk),
             "coverage": row, "polls": ps} for tk, (close, row, ps) in best.items() if ps]


def load_r6(series: set, min_close: int) -> list:
    """Recorder R6 windows: polls [quote2b.Poll in exchange time], trades [(t, yes_price, count, side)], the coverage row, the result."""
    from . import r6tests as r6
    ws = {k: v for k, v in r6.windows().items() if k[1] in series and k[0] > min_close}
    byrun = defaultdict(list)
    for k, (r, row) in ws.items():
        byrun[r].append((k, row))
    results, out = _fresh_results(), []
    for r, ks in sorted(byrun.items()):
        book = r6._csv(f"{r}/book.csv.gz")
        off = r6._offset(book)
        if off is None:
            continue
        tick = {row["ticker"]: (k, row) for k, row in ks}
        polls, trades = defaultdict(list), defaultdict(list)
        for x in book:
            if x["ticker"] in tick:
                polls[x["ticker"]].append(r6._poll(x, off))
        del book
        for x in r6._csv(f"{r}/trades.csv.gz"):
            if x["ticker"] in tick:
                trades[x["ticker"]].append((r6._ts(x["created_time"]), float(x["yes_price_dollars"]), float(x["count_fp"]),
                                            1 if x["taker_outcome_side"] == "yes" else -1))
        for tk, ((close, se), row) in tick.items():
            res = row.get("result") if row.get("result") in ("yes", "no") else results.get(tk)
            out.append({"source": "r6", "ticker": tk, "series": se, "close_ts": close, "result": res, "coverage": row,
                        "polls": sorted(polls.get(tk, []), key=lambda p: p.t), "trades": sorted(trades.get(tk, []))})
    return out


LOADERS = {"candles": load_candles, "quotes": load_quotes, "r6": load_r6}


# ---------------------------------------------------------------- candidates

def read_candidates(cdir: Path) -> list:
    out = []
    for f in sorted(cdir.glob("*.json")):
        c = {"id": f.stem, "_file": f.name}
        try:
            c.update(json.loads(f.read_text()))
            miss = [k for k in REQUIRED if k not in c]
            if miss:
                raise ValueError(f"missing {', '.join(miss)}")
            if c["source"] not in SOURCES:
                raise ValueError(f"unknown source {c['source']!r}")
            c["_markets"] = {c["market"]} if isinstance(c["market"], str) else set(c["market"])
            c["_freeze"] = parse_ts(c["freeze_utc"])
            mod, fn = c["evaluator"].split(":")
            c["_fn"] = getattr(importlib.import_module(mod), fn)
        except Exception as ex:
            c["_error"] = f"{type(ex).__name__}: {str(ex)[:200]}"
        out.append(c)
    return out


def evaluate(c: dict, windows: list) -> dict:
    trades, nodata, errors, last_err, evaluated = [], 0, 0, "", []
    for w in windows:
        if w["series"] not in c["_markets"] or w["close_ts"] <= c["_freeze"] or w.get("result") not in ("yes", "no"):
            continue
        try:
            tr = c["_fn"](w, c["params"])
        except NoData:
            nodata += 1
            continue
        except Exception as ex:          # one window's crash is counted and shown, never fatal
            errors += 1; last_err = f"{type(ex).__name__}: {str(ex)[:160]}"
            continue
        evaluated.append(w["close_ts"])
        if tr is None:
            continue
        if tr.get("side") not in ("yes", "no") or not 0.0 < float(tr["entry"]) < 1.0:
            errors += 1; last_err = f"bad trade {tr!r}"[:160]
            continue
        tr = dict(tr, entry=float(tr["entry"]), exit=None if tr.get("exit") is None else float(tr["exit"]))
        row = {"ticker": w["ticker"], "series": w["series"], "close_ts": w["close_ts"], "result": w["result"], "side": tr["side"],
               "entry": tr["entry"], "exit": tr["exit"], "zero_volume": bool(tr.get("zero_volume", False))}
        for C in SIZES:
            row[f"net{C}"] = net_per_contract(tr, w["result"], C)
        row["net10s"] = net_per_contract(tr, w["result"], 10, 1.2)
        trades.append(row)
    return {"trades": trades, "nodata": nodata, "errors": errors, "last_err": last_err, "evaluated": evaluated}


def summary(c: dict, ev: dict, now: int) -> dict:
    t = ev["trades"]
    days = sorted({day(x) for x in ev["evaluated"]})
    tdays = sorted({day(x["close_ts"]) for x in t})
    span_days = max(1.0, ((max(ev["evaluated"]) if ev["evaluated"] else now) - c["_freeze"]) / 86400)
    s = {"n": len(t), "wins": sum(1 for x in t if x["net10"] > 0), "losses": sum(1 for x in t if x["net10"] <= 0),
         "pf1": pf([x["net1"] for x in t]), "pf10": pf([x["net10"] for x in t]), "pf10s": pf([x["net10s"] for x in t]),
         "mean1": sum(x["net1"] for x in t) / len(t) if t else 0.0, "mean10": sum(x["net10"] for x in t) / len(t) if t else 0.0,
         "days": len(days), "tdays": len(tdays), "per_week": len(t) / span_days * 7 if ev["evaluated"] else 0.0,
         "windows": len(ev["evaluated"]), "zv": sum(x["zero_volume"] for x in t)}
    s["ready"] = (s["n"] >= READY_TRADES and s["tdays"] >= READY_DAYS and s["pf1"] >= READY_PF and s["pf10"] >= READY_PF)
    return s


def fpf(x: float) -> str:
    return "inf" if x == float("inf") else f"{x:.2f}"


def render(cands: list, res: dict, now: int) -> str:
    stamp = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = ["# FORWARD LEDGER (automatic; research only)", "",
         f"Written by `python -m scalper.fwdledger run` (once per AUTO pass, `scalper.autoscore check`). Last updated {stamp}.",
         "Forward evidence counts only windows that CLOSED after a candidate's freeze time, had the data its rule needs and have settled.",
         "Fees 7% x C x p x (1-p) rounded up to the cent per order, at 1 and 10 contracts; held to settlement pays the entry fee only. "
         "Win = net at 10 contracts above zero. Net per contract is at 10 contracts. Trades per week: forward trades over the time from "
         "the freeze to the last evaluated close.",
         f"This ledger never promotes anything. READY FOR THE FALSIFIER means only: forward PF {READY_PF}+ at 1 and at 10 contracts on "
         f"{READY_TRADES}+ trades over {READY_DAYS}+ trade days. It earns a falsifier read, nothing more. "
         "How a generator adds a candidate: `workers/candidates/README.md`.", "",
         "| id | market | stage | freeze | fwd days | trades | wins | losses | PF 1c | PF 10c | net/contract | trades/week | updated | flag |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    order = sorted(cands, key=lambda c: (-(c.get("_freeze") or 0), c["id"]))
    for c in order:
        mk = c.get("market") if isinstance(c.get("market"), str) else ",".join(c.get("market") or [])
        fz = day(c["_freeze"]) if c.get("_freeze") else str(c.get("freeze_utc", "?"))
        r = res.get(c["id"])
        if c.get("_error") or (r and r.get("error")):
            L.append(f"| {c['id']} | {mk} | {c.get('stage', '?')} | {fz} | | | | | | | | | {stamp} | NOT_RUNNABLE: {(c.get('_error') or r['error'])[:120]} |")
            continue
        s = r["s"]
        flag = ("READY FOR THE FALSIFIER" if s["ready"] else "") + (f" EVALUATOR ERRORS {r['ev']['errors']}" if r["ev"]["errors"] else "")
        L.append(f"| {c['id']} | {mk} | {c['stage']} | {fz} | {s['days']} | {s['n']} | {s['wins']} | {s['losses']} | {fpf(s['pf1'])} | "
                 f"{fpf(s['pf10'])} | {s['mean10'] * 100:+.2f}c | {s['per_week']:.1f} | {stamp} | {flag} |")
    L += ["", "## History per candidate", ""]
    for c in order:
        r = res.get(c["id"])
        L.append(f"### {c['id']}")
        if c.get("_error") or (r and r.get("error")):
            L += ["", f"NOT_RUNNABLE: {c.get('_error') or r['error']}", ""]
            continue
        s, ev = r["s"], r["ev"]
        L += ["", f"Evaluator `{c['evaluator']}`, source `{c['source']}`, frozen {c['freeze_utc']}. {c.get('description', '')}".rstrip(),
              f"Windows evaluated {s['windows']} on {s['days']} days; without the data the rule needs {ev['nodata']}; evaluator errors {ev['errors']}"
              + (f" (last: {ev['last_err']})" if ev["errors"] else "") + f". Trades {s['n']} on {s['tdays']} days; zero-volume trades {s['zv']}.",
              f"PF at 1 contract {fpf(s['pf1'])}, at 10 contracts {fpf(s['pf10'])}, at 10 contracts with fees x1.2 {fpf(s['pf10s'])}; "
              f"net per contract {s['mean1'] * 100:+.2f}c at 1, {s['mean10'] * 100:+.2f}c at 10.", ""]
        if ev["trades"]:
            L += ["| date (UTC) | trades | wins | losses | net/contract 10c (day) | cumulative net/contract 10c | cumulative PF 10c |", "|---|---|---|---|---|---|---|"]
            by = defaultdict(list)
            for x in ev["trades"]:
                by[day(x["close_ts"])].append(x)
            cum = []
            for d in sorted(by):
                v = by[d]; cum += [x["net10"] for x in v]
                L.append(f"| {d} | {len(v)} | {sum(1 for x in v if x['net10'] > 0)} | {sum(1 for x in v if x['net10'] <= 0)} | "
                         f"{sum(x['net10'] for x in v) * 100:+.1f}c | {sum(cum) * 100:+.1f}c | {fpf(pf(cum))} |")
            L.append("")
        else:
            L += ["No forward trades yet.", ""]
    return "\n".join(L) + "\n"


def run(cand_dir: Path = CAND_DIR, out: Path = OUT, now: int | None = None) -> str:
    now = int(datetime.now(timezone.utc).timestamp()) if now is None else now
    cands = read_candidates(Path(cand_dir))
    ok = [c for c in cands if not c.get("_error")]
    data, res = {}, {}
    for src in SOURCES:
        cs = [c for c in ok if c["source"] == src]
        if not cs:
            continue
        try:
            data[src] = LOADERS[src](set().union(*(c["_markets"] for c in cs)), min(c["_freeze"] for c in cs))
        except Exception as ex:        # a source that cannot load stops only its own candidates
            for c in cs:
                res[c["id"]] = {"error": f"source {src} failed: {type(ex).__name__}: {str(ex)[:160]}"}
    dump = {}
    for c in ok:
        if c["id"] in res:
            continue
        try:
            ev = evaluate(c, sorted(data[c["source"]], key=lambda w: (w["close_ts"], w["ticker"])))
            res[c["id"]] = {"ev": ev, "s": summary(c, ev, now)}
            dump[c["id"]] = ev["trades"]
        except Exception as ex:
            res[c["id"]] = {"error": f"{type(ex).__name__}: {str(ex)[:160]}"}
            traceback.print_exc()
    Path(out).write_text(render(cands, res, now))
    try:
        TRADES_OUT.write_text(json.dumps(dump))
    except Exception:
        pass
    parts = []
    for c in cands:
        r = res.get(c["id"], {})
        if c.get("_error") or r.get("error"):
            parts.append(f"{c['id']} NOT_RUNNABLE")
        else:
            parts.append(f"{c['id']} {r['s']['n']} trades PF10 {fpf(r['s']['pf10'])}" + (" READY FOR THE FALSIFIER" if r["s"]["ready"] else ""))
    line = f"FWDLEDGER: {len(cands)} candidates; " + "; ".join(parts)
    print(line, flush=True)
    return line


def main(argv: list) -> None:
    if len(argv) < 2 or argv[1] != "run":
        print(__doc__); return
    kw = {}
    if "--candidates" in argv:
        kw["cand_dir"] = Path(argv[argv.index("--candidates") + 1])
    if "--out" in argv:
        kw["out"] = Path(argv[argv.index("--out") + 1])
    run(**kw)


if __name__ == "__main__":
    main(sys.argv)
