"""Where the research data lives: one SQLite file filled by `scalper.backfill`."""
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB = DATA_DIR / "book.sqlite"
