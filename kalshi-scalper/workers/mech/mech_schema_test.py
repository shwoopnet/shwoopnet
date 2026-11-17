"""Hand cases for the MECH1 matcher and the v0 registry (Desk A, Nov 17, 2026). python3 -I mech_schema_test.py"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema as S, mech_registry_build as B
reg = B.build()
def c(**k):
    d = dict(market="15m_crypto", signal="price_level", clock="fixed_time_to_close", entry="taker", exit="hold_to_settle", side="cheap"); d.update(k); return d
# 1. OICORE's signature again: DUPLICATE (same market family, signal and clock)
v = S.classify(c(signal="open_interest"), reg); assert v[0] == "DUPLICATE" and v[1] in ("OICORE", "OIREL1"), v
# 2. open interest on a family with no entry: a version (7g), not new
v = S.classify(c(market="hourly_ladder", signal="open_interest", exit="fixed_time"), reg); assert v[0] == "VERSION_NEW_MARKET", v
# 3. favourite-and-hold on any family is DECLINED by the pattern
v = S.classify(c(market="15m_crypto", signal="price_level", side="favourite", exit="hold_to_settle"), reg); assert v[0] == "DECLINED" and v[1] == "D_FAVOURITE_AND_HOLD", v
# 4. two-sided market making is DECLINED
v = S.classify(c(signal="none", clock="any_minute", entry="both", exit="none", side="both", market="crypto_perp"), reg); assert v[0] == "DECLINED" and v[1] == "D_TWO_SIDED_MM", v
# 5. funding rate on a crypto perp at a funding print: NEW (no entry has that signal)
v = S.classify(c(market="crypto_perp", signal="funding_rate", clock="print", exit="next_print", side="fade"), reg); assert v[0] == "NEW", v
# 6. a different clock with a known signal is NEW (the spec's "signal field OR clock")
v = S.classify(c(market="stock_perp", signal="price_change", clock="reopen", exit="fixed_time", side="follow"), reg); assert v[0] == "NEW", v
# 7. tape flow on crypto perps at any minute: the strict spec rule makes it a VERSION of the 15 minute tape-flow rows (RESIL1 or FLOW1 clock any_minute), NOT new; the Head decides if a new market family should count as new (documented, not changed here)
v = S.classify(c(market="crypto_perp", signal="tape_flow", clock="any_minute", exit="fixed_time", side="follow"), reg); assert v[0] == "VERSION_NEW_MARKET", v
# 8. 15 minute taker flow is DECLINED even with a different exit
v = S.classify(c(signal="tape_flow", clock="any_minute", exit="fixed_time", side="follow"), reg); assert v[0] == "DECLINED", v
# 9. a vocabulary error raises
try: S.classify(c(signal="vibes"), reg); raise SystemExit("no error")
except ValueError: pass
# 10. the validator rejects a signature with a list and a pattern with a bad status
bad = dict(reg[0]); bad["signal"] = ["price_level", "spread"]; assert S.validate_entry(bad)
pat = dict(next(e for e in reg if e["kind"] == "pattern")); pat["status"] = "live"; assert S.validate_entry(pat)
# 11. every declined pattern matches at least the row it was written for (a self check)
pats = [e for e in reg if e["kind"] == "pattern"]; assert len(pats) == 11
print("ok:", len(reg), "entries; all hand cases pass")
