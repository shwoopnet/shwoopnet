# COMBOPRICE1: pricing procedure and honesty rules for politics-leg combos (design only)

Status: DESIGN. No Kalshi call was made writing it, nothing is live. Code: `src/scalper/combo_price.py`, tests `tests/test_combo_price.py` (`python3 -I tests/test_combo_price.py`). Sits under POLCOMBO1 amendment 2 (politics-leg combos allowed past the 14 day cap, money held until settlement, return per dollar-year), COMBO1, PARLAY1. Owner rules designed inside (caps are for a FUTURE spec only; each probe needs its own owner popup): up to 30 legs, $2 per parlay, $40 total stop, entry 10c to 90c where relevant, either side, hold to settlement, paper edge 10c per dollar after fees before any live probe, linked legs allowed with the link written down.

## 1. Reads needed per combo, and the budget

Minimum per combo = 1 + legs: one read of the combo market object (it lists the legs, `mve_selected_legs`, and carries the combo's own bid/ask) plus one market read per leg (bid, ask, sizes, close_time). Candlesticks are extra and only needed for a history-based price (staleness check, simulation): one for the combo and one per leg, so a candlestick-complete combo costs 2 x (1 + legs). Legs shared by several combos are read once and cached for the run, so a census of many combos costs far less than the sum.

At 4 requests a minute (the V2 share):

| legs | minimum reads | minutes | with candlesticks | minutes |
|---|---|---|---|---|
| 2 | 3 | 0.75 | 6 | 1.5 |
| 5 | 6 | 1.5 | 12 | 3.0 |
| 10 | 11 | 2.75 | 22 | 5.5 |
| 20 | 21 | 5.25 | 42 | 10.5 |
| 30 | 31 | 7.75 | 62 | 15.5 |

So a 30 leg spec is about 8 to 16 minutes of read budget for ONE combo; pricing is the rate limit. Rule: price at most the combos that already passed a cheap filter (a politics leg present, ask in band, spread at most 0.05), never the whole 146,000. A 429 is never retried inside the pricing run; the combo is marked UNPRICED and reported.

## 2. Procedure, step by step

1. Combo object: ticker, side to buy, `yes_ask`/`yes_bid` (NO ask = 1 - YES bid), close_time, `mve_selected_legs` (leg ticker and side). Skip if the side's ask is missing, outside 0.10 to 0.90 (the owner's band; the cheap-side 0.04 to 0.30 bands of COMBO1 stay for their own card), or spread above 0.05.
2. Each leg: GET the market. Leg ask/bid/mid FOR THE SIDE BOUGHT: a YES leg uses yes_bid, yes_ask; a NO leg uses 1 - yes_ask as its bid and 1 - yes_bid as its ask. Mid = (bid + ask)/2, requires a two sided quote with spread at most 0.10; otherwise the leg is UNQUOTED and the combo gets no estimate (never a last price filled in silently).
3. Staleness: the leg quote must be read within 5 minutes of the combo read (same pass, timestamps stored). A leg whose last trade or candle is older than 24 hours AND whose spread is above 0.05 is flagged STALE; a combo with any STALE leg can be priced but cannot be a candidate. With candlesticks, the leg mid used is the last candle ending at or before the combo read time; a gap over 2 hours is STALE.
4. Leg probability p_i = mid of the side bought. Win chance under independence = product (`independence_product`). Frechet bounds `frechet_bounds`: lower max(0, sum - (n-1)), upper min p_i; these hold for ANY dependence.
5. Correlation sensitivity: one-factor Gaussian copula, common rho, `copula_joint` (Gauss-Hermite, 200 nodes), rho in 0, 0.1, 0.3, 0.5, 0.7, plus both Frechet bounds (`sensitivity`). Checked: equals the product at rho 0 and the minimum at rho 1 (tests). Negative dependence is not modelled by the copula; for legs that oppose each other the only honest number is the Frechet lower bound.
6. Fee: standard taker formula, 0.07 p (1-p) per contract on the COMBO price, ceiled to the cent (`taker_fee`). It is the standard formula only; any combo-specific Kalshi fee, a maker half fee, a 3.1% markup or a 10 to 26.5% vig are UNVERIFIED third-party claims until a market object or Kalshi's fee schedule shows them. The spec prints the fee field source or "UNVERIFIED".
7. Edge per dollar = (win chance - ask - fee) / (ask + fee) (`edge_per_dollar`; cost includes the fee). Return per dollar-year = edge / years to the expected settlement date (`return_per_dollar_year`). A combo settling in 2027 must clear the 10c per dollar bar on that basis, and the spec states 10c over a year is about 10% a year before the alternative use of the money.
8. Break-even rho (`breakeven_rho`): the smallest correlation at which the model win chance covers ask + fee.
9. Spec popup (`format_popup_spec`), one page, fields: exact legs (ticker, side, chance), buy side and price, win chance (independence, assumed rho, Frechet range), the written link, lock-up and expected settlement date, MONEY HELD UNTIL SETTLEMENT, edge table by rho and per dollar-year, break-even rho, the caps ($2 per parlay, $40 total stop), and the honesty lines of section 4.

## 3. What the paper edge is, and the assumption it rests on

The 10c per dollar bar is only meaningful if the win chance is right. A listed combo's price embeds Kalshi's own view of the joint; our estimate of the joint is an assumption, and for correlated legs the independence product is WRONG in the direction of understating the win chance (positive correlation raises the joint). That cuts both ways for honesty: the model edge at rho 0.3 can look huge only because the assumed rho is invented. Fixed rule: a candidate must show edge at least 0.10 per dollar at the stated rho AND a stated reason for that rho written before the ask is looked at (same race, same party direction, same election night). The independence product is the edge floor only for positively linked legs; for legs not linked, the independence product is the estimate and no correlation edge may be claimed. The rho is never fit to this combo's price (that would make the edge zero by construction). The only evidence about rho is settled history: the simulation from singles (section 6) and settled combos once there are at least 100.

## 4. Honesty 1: win chance versus legs (independence, then rho 0.3)

Chance every leg wins, all legs equal p (`independence_product` / `copula_joint`):

| legs | p=0.5 indep | p=0.5 rho .3 | p=0.7 indep | p=0.7 rho .3 | p=0.9 indep | p=0.9 rho .3 |
|---|---|---|---|---|---|---|
| 2 | 0.250 | 0.298 | 0.490 | 0.528 | 0.810 | 0.822 |
| 5 | 0.031 | 0.105 | 0.168 | 0.287 | 0.590 | 0.660 |
| 10 | 0.001 | 0.036 | 0.028 | 0.148 | 0.349 | 0.505 |
| 20 | 0.000001 | 0.011 | 0.0008 | 0.066 | 0.122 | 0.350 |
| 30 | about 1e-9 | 0.005 | 0.00002 | 0.039 | 0.042 | 0.270 |

At 0.7 per leg, 10 legs win under 3 times in 100 and 30 legs about 2 in 100,000 if independent. A $2 parlay at 30 legs is, to a first approximation, a lottery ticket: the $40 stop is 20 tickets. The spec must show this row for its own legs.

## 5. Honesty 2: correlation sensitivity, worked synthetic example

Six legs, each 0.70, combo YES ask 0.12 (the independence product is 0.1176, so the ask is a haircut-free price), held one year. Edge per dollar after the ceiled fee:

| model | joint | edge per dollar | per dollar-year |
|---|---|---|---|
| rho 0 | 0.118 | -0.095 | -0.095 |
| rho 0.1 | 0.161 | +0.235 | +0.235 |
| rho 0.3 | 0.245 | +0.885 | +0.885 |
| rho 0.5 | 0.332 | +1.551 | +1.551 |
| rho 0.7 | 0.427 | +2.285 | +2.285 |
| Frechet lower | 0.000 | -1.000 | -1.000 |
| Frechet upper | 0.700 | +4.385 | +4.385 |

Break-even rho is 0.05. Reading: the sign of the edge flips between rho 0 and 0.1, and the size is driven almost entirely by the assumed rho. That is the point: a "10c per dollar" edge on a linked many-leg combo is mostly a claim about rho, so the spec states rho, the reason, and the rho 0 row beside it. 20 legs at 0.80 and ask 0.02: joint 0.0115 (rho 0), 0.048 (0.1), 0.151 (0.3), 0.276 (0.5); edge -0.62, +0.59, +4.03, +8.19. The Frechet upper bound figure (+25.7) is shown only as a bound, never as an estimate.

## 6. Rules for a SIMULATION FROM SINGLES

Used when no settled combos exist. Joins settled single markets (same event date or topic) into synthetic combos of 2 to 30 legs and measures the REALISED joint frequency, never a product. Rules: (1) label SIMULATION in every line, never live evidence; (2) legs and their single prices are those at a fixed time before close (the same T rule as COMBO1), two sided only; (3) the combo's price is NOT observed, so the output is the realised joint frequency against the independence product at each leg count and an estimated rho (the rho at which `copula_joint` matches the realised frequency), not an edge; an edge may be computed only against a hypothetical ask stated in advance; (4) joined families are counted in N; (5) at least 100 synthetic combos per leg count and no more than 30% of them from one event cluster, else NOT_ENOUGH_DATA; (6) development and held-out split by event date, held-out read once; (7) overlapping legs (the same leg in many synthetic combos) are one cluster for z; (8) the result can only decide whether it is worth asking for or watching a real combo, never open a probe.

## 7. Gate summary for a candidate spec

All required, any miss means no popup: politics leg present; legs 2 to 30 with a $2 cap; ask in 0.10 to 0.90 and spread at most 0.05; every leg two sided and not STALE; link written before the ask is read; edge at least 0.10 per dollar at the written rho AND shown at rho 0; per dollar-year figure shown with years to the expected settlement; break-even rho shown; lock-up line present; fee marked standard formula and combo fee UNVERIFIED; 40 settled paper combos (or SIMULATION labelled) per POLCOMBO1; owner popup for each live probe; live KILL, RETURN and open-position caps from POLCOMBO1 unchanged.
