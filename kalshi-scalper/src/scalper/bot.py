"""The paper bot: watches live Kalshi prices, makes SIMULATED trades, keeps records.

PAPER ONLY. It cannot place a real order: there is no order code in this file,
and the constructor refuses any mode but "paper". Real orders will be written
only after a strategy passes its pre-registered test in paper trading (see the
README), and then behind a separate switch.

The strategy here is H2 (buy about 40c or 50c, sell at 80c, otherwise hold to
settlement). H2 was FALSIFIED on 30 days of history and expects to lose roughly
its costs. It is here as a PLUMBING strategy: something simple and fully
specified to exercise the whole loop (quotes, limits, fills, settlement, records)
and to give a forward, out-of-sample check of the verdict. A paper result far
worse than the history says the plumbing is wrong, not that the market moved.

Rules built into the structure:
- Every entry is idempotent. A position's id is derived from the strategy and the
  market ("h2-<ticker>"), so a restart, a second copy, or a repeated tick cannot
  enter the same market twice. This is the lesson of the 15 duplicate orders in
  shwoop-server: the guard must sit on the order, with a key every process
  computes identically.
- Fail closed. Anything unreadable (an API error, a bad quote, an inactive
  exchange, a missing bankroll) means NO new entry. Exits and settlement carry on.
- The kill switch (a file named KILL) stops new entries only. Positions already
  open are still managed, because freezing them would be the more dangerous act.
- Size comes from the loss limits (limits.py, identical to the web page): at most
  1% of bankroll a trade, half that after a break, none after the hard stop.

Usage: python -m scalper.bot [--bankroll 100] [--interval 5] [--once]
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

from . import api as kalshi_api
from .analyze import valid_quote
from .backfill import iso_ts
from .fees import taker_fee
from .limits import tier_state
from .recorder import DB
from .risk import KILL_FILE
from .scalps import BANDS, MIN_LEFT_S, TARGET

BOT_DB = DB.parent / "bot.sqlite"
SERIES = ("KXBTC15M", "KXGOLD15M")
STRATEGY = "h2"
SETTLE_GRACE_S = 15
DEFAULT_BANKROLL = 100.0   # the owner starts the bot at $100
PING_EVERY_S = 60.0        # how often to tell an outside watchdog the bot is alive

SCHEMA = """
CREATE TABLE IF NOT EXISTS position(
  id TEXT PRIMARY KEY, ticker TEXT, series TEXT, side TEXT, band TEXT, contracts INTEGER,
  entry REAL, entry_fee REAL, entry_ts REAL, close_ts REAL, status TEXT,
  exit REAL, exit_fee REAL, exit_ts REAL, pnl REAL, settled_ts REAL, mode TEXT);
CREATE TABLE IF NOT EXISTS event(ts REAL, kind TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def position_id(ticker: str) -> str:
    """The same string in every process: this is what makes entry idempotent."""
    return f"{STRATEGY}-{ticker}"


def size_for(price: float, cap: float, displayed: float | None) -> int:
    """Most contracts whose cost INCLUDING the fee fits the cap, and that the
    displayed size at the touch can fill. 0 means do not trade."""
    if not (0 < price < 1) or not cap > 0:
        return 0
    n = int(cap // price)
    while n >= 1 and price * n + taker_fee(price, n) > cap + 1e-9:
        n -= 1
    if displayed is not None:
        n = min(n, int(displayed))
    return max(n, 0)


class PaperBot:
    def __init__(self, api, db_path: Path | str = BOT_DB, bankroll: float = DEFAULT_BANKROLL, clock=time.time,
                 kill_file: Path = KILL_FILE, mode: str = "paper", pinger=None):
        if mode != "paper":
            raise ValueError("live trading is not implemented: this bot is paper only")
        self.api, self.bankroll, self.clock, self.kill_file = api, bankroll, clock, Path(kill_file)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path))
        self.db.executescript(SCHEMA)
        self.exchange_active = False
        self.pinger, self._last_ping = pinger, None
        self._meta("bankroll", repr(float(bankroll)))
        self._meta("started", repr(clock()))

    # ---- records ----
    def _event(self, now: float, kind: str, detail: str) -> None:
        self.db.execute("INSERT INTO event VALUES(?,?,?)", (now, kind, detail))
        self.db.commit()

    def _meta(self, key: str, value: str | None = None) -> str | None:
        if value is not None:
            self.db.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, value))
            self.db.commit()
            return value
        r = self.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return r[0] if r else None

    def _note_block(self, now: float, reason: str | None) -> None:
        """Log why entries are blocked once per change, not once per tick."""
        if reason != self._meta("last_block"):
            self._meta("last_block", reason or "")
            if reason:
                self._event(now, "block", reason)

    def closed(self) -> list[tuple[float, float]]:
        return list(self.db.execute("SELECT settled_ts, pnl FROM position WHERE status='closed'"))

    def tier(self, now: float) -> dict:
        return tier_state(self.closed(), self.bankroll, now)

    # ---- the loop body ----
    def tick(self) -> None:
        now = self.clock()
        self._meta("heartbeat", repr(now))
        quotes: dict = {}
        quotes_ok = True
        try:
            st = self.api.exchange_status()
            self.exchange_active = bool(st.get("trading_active", st.get("exchange_active", False)))
            for series in SERIES:
                for m in self.api.markets(series, "open", 5):
                    quotes[m["ticker"]] = (series, m)
        except Exception as e:  # unreadable prices: no new entries, keep managing what is open
            quotes_ok = False
            self._event(now, "error", f"quotes: {e}")
        self._exits(now, quotes)
        self._settle(now)
        if quotes_ok:
            self._enter(now, quotes)
        else:
            self._note_block(now, "prices unreadable")
        self._ping(now, quotes_ok)

    def _ping(self, now: float, healthy: bool) -> None:
        """Tell an outside watchdog (for example healthchecks.io) the bot is alive.
        Only on a healthy tick, so unreadable prices go quiet and the watchdog
        raises the alarm. A failing ping must never affect trading."""
        if not (self.pinger and healthy):
            return
        if self._last_ping is not None and now - self._last_ping < PING_EVERY_S:
            return
        self._last_ping = now
        try:
            self.pinger()
        except Exception:
            pass

    def _exits(self, now: float, quotes: dict) -> None:
        for pid, ticker, side, n, entry, entry_fee, entry_ts in self.db.execute(
                "SELECT id,ticker,side,contracts,entry,entry_fee,entry_ts FROM position WHERE status='open'").fetchall():
            if ticker not in quotes or now <= entry_ts:   # never on the entry tick itself
                continue
            m = quotes[ticker][1]
            bid, ask = kalshi_api.f(m.get("yes_bid_dollars")), kalshi_api.f(m.get("yes_ask_dollars"))
            side_bid = bid if side == "yes" else (None if ask is None else 1 - ask)
            if side_bid is None or side_bid < TARGET:
                continue
            fee = taker_fee(TARGET, n)
            pnl = round(TARGET * n - fee - entry * n - entry_fee, 2)
            self.db.execute("UPDATE position SET status='closed', exit=?, exit_fee=?, exit_ts=?, pnl=?, settled_ts=? WHERE id=?",
                            (TARGET, fee, now, pnl, now, pid))
            self.db.commit()
            self._event(now, "exit", f"{pid} sold {n} at {TARGET:.2f}, net {pnl:+.2f}")

    def _settle(self, now: float) -> None:
        for pid, ticker, side, n, entry, entry_fee, close_ts in self.db.execute(
                "SELECT id,ticker,side,contracts,entry,entry_fee,close_ts FROM position WHERE status='open'").fetchall():
            if now < close_ts + SETTLE_GRACE_S:
                continue
            try:
                result = self.api.market(ticker).get("result")
            except Exception as e:
                self._event(now, "error", f"settle {ticker}: {e}")
                continue
            if result not in ("yes", "no"):
                continue                                   # not final yet: ask again next tick
            pnl = round((n if result == side else 0) - entry * n - entry_fee, 2)
            self.db.execute("UPDATE position SET status='closed', exit=?, exit_ts=?, pnl=?, settled_ts=? WHERE id=?",
                            (1.0 if result == side else 0.0, now, pnl, now, pid))
            self.db.commit()
            self._event(now, "settle", f"{pid} {result}, net {pnl:+.2f}")

    def blocked_reason(self, now: float) -> str | None:
        if self.kill_file.exists():
            return "kill switch"
        if not self.exchange_active:
            return "exchange not trading"
        t = self.tier(now)
        if t["mode"] == "done":
            return "done for the day" if self.bankroll else "no bankroll set"
        if t["mode"] == "break":
            return "on a break"
        return None

    def _enter(self, now: float, quotes: dict) -> None:
        reason = self.blocked_reason(now)
        self._note_block(now, reason)
        if reason:
            return
        cap = self.tier(now)["cap"]
        for ticker, (series, m) in quotes.items():
            if m.get("status") not in ("active", "open"):
                continue
            close_ts = iso_ts(m.get("close_time"))
            if close_ts is None or close_ts - now < MIN_LEFT_S:
                continue
            bid, ask = kalshi_api.f(m.get("yes_bid_dollars")), kalshi_api.f(m.get("yes_ask_dollars"))
            if not valid_quote(bid, ask):
                continue
            for side in ("yes", "no"):
                price = ask if side == "yes" else 1 - bid
                displayed = kalshi_api.f(m.get("yes_ask_size_fp") if side == "yes" else m.get("yes_bid_size_fp"))
                band = next((b for b, (lo, hi) in BANDS.items() if lo <= price <= hi), None)
                if band is None:
                    continue
                n = size_for(price, cap, displayed)
                if n < 1:
                    break
                fee = taker_fee(price, n)
                cur = self.db.execute(
                    "INSERT OR IGNORE INTO position VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (position_id(ticker), ticker, series, side, band, n, price, fee, now, close_ts, "open",
                     None, None, None, None, None, "paper"))
                self.db.commit()
                if cur.rowcount:                           # 0 means this market already has its position
                    self._event(now, "entry", f"{position_id(ticker)} bought {n} {side} at {price:.2f} (band {band})")
                break

    # ---- reporting ----
    def summary(self, now: float | None = None) -> dict:
        now = self.clock() if now is None else now
        t = self.tier(now)
        opened = self.db.execute("SELECT COUNT(*) FROM position WHERE status='open'").fetchone()[0]
        total = self.db.execute("SELECT COUNT(*), COALESCE(SUM(pnl),0) FROM position WHERE status='closed'").fetchone()
        hb = self._meta("heartbeat")
        return {"mode": "paper", "bankroll": self.bankroll, "limits": t, "open": opened,
                "closed": total[0], "net": round(total[1], 2),
                "heartbeat_age_s": None if hb is None else round(now - float(hb), 1)}

    def run(self, interval: float = 5.0) -> None:
        while True:
            try:
                self.tick()
            except Exception as e:                       # one bad tick must not stop the bot
                try:
                    self._event(self.clock(), "error", f"tick: {e}")
                except Exception:
                    pass
            time.sleep(interval)


def _pinger_from_env():
    """HEALTHCHECK_URL, if set, is fetched once a minute while the bot is healthy.
    A free service such as healthchecks.io then alerts a phone when the pings stop."""
    import os
    import urllib.request
    url = os.environ.get("HEALTHCHECK_URL")
    if not url:
        return None
    return lambda: urllib.request.urlopen(url, timeout=5).read()


def main() -> None:
    ap = argparse.ArgumentParser(description="Paper bot for Kalshi 15 minute Bitcoin and gold markets")
    ap.add_argument("--bankroll", type=float, default=100.0)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true", help="run one tick and print a summary")
    a = ap.parse_args()
    bot = PaperBot(kalshi_api, bankroll=a.bankroll, pinger=_pinger_from_env())
    print(f"paper bot, bankroll ${a.bankroll:.2f}. No real orders are possible. Create a file named KILL to stop new entries.", flush=True)
    if a.once:
        bot.tick()
        print(bot.summary())
        return
    bot.run(a.interval)


if __name__ == "__main__":
    main()
