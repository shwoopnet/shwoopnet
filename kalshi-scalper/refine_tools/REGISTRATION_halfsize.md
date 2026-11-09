# S-HALFSIZE1 (shadow, pre-registered 2026-11-06, before any scoring)

Question: is the OICORE bucket where the rounded-up cheaper price is under 0.10
worth its risk, i.e. does it net at most +3c per contract at real fills?

Strategy: OICORE (second slot, Bitcoin 15 min, 10 contracts, held to settlement).
Window: slotOrders with strategy OICORE, ts after 2026-11-05T16:18Z (the
S-BUCKET1 start), status filled and count > 0, settled only (result yes/no);
unsettled skipped.
Bucket key: the order's `price` field (the rounded-up cheaper-side price the
engine decided on). Under 0.10 means price < 0.10; the other group is 0.10+.
Real fill pnl per contract: paid = avgFill for YES, 1 - avgFill for NO.
Win (result equals side) pays 1 - paid - fee; loss pays -(paid + fee);
fee = avgFee per contract.

Report, for under-0.10 and 0.10+: fills, wins, net dollars, net cents per
contract (contract-weighted) with a bootstrap 90% interval (resample fills,
seed 1, 10000 draws), and the dollar effect of halving the under-0.10 group
(minus half its net dollars).

Read point: 40 fills in the under-0.10 group.
Kill rule for the half-size idea: if the under-0.10 group nets over +3c per
contract at 40 fills, drop the idea. If it nets under 0 with the interval's
upper end under +3c, it supports sending the idea to the owner. Otherwise wait.

History context: history PF 1.68 to 1.79 with half size; bucket +1.24c per
contract live (90% interval -1.3 to +4.0); about 410 splits tried, so nothing
survives deflation. This is a probe only, not a finding.
