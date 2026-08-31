
    

    create  table
      "weather_analytics"."main"."mart_global_hottest_days__dbt_tmp"
  
    
    as (
      

WITH ranked_locations_by_temperature AS (
    SELECT 
        ROUND(longitude, 0) as rlongitude, 
        ROUND(latitude, 0) as rlatitude, 
        date_trunc('day', date) AS day, 
        ROUND(MAX(temperature_2m_max), 2) AS tmp_max, 
        ROW_NUMBER() OVER (
            PARTITION BY ROUND(longitude, 0), ROUND(latitude, 0) 
            ORDER BY MAX(temperature_2m_max) DESC
        ) AS rnk
    FROM daily_global
    WHERE temperature_2m_max >= 45 -- mandatory threshold to adjust (else OOM)
    GROUP BY rlongitude, rlatitude, day
)

SELECT 
    rlongitude, 
    rlatitude, 
    day, 
    tmp_max, 
    rnk as rank
FROM ranked_locations_by_temperature
WHERE rnk <= 1 -- Top N hottest day PER LOCATION
ORDER BY rnk ASC, tmp_max DESC
    );
    
  