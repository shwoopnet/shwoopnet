# GOVSER1 registration: cheap-side brackets on government and agency series against a free official outside series (written 2026-11-05, before any price, candle or outcome was read; research only)

Worker for Strategy Research V2, family "pre-announced releases with a public numeric source not yet tested". Cheap side only (ask 3c to 30c, held, fee 7% x C x p x (1-p) rounded up, C = 10, taker at the ask). No favourite-and-hold, no 15 minute trigger. Touches no live code. Frozen last third of dates (cut 2026-10-03T16:00Z) never fetched.

## Duplicate check (README and workers/, read first)
Covered: GAS1, GAS2, ECONNEW2 (AAA gas, RBOB), ECONNEW1 (weekly jobless claims vs persistence), MORTGAGE1 (KX30YMORTW), TSA1 (KXTSAW), NOWCAST1 (CPI, core CPI, core PCE, GDP), ECONREL1 (duplicate, payrolls/unemployment/ISM/ADP/housing no keyless reference), FEDIMPL1, WTIW1 (KXWTIW, KXTNOTEW, USDJPY), SLOWSTAT1 (ADP, eggs, temp help, monthly yield extremes: NOT_RUNNABLE), EVENT1/EVENT830/EVT1, CALIB1 (Economics cheap side is -2c to -10c in every bucket), BARRIER1, DAILY2_CHECK (KXTNOTED no settled market).

## Step 1 (this registration): a count-only census, no price joined
Candidates fixed now from the public series list (Economics, Financials, Commodities, Transportation; source an agency or government): Treasury yield extremes (KX10YRDIRHW/LW/HM/LM, 2Y/5Y/7Y/30Y), KXUST*A daily par yields, KXTNOTED, KXNOTE10W/30W, KXEIACRUDEW, KXDIESELW/D, KXTGAW, KXCASED/KXCASEW, KXNATGASD/W, KXHOUSINGSTART, KXTSAD, KXAAAGASM/MTX, plus 40 other agency series. Metric: number of settled events (Kalshi `/events?status=settled`), no market price.

## Rule if a family has at least 100 settled events before the cut
Reference R = latest official value known at a fixed look (24 hours before close) from FRED or the agency; persistence plus a normal with sd fitted on the first two thirds of events; buy the cheap side (ask 3c to 30c) if model probability is at least 3 times the ask; at most 2 per event; held.

## Numeric prediction, kill criteria
Prediction: no family reaches 100 events with traded cheap markets; if one did, PF 0.2 to 1.0 (GAS2 -5.98c, WTIW1, MORTGAGE1 -5.77c). Prior of pass under 1%. FALSIFIED if mean net not above 0 in both halves or PF under 1.5 (150+ trades); NOT_ENOUGH_DATA under 100 events or 150 trades; NOT_RUNNABLE if the best family has events but no settled markets with quotes. N tried: +1 (running count about 730,441, deflated z bar about 5.27).
