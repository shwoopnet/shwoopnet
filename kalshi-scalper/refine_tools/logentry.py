#!/usr/bin/env python3
"""Prepend an entry to REFINE_STATUS.md after the intro. Never commits or pushes.
usage: logentry.py --title T (--body B | --body-file F) [--target PATH]
Heading time comes from the machine clock: UTC-6 until 2027-03-08, UTC-5 after."""
import argparse, sys, datetime as dt
DEFAULT = "/home/user/shwoopnet/kalshi-scalper/REFINE_STATUS.md"
CHANGE = dt.datetime(2027, 3, 8, tzinfo=dt.timezone.utc)

def stamp(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    off = 6 if now < CHANGE else 5
    ct = now - dt.timedelta(hours=off)
    return "%s %s CT (%sZ)" % (ct.strftime("%Y-%m-%d"), ct.strftime("%I:%M %p"), now.strftime("%H:%M"))

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--title", required=True)
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--body"); g.add_argument("--body-file")
    a.add_argument("--target", default=DEFAULT)
    o = a.parse_args()
    body = o.body if o.body is not None else open(o.body_file, encoding="utf-8").read()
    body = body.strip("\n")
    for label, text in (("title", o.title), ("body", body)):
        for n, line in enumerate(text.split("\n"), 1):
            if "—" in line:
                print("REFUSED: em dash in %s line %d: %s" % (label, n, line)); return 1
    src = open(o.target, encoding="utf-8").read()
    i = src.find("\n## ")
    if i < 0: print("REFUSED: no existing entry heading found"); return 1
    entry = "## %s: %s\n\n%s\n\n" % (stamp(), o.title, body)
    open(o.target, "w", encoding="utf-8").write(src[:i+1] + entry + src[i+1:])
    print("wrote entry: ## %s: %s" % (stamp(), o.title)); return 0

if __name__ == "__main__":
    sys.exit(main())
