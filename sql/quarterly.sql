CREATE VIEW quarterly AS
WITH levels AS (
    SELECT quarter_id,
           MAX(CASE WHEN series = 'RCCCBBALTOT' THEN value END) AS balances,
           MAX(CASE WHEN series = 'RCCCBBALDPD30P' THEN value END) AS delinquency,
           MAX(CASE WHEN series = 'RCCCBNCOPCT' THEN value END) AS charge_off
    FROM observation
    GROUP BY quarter_id
)
SELECT c.quarter_id,
       printf('%04d Q%d', c.quarter_id / 4, c.quarter_id % 4 + 1) AS quarter,
       c.balances, c.delinquency, c.charge_off,
       100.0 * (c.balances - p.balances) / NULLIF(p.balances, 0) AS balances_qoq,
       100.0 * (c.balances - y.balances) / NULLIF(y.balances, 0) AS balances_yoy,
       c.delinquency - p.delinquency AS delinquency_qoq,
       c.delinquency - y.delinquency AS delinquency_yoy,
       c.charge_off - p.charge_off AS charge_off_qoq,
       c.charge_off - y.charge_off AS charge_off_yoy
FROM levels c
LEFT JOIN levels p ON p.quarter_id = c.quarter_id - 1
LEFT JOIN levels y ON y.quarter_id = c.quarter_id - 4
WHERE c.quarter_id >= 2022 * 4;
