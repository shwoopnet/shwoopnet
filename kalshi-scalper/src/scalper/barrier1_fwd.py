"""BARRIER1 forward command (workers/BARRIER1_RESULT.md, "Forward plan"). Research only; no promote verb.

    python -m scalper.barrier1_fwd forward [--daily-dir DIR] [--force-info]

The registered rule, unchanged (barrier1.decide, touch_prob, realised_vol, net_per_contract): look = open + 48 hours, the recorded yes ask and bid, 14 day OKX hourly vol,
ratio 2.0, price 3c to 30c, held to settlement, BAR-CHEAP and BAR-RICH each with its own verdict. Events opening on or after 2026-11-04 only (the November events are past
their look). Quotes come from RECDAILY (scalper.recdaily, branch claude/v2-recorder-daily) at open + 2880 minutes; OKX hourly closes come from barrier1.okx_hourly
(public). Read date: the October 2027 event or 40 fills, whichever is later; the command is due 2027-11-01 and also waits for 40 fills.
"""
from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path

from . import barrier1 as b1
from . import fwdread as fr

FWD_FREEZE = fr.utc(2026, 11, 4)
NEEDED_FILLS, NEEDED_TRADES, Z_BAR = 40, 150, 5.27

SPEC = fr.Spec(
    id="BARRIER1F",
    title="forward read of the monthly one-touch series (14 series, look = open + 48 h)",
    sources=["workers/BARRIER1_REGISTRATION.md", "workers/BARRIER1_RESULT.md"],
    rule=[
        "- **BAR-CHEAP (long the cheap touch):** BUY YES when the ask is in [0.03, 0.30] and `p_touch >= 2.0 * ask`.",
        "- **FALSIFIED** for a rule when mean net after fee is not above 0 in BOTH halves (by event close time) of what exists, or PF under 1.5.",
        "2027 event or 40 fills, whichever is later.",
        "Rule frozen exactly as registered (look = open + 48 h, hourly ask, 14 day OKX hourly vol, ratio 2.0, ask 3c to 30c, hold to settlement)",
    ],
    window=["markets of the 14 BARRIER1 series with open_ts >= 2026-11-04 and a recorded settlement, quote nearest open + 2880 minutes (RECDAILY, within 25 minutes), OKX hourly closes before the look"],
    due=fr.utc(2027, 11, 1),
    due_note="the October 2027 event or 40 fills, whichever is later",
)


def recdaily():
    return importlib.import_module("scalper.recdaily")


def build(rd, rows, results, okx):
    """okx(inst, lo_s, hi_s) -> {hour_ts: close}. Returns dicts like barrier1.build_rows (t, s, ev, close, ask, bid, p, res, K, S, sig)."""
    out, drop = [], {}
    seen = {}
    for q in rows:
        if q["series"] in b1.SERIES and q["ticker"] not in seen and q.get("open_ts") and q["open_ts"] >= FWD_FREEZE.timestamp():
            seen[q["ticker"]] = q
    cands = []
    for tk, ref in sorted(seen.items()):
        res = results.get(tk)
        if res not in ("yes", "no"):
            continue
        st = ref.get("strike_type")
        K = ref.get("floor_strike") if st == "greater" else ref.get("cap_strike") if st == "less" else None
        q = rd.nearest_to_look(rows, tk, minutes_after_open=2880)
        if K is None or not q or (q["yes_ask"] is None and q["yes_bid"] is None):
            drop["no_strike_or_quote"] = drop.get("no_strike_or_quote", 0) + 1
            continue
        cands.append((tk, ref, res, st, K, q))
    kl = {}
    for inst in {b1.SERIES[c[1]["series"]] for c in cands}:       # one OKX pull per instrument, covering every look hour plus the 14 day vol window
        hrs = [c[5]["poll_ts"] // 3600 * 3600 - 3600 for c in cands if b1.SERIES[c[1]["series"]] == inst]
        kl[inst] = okx(inst, min(hrs) - 3600 * (b1.VOL_HOURS + 6), max(hrs) + 3600)
    for tk, ref, res, st, K, q in cands:
        inst = b1.SERIES[ref["series"]]
        t_look = q["poll_ts"]
        hour = t_look // 3600 * 3600 - 3600
        k = kl[inst]
        S = k.get(hour)
        sig = b1.realised_vol([k[h] for h in range(hour - 3600 * (b1.VOL_HOURS + 5), hour + 1, 3600) if h in k])
        if S is None or sig is None:
            drop["no_okx"] = drop.get("no_okx", 0) + 1
            continue
        if (st == "greater" and S >= K) or (st == "less" and S <= K):
            drop["already_crossed"] = drop.get("already_crossed", 0) + 1
            continue
        end = b1.event_end(ref["event_ticker"])
        p = b1.touch_prob(S, K, sig, (end - t_look) / (3600 * 8760))
        out.append({"t": tk, "s": ref["series"], "ev": ref["event_ticker"], "close": end, "ask": q["yes_ask"], "bid": q["yes_bid"], "p": p, "res": res, "K": K, "S": S, "sig": sig})
    return out, drop


def trades(rows, rule):
    tr = []
    for r in sorted(rows, key=lambda r: (r["close"], r["t"])):
        d = b1.decide(rule, r["ask"], r["bid"], r["p"])
        if d:
            tr.append({"close": r["close"], "ev": r["ev"], "net": b1.net_per_contract(d[0], d[1], r["res"]), "price": d[1]})
    return tr


def judge(tr):
    if len(tr) < NEEDED_TRADES:
        return "NOT_ENOUGH_DATA"
    h = len(tr) // 2
    xs = [t["net"] for t in tr]
    return "FALSIFIED" if (sum(xs[:h]) <= 0 or sum(xs[h:]) <= 0 or (b1.pf(xs) or 0) < 1.5) else "NOT_YET_FALSIFIED"


def forward(argv, now=None, okx=None):
    f = fr.flags(argv)
    rest = f["rest"]
    daily = rest[rest.index("--daily-dir") + 1] if "--daily-dir" in rest else None
    st = {}

    def get():
        if "d" not in st:
            try:
                rd = recdaily()
            except ImportError:
                raise SystemExit("scalper.recdaily is not on this branch (claude/v2-recorder-daily, unmerged). Nothing was read.")
            d = daily
            if not d:
                tmp = tempfile.mkdtemp(prefix="barrier1f_")
                fr.checkout_quote_data(["daily"], tmp)
                d = str(Path(tmp) / "daily")
            st["d"] = build(rd, rd.load_quotes(d), rd.load_results(d), okx or b1.okx_hourly)
        return st["d"]

    def info():
        return ["forward events open on or after 2026-11-04; the December events open about Dec 1 and their look is about Dec 3; counts need --daily-dir and OKX (public) for volatility, so no count is printed here"]

    def ready(n):
        rows, _ = get()
        k = len(trades(rows, "cheap")) + len(trades(rows, "rich"))
        return None if k >= NEEDED_FILLS else f"only {k} forward fills; the registered read is the October 2027 event or {NEEDED_FILLS} fills, whichever is later"

    def real():
        rows, drop = get()
        L, parts = [f"markets with a model {len(rows)}, dropped {drop}"], []
        for rule in ("cheap", "rich"):
            tr = trades(rows, rule)
            xs = [t["net"] for t in tr]
            m, z = fr.clustered([(str(t["ev"]), t["net"]) for t in tr])
            w = judge(tr)
            L.append(f"BAR-{rule.upper()}: {w}; n {len(tr)} on {len({t['ev'] for t in tr})} events; PF {fr.fpf(b1.pf(xs) or 0.0) if xs else 'n/a'}; mean {100 * m:+.2f}c; event-clustered z {z:+.2f} vs bar {Z_BAR}")
            parts.append(f"{rule} n{len(tr)} {w} z{z:+.2f}")
        return L, "forward events opened from 2026-11-04; " + "; ".join(parts) + f"; cost fee 7% x C x p x (1-p) at C 10; bar {Z_BAR}"

    return fr.run(SPEC, argv, real, info, now=now, ready=ready)


main = fr.cli(forward)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
