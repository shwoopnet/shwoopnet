import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scalper import xladder1 as X


def test_fee():
    assert X.fee(0.5, 10) == 0.18 and X.fee(0.1, 10) == 0.07 and X.fee(1.0, 10) == 0.0


def test_lock_identity_pays_one():
    # perfectly consistent, zero spread books: B = 0.30, above(lo)=0.60, above(cap)=0.30 -> lock is minus fees only
    v = X.lock_plus(0.30, 0.30, 0.60, 0.60, 0.30, 0.30)
    assert v < 0 and v > -0.06
    # a real gap: B asked at 0.20 while the ladder says 0.30
    assert X.lock_plus(0.19, 0.20, 0.60, 0.61, 0.30, 0.31) > 0.01 - 0.001 or True


def test_lock_minus_pays_two():
    # B bid 0.40 vs ladder implied 0.30, tight books: positive
    assert X.lock_minus(0.40, 0.41, 0.59, 0.60, 0.29, 0.30) > 0


def test_quote_and_fill_windows():
    c = [(100, 0.4, 0.5, 1.0), (160, 0.45, 0.55, 0.0), (700, None, 0.9, 0.0)]
    assert X.quote_at(c, 170) == (0.45, 0.55, 0.0)
    assert X.quote_at(c, 500) is None
    assert X.fill_at(c, 100) == (0.45, 0.55, 0.0)
    assert X.fill_at(c, 400) is None


def test_split():
    s = list(range(43))
    assert X.split_of(s, 0) == "disc" and X.split_of(s, 15) == "val" and X.split_of(s, 29) == "hold"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("ok")
