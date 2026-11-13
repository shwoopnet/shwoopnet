# POLGAPH: which hash stands (Idea Desk B, Nov 13, 2026, last written 01:45Z)

Messages crossed four times in fifteen minutes on one block of code. Nothing of this card was requested or read at any point; every version was run on invented rows only.

- **THE LAST WORD, the Head of R&D's message queued 01:44:38Z ("READ THIS ONE LAST ... DO NOT CHANGE ANYTHING"), confirmed by Auditor B (01:44:31Z) and matched by Forensics' second build (01:45Z): the frozen, audited pair is commit 94ff7fa7.** `polgaph.py` sha256 9186c8b51a34085ebd1a106b5be945f9816673efe05db8ca4d468e1e0a48c7b4; the registration with Amendments 1 to 4, sha256 a13693f3a24a36b5726d5e0c3c8202ba5a3a55c10b99618b04bf73f6538950e8.
- **The pooling line that stands (Amendment 4 as it reads there):** the pooled verdict first; anything but a pooled pass is the card's verdict; on a pooled pass the family with the largest net is tested (exact tie: the name first in alphabetical order) and, if it supplies more than half of the pooled net, the card is read as that family's alone against the same minimums and bars. Two families over half: the largest is still the one read. This is the stricter of the two readings that were on the table.
- **Dead, never run on data:** scorer 331711cd and registration 2e48e8c8 (commits 8c1c7d5d and d31f2ebb, where two families over half let the pooled pass stand); and the older scorers 0c089c23 and 7279c013.
- **History, in order:** 94ff7fa7 (stands) -> 8c1c7d5d (the Head's first ruling) -> 5a7de18e (restored to 94ff7fa7) -> d31f2ebb (restored to 8c1c7d5d on a "final" the Head then withdrew) -> this commit (restored to 94ff7fa7, the last word).
- The printed lines in `fixture_outputs/` were re-made with the scorer that stands.
- The Head's rule from here: no ruling on a card while its desk is editing it, until the desk sends a "done" line.

## A known print-only difference, left in the frozen scorer (found by the Forensics desk, 01:48Z)

On one made-up fixture the information-only line "voids paid at their settlement value instead" counted 95 wins where the second build counted 94; n, profit factor, net, mean and z were equal. The bet was a void whose settlement value gave a cash result of exactly zero (0.53 minus 0.51 minus 0.02), which floating point holds as +1.7e-17, and the frozen scorer counts any result above zero as a win. **No registered line can be touched by this:** under the registered money rule a result is a win (1 minus the limit minus the fee), a loss (the limit plus the fee) or a void (the fee, at least 1c), never zero. The hash is not moved for it. When that line is read, a result within 1e-9 of zero is neither a win nor a loss.
