-- ====================================================================
-- Production SQL Scripts - Day 2 Deliverables (Analytical Use Cases)
-- ====================================================================

-- Query 1: Calculate the rolling 30-day average NAV for each mutual fund scheme
-- Purpose: Evaluate asset smooth trendlines filtering out baseline volatility.
SELECT 
    f.amfi_code,
    d.full_date,
    n.nav,
    AVG(n.nav) OVER (
        PARTITION BY n.fund_id 
        ORDER BY d.full_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS rolling_30_day_avg_nav
FROM fact_nav_relational n
JOIN dim_fund f ON n.fund_id = f.fund_id
JOIN dim_date d ON n.date_id = d.date_id
ORDER BY f.amfi_code, d.full_date;


-- Query 2: Identify the top 5 schemes with the highest total transaction amounts
-- Purpose: Isolate liquidity trends and identify institutional investment scale preferences.
SELECT 
    f.amfi_code,
    COUNT(t.transaction_id) AS total_transactions_count,
    SUM(t.amount_inr) AS total_transaction_volume_inr
FROM fact_transactions_relational t
JOIN dim_fund f ON t.fund_id = f.fund_id
GROUP BY f.fund_id
ORDER BY total_transaction_volume_inr DESC
LIMIT 5;


-- Query 3: Segregate schemes based on expense ratio ranges and flag risk profiles
-- Purpose: Classify portfolio risk thresholds based on expense efficiency metrics.
SELECT 
    f.amfi_code,
    p.expense_ratio_pct,
    CASE 
        WHEN p.expense_ratio_pct < 0.5 THEN 'Low Expense / High Efficiency'
        WHEN p.expense_ratio_pct BETWEEN 0.5 AND 1.5 THEN 'Moderate / Industry Standard'
        ELSE 'High Expense Overheads'
    END AS expense_efficiency_tier,
    CASE 
        WHEN p.expense_ratio_anomaly = 1 THEN 'Flagged Anomaly (Investigate)'
        ELSE 'Compliant Regular'
    END AS structural_compliance_status
FROM fact_performance_relational p
JOIN dim_fund f ON p.fund_id = f.fund_id
ORDER BY p.expense_ratio_pct DESC;