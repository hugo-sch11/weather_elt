import duckdb
import time
from src.config.settings import settings


LOCAL_DB_PATH = "/mnt/storage/container/weather_analytics.duckdb"

# Queries can be extended to all quantitatives variables
queries = {
########## INTROSPECTION ########## 
#     "describe_view_dg": f"""
#         DESCRIBE daily_global
#     """,
#     "describe_view_dr": f"""
#         DESCRIBE daily_regional
#     """,
#     "summarize_view_dg": f"""
#         SUMMARIZE daily_global
#     """,
#     "summarize_view_dr": f"""
#         SUMMARIZE daily_regional
#     """,
##    "view_dr_regions": f"""
##        SELECT region
##        FROM daily_regional
##        GROUP BY region
##    """,
########## DESCRIPTIVE ########## 
#     "daily_regional_temperature_trend": f"""
#         SELECT 
#             region,
#             date_trunc('day', date) AS day,
#             temp_mean AS tmp_mean
#         FROM daily_regional
#         ORDER BY day
#     """,
#     "monthly_regional_averages": f"""
#         SELECT 
#             region,
#             date_trunc('month', date) AS month,
#             ROUND(AVG(temp_mean),2) AS tmp_avg
#         FROM daily_regional
#         GROUP BY region, month
#         ORDER BY month, tmp_avg
#     """,
#     "hottest_days_per_region": f"""
#         SELECT region, day, tmp_max, rnk as rank
#         FROM (
#             SELECT 
#                 region,
#                 date_trunc('day', date) AS day,
#                 ROUND(MAX(temp_max), 2) AS tmp_max,
#                 ROW_NUMBER() OVER (
#                     PARTITION BY region ORDER BY MAX(temp_MAX) DESC
#                 ) AS rnk
#             FROM daily_regional
#             GROUP BY region, day
#         ) ranked
#         WHERE rnk <= 50 -- Top N hottest day PER REGION
#         ORDER BY rnk ASC, tmp_max DESC
#     """,
    "hottest_day_precise_location": f"""
        SELECT rlongitude, rlatitude, day, tmp_max, rnk as rank
        FROM (
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
        ) ranked
        WHERE rnk <= 1 -- Top N hottest day PER LOCATION
        ORDER BY rnk ASC, tmp_max DESC
    """,
########## COMPARATIVE ########## 
#     "compare_regions_over_time": f"""
#         SELECT 
#             date_trunc('day', date) AS day,
#             region,
#             ROUND(AVG(temp_mean), 2) AS tmp_avg
#         FROM daily_regional
#         GROUP BY day, region
#         ORDER BY day, region
#     """,
########## ROLLING ########## 
#     "7d_rolling_average": f"""
#         SELECT
#             region,
#             date_trunc('day', date) AS day,
#             ROUND(temp_mean, 2) AS tmp_mean,
#             ROUND(AVG(temp_mean) OVER(
#                 PARTITION BY region
#                 ORDER BY day
#                 ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
#             ), 2) AS tmp_avg_rolling_7d
#         FROM daily_regional
#         ORDER BY day
#     """,
#     "30d_rolling_average": f"""
#         SELECT
#             region,
#             date_trunc('day', date) AS day,
#             ROUND(temp_mean, 2) AS tmp_mean,
#             ROUND(AVG(temp_mean) OVER(
#                 PARTITION BY region
#                 ORDER BY day
#                 ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
#             ), 2) AS tmp_avg_rolling_30d
#         FROM daily_regional
#         ORDER BY day
#     """,
}

def main() -> None:
    with duckdb.connect(LOCAL_DB_PATH) as con:
        # Credentials
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute(f"SET s3_endpoint='{settings.MINIO_ENDPOINT}';")
        con.execute(f"SET s3_access_key_id='{settings.MINIO_ROOT_USER}';")
        con.execute(f"SET s3_secret_access_key='{settings.MINIO_ROOT_PASSWORD}';")
        con.execute("SET s3_region='eu-west-3';")
        con.execute("SET s3_use_ssl=false;")
        con.execute("SET s3_url_style='path';")
        for name, query in queries.items():
            start = time.time()
            df = con.execute(query).df()
            print(f"Query '{name}' execution time: {time.time() - start:.2f}s")
            print(df)

if __name__ == "__main__":
    main()

"""
"""
