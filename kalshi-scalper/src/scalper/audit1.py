"""AUDIT1: a read-only audit of every registered result in README.md and workers/*_RESULT.md.

Builds workers/AUDIT1_TABLE.csv (one row per registered try or family result) by grep and reading,
then computes the statistics in workers/AUDIT1_REPORT.md. It never modifies a result, trades nothing,
and adds no try (N +0). A field that cannot be parsed is left blank or written "unknown", never guessed.

    cd src && python -B -m scalper.audit1 table     # writes ../workers/AUDIT1_TABLE.csv
    cd src && python -B -m scalper.audit1 report    # prints the statistics (the report is written by hand from them)
"""
import csv
import math
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
README = os.path.join(ROOT, "README.md")
WORKERS = os.path.join(ROOT, "workers")
TABLE = os.path.join(WORKERS, "AUDIT1_TABLE.csv")

VERDICTS = ["NOT_YET_FALSIFIED", "NOT_ENOUGH_DATA", "NOT_RUNNABLE", "NO_WINNER", "FALSIFIED", "SURVIVES",
            "MIXED", "DUPLICATE", "PASSED", "INFORMATION"]

LANES = ["15-minute crypto", "15-minute gold", "15-minute crypto+gold", "other 15-minute series", "hourly ladders",
         "daily/weekly ladders", "weather", "sports", "economics/macro", "politics", "entertainment",
         "perps/venues", "options", "cost/execution", "other"]

# keyword patterns per lane, matched on lower-cased text
LANE_KW = {
    "15-minute crypto": [r"kxbtc15m", r"kxeth15m", r"kxxrp15m", r"kxdoge15m", r"bitcoin 15", r"ethereum 15", r"\bxrp\b",
                         r"dogecoin", r"\bbtc\b", r"bitcoin", r"ethereum", r"open interest core", r"oicore"],
    "15-minute gold": [r"kxgold15m", r"\bgold\b", r"gold's"],
    "other 15-minute series": [r"eurusd", r"gbpusd", r"usdjpy", r"audusd", r"usdcad", r"silver", r"copper", r"\bwti\b",
                               r"natural gas", r"\bhype\b", r"\bbnb\b", r"zcash", r"\bnear\b", r"\bsolana\b",
                               r"other 15 minute", r"15 minute series", r"commodit", r"\bfx\b"],
    "hourly ladders": [r"kxbtcd", r"kxethd", r"kxgoldh", r"hourly", r"kxsold", r"kxxrpd"],
    "daily/weekly ladders": [r"daily ladder", r"weekly", r"daily wti", r"kxgoldd", r"kxgoldw", r"s&p 500", r"nasdaq",
                             r"range ladder", r"\bladder\b"],
    "weather": [r"weather", r"temperature", r"\brain\b", r"kxrain", r"forecast", r"\bwx", r"high-temperature"],
    "sports": [r"sports", r"\bnba\b", r"\bnfl\b", r"\bnhl\b", r"\bmlb\b", r"espn", r"esports", r"game winner",
               r"game-winner", r"moneyline", r"college football"],
    "economics/macro": [r"\bcpi\b", r"jobless", r"\bpce\b", r"\bfomc\b", r"mortgage", r"\btsa\b", r"nowcast", r"gas price",
                        r"aaa", r"macro", r"economic", r"\bfed\b", r"treasury", r"payroll", r"gdp"],
    "politics": [r"election", r"midterm", r"truth social", r"politic", r"senate", r"president"],
    "entertainment": [r"netflix", r"spotify", r"billboard", r"entertainment", r"mention", r"earnings-call", r"box office",
                      r"culture", r"\bchart\b"],
    "perps/venues": [r"perp", r"funding", r"polymarket", r"venue", r"binance", r"deribit", r"basis", r"liquidation"],
    "options": [r"straddle", r"options", r"thetadata", r"implied vol"],
    "cost/execution": [r"\bfee\b", r"fee rounding", r"slippage", r"sizing", r"size ladder", r"fill model", r"queue",
                       r"execution cost", r"order size"],
}

SHAPES = [
    ("structural lock", [r"\block\b", r"locks", r"arbitrage", r"dutch book", r"consisten", r"crossed", r"\barb\d", r"full-set"]),
    ("maker", [r"maker", r"resting", r"market making", r"market maker", r"queue"]),
    ("generator/search", [r"generator", r"\bgen\d+", r"search", r"autopilot", r"mutation", r"decision tree", r"\btree\d", r"auto\d",
                          r"sweep", r"grid"]),
    ("model-vs-price", [r"against a (?:public )?(?:forecast|model|nowcast|base rate|persistence)", r"fair value", r"nowcast",
                        r"implied", r"forecast", r"lognormal", r"reflection", r"model", r"against .{0,40}(?:espn|reference)"]),
    ("cheap side", [r"cheap side", r"cheap far", r"cheap tail", r"underdog", r"far tail", r"cheaper side", r"cheap sides",
                    r"tail"]),
    ("favourite", [r"favou?rite", r"88c to 97c", r"\bl1\b"]),
    ("exit/risk rule", [r"\bexit", r"stop\b", r"take profit", r"time stop", r"profit cap", r"loss cap", r"cooldown"]),
    ("filter on L1", [r"filter", r"skip", r"stand-down"]),
    ("round-trip scalp", [r"scalp", r"round trip", r"momentum", r"spike", r"mean reversion", r"snapback", r"lag"]),
    ("seasonality/calendar", [r"seasonal", r"time-of-day", r"hour-of-day", r"calendar", r"weekday", r"event"]),
]

LANE_OVERRIDE = {}

_LANE_GROUPS = {
    "15-minute crypto+gold": "H1 H2 H3 H4 H5 L1 L2 L3 B1 B2 B3 B4 M1 P2 Q1 Q2 Q3 X1 X2 X3 X4 X5 X6 X7 T1 T4 T5 OW2 OW3 OW4 OW7 SS1 SS2 TP1 "
                             "L1B SCALP1 SCALP2 GEN1 GEN1S GEN2 GEN6 GEN7 GEN8 GEN9 NEWH1 NEWH6 NEWH7 EVT1 EXITOI-G MAKER1 MAKER2 MAKER3 MAKER4 "
                             "DAYCUT1 HOUSE1 HOUSE2 HOUSE3 DCAP1 TIMEX1 SPREAD1 EXIT1 EXIT2 REGIME1 GROW1 THROTTLE1 RISK1 FALS2 MKTTIME1 "
                             "AUTO1 AUTO2 AUTO3 HIST1 MUT1 PPW1 BAND2 NEWH5 CONF2 SEARCH5K FACT1 UNDER1 P5 P6 RT1 RT2 TAPE20 BTCBOOK HUNT1 HUNT2 PULL1 "
                             "BOUNCE1 HOURS2 QUIRK1 FALS1 GOLD1D",
    "15-minute crypto": "H7 N1 N2 E1 E2 E3B GEN4 FALS3 FALS4 FALS5 OIDRIFT MECH1 MECHOI1 OEXIT1 NEWH3 NEWH8 NEWH12 ETHFUNNEL SLOTEX SLOTEX-ETH "
                        "XLEAD1 CRYPTO1 GEN11 LATECAL BTCAVG",
    "15-minute gold": "NEWH2 GOLDFV1 GOLDFILL GOLDPYTH-H GEN10 MM1 NEWH11 GEN5",
    "other 15-minute series": "E3 E3C HYPE BNB E5 E5B OICOREX1 EVENT1 TODSEAS1 SPIKE1 VOLSLOT1 XCRY1 XOI1 XMET1 LAG15 FXUSD SETTLE1 NEWH15 NEWH17 "
                              "QSTALE1 TSLM1 CMD1",
    "hourly ladders": "E4 XM1 LAD1 NEWH4 NEWH9 NEWH10 NEWH14 LADLONG1 LADFADE OIHR1 HRSEAS1 HOURLY1 SKEW1 VOLGAP1 PERPOI1 MAKERTAIL1 GEN3 CORR1 "
                      "CONF1 TWIN TAPE LADDER LADL1 LOCK2 LOCK2H NEWH13 VENUES1 CPIX",
    "daily/weekly ladders": "GAS1 APP1 DAILY2 INX1 WTIW1 XLADDER1 IDXFUT1 USWEEP1",
    "weather": "WX3 WXNEW1",
    "sports": "SP1 F6 F7 SC1 ESPN1 ARB5 SPORTCONS1 FAMSPORTS FAMXV ESPORT1 SWING1 THETA1",
    "economics/macro": "CPI1 CPIMENT_RERUN CPIMENT-RERUN ECONNEW1 ECONNEW2 MORTGAGE1 TSA1 NOWCAST1 FAM2 PROG1",
    "entertainment": "MENT1 CHART1 SPOTD1 ENTER1",
    "perps/venues": "FUND1 PERP1 PERP2 PERP3 CARRY1 PAIRS1 FUNDX1 PERPFLOW1 LIQ1-INFO SNAPBACK1 XVENUE1 PM1 PM2 FLOW1",
    "cost/execution": "SIZE1 SIZE2 SIZE3 COST1 DL1 DL10 CAP1 MC1 SF1",
    "options": "STRADDLE1 BUYDIP1",
    "other": "ARB1 ARB2 ARB3 ARB4 FLB1 IDX1 SLOW1 SECT1 EQUAKE1 PUB20 P06 CAL AUTO QUOTE1 CAL1 WX3X",
}
for _lane, _ids in _LANE_GROUPS.items():
    for _i in _ids.split():
        LANE_OVERRIDE[re.sub(r"[^A-Z0-9]", "", _i.upper())] = _lane

# ---------------------------------------------------------------- numeric helpers


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sf(z):
    """P(Z >= z) for a standard normal."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def binom_sf(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p), exact."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if not 0 < p < 1:
        return 1.0 if p >= 1 else 0.0
    tot = 0.0
    for i in range(k, n + 1):
        tot += math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                        + i * math.log(p) + (n - i) * math.log(1 - p))
    return min(1.0, tot)


def max_p(z, k):
    """P(max of k independent standard normals >= z): the row-level p-value for 'best of k'."""
    return 1.0 - (1.0 - sf(z)) ** max(1, k)


def fisher_combined(ps):
    """Fisher's method over p-values; returns (statistic, df, p) with the chi-square tail by series."""
    ps = [min(max(p, 1e-300), 1.0) for p in ps]
    stat = -2.0 * sum(math.log(p) for p in ps)
    df = 2 * len(ps)
    x = stat / 2.0
    term, tot = 1.0, 1.0
    for i in range(1, df // 2):
        term *= x / i
        tot += term
    return stat, df, min(1.0, math.exp(-x) * tot)


def pcurve_right_skew(ps, alpha=0.05):
    """Simonsohn p-curve: among p < alpha, true effects pile up near 0. Returns (n_sig, n_below_half, binomial p)."""
    sig = [p for p in ps if p < alpha]
    low = sum(1 for p in sig if p < alpha / 2)
    return len(sig), low, binom_sf(low, len(sig), 0.5) if sig else 1.0


def z_from_mean_ci(mean, lo, hi):
    """Derive z from a mean and a 95% confidence interval (symmetric normal approximation)."""
    if hi <= lo:
        return None
    se = (hi - lo) / (2 * 1.96)
    return mean / se if se > 0 else None


# ---------------------------------------------------------------- text parsing

NUM = r"[+\-\u2212]?\d+(?:\.\d+)?"
Z_PAT = re.compile(r"(?<![A-Za-z])\b([zt])\s*(?:=|of)?\s*([+\-\u2212]\d+(?:\.\d+)?)", re.I)
Z_PLAIN = re.compile(r"\bz\s+(\d+\.\d+)\b")
BAR_WORDS = r"(?:bar|against|below|under|above|least|needs?|needed|threshold|deflated|bonferroni|gate|than|beats?|crosses|cross|of|bars)"
MEANCI = re.compile(r"mean\s*(" + NUM + r")c?[^.;]{0,40}?(?:95% )?(?:CI|confidence interval)[^\d\-+\u2212]{0,12}(" + NUM + r")[^\d\-+\u2212]{1,12}(" + NUM + r")", re.I)


def _f(s):
    return float(s.replace("\u2212", "-"))


def parse_z_values(text):
    """All z/t statistics reported for results in the text (signed). A bar or threshold is excluded: an explicit sign is
    read as a result unless a bar word precedes it; an unsigned 'z 4.42' is read as a result only after 'day', 'clustered', 'NW' or '('."""
    out = []
    for m in Z_PAT.finditer(text):
        pre = text[max(0, m.start() - 24):m.start()].lower().rstrip()
        if re.search(BAR_WORDS + r"\s*(?:about\s*)?$", pre):
            continue
        try:
            v = _f(m.group(2))
        except ValueError:
            continue
        if abs(v) < 40:
            out.append(v)
    for m in Z_PLAIN.finditer(text):
        pre = text[max(0, m.start() - 24):m.start()].lower().rstrip()
        if re.search(BAR_WORDS + r"\s*(?:about\s*)?$", pre):
            continue
        if re.search(r"(day|clustered|nw)$", pre) or pre.endswith("("):
            v = float(m.group(1))
            if v < 40:
                out.append(v)
    for m in MEANCI.finditer(text):
        z = z_from_mean_ci(_f(m.group(1)), _f(m.group(2)), _f(m.group(3)))
        if z is not None and abs(z) < 40:
            out.append(z)
    return out


def table_z_values(text):
    """z values from markdown table columns whose header mentions z (the last number of the cell)."""
    out = []
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("|") and re.search(r"\bz\b|z\)", ln, re.I) and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|\s*$", lines[i + 1]):
            hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
            zcols = [j for j, c in enumerate(hdr) if re.search(r"\bz\b|z\)|z$", c, re.I) and not re.search(r"bar", c, re.I)]
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                for c in zcols:
                    if c < len(cells):
                        nums = re.findall(r"[+\-\u2212]?\d+(?:\.\d+)?", cells[c].replace(",", ""))
                        if nums:
                            try:
                                v = _f(nums[-1])
                                if abs(v) < 40:
                                    out.append(v)
                            except ValueError:
                                pass
                j += 1
    return out


Z_ARTEFACT = 15.0  # a |z| this large in a result note is arithmetic on a derived quantity, not a test of an edge


def all_z(text):
    return parse_z_values(text) + table_z_values(text)


def find_verdict(text):
    """The verdict word that appears first in the heading region of the text, else the first anywhere, else unknown."""
    for src in (text[:1500], text):
        best, pos = None, None
        for v in VERDICTS:
            m = re.search(r"(?<![A-Za-z_])" + v + r"(?![A-Za-z_])", src)
            if m and (pos is None or m.start() < pos):
                best, pos = v, m.start()
        if best:
            return best
    head = text[:1500]
    if re.search(r"\bsurvives?\b", head, re.I):
        return "SURVIVES"
    if re.search(r"\bpass(?:es|ed)\b", head, re.I):
        return "PASSED"
    return "unknown"


def find_n_charged(text):
    """The N charged (tries added to the running count), or None if the text does not say."""
    m = (re.search(r"\bN\s*(?:added)?\s*[:=]?\s*\+\s*([\d,]+)", text) or re.search(r"\bN added[: ]+\s*([\d,]+)", text)
         or re.search(r"\b(\d[\d,]*) tries\b", text) or re.search(r"\b(\d[\d,]*) try\b", text))
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    if re.search(r"\bN\s*[:=]?\s*\+?0\b|\b0 tries|no try spent|N unchanged", text):
        return 0
    return None


COUNT_NOUN = r"(?:trades|entries|windows|markets|orders|games|signals|fills|closes|events|observations|months)"


def find_n(text):
    m = re.search(r"\bn\s*=\s*([\d,]{2,})", text) or re.search(r"\b(\d{1,3}(?:,\d{3})+|\d{3,})\s+" + COUNT_NOUN + r"\b", text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


PF_PAIR = re.compile(r"\bPF\w*(?:\s*\(?[^\d\n|]{0,12}\)?)?\s*[:=]?\s*\**(\d+\.\d+)\**\s*(?:/|then|and|,)\s*\**(\d+\.\d+)")
PF_ONE = re.compile(r"\bPF\w*\s*[:=]?\s*\**(\d+\.\d+)")


def find_pf(text):
    pairs = [(float(a), float(b)) for a, b in PF_PAIR.findall(text)]
    ones = [float(x) for x in PF_ONE.findall(text)]
    return pairs, ones


def holdout_status(text, verdict):
    """(read, outcome): read is yes / no / unknown; outcome is survived / failed / n.a. / unknown."""
    no = re.search(r"holdout[^.\n]{0,60}(?:not read|unread|never read)|(?:frozen third|window C|W3)[^.\n]{0,40}(?:unread|not read)|"
                   r"frozen[^.\n]{0,30}unread|holdout[^.\n]{0,40}nothing (?:passed|survived)|nothing (?:passed|survived)[^.\n]{0,60}holdout",
                   text, re.I)
    yes = re.search(r"holdout[^.\n]{0,30}(?:read once|was read|read:|PF\s*\d|failed|passed 1)|read once[^.\n]{0,40}holdout|frozen[^.\n]{0,60}read once", text, re.I)
    if no and not yes:
        return "no", "n.a."
    if yes:
        if re.search(r"holdout[^.\n]{0,80}(?:failed|FAILED|FALSIFIED|did not|void)|FAILED_GATE_HOLDOUT|1 of 2 passed", text, re.I) or verdict == "FALSIFIED":
            return "yes", "failed"
        if verdict in ("NOT_YET_FALSIFIED", "SURVIVES", "PASSED"):
            return "yes", "survived"
        return "yes", "unknown"
    if verdict in ("FALSIFIED", "NOT_ENOUGH_DATA", "NOT_RUNNABLE", "NO_WINNER", "DUPLICATE", "INFORMATION"):
        return "no", "n.a."
    return "unknown", "unknown"


def classify_lane(rid, title, text):
    if rid in LANE_OVERRIDE:
        return LANE_OVERRIDE[rid]
    blob = (title.lower() + " ") * 3 + text[:3000].lower()
    scores = {lane: sum(len(re.findall(p, blob)) for p in pats) for lane, pats in LANE_KW.items()}
    best = max(scores, key=lambda k: (scores[k], -LANES.index(k)))
    if scores[best] == 0:
        return "other"
    c, g = scores["15-minute crypto"], scores["15-minute gold"]
    if best in ("15-minute crypto", "15-minute gold") and min(c, g) >= 3 and 0.35 <= c / max(g, 1) <= 2.9:
        return "15-minute crypto+gold"
    return best


def classify_shape(title, text):
    blob = (title.lower() + " ") * 2 + text[:2000].lower()
    best, bs = "other/unclear", 0
    for name, pats in SHAPES:
        s = sum(len(re.findall(p, blob)) for p in pats)
        if s > bs:
            best, bs = name, s
    return best


def find_universe(text):
    seen = []
    for t in re.findall(r"\bKX[A-Z0-9]{2,}\b", text[:3000]):
        if t not in seen:
            seen.append(t)
    return " ".join(seen[:4])


def first_date(text):
    m = re.search(r"20\d\d-\d\d-\d\d", text)
    return m.group(0) if m else ""


def norm_id(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())


ID_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,}(?:[-_][A-Z0-9]+)*)\b")
STOP = {"AND", "THE", "FOR", "NOT", "OF", "TO", "ON", "AT", "PF", "OR", "ONE", "ALL", "NO", "IN", "US", "UTC", "CT", "N",
        "RESULT", "RESULTS", "PRE", "REGISTRATION", "DRAFT", "FALSIFIED", "FILES", "NOTE", "AMENDMENT", "INFORMATION",
        "INFRASTRUCTURE", "OWNER", "SCOPE", "STRATEGY", "CARD", "LIVE", "ANALYSE", "STATUS", "VERDICTS", "SELF", "ROUND",
        "NOT_ENOUGH_DATA", "FAMILY", "SUMMARY", "LEDGER", "CORRECTION", "ERROR", "NEW", "BTC", "ETH", "WITH", "PAPER", "BOOK",
        "ID", "OK", "PR", "PM", "AM", "II", "I", "A", "AUDIT", "FAILURE", "GOLD", "BITCOIN", "FX", "ETF", "QLD", "QQQ", "SPDR",
        "KXBTC15M", "KXETH15M", "KXGOLD15M", "SPY", "SPX", "WTI", "CPI", "PCE", "GDP", "NBA", "NFL", "MLB", "NHL"}


def ids_from_title(title):
    t = re.sub(r"^(?:Pre-registration|Preregistration|Registration and result|Registration|Registered|Results?|Strategy card|"
               r"Amendment to|Amendment|Infrastructure|DRAFT[^:]*|Information)\s*:?\s*", "", title, flags=re.I)
    t = t.split("(")[0]
    t = re.split(r",\s*L1 unchanged|\bunchanged\b", t)[0]
    t = re.split(r",\s*(?:one run|run once|read once|the |a |an |of |owner|written|fixed)|:\s|\bagainst\b|\bfor\b", t)[0]
    out, seen = [], set()
    for m in ID_RE.finditer(t):
        x = m.group(1)
        if x in STOP or len(norm_id(x)) < 2 or norm_id(x) in seen:
            continue
        seen.add(norm_id(x))
        out.append(x)
    return out[:8]


# ---------------------------------------------------------------- reading the sources


def read_readme_blocks():
    lines = open(README, encoding="utf-8").read().split("\n")
    heads = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{2,4})\s+(.*)", ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    blocks = []
    for k, (i, lvl, title) in enumerate(heads):
        j = len(lines)
        for i2, lvl2, _ in heads[k + 1:]:
            if lvl2 <= lvl:
                j = i2
                break
        blocks.append({"line": i + 1, "level": lvl, "title": title, "text": "\n".join(lines[i + 1:j])})
    # dated bold verdict lines in the early Verdicts section: "**2026-10-05: H1, ...: `FALSIFIED`.**"
    for i, ln in enumerate(lines[:2900]):
        m = re.match(r"^\*\*(20\d\d-\d\d-\d\d): (.*?)\*\*", ln)
        if m:
            j = i + 1
            while j < len(lines) and not lines[j].startswith(("**20", "## ")) and j - i < 60:
                j += 1
            blocks.append({"line": i + 1, "level": 9, "title": "Verdict " + m.group(2), "text": ln + "\n" + "\n".join(lines[i + 1:j]),
                           "bold_date": m.group(1)})
    return blocks


def is_result_block(title):
    return title.lower().startswith(("result", "verdict", "registration and result"))


def early_verdict_ids(title):
    """'Verdict 2026-10-05: H1, favourites ...: FALSIFIED.' -> ['H1']; 'X1 to X4' expands."""
    t = re.sub(r"^Verdict ", "", title)
    t = re.sub(r"^20\d\d-\d\d-\d\d:\s*", "", t)
    head = re.split(r"[:(]| ran | each | the | all |first |overnight", t)[0]
    rng = re.match(r"^\s*([A-Z]+)(\d+) to ([A-Z]+)(\d+)", head)
    if rng and rng.group(1) == rng.group(3):
        return [f"{rng.group(1)}{n}" for n in range(int(rng.group(2)), int(rng.group(4)) + 1)]
    ids = []
    for m in re.finditer(r"\b([A-Z]{1,6}\d{1,3}[A-Z]?|[A-Z]{3,}\d?)\b", head):
        if m.group(1) not in STOP:
            ids.append(m.group(1))
    return ids[:6]


def paragraphs_for(rid, text):
    """Paragraphs of the block that mention the id (used when one block reports several ids)."""
    return "\n\n".join(p for p in re.split(r"\n\s*\n", text) if re.search(r"\b" + re.escape(rid) + r"\b", p))


def build_rows():
    rows = {}

    def add(rid, source, title, text, date, multi):
        r = rows.setdefault(norm_id(rid), {"id": rid, "titles": [], "texts": [], "sources": [], "dates": [], "multi": False})
        r["titles"].append(title)
        r["texts"].append(text)
        r["sources"].append(source)
        if date:
            r["dates"].append(date)
        r["multi"] = r["multi"] or multi

    for b in read_readme_blocks():
        if b["level"] == 9:
            ids = early_verdict_ids(b["title"])
        elif is_result_block(b["title"]):
            ids = ids_from_title(b["title"])
        else:
            continue
        d = b.get("bold_date") or first_date(b["title"]) or first_date(b["text"][:400])
        for rid in ids:
            txt = b["text"] if len(ids) == 1 else (paragraphs_for(rid, b["text"]) or b["text"])
            add(rid, f"README:{b['line']}", b["title"], txt, d, len(ids) > 1)

    regs = {}
    for b in read_readme_blocks():
        if b["level"] != 9 and re.match(r"(?i)(pre-registration|registration|registered|strategy card)", b["title"]):
            for rid in ids_from_title(b["title"]):
                regs.setdefault(norm_id(rid), (rid, b["title"], b["text"], b["line"]))
    for fn in sorted(os.listdir(WORKERS)):
        m = re.match(r"^([A-Za-z0-9_]+?)_REGISTRATION\.md$", fn)
        if m:
            txt = open(os.path.join(WORKERS, fn), encoding="utf-8", errors="replace").read()
            regs.setdefault(norm_id(m.group(1)), (m.group(1), txt.split("\n", 1)[0].lstrip("# ").strip(), txt, "workers/" + fn))
    for fn in sorted(os.listdir(WORKERS)):
        m = re.match(r"^([A-Za-z0-9_]+?)_RESULT\.md$", fn)
        if not m:
            continue
        txt = open(os.path.join(WORKERS, fn), encoding="utf-8", errors="replace").read()
        add(m.group(1), "workers/" + fn, txt.split("\n", 1)[0].lstrip("# ").strip(), txt, first_date(txt[:800]), False)
    paras = re.split(r"\n\s*\n", open(README, encoding="utf-8").read())
    for key, (rid, title, txt, where) in regs.items():
        if key not in rows and not any(k.startswith(key) or key.startswith(k) for k in rows if len(k) >= 4 and len(key) >= 4):
            hits = [p for p in paras if re.search(r"(?<![A-Za-z0-9])" + re.escape(rid) + r"(?![A-Za-z0-9])", p)
                    and p[:300] != txt[:300] and re.search("|".join(VERDICTS), p)
                    and not re.match(r"(?i)\s*#+\s*(pre-registration|registration)", p)]
            if hits:
                add(rid, f"README-text:{rid}", title, "\n\n".join(hits[:4]), first_date(title) or first_date(txt[:600]), False)
                rows[key]["from_text"] = True
            else:
                add(rid, f"REG:{where}", title, txt, first_date(title) or first_date(txt[:600]), False)
                rows[key]["registration_only"] = True
    return rows


# ---------------------------------------------------------------- table assembly

OVERRIDES = {}  # hand-checked facts, keyed by norm_id; filled in the OVERRIDES section below


def make_row(key, r):
    title = " | ".join(dict.fromkeys(r["titles"]))[:200]
    text = "\n\n".join(r["texts"])
    rid = r["id"]
    zs_raw = all_z(text)
    zs = [z for z in zs_raw if abs(z) < Z_ARTEFACT]
    verdict = "unknown"
    for ti, t in zip(r["titles"], r["texts"]):
        verdict = find_verdict(ti + "\n" + t)
        if verdict != "unknown":
            break
    pairs, ones = find_pf(text)
    ho_read, ho_out = holdout_status(text, verdict)
    n_ch = find_n_charged(text)
    n = find_n(text)
    reg_only = bool(r.get("registration_only"))
    from_text = bool(r.get("from_text"))
    mention = ""
    if reg_only:
        verdict = "no result parsed"
        ho_read, ho_out = "unknown", "unknown"
    if from_text:
        # the verdict word came from a README paragraph that only mentions the id: kept as a note, not as the row's verdict
        mention, verdict = verdict, "unknown"
        ho_read, ho_out = "unknown", "unknown"
    row = {
        "level": "family",
        "confidence": "none" if reg_only else ("low" if from_text else "high"),
        "verdict_mention": mention,
        "id": rid,
        "date": min(r["dates"]) if r["dates"] else "",
        "lane": classify_lane(norm_id(rid), title, text),
        "universe": find_universe(text),
        "rule_shape": classify_shape(title, text),
        "n": "" if n is None else n,
        "n_z": len(zs),
        "n_z_dropped": len(zs_raw) - len(zs),
        "z_first": f"{zs[0]:.2f}" if zs else "",
        "z_max": f"{max(zs):.2f}" if zs else "",
        "z_min": f"{min(zs):.2f}" if zs else "",
        "pf_first": f"{pairs[0][0]:.2f}" if pairs else (f"{ones[0]:.2f}" if ones else ""),
        "pf_second": f"{pairs[0][1]:.2f}" if pairs else "",
        "pos_both_halves": ("yes" if pairs[0][0] > 1.0 and pairs[0][1] > 1.0 else "no") if pairs else "",
        "verdict": verdict,
        "holdout_read": ho_read,
        "holdout_outcome": ho_out,
        "n_charged": "" if n_ch is None else n_ch,
        "source": ";".join(dict.fromkeys(r["sources"]))[:120],
        "shared_block": "yes" if r["multi"] else "",
        "title": title,
        "_zs": zs,
    }
    row.update(OVERRIDES.get(norm_id(rid), {}))
    return row


def parse_try_rows(rid, text, lane, shape, date):
    """One row per table line that carries a z column: the registered tries/cells of a family (level 'try')."""
    out = []
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if not (ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|\s*$", lines[i + 1])):
            continue
        hdr = [c.strip() for c in ln.strip().strip("|").split("|")]
        zcols = [j for j, c in enumerate(hdr) if re.search(r"\bz\b|z\)|z$", c, re.I) and not re.search(r"bar", c, re.I)]
        if not zcols:
            continue
        vcol = next((j for j, c in enumerate(hdr) if re.search(r"verdict", c, re.I)), None)
        ncol = next((j for j, c in enumerate(hdr) if re.match(r"(?i)^(n|entries|trades|windows|markets|disc n)\b", c)), None)
        pcol = next((j for j, c in enumerate(hdr) if re.search(r"\bPF", c)), None)
        j = i + 2
        k = 0
        while j < len(lines) and lines[j].startswith("|"):
            cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
            j += 1
            k += 1
            vals = []
            for c in zcols:
                if c < len(cells):
                    nums = re.findall(r"[+\-\u2212]?\d+(?:\.\d+)?", cells[c].replace(",", ""))
                    if nums:
                        try:
                            vals.append(_f(nums[-1]))
                        except ValueError:
                            pass
            vals = [v for v in vals if abs(v) < Z_ARTEFACT]
            if not vals:
                continue
            label = re.sub(r"[*`]", "", cells[0])[:40]
            n = ""
            if ncol is not None and ncol < len(cells):
                mm = re.search(r"\d[\d,]*", cells[ncol])
                n = int(mm.group(0).replace(",", "")) if mm else ""
            pf = ""
            if pcol is not None and pcol < len(cells):
                mm = re.search(r"\d+\.\d+", cells[pcol])
                pf = mm.group(0) if mm else ""
            verdict = "unknown"
            if vcol is not None and vcol < len(cells):
                verdict = find_verdict(cells[vcol])
            out.append({"level": "try", "confidence": "high", "verdict_mention": "", "id": f"{rid}:{label}", "date": date, "lane": lane, "universe": "", "rule_shape": shape,
                        "n": n, "n_z": len(vals), "z_first": f"{vals[0]:.2f}", "z_max": f"{max(vals):.2f}", "z_min": f"{min(vals):.2f}",
                        "pf_first": pf, "pf_second": "", "pos_both_halves": "", "verdict": verdict, "holdout_read": "", "holdout_outcome": "",
                        "n_charged": "", "source": "table in " + rid, "shared_block": "", "title": "", "_zs": vals, "family": rid})
    return out


# Hand-read rows for results that sit in README prose without a "Result" heading. Each carries its README line.
MANUAL = [
    {"id": "SEARCH1", "date": "2026-10-07", "lane": "15-minute crypto+gold", "rule_shape": "generator/search", "n": 437, "z_first": "2.99",
     "z_max": "2.99", "n_z": 1, "verdict": "FALSIFIED", "holdout_read": "yes", "holdout_outcome": "failed", "n_charged": 437,
     "source": "manual:README:857", "title": "first automated rule search, 437 rules; best design z 2.99, holdout best z 1.62 (-0.90c)"},
    {"id": "OVERNIGHT", "date": "2026-10-07", "lane": "15-minute crypto+gold", "rule_shape": "generator/search", "n": 311, "z_first": "3.46",
     "z_max": "3.46", "n_z": 1, "verdict": "NOT_ENOUGH_DATA", "holdout_read": "no", "holdout_outcome": "n.a.", "n_charged": 311,
     "source": "manual:README:903", "title": "overnight search on older data, 311 rules, 4 survivors, best pooled z 3.46 (null best-of P 0.008); forward read all NOT_ENOUGH_DATA"},
    {"id": "STRATSEARCH42", "date": "2026-10-08", "lane": "15-minute crypto+gold", "rule_shape": "generator/search", "n": 41569, "z_first": "1.17",
     "z_max": "1.17", "n_z": 1, "verdict": "FALSIFIED", "holdout_read": "no", "holdout_outcome": "n.a.", "n_charged": 42,
     "source": "manual:README:1214", "title": "S01 to S42, 42 strategies, 0 survivors, best z 1.17, null best-of P 0.596; W3 holdout never read"},
    {"id": "OICORE", "date": "2026-10-29", "lane": "15-minute crypto", "rule_shape": "cheap side", "n": 555, "z_first": "4.53", "z_max": "4.53",
     "z_min": "4.42", "n_z": 2, "pf_first": "2.28", "pf_second": "1.85", "pos_both_halves": "yes", "verdict": "NOT_YET_FALSIFIED",
     "holdout_read": "no", "holdout_outcome": "n.a.", "n_charged": 1, "source": "manual:README:7728,7732",
     "title": "Bitcoin open interest core (GEN6 survivor; FALS4 reimplementation z 4.42): history windows only, no frozen holdout; forward rows running"},
    {"id": "L1", "date": "2026-10-07", "lane": "15-minute crypto+gold", "rule_shape": "favourite", "n": 1447, "z_first": "1.45", "z_max": "2.94",
     "z_min": "1.45", "n_z": 3, "pf_first": "", "pos_both_halves": "yes", "verdict": "FALSIFIED", "holdout_read": "no", "holdout_outcome": "n.a.",
     "n_charged": 1, "source": "manual:README:752,903,3389",
     "title": "L1 favourite 88c to 97c at 6 min: first run (30 days) z 1.45 FALSIFIED; older W0 z 2.68; 28 older days pooled z 3.20; 68 days z 2.52 (BTC 0.81, ETH 1.26, gold 2.94)"},
    {"id": "L1-GOLD-FIRST", "date": "2026-10-21", "lane": "15-minute gold", "rule_shape": "favourite", "n": 1397, "z_first": "2.94", "z_max": "2.94",
     "n_z": 1, "verdict": "NOT_YET_FALSIFIED", "holdout_read": "no", "holdout_outcome": "n.a.", "n_charged": 0,
     "source": "manual:README:3402,CLAUDE.md gold first",
     "title": "gold chosen as the only ladder market AFTER the 68 day split by series (z 2.94) and the first 302 live trades; selection among 3 series, charged 0"},
]


FIELDS = ["level", "confidence", "verdict_mention", "id", "date", "lane", "universe", "rule_shape", "n", "n_z", "z_first", "z_max", "z_min", "pf_first", "pf_second",
          "pos_both_halves", "verdict", "holdout_read", "holdout_outcome", "n_charged", "source", "shared_block", "title"]


def build_table():
    out = []
    for k, r in build_rows().items():
        fam = make_row(k, r)
        out.append(fam)
        if not r.get("registration_only"):
            out.extend(parse_try_rows(fam["id"], "\n\n".join(r["texts"]), fam["lane"], fam["rule_shape"], fam["date"]))
    manual_ids = {norm_id(m["id"]) for m in MANUAL}
    out = [x for x in out if not (x["level"] == "try" and norm_id(x["family"]) in manual_ids)]
    for m in MANUAL:
        row = {k: "" for k in FIELDS}
        row.update({"level": "family", "confidence": "manual", "verdict_mention": "", "universe": "", "shared_block": ""})
        row.update(m)
        row["_zs"] = [float(row["z_first"])] if row.get("z_first") else []
        out = [x for x in out if not (x["level"] == "family" and norm_id(x["id"]) == norm_id(m["id"]))]
        out.append(row)
    out.sort(key=lambda x: (x["date"] or "9999", x["id"].split(":")[0], x["level"] != "family", x["id"]))
    return out


def write_table(rows, path=TABLE):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("unknown" if (r.get(k) in ("", None) and k in ("lane", "verdict", "holdout_read")) else r.get(k, ""))
                        for k in FIELDS})


# ---------------------------------------------------------------- statistics (read the table back, never the sources)


def load_table(path=TABLE):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    for r in rows:
        r["family"] = r["id"].split(":")[0]
        for k in ("z_first", "z_max", "z_min", "pf_first", "pf_second"):
            try:
                r[k + "_f"] = float(r[k])
            except (ValueError, KeyError):
                r[k + "_f"] = None
        try:
            r["n_z_i"] = int(r["n_z"] or 0)
        except ValueError:
            r["n_z_i"] = 0
        try:
            r["n_charged_i"] = int(r["n_charged"])
        except (ValueError, KeyError):
            r["n_charged_i"] = None
    return rows


def z_units(rows):
    """One z per testable unit: the first reported z of each table cell (try row), and of each family with prose z values
    but no table. The first mention is used (not the largest) so the choice cannot select on size."""
    with_cells = {r["family"] for r in rows if r["level"] == "try"}
    units = []
    for r in rows:
        if r["z_first_f"] is None:
            continue
        if r["level"] == "try":
            units.append({"id": r["id"], "lane": r["lane"], "shape": r["rule_shape"], "z": r["z_first_f"], "kind": "cell"})
        elif r["level"] == "family" and r["confidence"] in ("high", "manual") and r["id"] not in with_cells:
            units.append({"id": r["id"], "lane": r["lane"], "shape": r["rule_shape"], "z": r["z_first_f"], "kind": "family"})
    return units


def tail_summary(zs):
    """Counts of z above 2 and 3 (and below -2, -3) against the standard normal expectation, with exact binomial p."""
    n = len(zs)
    out = {"n": n}
    for thr in (2.0, 3.0):
        k = sum(1 for z in zs if z > thr)
        pe = sf(thr)
        out[f"gt{int(thr)}"] = k
        out[f"exp_gt{int(thr)}"] = n * pe
        out[f"p_gt{int(thr)}"] = binom_sf(k, n, pe)
        kn = sum(1 for z in zs if z < -thr)
        out[f"lt-{int(thr)}"] = kn
    out["mean"] = sum(zs) / n if n else float("nan")
    out["sd"] = (sum((z - out["mean"]) ** 2 for z in zs) / (n - 1)) ** 0.5 if n > 1 else float("nan")
    out["share_pos"] = sum(1 for z in zs if z > 0) / n if n else float("nan")
    return out


def best_of_k(rows, cap=40):
    """Per family: the best reported z with k = number of z values it reported, and the p of 'best of k' under the null."""
    out = []
    for r in rows:
        if r["level"] != "family" or r["confidence"] not in ("high", "manual") or r["z_max_f"] is None:
            continue
        k = min(max(r["n_z_i"], 1), cap)
        out.append({"id": r["id"], "lane": r["lane"], "shape": r["rule_shape"], "z": r["z_max_f"], "k": k, "p": max_p(r["z_max_f"], k)})
    return out


def survival(rows):
    fam = [r for r in rows if r["level"] == "family"]
    pos = [r for r in fam if r["pos_both_halves"] == "yes"]
    read = [r for r in pos if r["holdout_read"] == "yes"]
    surv = [r for r in read if r["holdout_outcome"] == "survived"]
    return fam, pos, read, surv


def per_lane(rows, units):
    fam = [r for r in rows if r["level"] == "family"]
    out = {}
    for lane in sorted({r["lane"] for r in fam}):
        fr = [r for r in fam if r["lane"] == lane]
        zu = [u["z"] for u in units if u["lane"] == lane]
        zmax = [u["z"] for u in units if u["lane"] == lane]
        nyf = sum(1 for r in fr if r["verdict"] == "NOT_YET_FALSIFIED")
        out[lane] = {"families": len(fr), "cells": len(zu), "gt2": sum(1 for z in zu if z > 2), "gt3": sum(1 for z in zu if z > 3),
                     "best_z": max(zmax) if zmax else None, "not_yet_falsified": nyf,
                     "holdout_survivors": sum(1 for r in fr if r["holdout_read"] == "yes" and r["holdout_outcome"] == "survived"),
                     "n_charged": sum(r["n_charged_i"] or 0 for r in fr)}
    return out


# Contracts traded in the last 69 days by Kalshi category, from the 2026-10-20 census in README.md (daily series); the
# 15 minute and hourly lanes are not in it. Used only to rank how thin the coverage is, never as a result.
CENSUS_MILLIONS = {"weather": 165.0, "economics/macro": 61.0, "daily/weekly ladders": 27.0, "politics": 15.0, "sports": 9.0}


def untested_ranking(lane_stats):
    rank = []
    for lane, mil in CENSUS_MILLIONS.items():
        st = lane_stats.get(lane, {"families": 0})
        rank.append((mil / max(st["families"], 0.5), lane, mil, st["families"]))
    rank.sort(reverse=True)
    return rank


def clean_units(units):
    """Drop z values the README itself calls artefacts or information: USWEEP1 zero-variance cells (z 5 to 22, 'a statistic
    artefact'), and pooled / information-only rows ('not a try')."""
    out = []
    for u in units:
        fam = u["id"].split(":")[0]
        label = u["id"].lower()
        if fam == "USWEEP1" and u["z"] >= 5.0:
            continue
        if "information" in label or "pooled" in label:
            continue
        out.append(u)
    return out


def collapse_by_family(units):
    """One unit per family: its first one in table order. Removes the dependence between cells of one family
    (GEN6's thirteen survivors are one bet, a table's slices share trades)."""
    seen, out = set(), []
    for u in units:
        fam = u["id"].split(":")[0]
        if fam in seen:
            continue
        seen.add(fam)
        out.append(u)
    return out


def tail_balance(zs, thr):
    """Sign test on the two tails at +/- thr: under symmetric noise, right and left tail counts are Binomial(r + l, 0.5).
    Net-of-cost z values drift negative, so this is conservative against finding positive enrichment."""
    r = sum(1 for z in zs if z > thr)
    l = sum(1 for z in zs if z < -thr)
    return r, l, binom_sf(r, r + l, 0.5) if r + l else 1.0


# Hand-read provenance of the candidates that passed their development windows (positive in both halves or passed the
# pre-set validation gate), with what happened in the next out-of-sample read. Every line is from README.md or workers/.
DEV_PASSES = [
    # id, registered, development result, next out-of-sample read, outcome, source
    ("L1", "2026-10-07", "first 30 days z 1.45 (halves +0.71c/+1.22c) below the 2.1 bar", "no frozen holdout; backward windows read later: W0 z 2.68, 28 older days z 3.20, 68 days z 2.52", "persisting, thin; live", "README 752, 903, 3389"),
    ("OVERNIGHT survivors (4)", "2026-10-07", "pooled z 3.46 over 311 rules (null best-of P 0.008)", "forward check 2026-10-08", "all NOT_ENOUGH_DATA, later outcome not located", "README 903, 1010"),
    ("E3 XRP, Dogecoin", "2026-10-13", "z 2.37 and 2.97 on 41 days, halves positive", "E3B backward holdout, 29 days: pooled z 3.97", "SURVIVED the holdout; E3F forward unread; live XRP paused 2026-10-28 (PF 0.49 over 65 fills)", "README 3187, 3316, 7734"),
    ("L1B Ethereum, gold", "2026-10-13", "older 28 days z 2.24 and 2.73", "none frozen; live", "live; gold kept (z 2.94 over 68 days), Ethereum capped", "README 3389"),
    ("PERP1", "2026-10-21", "z 2.76 over 17 years", "none; 2022 on is 0.00%", "decayed: edge lives in 2017 to 2021", "README 3962"),
    ("FEAT2", "2026-10-22", "kept set z 3.85, halves +1.34c/+0.73c", "FEAT2-F forward, dated", "unresolved; monthly gain shrinking 1.46c, 0.90c, 0.61c", "README 5286"),
    ("GEN3-H1 (hourly ladder)", "2026-10-29", "validation z 5.66 vs bar 5.17", "frozen holdout passed 1 of 2", "VOID: universe look-ahead; CORR1 FALSIFIED on a clean file", "README 7403, 7487"),
    ("OICORE (GEN6 core)", "2026-10-29", "PF 2.28 / 1.85, z 4.53 (FALS4 4.42) vs bar about 5.2", "no frozen holdout; forward rows running", "unresolved; NOT_YET_FALSIFIED; counterparty unnamed", "README 7728, 7732"),
    ("GEN7 B01, B02", "2026-10-29", "PF 3.28/1.80 and 1.75/1.71", "forward ledger", "not independent of OICORE", "README 7736"),
]

# Live strategies: N already charged before their evidence existed, and the deflated bar then.
PROVENANCE = {
    "L1": {"prior_tries_in_ledger": "8 hypotheses plus a 437 rule search before its first run (11 hypotheses with L1, L2, L3)",
           "n_at_selection": 448, "bar": "2.1 (single try, undeflated)",
           "note": "first run z 1.45 failed its own bar; kept on later backward windows and the live record; gold-first chosen after a split of 3 series (z 2.94)"},
    "OICORE": {"prior_tries_in_ledger": "about 501,174 before GEN6; GEN6 charged 62,163 (13 survivors of 128 that passed discovery, of 5,000 distinct Bitcoin strategies)",
               "n_at_selection": 563337, "bar": "about 5.2 deflated",
               "note": "the core is one of the 13; its validation z 4.53 (FALS4 4.42) is below the bar"},
}


def report(path=TABLE):
    rows = load_table(path)
    units = z_units(rows)
    zs = [u["z"] for u in units]
    cu = clean_units(units)
    fu = collapse_by_family(cu)
    for name, sample in (("all cells", units), ("clean cells", cu), ("one per family, clean", fu)):
        zz = [u["z"] for u in sample]
        t = tail_summary(zz)
        print(f"[{name}] n={t['n']} gt2={t['gt2']} (exp {t['exp_gt2']:.1f}) gt3={t['gt3']} (exp {t['exp_gt3']:.2f}) lt-2={t['lt-2']} lt-3={t['lt-3']} "
              f"mean={t['mean']:+.2f} sd={t['sd']:.2f} share_pos={t['share_pos']:.2f}", "tails+-2", tail_balance(zz, 2.0), "tails+-3", tail_balance(zz, 3.0))
    print("rows:", len(rows), "families:", sum(r["level"] == "family" for r in rows), "cells:", sum(r["level"] == "try" for r in rows))
    print("overall", tail_summary(zs))
    for key in ("lane", "shape"):
        print("-- by", key)
        for g in sorted({u[key] for u in units}):
            zz = [u["z"] for u in cu if u[key] == g]
            if not zz:
                continue
            t = tail_summary(zz)
            print(f"{g:28s} n={t['n']:4d} gt2={t['gt2']:3d} (exp {t['exp_gt2']:.1f}, p {t['p_gt2']:.3f}) gt3={t['gt3']:3d} (exp {t['exp_gt3']:.2f}) "
                  f"lt-2={t['lt-2']:3d} lt-3={t['lt-3']:3d} mean={t['mean']:+.2f} tailsign_p={tail_balance(zz, 2.0)[2]:.3f}")
    bk = best_of_k(rows)
    ps = [b["p"] for b in bk]
    print("best-of-k families:", len(bk), "p<0.05:", sum(p < 0.05 for p in ps), "expected", 0.05 * len(bk), "fisher", fisher_combined(ps)[2],
          "pcurve", pcurve_right_skew(ps))
    fam, pos, read, surv = survival(rows)
    print("families", len(fam), "pos both halves", len(pos), "holdout read", len(read), "survived", len(surv), [r["id"] for r in surv])
    ls = per_lane(rows, cu)
    for lane, v in ls.items():
        print(lane, v)
    print(untested_ranking(ls))




if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "table"
    if cmd == "table":
        t = build_table()
        write_table(t)
        print(len(t), "rows ->", TABLE)
    elif cmd == "report":
        report()
