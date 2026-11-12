"""QUOTE2B DEVELOPMENT read (Idea Desk A, Nov 12, 2026). V2's committed scorer, unchanged, run on closes BEFORE the
pinned cutoff only. Held-out closes are dropped at load. Zero Kalshi calls: a strike-hour whose tape needs the API
re-fetch is excluded and counted. Usage: python3 -I q2b_dev.py <path to V2 checkout kalshi-scalper/src> <out.txt>"""
import sys
from pathlib import Path
PINNED_CUTOFF_TS = 1794063600   # 2026-11-07T15:00:00Z, same constant as MMSIM1 Amendment 3
src, out = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, src)
from scalper import quote2b as q
q.RESULT = out
q.NEEDED = 1                    # development is below the registered 300; the verdict word below is NOT a call
_closes = q.closes
q.closes = lambda: {c: v for c, v in _closes().items() if c < PINNED_CUTOFF_TS}
def _no_api(ticker, close):
    raise RuntimeError("no Kalshi calls: strike-hour excluded")
q.refetch = _no_api
cs = q.closes()
assert cs and max(cs) < PINNED_CUTOFF_TS
print("dev closes loaded:", len(cs), "latest", max(cs))
q.run()
