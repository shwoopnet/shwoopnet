"""Daily loss limits: the same three tiers as the Kalshi page in shwoopnet.

A Python port of kalshiTierState in index.html. The page and the bot must never
disagree about whether trading is allowed, so the numbers are identical and the
tests below use the same cases as the page's tests.

  per trade:  risk at most 1% of bankroll
  down 3% on the day: a 2 hour break, then half size
  down 5% on the day: done for the day

Counted from REALISED profit and loss in the local day, in the order trades
settled. The break starts when the trade that crossed the soft line settled and
later wins do not shorten it. The hard stop is sticky for the rest of the day.
No bankroll means no trading: fail closed.
"""
from __future__ import annotations

from datetime import datetime

PER_TRADE_PCT = 0.01
SOFT_STOP_PCT = 0.03
HARD_STOP_PCT = 0.05
BREAK_S = 2 * 60 * 60


def day_start(now: float) -> float:
    return datetime.fromtimestamp(now).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


def tier_state(closed: list[tuple[float, float]], bankroll: float, now: float) -> dict:
    """closed: (settled_ts, pnl) of every closed trade. Returns
    {mode: ok|break|half|done, cap, per_trade_cap, soft_limit, hard_limit,
     pnl_today, soft_at, break_until}. cap is the dollars one trade may risk now."""
    out = {"mode": "ok", "cap": 0.0, "per_trade_cap": 0.0, "soft_limit": 0.0, "hard_limit": 0.0,
           "pnl_today": 0.0, "soft_at": None, "break_until": None}
    try:
        bank = float(bankroll)
    except (TypeError, ValueError):
        bank = 0.0
    if not bank > 0:
        out["mode"] = "done"
        return out
    out["per_trade_cap"] = bank * PER_TRADE_PCT
    out["soft_limit"] = bank * SOFT_STOP_PCT
    out["hard_limit"] = bank * HARD_STOP_PCT
    start = day_start(now)
    today = sorted((t, p) for t, p in closed if start <= t <= now)
    cum, hard = 0.0, False
    for t, pnl in today:
        cum += pnl
        if out["soft_at"] is None and cum <= -out["soft_limit"]:
            out["soft_at"] = t
        if cum <= -out["hard_limit"]:
            hard = True
    out["pnl_today"] = round(cum, 2)
    if hard:
        out["mode"] = "done"
    elif out["soft_at"] is not None:
        out["break_until"] = out["soft_at"] + BREAK_S
        if now < out["break_until"]:
            out["mode"] = "break"
        else:
            out["mode"] = "half"
            out["cap"] = out["per_trade_cap"] / 2
    else:
        out["cap"] = out["per_trade_cap"]
    return out
