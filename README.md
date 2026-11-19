# Credit Card Delinquency Trends Dashboard

SQL and Streamlit analysis of U.S. large-bank consumer credit card balances and risk, covering 2022 Q1 through 2026 Q2. Four 2021 quarters support prior-period comparisons.

## Run locally

Use Python 3.13. From the project folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe import_data.py
.\.venv\Scripts\python.exe analyze.py
.\.venv\Scripts\python.exe verify.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The date filter updates the charts and table. The KPI cards stay on the latest quarter.

## Data

The [Philadelphia Fed FR Y-14M release](https://www.philadelphiafed.org/surveys-and-data/large-bank-credit-card-and-mortgage-data) lists a [2026 Q2 Credit Card Balances CSV](https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/Y14/2026/Q2/26Q2-CreditCardBalances.csv). The direct download was inaccessible during setup. To retain it for reconciliation, save it as `data/credit_card_balances.csv`. The importer uses `data/fred_snapshot.csv`, a merged snapshot of the same Philadelphia Fed series from the official FRED tables, retrieved November 19, 2026. FRED uses quarter-start dates as labels for the observations.

| FRED series | Original unit | Definition |
| --- | --- | --- |
| [RCCCBBALTOT](https://fred.stlouisfed.org/data/RCCCBBALTOT) | Billions of U.S. dollars | Outstanding consumer credit card balances at quarter end |
| [RCCCBBALDPD30P](https://fred.stlouisfed.org/data/RCCCBBALDPD30P) | Percent | Share of outstanding balances flagged 30 or more days past due |
| [RCCCBNCOPCT](https://fred.stlouisfed.org/data/RCCCBNCOPCT) | Percent, annualized | Four times quarterly net charge-offs divided by the three-month average outstanding balance |

See the [official definitions](https://www.philadelphiafed.org/surveys-and-data/y14-definitions) and [methodology](https://www.philadelphiafed.org/surveys-and-data/y14-methodology). These aggregates cover the FR Y-14M large-bank reporting panel and are not seasonally adjusted. Panel composition and historical observations can change between releases.

## SQL and findings

The importer rejects duplicate quarter-series keys and preserves missing observations as SQL NULL. A CTE in `sql/quarterly.sql` pivots the three series and joins by exact calendar-quarter offsets of one and four. Balance growth is a percent change. Rate changes are percentage points. Missing comparisons or zero starting balances yield NULL.

1. From 2022 Q1 to 2026 Q2, balances rose from $679.97B to $978.09B (+43.84%). Delinquency rose from 1.85% to 2.99% and net charge-offs rose from 2.28% to 5.01%.
2. In 2026 Q2, balances grew while both rates fell on a QoQ and YoY basis. Balances rose with falling delinquency in five quarters and fell with rising delinquency in three quarters. Run `analyze.py` for the full list.

| Latest-quarter metric | 2026 Q2 | QoQ | YoY |
| --- | ---: | ---: | ---: |
| Total balances | $978.09B | +2.36% | +3.35% |
| 30+ days past due | 2.99% | −0.30 pp | −0.15 pp |
| Annualized net charge-off rate | 5.01% | −0.18 pp | −0.30 pp |

Track both risk rates alongside balance growth across subsequent releases. Compare the same quarters across years to account for recurring seasonal patterns and review whether the latest declines persist.

## Verification and deployment

The source check compares nine levels and all six latest deltas with published FRED observations. For example, (978.09 − 955.52) / 955.52 × 100 = 2.36% after rounding. The Streamlit test checked the KPI values, both chart elements, and a slider change from the full range to 2024. The direct Philadelphia Fed CSV and browser rendering remain unverified.

For Streamlit Community Cloud, choose Python 3.13 and `app.py` as the entry point. Include the bundled FRED snapshot in the repository. The app builds its local database on first run.
