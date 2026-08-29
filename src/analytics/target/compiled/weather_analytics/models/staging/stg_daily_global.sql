

SELECT *
FROM read_parquet('s3://weather-data-bucket/gold/daily_global/**/*.parquet')