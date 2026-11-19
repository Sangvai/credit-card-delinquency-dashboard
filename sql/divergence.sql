SELECT quarter, balances_qoq AS balance_growth_pct,
       delinquency_qoq AS delinquency_change_pp,
       CASE WHEN balances_qoq > 0 THEN 'Balances up, delinquency down'
            ELSE 'Balances down, delinquency up' END AS direction
FROM quarterly
WHERE (balances_qoq > 0 AND delinquency_qoq < 0)
   OR (balances_qoq < 0 AND delinquency_qoq > 0)
ORDER BY quarter_id;
