# WHEEL0 templates and the wheel's shadow list: a note, not an admission (Forensics desk, 2026-11-13)

Asked by the Head of R&D: which of WHEEL0's templates could be logged forward on the wheel recorders' series. **Nothing here is admitted, proposed for a seat or tuned.** WHEEL0 has not been read; no outcome was used for this note.

## 1. Where the templates could be logged forward (a technical answer)

A template needs a quote at 600, 360 or 180 seconds before a 15 minute market's close and, for the lane's "fillable" test, a second look within 4 seconds that still offers 10 contracts at the ask plus 1c.

| Log source | Series | Second look within 4 s? | Until |
|---|---|---|---|
| R6 book recorder (polls every 2 s, top 5 levels) | Bitcoin, Ethereum, gold | Yes | 2026-12-31 |
| R6 | XRP, Dogecoin | Yes | **stops 2026-11-13 23:59 UTC**; no forward source after that |
| NC15 book recorder (polls every 5 s) | silver, copper, WTI oil, EUR/USD, GBP/USD, USD/JPY, HYPE, BNB, AUD/USD, USD/CAD, natural gas | **No.** The next poll is about 5 s later, so the lane's 4 second look cannot be met as written | 2026-12-31 |
| The bot's shadow logger | the L1 markets' quotes | No second look is built | n/a |

Two things follow for the admit list as a whole, not only for WHEEL0:

- The eleven NC15 places already on the list (batch 1b) meet the same wall: a 5 second recorder cannot show a fill "within 4 seconds". **Ruled by the Head of R&D on 2026-11-13 (00:07Z), written into the lane text as a stated variant:** on a log that polls slower than 4 seconds, the second look is the NEXT poll, and it must come at most 6 seconds after the signal poll; a signal whose next poll is later than 6 seconds is recorded as "not fill-checked" and does not count toward a block. A later look is the stricter test for a taker order, so this does not loosen the lane. On R6 (2 second polls) and the wheel recorder (3 second polls) the rule stays within 4 seconds as written.
- The measurement behind that ruling (from `FAMILY_COSTS_NOV12.md`, public book data only, no outcome used): on the eleven NC15 series, a 1 contract buy at the ask seen plus 1c, checked at the next poll about 5 seconds later, would still have filled 76% to 84% of the time (at the ask seen: 59% to 73%; at about 10 seconds with plus 1c: 69% to 78%). n: 51 to 65 fifteen minute windows a series, 638 windows in all, quotes about 6 minutes before the close, either side, any price. Window: closes from 2026-11-11 19:45Z to 2026-11-12 16:00Z, about 20 hours of one weekday. A first reading, not a settled figure.
- XRP and Dogecoin lose their only book recorder tonight.

## 2. Which templates the existing rules would let onto the list: none without the owner's word

The 21 templates are plain price-band rules. Each one falls under a rule that is already written:

| Templates | What they are | The rule in the way |
|---|---|---|
| 9 cheap-side (5c to 50c, three looks) | a cheap-side price band on a 15 minute series | The declined list: cheap-side price, regime and grammar sweeps on the 15 minute series were closed by evidence on Nov 12. On Bitcoin at 180 s it is also OICORE's market, side and minute (lane section 4, point 7) |
| 9 favourite-side (50c to 88c, three looks), bought and held | favourite and hold | The Charter's ban on favourite-and-hold for new live strategies; it needs a named written exception from the owner |
| 3 favourite at 88c to 97c | favourite-late | Declined by name on Nov 11 as copies; on gold at 360 s it is gold L1 itself, which is outside the wheel |

So the template set is a measuring instrument for the wheel's premise. It is not a list of candidates.

## 3. If the owner ever wants template rules on the wheel after the read

Three conditions from the lane's own text would apply, and they matter more here than anywhere:

1. **Not the hot ones.** WHEEL0 will print results per template and per market. Choosing the templates that looked best there is exactly "picking the best of several variants after seeing them" (lane section 3, point 3). The only clean choices are all 18 on a market or none, fixed before the forward window.
2. **One set of parameters on every market**, and every place counted in the lane ledger: 18 places a market.
3. **Forward signals only**, from a source that can show the second look (section 1).

## 4. What WHEEL0 can and cannot tell the admit list

- If the premise is supported, it supports the entry bar as a filter on rules like these, on these five markets, over two months. It does not qualify any template.
- If it is not supported, the lane's entry bar has no evidence behind it on the only data where it could be tested, and that goes to the owner before any seat, whatever is on the list.
