"""MECH1 signature schema (Desk A, Nov 17, 2026), built to MECHANISM_ENGINE_SPEC.md (rnd-queue 785fe85a4). Pure, no I/O.
A signature has six fields, each from a CLOSED vocabulary below (the spec's lists, plus the three additions marked ADDED). A registry entry may hold a LIST of values (or "*" for any) in a field: that is how a declined row is stored as a pattern.
NEW rule (spec section 1), applied in this order:
  1. DECLINED: the candidate matches a declined pattern (every field of the pattern matches; "*" matches anything; a list matches any member).
  2. SAME: some registry entry has the same signal field AND the same clock. Then the candidate is NOT new. If the market family differs it is reported as VERSION_NEW_MARKET (7g: the same logic on a new market is a version, never a new strategy); if the market family is the same it is DUPLICATE.
  3. Otherwise NEW (it differs from every entry in its signal field or its clock).
Exit, entry type and side rule do not make a signature new on their own (a different exit of the same signal and clock is a version, 7g)."""
MARKET = ("15m_crypto", "15m_noncrypto", "hourly_ladder", "stock_perp", "index_perp", "metal_perp", "crypto_perp", "combo", "politics", "sports", "weather", "economics", "entertainment", "other")
SIGNAL = ("price_level", "price_change", "spread", "book_depth_imbalance", "open_interest", "volume", "funding_rate", "settlement_mark", "tape_flow", "spot_elsewhere", "event_calendar", "cross_market_residual",
          "none", "external_model")   # ADDED: "none" (no signal: liquidity provision or a pure calendar rule) and "external_model" (a public forecast or model that is not a price); both used by declined rows
CLOCK = ("fixed_time_to_close", "time_of_day", "scheduled_event", "print", "reopen", "any_minute")
ENTRY = ("taker", "maker_touch", "both")                 # ADDED: "both" for two sided quoting
EXIT = ("hold_to_settle", "fixed_time", "take_profit_multiple", "stop", "next_print", "none")   # ADDED: "none" for rows with no exit (declined patterns, ideas)
SIDE = ("favourite", "cheap", "follow", "fade", "both", "any")
FIELDS = (("market", MARKET), ("signal", SIGNAL), ("clock", CLOCK), ("entry", ENTRY), ("exit", EXIT), ("side", SIDE))
STATUS = ("live", "trial", "shadow", "paused", "retired", "falsified", "declined", "closed_by_evidence", "closed_unread", "idea", "paper")
def _vals(v): return ["*"] if v == "*" else (list(v) if isinstance(v, (list, tuple)) else [v])
def validate_entry(e):
    errs = []
    for k in ("id", "status", "source", "confidence") + tuple(f for f, _ in FIELDS):
        if k not in e: errs.append("missing " + k)
    if errs: return errs
    if e["status"] not in STATUS: errs.append("bad status %r" % e["status"])
    if e["confidence"] not in ("hand_read", "from_title", "from_ledger_row"): errs.append("bad confidence")
    pattern = e.get("kind") == "pattern"
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
    """-> (verdict, entry id or None, why). verdict: DECLINED | DUPLICATE | VERSION_NEW_MARKET | NEW. cand: dict with the six fields, one value each (it must validate as a signature)."""
    for f, vocab in FIELDS:
        if cand.get(f) not in vocab: raise ValueError("candidate %s %r not in vocabulary" % (f, cand.get(f)))
    for e in registry:
        if e.get("kind") == "pattern" and all(field_match(e[f], cand[f]) for f, _ in FIELDS):
            return "DECLINED", e["id"], "matches the declined pattern " + e["id"] + " (" + e.get("source", "") + ")"
    ver = None
    for e in registry:
        if e.get("kind") == "pattern": continue
        if field_match(e["signal"], cand["signal"]) and field_match(e["clock"], cand["clock"]):
            if field_match(e["market"], cand["market"]): return "DUPLICATE", e["id"], "same market family, signal and clock as " + e["id"]
            ver = ver or e["id"]
    if ver: return "VERSION_NEW_MARKET", ver, "same signal and clock as " + ver + " on another market family: a version (7g), not a new strategy"
    return "NEW", None, "differs from every entry in its signal field or its clock"
