"""Hand cases for the MECH1 matcher and the registry (Desk A, Nov 17, 2026, rewritten for the new NEW rule). python3 -I mech_schema_test.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mech_schema as S, mech_registry_build as B
reg = B.build()
def c(**k):
    d = dict(market="15m_crypto", signal="price_level", clock="fixed_time_to_close", entry="taker", exit="hold_to_settle", side="cheap"); d.update(k); return d
def v(**k): return S.classify(c(**k), reg)
# 1. OICORE's signal, clock class and exit again on the same family: DUPLICATE
r = v(signal="open_interest"); assert r[0] == "DUPLICATE" and r[1] in ("OICORE", "OIREL1") and not r[3]["provisional"], r
# 2. the same on a new family: a version, never NEW (the owner, Nov 17)
r = v(market="hourly_ladder", signal="open_interest"); assert r[0] == "VERSION_NEW_MARKET", r
# 2b. open interest on a new family with a NEW exit logic is NEW and provisional
r = v(market="hourly_ladder", signal="open_interest", exit="stop"); assert r[0] == "NEW" and r[3]["provisional"], r
# 3. favourite-and-hold on any family is DECLINED by the pattern
r = v(side="favourite"); assert r[0] == "DECLINED" and r[1] == "D_FAVOURITE_AND_HOLD", r
# 4. two-sided market making is DECLINED
r = v(signal="none", clock="any_minute", entry="both", exit="none", side="both", market="crypto_perp"); assert r[0] == "DECLINED" and r[1] == "D_TWO_SIDED_MM", r
# 5. funding rate at a print on a crypto perp: NEW, provisional
r = v(market="crypto_perp", signal="funding_rate", clock="print", exit="next_print", side="fade"); assert r[0] == "NEW" and r[3]["provisional"], r
# 6. PERPEQ1 (Monday gap: stock perp, price change, reopen, timed exit): the same on stock perps is DUPLICATE, on index perps a version, with a hold exit NEW
r = v(market="stock_perp", signal="price_change", clock="reopen", exit="fixed_time", side="follow"); assert r[0] == "DUPLICATE" and r[1] == "PERPEQ1", r
r = v(market="index_perp", signal="price_change", clock="reopen", exit="fixed_time", side="follow"); assert r[0] == "VERSION_NEW_MARKET" and r[1] == "PERPEQ1", r
r = v(market="stock_perp", signal="price_change", clock="reopen", exit="hold_to_settle", side="follow"); assert r[0] == "NEW", r
# 7. taker tape flow on any market is DECLINED by the wide patterns; as a maker it is a version of the 15 minute tape-flow rows
r = v(market="crypto_perp", signal="tape_flow", clock="any_minute", exit="fixed_time", side="follow"); assert r[0] == "DECLINED" and r[1] in ("D_CRON_CLUSTER", "D_FRACTIONAL_SIZE_FLOW"), r
r = v(market="crypto_perp", signal="tape_flow", clock="any_minute", entry="maker_touch", exit="fixed_time", side="follow"); assert r[0] == "VERSION_NEW_MARKET", r
# 8. 15 minute taker flow is DECLINED even with another exit
r = v(signal="tape_flow", clock="any_minute", exit="fixed_time", side="follow"); assert r[0] == "DECLINED", r
# 9. a vocabulary error raises
try: v(signal="vibes"); raise SystemExit("no error")
except ValueError: pass
# 10. the validator rejects a signature holding a list, a pattern with a bad status and a bad tickers field
bad = dict(reg[0]); bad["signal"] = ["price_level", "spread"]; assert S.validate_entry(bad)
pat = dict(next(e for e in reg if e["kind"] == "pattern")); pat["status"] = "live"; assert S.validate_entry(pat)
bt = dict(next(e for e in reg if e["id"] == "D_DOGE")); bt["tickers"] = ["DOGE"]; assert S.validate_entry(bt)
# 11. ticker bans: Dogecoin declines a candidate that trades only Dogecoin; with another ticker beside it the candidate stands and says what was excluded
r = v(market="15m_noncrypto", signal="volume", clock="any_minute", exit="fixed_time", tickers=["KXDOGE15M"]); assert r[0] == "DECLINED" and r[1] == "D_DOGE", r
r = v(market="15m_noncrypto", signal="volume", clock="any_minute", exit="fixed_time", tickers=["KXDOGE15M", "KXSILVER15M"]); assert r[0] != "DECLINED" and r[3]["excluded_tickers"] == ["KXDOGE15M"], r
r = v(signal="price_level", side="favourite", exit="stop", tickers=["KXXRP15M"]); assert r[0] == "DECLINED" and r[1] == "D_XRP_L1", r
r = v(market="15m_noncrypto", signal="volume", clock="any_minute", exit="fixed_time"); assert r[0] != "DECLINED" or r[1] not in ("D_DOGE", "D_XRP_L1"), r          # a ticker ban needs a candidate that names tickers
# 12. spot_elsewhere on the 15 minute families is DECLINED by the cheap-side grammar pattern (the VA's proposal 4)
r = v(signal="spot_elsewhere", clock="any_minute", exit="fixed_time", side="follow"); assert r[0] == "DECLINED" and r[1] == "D_CHEAP_REGIME_GRAMMAR_15M", r
# 13. the weather exceptions (WXDAYEND, ORHARVEST1) are not declined by D_WEATHER_FORECAST
r = v(market="weather", signal="external_model", clock="any_minute", exit="hold_to_settle", side="follow"); assert r[0] == "DECLINED" and r[1] == "D_WEATHER_FORECAST", r
r = S.classify(c(market="weather", signal="external_model", clock="any_minute", exit="hold_to_settle", side="follow", idea="ORHARVEST1"), reg); assert r[0] != "DECLINED" or r[1] != "D_WEATHER_FORECAST", r
# 14. unverified rows are marked
assert all(e["verified"] == (e["confidence"] == "hand_read") for e in reg)
pats = [e for e in reg if e["kind"] == "pattern"]; assert len(pats) == 19, len(pats)
print("ok:", len(reg), "entries; all hand cases pass;", sum(1 for e in reg if not e["verified"]), "rows unverified")
