Cross comparison of the two V1/V2 builds, Nov 13, 2026 (invented rows only, no recorded data).
inv_mine/: my invented set (gen_mine.py). The Miner's set is on claude/history-miner (resting2/inv). Both builds were run on both sets, values mapped unchanged (csv to csv.gz for mine, plain csv for theirs).
mine_on_theirs.py, both_on_mine.py: the harnesses (they point at scratch paths and a checkout of claude/history-miner in /tmp/cmp_hm).
Scorer 223326ee..., Miner's resting2.py 93f47fec... Result sent to the Head by message: SAME except halves with an infinite or empty half, and the fill rate denominator.

Rerun after the Miner aligned (resting2.py 8e402429, scorer 8bba0c54): SAME on both sets, no differences (D1 and D2 closed).
