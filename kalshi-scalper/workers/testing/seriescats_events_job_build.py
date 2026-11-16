#!/usr/bin/env python3
"""Builds the two pull job files of SERIESCATS_EVENTS (Testing Desk, Nov 16, 2026) from the SERIESCATS list answers (public Kalshi series metadata, scratch copies).
Usage: seriescats_events_job_build.py <dir with 0001.json.gz 0002.json.gz s2_0001.json.gz s2_0002.json.gz> <out dir>. Registration: SERIESCATS_EVENTS_REGISTRATION.md."""
import gzip, json, os, re, sys
CATS = ("Mentions", "Companies", "Science and Technology")
SERIES_RE = re.compile(r"[A-Z0-9]{2,32}")
EP = [{"name": "events_list", "method": "GET", "path_pattern": "/events", "params_allowed": ["series_ticker", "status", "limit", "cursor"]}]
STOP = {"pause_seconds_on_429": "5, doubling to 60", "stop_after_consecutive_429": 3, "note": "a 429 is waited out with a doubling pause and the same request is asked again; three in a row end the run; no other address, no proxy, no retry around a refusal"}


def load(d):
    S = {}
    for f in ("0001", "0002", "s2_0001", "s2_0002"):
        for s in json.load(gzip.open(os.path.join(d, f + ".json.gz")))["series"]: S[s["ticker"]] = s
    return S


def job(jid, purpose, notes, series, reqs):
    return {"job_id": jid, "registration": "kalshi-scalper/workers/testing/SERIESCATS_EVENTS_REGISTRATION.md", "purpose": purpose, "heldout": "none (event metadata only: event ticker, series, category, strike or close date; no market, no price, no result)",
            "allowed_endpoints": EP, "series_allowlist": series, "ticker_allowlist": [], "max_requests": len(reqs), "requests": reqs, "notes": notes, "owner": "MAIN", "host": "api.elections.kalshi.com", "base_path": "/trade-api/v2",
            "pacing_seconds": 1.0, "status": "active", "stop_rules": STOP}


def build(S):
    sel = sorted(t for t, s in S.items() if s["category"] in CATS)
    ok = [t for t in sel if SERIES_RE.fullmatch(t)]; refused = [t for t in sel if t not in ok]
    probe_series = ["KXTOKENUSED"] + [t for t in ok if S[t]["category"] == "Mentions"][:1] + [t for t in ok if S[t]["category"] == "Companies"][:1]
    pr = []
    for t in probe_series:
        pr += [{"id": "p_all_" + t, "path": "/events", "params": {"series_ticker": t, "limit": 200}, "max_pages": 1}, {"id": "p_settled_" + t, "path": "/events", "params": {"series_ticker": t, "status": "settled", "limit": 200}, "max_pages": 1}]
    probe = job("SERIESCATS_EVENTS_PROBE", "Probe: events list of 3 series with and without status, to see whether the default returns settled events. Metadata only.", "6 requests, 1 page each; nothing is read before the registration's reader step.", sorted(probe_series), pr)
    main = job("SERIESCATS_EVENTS", "Events list (series, category, strike or close date) of every Mentions, Companies and Science and Technology series, for events per day. No market, price or result.",
               "One request per series, 200 events a page, status as the probe showed; a series whose answer carries a cursor is listed apart and asked in a follow-up job.", ok,
               [{"id": "ev_" + t, "path": "/events", "params": {"series_ticker": t, "limit": 200}, "max_pages": 1} for t in ok])
    return probe, main, sel, refused


if __name__ == "__main__":
    probe, main, sel, refused = build(load(sys.argv[1]))
    for name, j in (("SERIESCATS_EVENTS_PROBE", probe), ("SERIESCATS_EVENTS", main)):
        with open(os.path.join(sys.argv[2], name + ".json"), "w") as fh: json.dump(j, fh, indent=1); fh.write("\n")
    print("selected", len(sel), "refused by the series pattern", refused, "requests", len(main["requests"]), "probe requests", len(probe["requests"]))
