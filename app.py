from contextlib import closing
import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

from import_data import DATABASE, load_snapshot, sql

st.set_page_config(page_title="Credit Card Delinquency Trends Dashboard", layout="wide")

# Community Cloud can initialize from the checked-in snapshot on its first run.
if not DATABASE.exists():
    load_snapshot()

with closing(sqlite3.connect(DATABASE)) as connection:
    data = pd.read_sql_query(sql("dashboard"), connection)
    latest = pd.read_sql_query(sql("latest"), connection).iloc[0]

st.title("Credit Card Delinquency Trends Dashboard")
st.caption("U.S. large-bank consumer credit cards · Quarterly · Not seasonally adjusted")
st.subheader(f"Latest available quarter · {latest.quarter}")

metrics = {
    "balances": ("Total Balances", "USD billions", "%"),
    "delinquency": ("Balances 30+ Days Past Due", "%", " pp"),
    "charge_off": ("Net Charge-Off Rate", "% annualized", " pp"),
}
table_labels = {"quarter": "Quarter"}
for column, (key, (label, unit, delta_unit)) in zip(st.columns(3), metrics.items()):
    value = latest[key]
    current = "—" if pd.isna(value) else (
        f"${value:,.2f}B" if key == "balances" else f"{value:.2f}%"
    )
    comparisons = {}
    for period in ("qoq", "yoy"):
        delta = latest[f"{key}_{period}"]
        comparisons[period] = "—" if pd.isna(delta) else f"{delta:+.2f}{delta_unit}"
        table_labels[f"{key}_{period}"] = f"{label} {period.upper()} ({delta_unit.strip()})"
    column.metric(label, current)
    column.caption(f"QoQ {comparisons['qoq']} · YoY {comparisons['yoy']}")
    table_labels[key] = f"{label} ({unit})"

# Include missing calendar quarters in charts so lines can show gaps.
quarters = range(int(data.quarter_id.min()), int(data.quarter_id.max()) + 1)
data = data.set_index("quarter_id").reindex(quarters)
data["quarter"] = [f"{q // 4} Q{q % 4 + 1}" for q in quarters]
labels = data.quarter.tolist()
if len(labels) > 1:
    start, end = st.select_slider("Quarter range", options=labels, value=(labels[0], labels[-1]))
else:
    start = end = labels[0]
view = data[data.quarter.between(start, end)]
left, right = st.columns(2)
for container, title, keys, axis in (
    (left, "Outstanding balance trend", ["balances"], "USD billions"),
    (right, "Credit risk trends", ["delinquency", "charge_off"], "Percent"),
):
    container.subheader(title)
    labels_by_key = {key: metrics[key][0] for key in keys}
    chart_data = view[["quarter", *keys]].rename(columns=labels_by_key).melt(
        id_vars="quarter", var_name="Series", value_name="Value"
    )
    chart = alt.Chart(chart_data).mark_line(point=True, invalid="break-paths-show-domains").encode(
        x=alt.X("quarter:O", title="Quarter", sort=view.quarter.tolist(), axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("Value:Q", title=axis),
        tooltip=[alt.Tooltip("quarter:O", title="Quarter"), "Series:N", alt.Tooltip("Value:Q", format=".2f")],
    )
    if len(keys) > 1:
        chart = chart.encode(color=alt.Color("Series:N", legend=alt.Legend(orient="bottom")))
    container.altair_chart(chart, width="stretch")

st.subheader("Quarterly comparisons")
st.caption("Balance changes are percent growth. Rate changes are percentage points. Blank cells indicate unavailable observations or comparisons.")
st.dataframe(
    view[list(table_labels)].rename(columns=table_labels).iloc[::-1].round(2),
    hide_index=True, width="stretch",
)

with st.expander("Source and metric definitions"):
    st.markdown("""
- **Total Balances** is outstanding consumer credit card balances for the reporting panel at quarter end.
- **Balances 30+ Days Past Due** is the share of total outstanding balances flagged 30 or more days past due.
- **Net Charge-Off Rate** is four times quarterly gross charge-offs less recoveries, divided by the quarter’s three-month average outstanding balance.
- **Source** is the [Philadelphia Fed FR Y-14M release](https://www.philadelphiafed.org/surveys-and-data/large-bank-credit-card-and-mortgage-data), via a [FRED snapshot](https://fred.stlouisfed.org/release?rid=447). See the [variable definitions](https://www.philadelphiafed.org/surveys-and-data/y14-definitions).
""")
