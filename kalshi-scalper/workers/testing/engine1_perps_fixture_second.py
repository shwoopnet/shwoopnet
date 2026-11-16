#!/usr/bin/env python3
"""ENGINE1 perps build 2: the shared invented fixture (KXHAND, KXHAND2, KXFUND, KXHANDB) and its all-rules print for the rule 16b comparison at 1e-9. Invented numbers only.
Usage: engine1_perps_fixture_second.py [json|print]   (json: the fixture the other build can load; print: one line per series, filter, side, exit and haircut)"""
import datetime, json, sys
import engine1_perps_second as p


def ts(y, mo, d, h, mi): return int(datetime.datetime(y, mo, d, h, mi, tzinfo=datetime.timezone.utc).timestamp())


def fixture():
    """invented series only: KXHAND, KXHANDB (a boundary), KXHAND2 and KXFUND on EST days; KXEDT on an EDT Tuesday; KXDST over Friday 2026-10-30 to Monday 2026-11-02 (the DST step). funding {print_ts: rate} of each ticker."""
    T0 = ts(2026, 11, 10, 14, 50); hand = {}
    mids = {i: 100.00 for i in range(41)}; mids.update({6: 100.02, 7: 100.04, 8: 100.06, 9: 100.08, 11: 100.10, 12: 100.30})
    for i in range(41): hand[T0 + 60 * i] = (round(mids[i] - 0.05, 6), round(mids[i] + 0.05, 6))
    hand[T0 + 600], hand[T0 + 780] = (100.00, 100.10), (100.60, 100.70)
    U0 = ts(2026, 11, 10, 14, 40); m2 = {i: 100.00 for i in range(381)}; m2.update({60: 100.50, 240: 99.60, 380: 101.00})
    h2 = {U0 + 60 * i: (round(m2[i] - 0.01, 6), round(m2[i] + 0.01, 6)) for i in range(381)}; h2[ts(2026, 11, 11, 14, 31)] = (101.99, 102.01)
    F0 = ts(2026, 11, 10, 20, 50); fund = {F0 + 60 * i: (99.99, 100.01) for i in range(31)}; fund[F0 + 1200] = (99.99, 100.01)
    est_prints = {ts(2026, 11, 9, 21, 0): 0.0001, ts(2026, 11, 10, 21, 0): -0.0002, ts(2026, 11, 11, 21, 0): 0.0003}
    T1 = ts(2026, 10, 13, 13, 50); edt = {}
    for i in range(41): edt[T1 + 60 * i] = (round(mids[i] - 0.05, 6), round(mids[i] + 0.05, 6))
    edt[T1 + 600], edt[T1 + 780] = (100.00, 100.10), (100.60, 100.70)
    edt[ts(2026, 10, 13, 20, 0)] = (101.95, 102.05); edt[ts(2026, 10, 14, 13, 31)] = (102.95, 103.05)
    edt_prints = {ts(2026, 10, 12, 20, 0): 0.0001, ts(2026, 10, 13, 20, 0): -0.0002, ts(2026, 10, 14, 20, 0): 0.0003}
    dst = {}
    for (d, h, m, mid_) in ((30, 13, 50, 100.0), (30, 14, 0, 100.1), (30, 20, 0, 100.4), (31, 12, 0, 100.2), (31, 20, 0, 100.3)): dst[ts(2026, 10, d, h, m)] = (round(mid_ - 0.01, 6), round(mid_ + 0.01, 6))
    for (h, m, mid_) in ((5, 59, 100.5), (6, 1, 100.6), (12, 0, 100.4), (20, 0, 100.7)): dst[ts(2026, 11, 1, h, m)] = (round(mid_ - 0.01, 6), round(mid_ + 0.01, 6))
    for (h, m, mid_) in ((14, 31, 101.0), (14, 50, 100.9), (21, 0, 101.2)): dst[ts(2026, 11, 2, h, m)] = (round(mid_ - 0.01, 6), round(mid_ + 0.01, 6))
    dst_prints = {ts(2026, 10, 29, 20, 0): 0.0001, ts(2026, 10, 30, 20, 0): 0.0001, ts(2026, 10, 31, 20, 0): 0.0002, ts(2026, 11, 1, 20, 0): 0.0004, ts(2026, 11, 2, 21, 0): 0.0008}
    ks = lambda d: {str(k): v for k, v in d.items()}
    return {"KXHAND": {"series": hand, "cuts": [9.0, 10.0], "boundary": None, "funding": ks(est_prints)},
            "KXHANDB": {"series": hand, "cuts": [9.0, 10.0], "boundary": T0 + 60 * 31, "funding": ks(est_prints)},
            "KXHAND2": {"series": h2, "cuts": [9.0, 10.0], "boundary": None, "funding": ks(est_prints)},
            "KXFUND": {"series": fund, "cuts": [9.0, 10.0], "boundary": None, "funding": ks({ts(2026, 11, 9, 21, 0): 0.0001, ts(2026, 11, 10, 21, 0): 0.0002, ts(2026, 11, 11, 21, 0): 0.0003})},
            "KXEDT": {"series": edt, "cuts": [9.0, 10.0], "boundary": None, "funding": ks(edt_prints)},
            "KXDST": {"series": dst, "cuts": [9.0, 10.0], "boundary": None, "funding": ks(dst_prints)}}


HS = (0.0002, 0.0005, 0.001, 0.002)


def lines():
    fx = fixture()
    for name in sorted(fx):
        d = fx[name]; fund = None if d["funding"] is None else {int(k): v for k, v in d["funding"].items()}
        for filt in p.FILTERS:
            for side in ("long", "short"):
                for ex in p.EXITS:
                    for h in HS:
                        tr, c = p.rule_trades(d["series"], tuple(d["cuts"]), filt, side, ex, h, boundary=d["boundary"], funding=fund)
                        b = p.booked(tr)
                        yield "%s %s %s %s %.4f n %d booked %d gross %.12f net_taker %.12f net_maker %.12f funding %.12f missing %d no_mark %d clipped %d fnb %d" % (
                            name, filt, side, ex, h, len(tr), len(b), sum(t["gross"] for t in b), sum(t["net_taker"] for t in b), sum(t["net_maker"] for t in b), sum(t["funding"] for t in b),
                            c["missing_feature"], c["no_mark"], c["clipped"], c["funding_not_booked"])


if __name__ == "__main__":
    if (sys.argv[1:] or ["print"])[0] == "json": print(json.dumps({k: {"series": [[t, q[0], q[1]] for t, q in sorted(v["series"].items())], **{x: v[x] for x in ("cuts", "boundary", "funding")}} for k, v in fixture().items()}))
    else:
        for l in lines(): print(l)
