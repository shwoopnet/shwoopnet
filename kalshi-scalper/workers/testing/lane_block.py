#!/usr/bin/env python3
"""Lane block reader (tool 2; Testing Desk, Nov 13, 2026). Research only: works on signal records it is given; INVENTED rows only in tests (SPXOI1_TOOLS_HAND_CASES.md, committed first).
Rules: ROTATION_LANE.md on rnd-queue (read as v1.3 with section 4 (a) to (u)); the NC15 fill check (the next poll within 6 s) is applied by spxoi1.fill_check when the signals are made; this module applies sections 3 and 4.
read_place(signals, params, start_ts, now) -> the record of one place: blocks, confirmation, state. `now` is ALWAYS passed (lane (k)); start_ts is the UTC start time (l).
A signal record: dict(ticker, side 'yes'|'no', t decision time in exchange seconds, limit_cents int, status 'filled'|'miss'|'not_fill_checked', fill price (dollars), result 'yes'|'no'|'void'|None (None = open)).
Cents (g): spxoi1.cash_cents (fee rounded up, floor(100 cash + 1e-6)); W and L are sums of integer cents (the sign of a signal's cents), no float in the bar: 10 W >= 13 L, W >= L per half; L = 0 and W > 0 passes, W = 0 fails.
"""
import os, sys, datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spxoi1 as s1

CENTRAL = ZoneInfo("America/Chicago")
DAY_S = 24 * 3600
EXPIRY_S = 21 * DAY_S
FAV_CENTS = 88


class Params:
    def __init__(self, band_lo_cents, band_hi_cents, favourites=False, block_n=60, days_min=7, rarer_min=10, confirm_n=30):
        """band_lo_cents / band_hi_cents: the registered band as the range of LIMITS in whole cents (lane (i)): required, no defaults."""
        self.lo, self.hi, self.fav = int(band_lo_cents), int(band_hi_cents), bool(favourites)
        self.block_n = 150 if favourites and block_n == 60 else block_n
        self.days_min, self.rarer_min, self.confirm_n = days_min, rarer_min, confirm_n
        self.need_wins = self.lo <= 50          # a band wholly at or under 50 needs wins; crossing 50 needs both; wholly above needs losses
        self.need_losses = self.hi > 50


def central_day(t):
    return datetime.datetime.fromtimestamp(t, CENTRAL).date().isoformat()


def ok_ratio(W, L):
    return W > 0 and 10 * W >= 13 * L


def ok_even(W, L):
    return W > 0 and W >= L


def counted(signals, prm, start_ts):
    """-> (sorted counted signals with cents/win/loss fields, exclusion counts by reason)."""
    ex, out = {}, []
    for sg in signals:
        why = None
        if sg["t"] < start_ts:
            why = "decided before the start time (l)"
        elif sg["status"] == "miss":
            why = "miss (m)"
        elif sg["status"] == "not_fill_checked":
            why = "not fill-checked (m)"
        elif sg["status"] != "filled":
            why = "unknown status"
        elif sg["limit_cents"] >= FAV_CENTS and not prm.fav:
            why = "limit 88c or above, rule not in the favourites class (i, m)"
        if why:
            ex[why] = ex.get(why, 0) + 1
            continue
        d = dict(sg)
        d["day"] = central_day(sg["t"])
        d["final"] = sg.get("result") is not None
        if d["final"]:
            d["cents"] = s1.cash_cents(sg["fill"], sg["side"], sg["result"])
            d["win"] = sg["result"] == sg["side"]
            d["loss"] = sg["result"] in ("yes", "no") and sg["result"] != sg["side"]          # a void is neither (n)
        out.append(d)
    out.sort(key=lambda d: (d["t"], d["ticker"], 0 if d["side"] == "yes" else 1))          # (p)
    return out, ex


def wl(rows):
    W = sum(d["cents"] for d in rows if d["cents"] > 0)
    L = -sum(d["cents"] for d in rows if d["cents"] < 0)
    return W, L


def read_block(rows, prm):
    """The block read once complete: PF 1.3 on the block and 1.0 in each half (halves by signal count in order, (e))."""
    n = len(rows)
    W, L = wl(rows)
    h = n // 2
    W1, L1 = wl(rows[:h])
    W2, L2 = wl(rows[h:])
    ok = ok_ratio(W, L) and ok_even(W1, L1) and ok_even(W2, L2)
    return {"passed": ok, "n": n, "W_cents": W, "L_cents": L, "half1": {"W": W1, "L": L1}, "half2": {"W": W2, "L": L2}}


def read_place(signals, prm, start_ts, now):
    cs, ex = counted(signals, prm, start_ts)
    rec = {"counted_signals": len(cs), "excluded": ex, "blocks": [], "state": None}
    pos = 0
    while True:
        if pos >= len(cs):
            rec["state"] = "NO_OPEN_BLOCK (no counted signal after the last record)"
            return rec
        first = cs[pos]
        t0 = first["t"]
        days, wins, losses = set(), 0, 0
        done = None          # index of the completing signal
        stop = None          # 'open' | 'window' | 'end'
        j = pos
        while j < len(cs):
            d = cs[j]
            if d["t"] > t0 + EXPIRY_S:
                stop = "window"; break
            if not d["final"]:
                stop = "open"; break
            days.add(d["day"]); wins += d["win"]; losses += d["loss"]
            n = j - pos + 1
            rarer_ok = (wins >= prm.rarer_min if prm.need_wins else True) and (losses >= prm.rarer_min if prm.need_losses else True)
            if n >= prm.block_n and len(days) >= prm.days_min and rarer_ok:
                done = j; break
            j += 1
        else:
            stop = "end"
        blk = {"first_t": t0, "start_index": pos}
        if done is None:
            nn = j - pos if stop in ("window", "open") else len(cs) - pos
            blk.update({"n_so_far": nn, "days_so_far": len(days), "wins_so_far": wins, "losses_so_far": losses})
            all_final_in_window = all(d["final"] for d in cs if d["t"] <= t0 + EXPIRY_S)
            if stop == "open":
                blk["state"] = "WAITING_FOR_RESULTS (an open result stops the search, (r)); expiry not yet decided"
                rec["blocks"].append(blk); rec["state"] = blk["state"]; return rec
            if stop == "window" or (stop == "end" and now > t0 + EXPIRY_S and all_final_in_window):
                blk["state"] = "EXPIRED (too slow for the wheel; unread, no PF)"
                rec["blocks"].append(blk)
                nxt = next((i for i, d in enumerate(cs) if d["t"] > t0 + EXPIRY_S), len(cs))
                pos = nxt; continue
            blk["state"] = "GROWING"
            rec["blocks"].append(blk); rec["state"] = "GROWING"; return rec
        rows = cs[pos:done + 1]
        r = read_block(rows, prm)
        blk.update(r); blk["last_t"] = cs[done]["t"]; blk["days"] = len(days); blk["wins"], blk["losses"] = wins, losses
        if not r["passed"]:
            blk["state"] = "FAILED (read once)"
            rec["blocks"].append(blk); pos = done + 1; continue
        blk["state"] = "CLEARED, confirmation next"
        rec["blocks"].append(blk)
        # confirmation (j): the next confirm_n counted signals after the block's last signal
        tl = cs[done]["t"]
        conf = cs[done + 1:done + 1 + prm.confirm_n]
        c = {"after_t": tl, "have": len(conf)}
        blk["confirmation"] = c
        in_window = [d for d in conf if d["t"] <= tl + EXPIRY_S]
        open_in = any(not d["final"] for d in cs[done + 1:] if d["t"] <= tl + EXPIRY_S)
        if len(conf) == prm.confirm_n and conf[-1]["t"] <= tl + EXPIRY_S and all(d["final"] for d in conf):
            W, L = wl(conf)
            c.update({"W_cents": W, "L_cents": L})
            if ok_even(W, L):
                c["state"] = "PASSED"; rec["state"] = "QUALIFIED"; return rec          # (t): no further block is read
            c["state"] = "FAILED"
            pos = done + 1 + prm.confirm_n; continue          # its signals never count toward a block
        if len(conf) == prm.confirm_n and conf[-1]["t"] <= tl + EXPIRY_S:
            c["state"] = "WAITING_FOR_RESULTS (a confirmation signal is open)"; rec["state"] = "CONFIRMING: " + c["state"]; return rec
        # not complete inside its 21 days
        if (any(d["t"] > tl + EXPIRY_S for d in cs[done + 1:]) or now > tl + EXPIRY_S) and not open_in:
            c["state"] = "EXPIRED (unread)"
            pos = next((i for i, d in enumerate(cs) if d["t"] > tl + EXPIRY_S), len(cs)); continue
        if open_in:
            c["state"] = "WAITING_FOR_RESULTS, expiry not yet decided"; rec["state"] = "CONFIRMING: " + c["state"]; return rec
        c["state"] = "GROWING (%d of %d)" % (len(in_window), prm.confirm_n); rec["state"] = "CONFIRMING: " + c["state"]; return rec


if __name__ == "__main__":
    print(__doc__)
