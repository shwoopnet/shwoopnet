import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scalper import straddle1_theta as T
from scalper import straddle1_events as E

D = dt.date


class FakeClient:
    def __init__(self, eod=None):
        self.calls = []
        self.eod = eod

    def option_list_expirations(self, symbol):
        self.calls.append(("exp", symbol))
        return [{"expiration": x} for x in ["2026-11-06", "2026-11-13", "2026-11-20", "2026-12-18"]]

    def option_list_strikes(self, symbol, expiration):
        self.calls.append(("strikes", symbol, expiration))
        return [{"strike": k} for k in (95.0, 100.0, 102.5, 105.0)]

    def option_history_eod(self, start, end, symbol, expiration, strike="*", right="both"):
        self.calls.append(("eod", start, end, symbol, expiration, strike, right))
        if self.eod is not None:
            return self.eod
        r = []
        for d, cb, ca, pb, pa in ((D(2026, 11, 2), 2.0, 2.1, 1.9, 2.0), (D(2026, 11, 5), 2.3, 2.4, 2.0, 2.1)):
            r.append({"created": f"{d}T16:00:00", "right": "CALL", "bid": cb, "ask": ca, "Strike": 102.5})
            r.append({"created": f"{d}T16:00:00", "right": "PUT", "bid": pb, "ask": pa, "Strike": 102.5})
        return r


def test_missing_credential_is_clear_and_silent():
    try:
        T.make_client(env={})
    except T.ThetaCredentialError as e:
        assert "THETADATA_API_KEY" in str(e)
        return
    raise AssertionError("no error")


def test_credential_paths_never_echo_secret():
    seen = []
    T.make_client(env={"THETADATA_API_KEY": "SECRETKEY"}, client_factory=lambda **kw: seen.append(kw) or "c")
    T.make_client(env={"THETADATA_EMAIL": "a@b.c", "THETADATA_PASSWORD": "pw"}, client_factory=lambda **kw: seen.append(kw) or "c")
    assert seen[0] == {"api_key": "SECRETKEY"} and seen[1] == {"email": "a@b.c", "password": "pw"}
    try:
        T.make_client(env={"THETADATA_EMAIL": "a@b.c"})
    except T.ThetaCredentialError as e:
        assert "a@b.c" not in str(e)


def test_expiration_and_strike_choice():
    ex = ["2026-11-06", "2026-11-13", "2026-11-20", "2026-12-18"]
    assert T.choose_expiration(ex, D(2026, 11, 5)) == D(2026, 11, 13)       # first at least 7 days after exit
    assert T.choose_expiration(ex, D(2026, 11, 5), monthly_only=True) == D(2026, 11, 20)  # third Friday
    assert T.choose_expiration(ex, D(2026, 12, 15)) is None
    assert T.choose_strike([95, 100, 102.5, 105], 101.4) == 102.5


def test_fetch_with_mock():
    c = FakeClient()
    out = T.fetch_straddle("XYZ", D(2026, 11, 2), D(2026, 11, 5), 102.0, client=c, sleep=lambda s: None)
    assert out["expiration"] == "2026-11-13" and out["strike"] == 102.5
    assert out["entry"] == dict(call_bid=2.0, call_ask=2.1, put_bid=1.9, put_ask=2.0)
    assert out["exit"]["call_bid"] == 2.3 and out["exit"]["put_ask"] == 2.1
    assert c.calls[-1][-2:] == ("102.5", "both") and len(c.calls) == 3


def test_missing_exit_quote_skips_and_bad_shape_fails_loudly():
    c = FakeClient(eod=[{"created": "2026-11-02", "right": "CALL", "bid": 1, "ask": 2},
                        {"created": "2026-11-02", "right": "PUT", "bid": 1, "ask": 2}])
    assert "missing exit" in T.fetch_straddle("X", D(2026, 11, 2), D(2026, 11, 5), 100, client=c, sleep=lambda s: None)["skip"]
    c = FakeClient(eod=[{"created": "2026-11-02", "right": "CALL", "nobid": 1}])
    try:
        T.fetch_straddle("X", D(2026, 11, 2), D(2026, 11, 5), 100, client=c, sleep=lambda s: None)
    except T.ThetaShapeError as e:
        assert "nobid" in str(e)
        return
    raise AssertionError


def test_event_classification_and_dates():
    td = E.trading_days()
    ET = E.NY
    assert E.classify(dt.datetime(2026, 7, 30, 16, 30)) == "AMC"
    assert E.classify(dt.datetime(2026, 7, 30, 8, 0)) == "BMO"
    assert E.classify(dt.datetime(2026, 7, 30, 12, 0)) == "INTRADAY"
    assert E.classify(dt.datetime(2026, 8, 1, 12, 0)) == "BMO"  # Saturday rolls to BMO
    fl = {1: [dict(form="8-K", items="2.02,9.01", filing_date="2026-07-30", acc="a", accept_utc="x",
                   utc=dt.datetime(2026, 7, 30, 20, 30, tzinfo=E.UTC), et=dt.datetime(2026, 7, 30, 16, 30, tzinfo=ET)),
              dict(form="8-K", items="2.02", filing_date="2026-08-05", acc="b", accept_utc="x",
                   utc=dt.datetime(2026, 8, 5, 12, 0, tzinfo=E.UTC), et=dt.datetime(2026, 8, 5, 8, 0, tzinfo=ET)),
              dict(form="8-K/A", items="2.02", filing_date="2026-08-06", acc="c", accept_utc="x",
                   utc=dt.datetime(2026, 8, 6, 12, 0, tzinfo=E.UTC), et=dt.datetime(2026, 8, 6, 8, 0, tzinfo=ET))]}
    ev, drops = E.build_events(fl, {1: {"ticker": "T"}}, td)
    assert len(ev) == 1 and ev[0]["timing"] == "AMC" and ev[0]["flag_multi202"] == 1
    assert ev[0]["exit_close"] == "2026-07-30" and ev[0]["entry_close"] == "2026-07-27"
    assert drops["8-K/A or other form with 2.02"] == 1


def test_split_by_date_only():
    ev = E.assign_split([{"announce_day": f"2025-01-{i+1:02d}"} for i in range(30)])
    s = [e["split"] for e in ev]
    assert s.count("A") == 10 and s.count("B") == 10 and s.count("FROZEN") == 10 and s[-1] == "FROZEN"


if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1
    print(f"test_straddle1_theta: {n} passed")
