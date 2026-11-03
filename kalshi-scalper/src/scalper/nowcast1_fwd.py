"""NOWCAST1 forward command (workers/NOWCAST1_RESULT.md, "Forward plan"). Research only; decides nothing; no promote verb.

    python -m scalper.nowcast1_fwd forward --nowcast-file F.json [--daily-dir DIR] [--force-info]

Looks (24 hours before the release; information only, nothing is scored): 2026-11-09 13:30Z (CPI Nov 10), 2026-11-24 13:30Z (core PCE and GDP Nov 25),
2026-12-09 13:30Z (CPI Dec 10), 2026-12-22 13:30Z (core PCE Dec 23, date to be confirmed from BEA). The registered read is on or after 2027-03-01 over the first 12
forward release-series. Quotes come from RECDAILY (scalper.recdaily, branch claude/v2-recorder-daily) at the 1440 minute look; the nowcast and its sd for each release
come from F.json, {"<event_ticker>": {"nowcast": x, "sd": s}}, prepared with the registered vintage rule (the last Cleveland vintage labelled strictly before the look date;
GDP: FRED GDPNOW with sd 1.2). The rule itself is nowcast1.choose and nowcast1.settle, unchanged. The frozen development holdout of NOWCAST1 is not touched.
"""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
from pathlib import Path

from . import fwdread as fr
from . import nowcast1 as nc

SERIES = ("KXCPI", "KXCPICORE", "KXPCECORE", "KXGDP")
FWD_FREEZE = fr.utc(2026, 11, 4)
LOOK_MIN = 1440
NEEDED_SERIES, NEEDED_TRADES, Z_BAR = 12, 150, 5.27
LOOKS = [("2026-11-09 13:30Z", "CPI Nov 10"), ("2026-11-24 13:30Z", "core PCE and GDP Nov 25"), ("2026-12-09 13:30Z", "CPI Dec 10"),
         ("2026-12-22 13:30Z", "core PCE Dec 23 (to be confirmed from BEA)")]

SPEC = fr.Spec(
    id="NOWCAST1F",
    title="forward README read of the first 12 forward release-series (cheap side, 3x nowcast ratio)",
    sources=["workers/NOWCAST1_REGISTRATION.md", "workers/NOWCAST1_RESULT.md"],
    rule=[
        "For each release-series, among its strikes: YES candidate if the ask is 0.03 to 0.30 and nowcast probability p >= 3 x ask; NO candidate if (1 - bid) is 0.03 to 0.30 and (1 - p) >= 3 x (1 - bid).",
        "read the first 12 forward release-series on or after 2027-03-01, decides nothing.",
        "- **NOT_ENOUGH_DATA**: under 150 trades (or under 100 development trades) regardless of PF; the output then states months to 40 forward fills and a forward freeze line.",
    ],
    window=[
        "release-series (KXCPI, KXCPICORE, KXPCECORE, KXGDP, 'greater' strikes) closing on or after 2026-11-04, first 12 by close time, quote at 1440 minutes before the close (RECDAILY, nearest poll within 25 minutes)",
        "nowcast values from --nowcast-file (registered vintage rule); NOWCAST1's development windows and its frozen holdout are not read",
    ],
    due=fr.utc(2027, 3, 1),
    due_note="and 12 settled forward release-series",
)


def recdaily():
    return importlib.import_module("scalper.recdaily")


def release_series(rd, rows, results, nowcasts):
    """[{event, close_ts, strikes:[(ticker, bid, ask, p)], res:{ticker: yes?}}] for forward events with a nowcast, a settlement and at least one two-sided look quote."""
    by = {}
    for q in rows:
        if q["series"] in SERIES and q.get("strike_type") == "greater" and q.get("close_ts") and q["close_ts"] >= FWD_FREEZE.timestamp():
            by.setdefault(q["event_ticker"], set()).add(q["ticker"])
    out = []
    for ev, tks in sorted(by.items(), key=lambda kv: min(next(q["close_ts"] for q in rows if q["ticker"] == t) for t in kv[1])):
        n = nowcasts.get(ev)
        if not n:
            continue
        strikes, res, close = [], {}, None
        for tk in sorted(tks):
            ref = next(q for q in rows if q["ticker"] == tk)
            close = ref["close_ts"]
            if results.get(tk) in ("yes", "no"):
                res[tk] = results[tk] == "yes"
            q = rd.nearest_to_look(rows, tk, minutes_before_close=LOOK_MIN)
            if not q or q["yes_bid"] is None or q["yes_ask"] is None or not 0 < q["yes_bid"] < q["yes_ask"] < 1 or ref["floor_strike"] is None:
                continue
            strikes.append((tk, q["yes_bid"], q["yes_ask"], nc.p_above(n["nowcast"], n["sd"], ref["floor_strike"])))
        if res:
            out.append({"event": ev, "close_ts": close, "strikes": strikes, "res": res})
    return sorted(out, key=lambda r: (r["close_ts"], r["event"]))


def trades(rs, mult=1.0):
    out = []
    for r in rs:
        pick = nc.choose(r["strikes"])
        if pick and pick[0] in r["res"]:
            tk, side, price, ratio = pick
            yes = r["res"][tk]
            out.append({"event": r["event"], "date": fr.day_of(r["close_ts"]), "tk": tk, "side": side, "price": price, "ratio": ratio, "win": yes == (side == "yes"),
                        "net": nc.settle(side, price, yes, mult)})
    return out


def judge(tr, n_series):
    if len(tr) < NEEDED_TRADES:
        return "NOT_ENOUGH_DATA"
    h = len(tr) // 2
    m1 = sum(t["net"] for t in tr[:h]) / h
    m2 = sum(t["net"] for t in tr[h:]) / (len(tr) - h)
    return "FALSIFIED" if (m1 <= 0 or m2 <= 0 or fr.pf([t["net"] for t in tr]) < 1.5) else "NOT_YET_FALSIFIED"


def forward(argv, now=None):
    f = fr.flags(argv)
    rest = f["rest"]
    daily = rest[rest.index("--daily-dir") + 1] if "--daily-dir" in rest else None
    nfile = rest[rest.index("--nowcast-file") + 1] if "--nowcast-file" in rest else None
    st = {}

    def get():
        if "d" not in st:
            try:
                rd = recdaily()
            except ImportError:
                raise SystemExit("scalper.recdaily is not on this branch (claude/v2-recorder-daily, unmerged). Nothing was read.")
            d = daily
            if not d:
                tmp = tempfile.mkdtemp(prefix="nowcast1f_")
                fr.checkout_quote_data(["daily"], tmp)
                d = str(Path(tmp) / "daily")
            nw = json.loads(Path(nfile).read_text()) if nfile else {}
            st["d"] = release_series(rd, rd.load_quotes(d), rd.load_results(d), nw)
        return st["d"]

    def info():
        L = ["looks (24 h before the release, information only): " + "; ".join(f"{a} {b}" for a, b in LOOKS)]
        if nfile or daily:
            rs = get()
            L.append(f"forward release-series with a nowcast and a settlement so far: {len(rs)} of the {NEEDED_SERIES} needed; trades they would give: {len(trades(rs))}")
        else:
            L.append("pass --nowcast-file and --daily-dir to count release-series")
        return L

    def ready(n):
        if not nfile:
            return "needs --nowcast-file (the nowcast and sd per release; nothing records them)"
        k = len(get())
        return None if k >= NEEDED_SERIES else f"only {k} settled forward release-series; the registered read is the first {NEEDED_SERIES}"

    def real():
        rs = get()[:NEEDED_SERIES]
        tr = trades(rs)
        tr12 = trades(rs, 1.2)
        nets = [t["net"] for t in tr]
        m, z = fr.clustered([(t["date"], t["net"]) for t in tr])
        w = judge(tr, len(rs))
        L = [f"NOWCAST1 FORWARD {w}: first {len(rs)} forward release-series, {len(tr)} trades on {len({t['date'] for t in tr})} dates; PF {fr.fpf(fr.pf(nets)) if nets else 'n/a'}; mean {100 * m:+.2f}c per contract; fees x1.2 PF {fr.fpf(fr.pf([t['net'] for t in tr12])) if tr12 else 'n/a'}; "
             f"date-clustered z {z:+.2f} against the bar {Z_BAR}. Decides nothing."]
        body = (f"first {len(rs)} forward release-series from the 2026-11-04 freeze to {fr.day_of(rs[-1]['close_ts']) if rs else 'n/a'}; n {len(tr)} trades on {len({t['date'] for t in tr})} dates; "
                f"cost fee 7% x C x p x (1-p) at C 10, x1.2 stress; PF {fr.fpf(fr.pf(nets)) if nets else 'n/a'}, z {z:+.2f} vs bar {Z_BAR}; VERDICT {w}; decides nothing")
        return L, body

    return fr.run(SPEC, argv, real, info, now=now, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
