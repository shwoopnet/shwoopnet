#!/usr/bin/env python3
"""NBAREBLADDER wrapper (Idea Desk C, Nov 16, 2026): the audited NBALADDER plugin (nbaladder.py) pointed at KXNBAREB. It changes four module
constants and nothing else, so the 624 cells, features, gates and print are the audited ones. Card: ../allkalshi/nbareb/NBAREB_CARD.md."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbaladder as N

N.SERIES = ("KXNBAREB",)
N.LIST_JOB, N.LIST_ID = "KXNBAREB_LISTS_A", "dev_KXNBAREB"
N.CANDLE_JOBS = ("NBAREB_CANDLES_P1", "NBAREB_CANDLES_P2")
run, decisions, games, N_RULES = N.run, N.decisions, N.games, N.N_RULES
