
  
  create view "weather_analytics"."main"."stg_daily_regional__dbt_tmp" as (
    

SELECT *
FROM read_parquet('s3://weather-data-bucket/gold/daily_regional/**/*.parquet')
  );
