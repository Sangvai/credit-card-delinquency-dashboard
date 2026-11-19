WITH baseline AS (
    SELECT * FROM quarterly WHERE quarter_id = 2022 * 4
), latest AS (
    SELECT * FROM quarterly ORDER BY quarter_id DESC LIMIT 1
)
SELECT baseline.quarter AS start_quarter, latest.quarter AS end_quarter,
       baseline.balances AS start_balances, latest.balances AS end_balances,
       100.0 * (latest.balances - baseline.balances) / NULLIF(baseline.balances, 0) AS balance_growth_pct,
       baseline.delinquency AS start_delinquency, latest.delinquency AS end_delinquency,
       latest.delinquency - baseline.delinquency AS delinquency_change_pp,
       baseline.charge_off AS start_charge_off, latest.charge_off AS end_charge_off,
       latest.charge_off - baseline.charge_off AS charge_off_change_pp
FROM baseline CROSS JOIN latest;
