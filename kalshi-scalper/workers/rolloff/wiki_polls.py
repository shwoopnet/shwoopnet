#!/usr/bin/env python3
"""Turn the wikitext of "Opinion polling on the second Trump presidency" (Wikimedia REST API,
source field saved to a file) into polls.csv for rolloff_proxy.py. Mechanical: the monthly
tables under "Nationwide job approval ratings", one row per poll, field END date from the
Date cell and the year from the section heading. Rows it cannot read are counted, not guessed.

Usage: python3 wiki_polls.py page.wikitext polls.csv
"""
import csv
import re
import sys
from datetime import date

MONTHS = {m: i + 1 for i, m in enumerate("January February March April May June July August September October November December".split())}


def cell(text):
    text = text.strip()
    if "|" in text and not text.startswith("["):
        head, _, tail = text.partition("|")
        if "=" in head:          # a style prefix such as style="..." | 63%
            text = tail.strip()
    return text


def plain(text):
    text = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.S)
    m = re.match(r"\[\S+\s+(.*?)\]", text)            # [url label]
    if m:
        text = m.group(1)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)   # [[page|label]]
    return re.sub(r"\s+", " ", text.replace("'''", "").replace("''", "")).strip()


def end_date(text, sec_month, sec_year):
    text = plain(text).replace("–", "-").replace("—", "-")
    last = text.split("-")[-1].strip()
    m = re.match(r"(?:([A-Z][a-z]+)\s+)?(\d{1,2})(?:,\s*(\d{4}))?$", last)
    if not m:
        return None
    month = MONTHS.get(m.group(1) or "", None)
    if month is None:
        first = re.match(r"([A-Z][a-z]+)", text)
        month = MONTHS.get(first.group(1)) if first else None
    if month is None:
        return None
    year = int(m.group(3)) if m.group(3) else sec_year
    if not m.group(3) and month == 1 and sec_month == 12:
        year += 1
    if not m.group(3) and month == 12 and sec_month == 1:
        year -= 1
    try:
        return date(year, month, int(m.group(2)))
    except ValueError:
        return None


def pct(text):
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", plain(text))
    return float(m.group(1)) if m else None


def main():
    src = open(sys.argv[1], encoding="utf-8").read()
    a = re.search(r"^==\s*Nationwide job approval ratings", src, flags=re.M).start()
    b = re.search(r"^===\s*Approval of transition as president-elect", src, flags=re.M).start()
    body = src[a:b]
    parts = re.split(r"^====\s*([A-Z][a-z]+) (\d{4})\s*====\s*$", body, flags=re.M)
    rows, bad = [], 0
    for i in range(1, len(parts), 3):
        mon, year, text = MONTHS.get(parts[i]), int(parts[i + 1]), parts[i + 2]
        if mon is None:
            continue
        table = text[text.find("{|"):text.find("|}")]
        for chunk in table.split("\n|-")[1:]:
            cells = [cell(c[1:]) for c in chunk.split("\n") if c.startswith("|") and not c.startswith("|+")]
            if len(cells) < 6:
                continue
            end, ap, dis = end_date(cells[1], mon, year), pct(cells[4]), pct(cells[5])
            if end is None or ap is None or dis is None:
                bad += 1
                continue
            rows.append([plain(cells[0]), "", end.isoformat(), ap, dis])
    with open(sys.argv[2], "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pollster", "start", "end", "approve", "disapprove"])
        w.writerows(rows)
    print(f"polls written {len(rows)} | rows not readable {bad}")


if __name__ == "__main__":
    main()
