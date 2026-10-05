"""Is the paper bot alive, and what has it done? Reads its database; the bot can be running.

Usage: python -m scalper.botstatus
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from .bot import BOT_DB
from .limits import tier_state


def health(age: float | None) -> str:
    """The same three words an outside watchdog would use."""
    if age is None:
        return "NEVER RAN"
    return "OK" if age < 30 else ("STALE" if age < 120 else "DOWN")


def report(db_path: Path | str = BOT_DB, now: float | None = None) -> str:
    now = time.time() if now is None else now
    if not Path(db_path).exists():
        return f"No bot database at {db_path}. Start it: python -m scalper.bot"
    db = sqlite3.connect(str(db_path))
    meta = dict(db.execute("SELECT key, value FROM meta"))
    bank = float(meta.get("bankroll", 0) or 0)
    hb = meta.get("heartbeat")
    age = None if hb is None else now - float(hb)
    closed = list(db.execute("SELECT settled_ts, pnl FROM position WHERE status='closed'"))
    t = tier_state(closed, bank, now)
    open_pos = db.execute("SELECT ticker, side, contracts, entry FROM position WHERE status='open' ORDER BY entry_ts").fetchall()
    tot = db.execute("SELECT COUNT(*), COALESCE(SUM(pnl), 0) FROM position WHERE status='closed'").fetchone()
    lines = [f"Bot: {health(age)}" + ("" if age is None else f" (last tick {age:.0f}s ago)") + ", PAPER mode, no real orders possible",
             f"Bankroll ${bank:.2f}. Limits: ${t['per_trade_cap']:.2f} a trade, break at -${t['soft_limit']:.2f}, done at -${t['hard_limit']:.2f}",
             f"Now: {t['mode']}, today {t['pnl_today']:+.2f}",
             f"All time: {tot[0]} closed trades, net {tot[1]:+.2f}. Open positions: {len(open_pos)}"]
    lines += [f"  open: {n} {side} {tk} at {e:.2f}" for tk, side, n, e in open_pos]
    lines.append("Recent events:")
    lines += [f"  {time.strftime('%m-%d %H:%M:%S', time.localtime(ts))} {k:>6} {d}"
              for ts, k, d in db.execute("SELECT ts, kind, detail FROM event ORDER BY ts DESC, rowid DESC LIMIT 8")]
    return "\n".join(lines)


def main() -> None:
    print(report())


if __name__ == "__main__":
    main()
