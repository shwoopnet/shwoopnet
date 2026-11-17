"""MECH1 signature schema (Desk A, Nov 17, 2026), built to MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4). Pure, no I/O.
A signature has six fields, each from a CLOSED vocabulary below (the spec's lists, plus the three additions marked ADDED). A registry entry may hold a LIST of values (or "*" for any) in a field: that is how a declined row is stored as a pattern.
NEW rule (rewritten Nov 17, 2026 after the VA's audit and the owner's "Keep it a version"), applied in this order:
  1. DECLINED: the candidate matches a declined pattern (every field of the pattern matches; "*" matches anything; a list matches any member; a pattern with `tickers` matches only a candidate whose `tickers` are all inside the pattern's; a candidate whose `idea` is in the pattern's `exceptions` skips that pattern). A candidate that names tickers, some banned and some not, is classified on the rest and reports `excluded_tickers`.
  2. SAME MECHANISM: some registry entry has the same signal field, the same clock CLASS and the same exit logic. The clock class is the `clock` field (relative to close, time of day, scheduled event, print, reopen, any minute); a new clock VALUE inside a class is a parameter, never a new signature. If the market family differs it is VERSION_NEW_MARKET (the owner: same signal on a new instrument class is a version, never NEW); if it is the same it is DUPLICATE.
  3. Otherwise NEW: a new signal field, a new clock class or a new exit logic. Every NEW is PROVISIONAL until the Verification Analyst signs it (the verdict carries provisional true).
Entry type and side rule never make a signature new."""
MARKET = ("15m_crypto", "15m_noncrypto", "hourly_ladder", "stock_perp", "index_perp", "metal_perp", "crypto_perp", "combo", "politics", "sports", "weather", "economics", "entertainment", "weekly_fx", "daily_yield", "mentions", "other")
SIGNAL = ("price_level", "price_change", "spread", "book_depth_imbalance", "open_interest", "volume", "funding_rate", "settlement_mark", "tape_flow", "spot_elsewhere", "event_calendar", "cross_market_residual",
          "none", "external_model")   # ADDED: "none" (no signal: liquidity provision or a pure calendar rule) and "external_model" (a public forecast or model that is not a price); both used by declined rows
CLOCK = ("fixed_time_to_close", "time_of_day", "scheduled_event", "print", "reopen", "any_minute")
ENTRY = ("taker", "maker_touch", "both")                 # ADDED: "both" for two sided quoting
EXIT = ("hold_to_settle", "fixed_time", "take_profit_multiple", "stop", "next_print", "none")   # ADDED: "none" for rows with no exit (declined patterns, ideas)
SIDE = ("favourite", "cheap", "follow", "fade", "both", "any")
FIELDS = (("market", MARKET), ("signal", SIGNAL), ("clock", CLOCK), ("entry", ENTRY), ("exit", EXIT), ("side", SIDE))
STATUS = ("live", "trial", "shadow", "paused", "retired", "falsified", "declined", "closed_by_evidence", "closed_unread", "idea", "paper", "exploratory")
def _vals(v): return ["*"] if v == "*" else (list(v) if isinstance(v, (list, tuple)) else [v])
def validate_entry(e):
    errs = []
    for k in ("id", "status", "source", "confidence") + tuple(f for f, _ in FIELDS):
        if k not in e: errs.append("missing " + k)
    if errs: return errs
    if e["status"] not in STATUS: errs.append("bad status %r" % e["status"])
    if e["confidence"] not in ("hand_read", "from_title", "from_ledger_row"): errs.append("bad confidence")
    pattern = e.get("kind") == "pattern"
    if "tickers" in e and e["tickers"] != "*" and not (isinstance(e["tickers"], list) and all(isinstance(t, str) and t.startswith("KX") for t in e["tickers"])): errs.append("tickers must be a list of KX... tickers or *")
    for f, vocab in FIELDS:
        vs = _vals(e[f])
        if not pattern and (len(vs) != 1 or vs[0] == "*"): errs.append("signature field %s must be one value" % f)
        for v in vs:
            if v != "*" and v not in vocab: errs.append("%s: %r not in vocabulary" % (f, v))
    if pattern and e["status"] not in ("declined", "closed_by_evidence", "falsified"): errs.append("a pattern must be declined, closed_by_evidence or falsified")
    return errs
def field_match(entry_v, cand_v):
    vs = _vals(entry_v)
    return "*" in vs or cand_v in vs
def classify(cand, registry):
    """-> (verdict, entry id or None, why, extra). verdict: DECLINED | DUPLICATE | VERSION_NEW_MARKET | UNVERIFIED_MATCH | NEW. cand: dict with the six fields, one value each; optional `tickers` (list) and `idea` (a name). extra: {"provisional": bool, "excluded_tickers": [...]}."""
    for f, vocab in FIELDS:
        if cand.get(f) not in vocab: raise ValueError("candidate %s %r not in vocabulary" % (f, cand.get(f)))
    ctick = list(cand.get("tickers") or []); excluded = set()
    for e in registry:
        if e.get("kind") != "pattern" or not all(field_match(e[f], cand[f]) for f, _ in FIELDS): continue
        if cand.get("idea") and cand["idea"] in (e.get("exceptions") or []): continue
        pt = e.get("tickers")
        if pt and pt != "*":
            if not ctick: continue                                   # a ticker ban applies only to a candidate that names tickers
            hit = [t for t in ctick if t in pt]
            if not hit: continue
            if len(hit) < len(ctick): excluded.update(hit); continue
        return "DECLINED", e["id"], "matches the declined pattern " + e["id"] + " (" + e.get("source", "") + ")", {"provisional": False, "excluded_tickers": sorted(excluded)}
    ver = None; unv = None
    for e in registry:
        if e.get("kind") == "pattern": continue
        if field_match(e["signal"], cand["signal"]) and field_match(e["clock"], cand["clock"]) and field_match(e["exit"], cand["exit"]):
            if e.get("verified") is False: unv = unv or e["id"]; continue         # a row nobody read (from_title, from_ledger_row) never decides DUPLICATE or VERSION alone (Desk B, the VA)
            if field_match(e["market"], cand["market"]): return "DUPLICATE", e["id"], "same market family, signal, clock class and exit logic as " + e["id"], {"provisional": False, "excluded_tickers": sorted(excluded)}
            ver = ver or e["id"]
    if ver: return "VERSION_NEW_MARKET", ver, "same signal, clock class and exit logic as " + ver + " on another market family: a version (owner, Nov 17: never NEW)", {"provisional": False, "excluded_tickers": sorted(excluded)}
    if unv: return "UNVERIFIED_MATCH", unv, "matches only the UNVERIFIED row " + unv + " (not read against its rule text); scored and labelled, a human or the VA decides", {"provisional": True, "excluded_tickers": sorted(excluded)}
    return "NEW", None, "a new signal field, clock class or exit logic against every entry; provisional until the VA signs it", {"provisional": True, "excluded_tickers": sorted(excluded)}
