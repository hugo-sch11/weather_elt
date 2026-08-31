{{ config(materialized='table') }}

SELECT 
    region,
    date_trunc('month', date) AS month,
    ROUND(AVG(temp_mean), 2) AS tmp_avg,
    ROUND(MAX(temp_max), 2) AS tmp_max,
    COUNT(*) AS days_in_month
FROM {{ ref('stg_daily_regional') }}
GROUP BY region, month
ORDER BY month, tmp_avg

