
  
  create view "weather_analytics"."main"."stg_daily_global__dbt_tmp" as (
    

SELECT *
FROM read_parquet('s3://weather-data-bucket/gold/daily_global/**/*.parquet')
  );
