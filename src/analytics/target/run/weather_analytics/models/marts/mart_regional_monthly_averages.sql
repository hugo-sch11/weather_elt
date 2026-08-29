
    

    create  table
      "weather_analytics"."main"."mart_regional_monthly_averages__dbt_tmp"
  
    
    as (
      

SELECT 
    region,
    date_trunc('month', date) AS month,
    ROUND(AVG(temp_mean), 2) AS tmp_avg,
    ROUND(MAX(temp_max), 2) AS tmp_max,
    COUNT(*) AS days_in_month
FROM "weather_analytics"."main"."stg_daily_regional"
GROUP BY region, month
ORDER BY month, tmp_avg
    );
    
  