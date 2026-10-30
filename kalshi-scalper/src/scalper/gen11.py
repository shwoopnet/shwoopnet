"""GEN11 (workers/GEN11_REGISTRATION.md): GEN10 on BITCOIN. A generator on Bitcoin's public trade tape (KXBTC15M, 10 second bars
from data/gen9/bars.sqlite, the 1,004 fetched markets): ENTER mid-window on a tape signal and HOLD TO SETTLEMENT. The signal bar
ends 840 to 420 s before the close (minutes 1 to 8 of the window); nothing at 360 s or later. The side is chosen by the tape (every
rule has at least one SIGNED tape condition), priced 15c to 85c at the signal bar. Fill: the NEXT 10 s bar's last trade price on the
side + half the candle spread + 1c (GEN9's model: derived from trades, NOT a book). One fee, 7% x C x p x (1 - p) rounded up per
order, C = 10 (C = 1 and fees x1.2 reported); settlement is free. No open interest feature exists in the grammar (the tape has none),
so the GEN6 / FALS5 open interest jump at 180 s cannot be reproduced here. Research only; nothing here places an order, reads a key
or decides anything live.

The code path IS gen10's (features, the four GEN10 additions, fill, fees, dedupe, screens, side-shuffle control, family control):
this module only changes the series, the output folder, the draw seed and the prior N, then calls gen10's functions.
    python -m scalper.gen11 discovery      (build discovery rows, generate, dedupe, screen, freeze)
    python -m scalper.gen11 validate       (once, after the frozen files are committed and pushed)
"""
from __future__ import annotations

import sys

from . import gen10 as g
from .paths import DATA_DIR

SERIES = "KXBTC15M"
SEED = 11                      # draw rng = random.Random(SEED * 1000 + 2) = 11002; the shuffle seed stays gen10's 1010
N_PRIOR = 700_173              # the lead's running count before this round (README, NEWH13 correction)


def configure():
    g.SERIES = SERIES
    g.G = DATA_DIR / "gen11"
    g.SEED = SEED
    g.N_PRIOR = N_PRIOR


if __name__ == "__main__":
    configure()
    cmd = sys.argv[1]
    if cmd == "discovery":
        g.discovery()
    elif cmd == "validate":
        g.validate()
    elif cmd == "zbar":
        print(g.bonferroni_z(int(sys.argv[2])))
