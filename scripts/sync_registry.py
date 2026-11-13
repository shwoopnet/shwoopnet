#!/usr/bin/env python3
"""Regenerate the wheel and closure rows of strategies-registry.json from the Head of R&D's files.

Reads WHEEL_ADMIT_LIST.md and RND_QUEUE.md from the git branch `rnd-queue` with `git show` (no network, no secret,
no other input). Only rows whose id starts with WH- (wheel places) or CL- (closures) are ever written; every other
row is hand-written (live strategies, hand notes) and is copied through untouched. Output is deterministic, so a
second run changes nothing. If a source file no longer carries the line a row rests on, the script exits 1 and
writes nothing (fail closed), so a reworded ledger cannot silently retire or revive a row.
Usage: sync_registry.py [--ref origin/rnd-queue] [--registry strategies-registry.json] [--check]
"""
import argparse, json, re, subprocess, sys
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

MANAGED = ('WH-', 'CL-')
KEYS = ['id', 'name', 'stage', 'rule', 'label', 'startDate', 'nextRead', 'nextReadText', 'n', 'nBasis', 'kill', 'return',
        'retiredOn', 'reason', 'notes', 'code', 'roomTarget', 'roomWhat', 'cause', 'figures']
SRC = {'admit': 'WHEEL_ADMIT_LIST.md', 'queue': 'RND_QUEUE.md'}

SHADOW_KILL = ("Shadow only: no order, nothing to lose. The place is dropped if its registered research read is falsified "
               "(all its places at once) or it cannot reach 60 fill-checked signals in 21 days")
SHADOW_RETURN = ("Takes a live seat only after one block of 60 fillable signals in 21 days on 7 or more days, cash PF 1.3+ and 1.0+ in each half, "
                 "then the owner's popup with the exact spec and the Chief of Staff's review (docs/ROTATION_LANE.md)")
NC15_RULE = "Top-5 size skew between the two sides of 0.50 or more at the last poll at or before 600 seconds to the close; buy at the ask between 10c and 90c, hold to settlement"
NC15_BASIS = "Public NC15 book recorder; the count is read from the private log, not stored here"


def wheel(i, name, rule, marker, src='admit', retire=None, **kw):
    return dict(id=i, name=name, rule=rule, marker=marker, src=src, retire=retire, kind='wheel', **kw)


def closure(i, name, marker, src, date, cause, reason, ret, rule='', notes=None):
    return dict(id=i, name=name, rule=rule, marker=marker, src=src, kind='closure', date=date, cause=cause, reason=reason, ret=ret, notes=notes or [])


NEVER = "Never as written (a new, differently registered rule would start from zero)"
CATALOG = [
    wheel('WH-CFRTIK-BTC', 'Perp-model longshot, wheel place (Bitcoin)',
          "Bitcoin 15 minute: the Kalshi-only cheap side with a model edge from the Bitcoin perpetual; replay of the R6 books plus public candles", r'CFRTI-K on Bitcoin',
          counting='cfrti', basis="Replay of the R6 books; the count is read from the private log, not stored here"),
    *[wheel('WH-CFRTIK-' + k, 'Perp-model longshot, wheel place (%s)' % n,
            "%s 15 minute: the CFRTI-K model edge, listed; admission waits on the perps archive files" % n, r'five further CFRTI-K places', counting='waiting',
            wait="Listed; the nightly perps archive takes this perpetual from Nov 12, 2026 (PR 861); admission is the Head of R&D's call once its first files land", basis="Replay of recorded books; the count is read from the private log, not stored here")
      for k, n in (('SILVER', 'Silver'), ('COPPER', 'Copper'), ('WTI', 'WTI oil'), ('HYPE', 'HYPE'), ('BNB', 'BNB'))],
    *[wheel('WH-NC15-' + k, 'Depth cell, wheel place (%s)' % n, NC15_RULE, r'silver, copper, WTI, HYPE, BNB, USD/CAD', counting='batch2', basis=NC15_BASIS,
            extra=("Marginal: re-counted once on 2026-11-19, withdrawn if under 60 fill-checked signals per 21 days" if k in ('SILVER', 'USDCAD') else None))
      for k, n in (('SILVER', 'silver'), ('COPPER', 'copper'), ('WTI', 'WTI oil'), ('HYPE', 'HYPE'), ('BNB', 'BNB'), ('USDCAD', 'USD/CAD'), ('NATGAS', 'natural gas'))],
    *[wheel('WH-IPJ-' + k, 'In-play jump, wheel place (%s)' % n, "Follow an in-play price jump (the jump rule registered by Desk B), %s" % n, r'Every sports and esports place is withdrawn', retire=True,
            date='2026-11-13', cause='failed the bar', reason="Withdrawn Nov 13: every sports and esports place is withdrawn (INPLAYJUMP's families closed or falsified; the Head of R&D's admit list)", ret=NEVER)
      for k, n in (('ESOCCER', 'e-soccer'), ('TT', 'table tennis'), ('EBASKET', 'e-basketball'), ('ITF', 'ITF tennis'), ('CHALL', 'challenger tennis'))],
    wheel('WH-ESOCTIE', 'E-soccer tie against base rate, wheel place', "E-soccer: the listed Tie bought pre-match when a walk-forward base rate beats its ask by 10c or more at a spread of 4c or less",
          r'Every sports and esports place is withdrawn', retire=True, date='2026-11-13', cause='failed the bar',
          reason="Withdrawn Nov 13: every sports and esports place is withdrawn (ESOCTIE closed or falsified; the Head of R&D's admit list)", ret=NEVER),
    *[wheel('WH-NC15-' + k, 'Depth cell, wheel place (%s)' % n, NC15_RULE, r'EUR/USD 13, GBP/USD 0', retire=True, date='2026-11-13', cause='failed the bar',
            reason="Withdrawn Nov 13: Desk A's count of fill-checked signals per 21 days is far under the 60 a block needs", ret=NEVER)
      for k, n in (('EURUSD', 'EUR/USD'), ('GBPUSD', 'GBP/USD'), ('USDJPY', 'USD/JPY'), ('AUDUSD', 'AUD/USD'))],
    closure('CL-MAPBREAK', 'Esports break rule (MAPBREAK)', r'WITHDRAWN Nov 13 00:48Z', 'admit', '2026-11-13', 'failed the bar',
            "Closed Nov 13: out at step 1 at both looks on every title, CS2 included (two independent builds agree; the Head of R&D confirmed Nov 12, 7:49 PM CT)", NEVER,
            rule="Esports matches: a rule on the break between maps (CS2 and Dota 2)"),
    closure('CL-REMATCH', 'Rematch fade (REMATCH)', r'REMATCH closed at stage 1', 'admit', '2026-11-13', 'failed the bar',
            "Closed Nov 13 at stage 1 on tradeability: the later match's market is listed but not tradeably quoted before the earlier match (two builds agree)", NEVER,
            rule="E-soccer: fade the previous loser's fall when the same two players meet again"),
    closure('CL-TIE3', 'Period tie (TIE3)', None, None, '2026-11-13', 'failed the bar',
            "Closed per the Head of R&D's confirmation (Nov 12, 7:49 PM CT)", NEVER, rule="Period ties on NHL periods, NFL quarters and soccer first halves",
            notes=["to confirm with the Head of R&D: the closing read is not yet in the ledger files on rnd-queue; stage taken from the owner's EA message"]),
    closure('CL-WXDAYEND', 'Weather after the day ends (WXDAYEND)', None, None, '2026-11-13', 'failed the bar',
            "Closed per the Head of R&D's confirmation (Nov 12, 7:49 PM CT)", NEVER, rule="Daily temperature brackets after the climate day ends",
            notes=["to confirm with the Head of R&D: the closing read is not yet in the ledger files on rnd-queue; stage taken from the owner's EA message"]),
    closure('CL-PERPBIN1', 'Perp against binary (PERPBIN1)', r'PERPBIN1: FALSIFIED on development', 'queue', '2026-11-12', 'failed the bar',
            "Falsified on development, both tries (open interest change carries no direction); held-out never read", NEVER, rule="Perpetual open interest change against the 15 minute binary"),
    closure('CL-S2-STOCKS', 'Stock test S2 (long leg)', r'S2 long leg \(stocks\)', 'queue', '2026-11-12', 'failed the bar',
            "Read once on development, below the bar and closed; held-out never opened. No Databento-derived figure is stored in this public file", NEVER,
            rule="Stocks, long leg", notes=["to confirm with the Head of R&D: whether this is the 'stock overnight test' the owner asked about"]),
    closure('CL-POLI2', 'Politics cost screen (POL-i2)', r'POL-i2: CLOSED on cost', 'queue', '2026-11-12', 'failed the bar',
            "Closed on cost: the round trip was above the line fixed before the pull, so its settled lists and candles were never pulled", NEVER, rule="Politics single markets, exit before settlement"),
    closure('CL-PROPUNDER', 'Player-prop under (PROPUNDER)', r'PROPUNDER', 'queue', '2026-11-12', 'superseded',
            "Closed unread, no try spent: the same rule as an earlier one that failed on cost", NEVER, rule="NBA player-prop NO side before tip"),
    closure('CL-PREMOVE', 'Pre-match move (PREMOVE)', r'PREMOVE WITHDRAWN UNREAD', 'queue', '2026-11-12', 'superseded',
            "Withdrawn unread by its author: the published evidence went against its direction and it could not be read in time", NEVER, rule="Follow a pre-match move on esports and table tennis"),
    closure('CL-PREDRIFT', 'Pre-drift (PREDRIFT)', r'PREDRIFT', 'queue', '2026-11-12', 'superseded',
            "Ruled a duplicate of PREMOVE (a 30 minute window against 60 is a parameter); no new tries", NEVER, rule="Pre-match drift, other side and exit than PREMOVE"),
]


def git_show(ref, path):
    r = subprocess.run(['git', 'show', '%s:%s' % (ref, path)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('sync_registry: cannot read %s:%s (%s)' % (ref, path, r.stderr.strip()[:200]))
    return r.stdout


def ct_text(stamp):
    d = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone(ZoneInfo('America/Chicago'))
    return d.strftime('%B ') + str(d.day) + ' at ' + str(int(d.strftime('%I'))) + d.strftime(':%M %p') + ' CT'


def build(spec, text, batch, start=None):
    if spec['marker'] and not re.search(spec['marker'], text[spec['src']]):
        sys.exit('sync_registry: %s no longer found in %s; not writing (fail closed)' % (spec['marker'], SRC[spec['src']]))
    row = {k: None for k in KEYS}
    row.update(id=spec['id'], name=spec['name'], rule=spec['rule'], notes=[], code={})
    if spec['kind'] == 'closure' or spec.get('retire'):
        row.update(stage='Retired', retiredOn=spec['date'], reason=spec['reason'], cause=spec['cause'], **{'return': spec.get('ret')})
        row['notes'] = list(spec.get('notes', []))
        return row
    row.update(stage='Shadow', label='UNPROVEN', kill=SHADOW_KILL, nBasis=spec['basis'], **{'return': SHADOW_RETURN})
    row['notes'] = [spec['extra']] if spec.get('extra') else []
    c = spec['counting']
    if c in ('batch2', 'cfrti') and batch:
        # The NC15 places count from the START TIME line of the admit list when there is one (it was moved twice after the batch 2 admission, Nov 13, 2026), else from the admission.
        stamp = (start or batch) if c == 'batch2' else batch
        row['startDate'] = stamp[:10]
        if c == 'batch2':
            row['nextReadText'] = "Counting since %s (the start time in the Head of R&D's admit list); n is read from the private log, not stored here" % ct_text(stamp)
        else:
            row['nextReadText'] = "Admitted %s but mute: it logs 'no signal: no mark' until the first nightly archive files with the Bitcoin perpetual land (the archive takes it from Nov 12, 2026), so no signal counts yet" % ct_text(stamp)
    elif c in ('batch2', 'cfrti'):
        row['nextReadText'] = "Admitted; start time to confirm with the Head of R&D"
        row['notes'].append("to confirm with the Head of R&D: the admit time was not found in the list")
    else:
        row['nextReadText'] = spec['wait']
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', default='origin/rnd-queue')
    ap.add_argument('--registry', default='strategies-registry.json')
    ap.add_argument('--check', action='store_true', help='exit 1 if the file would change')
    a = ap.parse_args()
    text = {k: git_show(a.ref, v) for k, v in SRC.items()}
    m = re.search(r'ADMITTED, BATCH 2, dated (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', text['admit'])
    batch = m.group(1) if m else None
    ms = re.search(r'START TIME OF THE FORWARD COUNT for the 7 NC15 depth-cell places[^:]*:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)', text['admit'])
    start = ms.group(1) if ms else None
    old = open(a.registry, encoding='utf-8').read()
    reg = json.loads(old)
    hand = [x for x in reg['strategies'] if not x['id'].startswith(MANAGED)]
    reg['strategies'] = hand + [build(s, text, batch, start) for s in CATALOG]
    ids = [x['id'] for x in reg['strategies']]
    if len(ids) != len(set(ids)):
        sys.exit('sync_registry: duplicate id')
    new = json.dumps(reg, indent=1, ensure_ascii=False) + '\n'
    if chr(0x2014) in new:
        sys.exit('sync_registry: em dash in output')
    if new == old:
        print('registry unchanged')
        return
    if a.check:
        print('registry would change')
        sys.exit(1)
    open(a.registry, 'w', encoding='utf-8').write(new)
    print('registry updated: %d rows (%d hand, %d managed)' % (len(ids), len(hand), len(CATALOG)))


if __name__ == '__main__':
    main()
