"""Load the Philadelphia Fed series snapshot distributed by FRED into SQLite."""
import hashlib
from pathlib import Path
import sqlite3
from tempfile import NamedTemporaryFile

import pandas as pd

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "data/fred_snapshot.csv"
DATABASE = ROOT / "data/portfolio.sqlite"
SERIES = ("RCCCBBALTOT", "RCCCBBALDPD30P", "RCCCBNCOPCT")
SOURCE = "https://fred.stlouisfed.org/release?rid=447"


def sql(name):
    return (ROOT / "sql" / f"{name}.sql").read_text(encoding="utf-8")


def load_snapshot(path=SNAPSHOT, database=DATABASE):
    data = pd.read_csv(path, dtype="string", keep_default_na=False)
    if tuple(data.columns) != ("DATE", *SERIES):
        raise ValueError("Unexpected headers. Supply DATE and the three documented FRED series IDs.")
    if data.empty or not data["DATE"].str.fullmatch(r"\d{4}-(01|04|07|10)-01").all():
        raise ValueError("Dates must mark calendar-quarter starts in YYYY-MM-DD format.")
    dates = pd.to_datetime(data.pop("DATE"), format="%Y-%m-%d")
    data["quarter_id"] = dates.dt.year * 4 + dates.dt.quarter - 1
    long = data.melt(id_vars="quarter_id", var_name="series", value_name="value")
    if long.duplicated(["quarter_id", "series"]).any():
        raise ValueError("Duplicate quarter and series in input.")
    numbers = pd.to_numeric(long["value"].str.strip().replace({"": pd.NA, ".": pd.NA}), errors="raise")
    if numbers.isin([float("inf"), float("-inf")]).any():
        raise ValueError("Infinite values are invalid.")
    rows = [
        (int(q), series, None if pd.isna(value) else float(value))
        for (q, series), value in zip(long[["quarter_id", "series"]].itertuples(index=False, name=None), numbers)
    ]
    if not any(q >= 2022 * 4 and value is not None for q, _, value in rows):
        raise ValueError("No observed values in the dashboard period.")
    database.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=database.parent, suffix=".sqlite", delete=False) as temporary:
        staging = Path(temporary.name)
    try:
        connection = sqlite3.connect(staging)
        try:
            connection.executescript(sql("schema") + sql("quarterly"))
            with connection:
                connection.executemany("INSERT INTO observation VALUES (?, ?, ?)", rows)
                connection.execute("INSERT INTO source VALUES (?, ?, ?)", (
                    SOURCE, path.name, hashlib.sha256(path.read_bytes()).hexdigest(),
                ))
        finally:
            connection.close()
        staging.replace(database)
    finally:
        staging.unlink(missing_ok=True)
    return len(rows)


if __name__ == "__main__":
    print(f"Imported {load_snapshot()} quarter-series rows into {DATABASE}")
