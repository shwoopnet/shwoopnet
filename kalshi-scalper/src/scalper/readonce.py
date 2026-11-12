"""Read-once guard for held-out reads (standing rule, Nov 12, 2026).

A registration carries ONE committed line:
  READ-ONCE MARKER: not yet read; first read allowed on or after YYYY-MM-DD; after the read: READ ON <date>, commit <hash>
After the read that line is replaced (in a commit) by:
  READ-ONCE MARKER: READ ON <date>, commit <hash>
`require_unread` reads the COMMITTED file (git show HEAD:path), so an uncommitted edit cannot hide a past read,
refuses before the allowed date, and refuses if the line is missing or says READ. It never opens any data.
"""
import re, subprocess, os, datetime as dt
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PREFIX = "READ-ONCE MARKER:"
def marker_lines(relpath):
    """Committed marker lines of kalshi-scalper/<relpath>; [] if the file or line is absent."""
    r = subprocess.run(["git", "-C", REPO, "show", "HEAD:kalshi-scalper/" + relpath], capture_output=True)
    if r.returncode != 0: return []
    return [l.strip() for l in r.stdout.decode().splitlines() if l.strip().startswith(PREFIX)]
def require_unread(relpath, tag=None, now=None):
    """Raise SystemExit unless exactly the committed marker(s) for `tag` say not yet read and the date has come."""
    ls = [l for l in marker_lines(relpath) if tag is None or tag in l]
    if not ls: raise SystemExit("refused: no committed '%s' line for %s in %s" % (PREFIX, tag or "this read", relpath))
    now = now or dt.datetime.now(dt.timezone.utc)
    for l in ls:
        if not l.startswith(PREFIX + " not yet read;"):
            raise SystemExit("refused: held-out already read (%s)" % l[:120])
        m = re.search(r"on or after (\d{4}-\d\d-\d\d)", l)
        if not m: raise SystemExit("refused: marker has no allowed date: " + l[:120])
        if now < dt.datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=dt.timezone.utc):
            raise SystemExit("refused: held-out read not allowed before %s" % m.group(1))
    return True
