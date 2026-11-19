"""Print the SQL analysis without launching Streamlit."""
from contextlib import closing
import sqlite3

import pandas as pd

from import_data import DATABASE, sql


if __name__ == "__main__":
    if not DATABASE.exists():
        raise SystemExit("Run python import_data.py first.")
    with closing(sqlite3.connect(DATABASE)) as connection:
        for name in ("since_2022", "latest", "divergence"):
            print(f"\n{name}")
            print(pd.read_sql_query(sql(name), connection).round(4).to_string(index=False))
