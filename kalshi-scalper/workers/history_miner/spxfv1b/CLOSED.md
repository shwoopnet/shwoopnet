# SPXFV1 build 2: CLOSED UNREAD 2026-11-13, family declined

The Head of R&D, 2026-11-13 16:58Z: SPXFV1 is CLOSED UNREAD. Its family (an outside reference price against a Kalshi 15 minute market) is declined under the three-falsified rule: GOLDFV1, INX1, H7, CMD1. No real row was read by build 2 or its rows builder.

Last state, kept as the record:
- spxfv1b.py 9032013a (3ecd0925): CLEAN by Auditor B and the Head. The PF-kill alignment (PF < 1.0 - 1e-9) the Head asked for at 16:57Z was stopped at 16:58Z and is NOT made.
- builder/build_windows.py 84c9767c (3514ef5d): the Kalshi half, sent to Auditor B; its audit is no longer needed. The futures half was never written.

No further work on these files.
