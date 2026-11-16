#!/usr/bin/env python3
"""LADHOUR1 second build (Testing Desk, Nov 16, 2026): ETHLATE1's mechanism per series (hand case LADHOUR1_SECOND_HAND_CASE.md, readings L1 to L6). One engine run per series with its own split, spread cuts and gates; BH over m_carried + 384.
Pure functions; the loader waits for the forward data and the allow line."""
import ethlate1_second as e

SERIES = ("KXINXU", "KXNASDAQ100U", "KXWTIH", "KXGOLDH")
RULES_PER_SERIES = e.N_RULES
M_NEW = RULES_PER_SERIES * len(SERIES)          # 384
assert M_NEW == 384


def in_series(ticker, series): return ticker.startswith(series + "-")


def m_total(m_carried): return m_carried + M_NEW


def split_by_series(markets, candles):
    """-> {series: (markets, candles)}; a ticker outside the four series is dropped before anything else is used"""
    out = {s: ({}, {}) for s in SERIES}
    for tk, mk in markets.items():
        for s in SERIES:
            if in_series(tk, s): out[s][0][tk] = mk; out[s][1][tk] = candles.get(tk, {}); break
    return out


def run(markets, candles, m_carried):
    """-> {series: ethlate1_second.run result} with m = m_carried + 384 for every series"""
    mt = m_total(m_carried)
    return {s: e.run(mk, cd, mt) for s, (mk, cd) in split_by_series(markets, candles).items()}
