"""STRADDLE1 skeleton (registered in workers/STRADDLE1_REGISTRATION.md). Synthetic-tested only; scores nothing."""
import datetime as dt

FEE_PER_SHARE = 0.0012   # $0.03 a contract, 4 transactions, per share
MAX_REL_SPREAD = 0.03


def exit_day(accept_et, trading_days):
    """Close at which the straddle is sold. accept_et: naive datetime in New York time.
    trading_days: sorted list of dates. after-close on D -> close of D; otherwise close of the day before the announcement day."""
    d = accept_et.date()
    t = accept_et.time()
    on_trading = d in trading_days
    if on_trading and t >= dt.time(16, 0):
        return d                                        # after close: sold at D's own close
    # before-open / during-day / non-trading day: announcement day is the next trading day on or after d
    ann = min(x for x in trading_days if x >= d)
    i = trading_days.index(ann)
    return trading_days[i - 1]


def entry_day(exit_d, trading_days):
    return trading_days[trading_days.index(exit_d) - 3]


def eligible(call_bid, call_ask, put_bid, put_ask):
    if min(call_bid, put_bid) <= 0:
        return False
    bid, ask = call_bid + put_bid, call_ask + put_ask
    mid = (bid + ask) / 2
    return mid >= 0.5 and (ask - bid) / mid <= MAX_REL_SPREAD


def event_return(entry_call_ask, entry_put_ask, exit_call_bid, exit_put_bid, fee_mult=1.0):
    cost = entry_call_ask + entry_put_ask
    return (exit_call_bid + exit_put_bid - cost - FEE_PER_SHARE * fee_mult) / cost
