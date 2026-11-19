"""Validate the latest SQL comparisons against published FRED values."""
from contextlib import closing
from math import isclose
import sqlite3

from import_data import DATABASE, sql

expected = {
    "2026 Q2": (978.09, 2.99, 5.01),
    "2026 Q1": (955.52, 3.29, 5.19),
    "2025 Q2": (946.42, 3.14, 5.31),
}

with closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True)) as connection:
    connection.row_factory = sqlite3.Row
    for quarter, levels in expected.items():
        row = connection.execute(
            "SELECT balances, delinquency, charge_off FROM quarterly WHERE quarter = ?",
            (quarter,),
        ).fetchone()
        assert row is not None and tuple(row) == levels, quarter
    latest = connection.execute(sql("latest")).fetchone()
    assert latest["quarter"] == "2026 Q2"
    balance, risk, charge_off = expected["2026 Q2"]
    for comparison, quarter in (("qoq", "2026 Q1"), ("yoy", "2025 Q2")):
        prior_balance, prior_risk, prior_charge_off = expected[quarter]
        for metric, delta in {
            "balances": (balance - prior_balance) / prior_balance * 100,
            "delinquency": risk - prior_risk,
            "charge_off": charge_off - prior_charge_off,
        }.items():
            assert isclose(latest[f"{metric}_{comparison}"], delta, abs_tol=1e-10)

with closing(sqlite3.connect(":memory:")) as connection:
    connection.executescript(sql("schema") + sql("quarterly"))
    connection.executemany(
        "INSERT INTO observation VALUES (?, 'RCCCBBALTOT', ?)",
        [(8088, 0), (8089, 50), (8092, 100)],
    )
    query = "SELECT balances_qoq, balances_yoy FROM quarterly WHERE quarter_id = 8092"
    assert connection.execute(query).fetchone() == (None, None)
    connection.execute("UPDATE observation SET value = 80 WHERE quarter_id = 8088")
    assert connection.execute(query).fetchone() == (None, 25)

print("Verified nine source values, six SQL deltas, missing-quarter alignment, and zero denominators.")
