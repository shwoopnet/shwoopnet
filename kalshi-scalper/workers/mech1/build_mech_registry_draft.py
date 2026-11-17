#!/usr/bin/env python3
"""MECH1 registry draft builder (Desk B, Nov 17 2026; DRAFT). Reads ONLY (a) headings of kalshi-scalper/README.md (the research branch copy), (b) the pre-registration paragraph that follows a 'Pre-registration: ID' heading, never a result paragraph, and (c) the hand-written declined patterns below (docs/STRATEGY_LIFECYCLE.md 7e).
Writes MECH_REGISTRY_DRAFT_B.json: one entry per test id with status (FALSIFIED or NOT_ENOUGH_DATA from its result HEADING), the six fields of MECHANISM_ENGINE_SPEC.md inferred by keyword from the pre-registration text, `inferred` (which fields were keyword matches) and `confidence` (auto only if all six matched a keyword; else review). No outcome number is read or stored.
Usage: build_mech_registry_draft.py <README.md> <out.json>"""
import re, sys, json, collections
FIELDS = ("market_family", "signal_field", "clock", "entry_type", "exit_type", "side_rule")
RULES = {
 "market_family": [("combo|parlay", "combo"), ("politic|election|senate|fed chair", "politics"), ("nba|nhl|nfl|mlb|sports|game total|moneyline", "sports"), ("weather|temperature|rain|nws", "weather"),
                   ("perp", "perp (crypto, stock, index or metal by ticker)"), ("ladder|hourly|above k", "hourly ladder"), ("silver|copper|wti|natural gas|natgas|eurusd|gbpusd|usdjpy|audusd|usdcad|forex|fx\\b|hype|bnb|non-crypto", "15 min non-crypto"),
                   ("bitcoin|btc|ethereum|eth\\b|xrp|doge|solana|crypto|gold", "15 min crypto")],
 "signal_field": [("open interest|\\boi\\b", "open interest"), ("funding", "funding rate"), ("spread", "spread"), ("depth|book|imbalance|queue|resting", "book depth or imbalance"), ("volume", "volume"), ("taker flow|tape|sweep|trade flow|flow", "trade-tape flow"),
                  ("spot|coinbase|kraken|bitstamp|binance|lag", "a spot price elsewhere"), ("calendar|release|cpi|fomc|earnings|schedule", "an event calendar"), ("residual|cross-market|lead-lag|cross series|twin|butterfly|monoton", "a cross-market residual"),
                  ("momentum|rise|drift|climb|path|change|move|jump|reversal|flip", "price change"), ("settlement mark|settle mark", "settlement mark"), ("price|band|favourite|favorite|cheap|\\d+c\\b", "price level")],
 "clock": [("funding time|funding print|reopen|reopens|print\\b", "a print or reopen"), ("release|calendar|cpi|fomc|earnings|scheduled", "a scheduled event"), ("time of day|hour of|overnight|session|weekday|utc hour|by hour|:00 utc", "time of day"),
           ("minutes? (?:left|before)|seconds? before|before the close|before close|\\blook\\b|\\d+ ?s\\b|\\d+ min", "fixed time to close"), ("any minute|every minute|continuous", "any minute")],
 "entry_type": [("maker|resting|limit order|rest at|post at", "maker at the touch"), ("taker|buy at|ask|enter|entry|cross", "taker")],
 "exit_type": [("take profit|target|99c|sell at \\d|multiple|cash out", "take profit as a multiple"), ("stop|25c line|stop out", "stop"), ("fixed hold|minutes later|\\bm60\\b|sell at close|exit at|time exit|sell 60", "fixed time"), ("hold|settle|to the end|expiry|resolve", "hold to settle"), ("next print|next funding", "the next print")],
 "side_rule": [("favourite|favorite|high price|88c|9\\dc", "favourite"), ("cheap|longshot|tail|low price|5c to", "cheap side"), ("fade|against|reversal|mean revert|contrarian|bounce", "fade"), ("follow|momentum|continuation|with the move|trend", "follow")],
}
DEFAULT = {"market_family": "15 min crypto", "signal_field": "price level", "clock": "fixed time to close", "entry_type": "taker", "exit_type": "hold to settle", "side_rule": "favourite"}
def infer(text):
    t = text.lower(); out = {}; inferred = []
    for f in FIELDS:
        for pat, val in RULES[f]:
            if re.search(pat, t): out[f] = val; inferred.append(f); break
        else: out[f] = DEFAULT[f]
    return out, inferred
HEAD = re.compile(r"^(#{2,4}) (.*)$")
STATUS = [("NOT_ENOUGH_DATA", "NOT_ENOUGH_DATA"), ("FALSIFIED", "FALSIFIED"), ("none passed", "FALSIFIED")]
ID_RE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*\d[A-Z0-9\-]*|[A-Z]{3,}[0-9]*")
STOP = {"FALSIFIED", "NOT_ENOUGH_DATA", "NOT_YET_FALSIFIED", "UTC", "BTC", "ETH", "XRP", "DOGE", "USD", "NYC", "NFL", "NBA", "NHL", "MLB", "CPI", "FOMC", "OI", "HTTP", "PASSED", "FAILED"}
def first_id(s):
    for m in ID_RE.finditer(s):
        if m.group(0) not in STOP: return m.group(0)
    return None
def build(lines):
    prereg = {}                      # id -> (line, first paragraph after a 'Pre-registration: ID' heading)
    heads = [(i, HEAD.match(l)) for i, l in enumerate(lines)]
    for i, m in heads:
        if not m: continue
        txt = m.group(2)
        if not re.match(r"(Pre-registration|Pre-register)", txt, re.I): continue
        ids = ID_RE.findall(txt.split("(")[0]); j = i + 1; para = []
        while j < len(lines) and not HEAD.match(lines[j]) and len(para) < 6:
            if lines[j].strip(): para.append(lines[j])
            elif para: break
            j += 1
        for pid in ids:
            if pid not in STOP and pid not in prereg: prereg[pid] = (i + 1, txt + " " + " ".join(para)[:1500])
    entries = {}
    for i, m in heads:
        if not m: continue
        txt = m.group(2)
        mm = re.match(r"(.+?) result\b", txt); rm = re.match(r"Result: (.+?)(?: \((?:run|read)[^)]*\))?:", txt)
        if not (mm or rm): continue
        head_ids_txt = mm.group(1) if mm else rm.group(1)
        stat_txt = txt.split("):")[-1] if "):" in txt else txt.split(":", 2)[-1]
        sts = [v for k, v in STATUS if k.lower() in stat_txt.lower()]
        if not sts: continue
        st = "MIXED" if len(set(sts)) > 1 else sts[0]
        label = re.sub(r"^[A-Z][A-Z0-9\-]*\d?[A-Z0-9\-]*(?:,| and)?\s*", "", head_ids_txt) if rm else ""
        head0 = re.split(r",|:", head_ids_txt)[0]
        ids = [x for x in ID_RE.findall(head0) if x not in STOP][:2] or [first_id(head_ids_txt)]
        for pid in ids:
            if not pid or pid in entries: continue
            src_line, text = prereg.get(pid, (None, head_ids_txt))
            fields, inferred = infer(text + " " + label)
            entries[pid] = {"id": pid, "status": st, "source": "kalshi-scalper/README.md line %d (result heading)" % (i + 1), "prereg_line": src_line, "label": label.strip() or None, **fields, "inferred": inferred, "confidence": "auto" if len(inferred) == 6 else "review"}
    return entries
def main():
    lines = open(sys.argv[1], encoding="utf-8").read().split("\n")
    e = build(lines); c = collections.Counter(v["confidence"] for v in e.values()); s = collections.Counter(v["status"] for v in e.values())
    json.dump({"note": "DRAFT by Desk B, Nov 17 2026. Fields inferred by keyword from the pre-registration paragraph (never a result paragraph); confidence review means at least one field fell to the default. A reviewer must correct every review entry.", "entries": list(e.values())}, open(sys.argv[2], "w"), indent=1)
    print("entries %d | by status %s | by confidence %s | without a pre-registration paragraph %d" % (len(e), dict(s), dict(c), sum(1 for v in e.values() if v["prereg_line"] is None)))
if __name__ == "__main__": main()
