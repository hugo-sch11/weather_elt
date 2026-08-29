import duckdb
import time
from src.config.settings import settings


print(f"duckdb version: {duckdb.__version__}")
LOCAL_DB_PATH = "/mnt/storage/container/weather_analytics.duckdb"

# Queries can be extended to all quantitatives variables
queries = {
# ########## INTROSPECTION ########## 
#     "information_schema_table": f"""
#         SELECT *
#         FROM information_schema.tables
#     """,
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
#     "view_dr_regions": f"""
#         SELECT region
#         FROM daily_regional
#         GROUP BY region
#     """,
# ########## DESCRIPTIVE ########## 
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
#     "hottest_day_precise_location": f"""
#         SELECT rlongitude, rlatitude, day, tmp_max, rnk as rank
#         FROM (
#             SELECT 
#                 ROUND(longitude, 0) as rlongitude, 
#                 ROUND(latitude, 0) as rlatitude, 
#                 date_trunc('day', date) AS day, 
#                 ROUND(MAX(temperature_2m_max), 2) AS tmp_max, 
#                 ROW_NUMBER() OVER (
#                     PARTITION BY ROUND(longitude, 0), ROUND(latitude, 0) 
#                     ORDER BY MAX(temperature_2m_max) DESC
#                 ) AS rnk
#             FROM daily_global
#             WHERE temperature_2m_max >= 45 -- mandatory threshold to adjust (else OOM)
#             GROUP BY rlongitude, rlatitude, day
#         ) ranked
#         WHERE rnk <= 1 -- Top N hottest day PER LOCATION
#         ORDER BY rnk ASC, tmp_max DESC
#     """,
# ########## COMPARATIVE ########## 
#     "compare_regions_over_time": f"""
#         SELECT 
#             date_trunc('day', date) AS day,
#             region,
#             ROUND(AVG(temp_mean), 2) AS tmp_avg
#         FROM daily_regional
#         GROUP BY day, region
#         ORDER BY day, region
#     """,
# ########## ROLLING ########## 
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
Query 'describe_view_dg' execution time: 0.03s
           column_name column_type null   key default extra
0             latitude      DOUBLE  YES  None    None  None
1            longitude      DOUBLE  YES  None    None  None
2          spatial_ref      BIGINT  YES  None    None  None
3  temperature_2m_mean       FLOAT  YES  None    None  None
4   temperature_2m_min       FLOAT  YES  None    None  None
5   temperature_2m_max       FLOAT  YES  None    None  None
6  wind_speed_10m_mean       FLOAT  YES  None    None  None
7   wind_speed_10m_max       FLOAT  YES  None    None  None
8                 date        DATE  YES  None    None  None
Query 'describe_view_dr' execution time: 0.66s
       column_name column_type null   key default extra
0             date        DATE  YES  None    None  None
1           region     VARCHAR  YES  None    None  None
2        temp_mean      DOUBLE  YES  None    None  None
3         temp_max      DOUBLE  YES  None    None  None
4  wind_speed_mean      DOUBLE  YES  None    None  None
5   wind_speed_max      DOUBLE  YES  None    None  None
Query 'summarize_view_dg' execution time: 67.99s
           column_name column_type  ...      count null_percentage
0             latitude      DOUBLE  ...  374804640             0.0
1            longitude      DOUBLE  ...  374804640             0.0
2          spatial_ref      BIGINT  ...  374804640             0.0
3  temperature_2m_mean       FLOAT  ...  374804640             0.0
4   temperature_2m_min       FLOAT  ...  374804640             0.0
5   temperature_2m_max       FLOAT  ...  374804640             0.0
6  wind_speed_10m_mean       FLOAT  ...  374804640             0.0
7   wind_speed_10m_max       FLOAT  ...  374804640             0.0
8                 date        DATE  ...  374804640             0.0

[9 rows x 12 columns]
Query 'summarize_view_dr' execution time: 0.11s
       column_name column_type  ... count null_percentage
0             date        DATE  ...  1083             0.0
1           region     VARCHAR  ...  1083             0.0
2        temp_mean      DOUBLE  ...  1083             0.0
3         temp_max      DOUBLE  ...  1083             0.0
4  wind_speed_mean      DOUBLE  ...  1083             0.0
5   wind_speed_max      DOUBLE  ...  1083             0.0

[6 rows x 12 columns]
Query 'view_dr_regions' execution time: 0.04s
               region
0              europe
1       north_america
2  global_land_approx
Query 'daily_regional_temperature_trend' execution time: 0.04s
                  region        day  tmp_mean
0          north_america 2015-01-15  2.178483
1     global_land_approx 2015-01-15  3.951017
2                 europe 2015-01-15  3.486115
3     global_land_approx 2015-01-16  4.037508
4          north_america 2015-01-16  2.570065
...                  ...        ...       ...
1078  global_land_approx 2016-01-14  5.134937
1079       north_america 2016-01-14  2.848937
1080       north_america 2016-01-15  2.857311
1081              europe 2016-01-15  0.165729
1082  global_land_approx 2016-01-15  5.106966

[1083 rows x 3 columns]
Query 'monthly_regional_averages' execution time: 0.04s
                region      month  tmp_avg
0        north_america 2015-01-01     2.25
1               europe 2015-01-01     2.49
2   global_land_approx 2015-01-01     3.79
3        north_america 2015-02-01     0.97
4               europe 2015-02-01     2.55
5   global_land_approx 2015-02-01     3.68
6   global_land_approx 2015-03-01     3.91
7        north_america 2015-03-01     4.37
8               europe 2015-03-01     5.23
9   global_land_approx 2015-04-01     5.10
10              europe 2015-04-01     7.69
11       north_america 2015-04-01     8.36
12  global_land_approx 2015-05-01     6.63
13              europe 2015-05-01    11.85
14       north_america 2015-05-01    12.93
15  global_land_approx 2015-06-01     8.21
16              europe 2015-06-01    15.16
17       north_america 2015-06-01    16.88
18  global_land_approx 2015-07-01     8.40
19              europe 2015-07-01    17.88
20       north_america 2015-07-01    19.01
21  global_land_approx 2015-08-01     8.23
22              europe 2015-08-01    18.59
23       north_america 2015-08-01    19.07
24  global_land_approx 2015-09-01     7.07
25              europe 2015-09-01    15.45
26       north_america 2015-09-01    16.82
27  global_land_approx 2015-10-01     6.38
28              europe 2015-10-01    10.43
29       north_america 2015-10-01    12.83
30  global_land_approx 2015-11-01     5.34
31              europe 2015-11-01     7.72
32       north_america 2015-11-01     8.22
33       north_america 2015-12-01     4.65
34  global_land_approx 2015-12-01     4.86
35              europe 2015-12-01     5.38
36              europe 2016-01-01     0.27
37       north_america 2016-01-01     3.08
38  global_land_approx 2016-01-01     5.04
Query 'hottest_days_per_region' execution time: 0.04s
                 region        day  tmp_max  rank
0    global_land_approx 2015-05-29    51.56     1
1         north_america 2015-08-17    47.94     1
2                europe 2015-06-30    46.56     1
3    global_land_approx 2015-07-30    51.38     2
4         north_america 2015-08-16    47.63     2
..                  ...        ...      ...   ...
145       north_america 2015-10-18    43.94    49
146              europe 2015-07-11    42.44    49
147  global_land_approx 2015-06-01    49.38    50
148       north_america 2015-07-11    43.94    50
149              europe 2015-08-22    42.38    50

[150 rows x 4 columns]
Query 'hottest_day_precise_location' execution time: 0.32s
      rlongitude  rlatitude        day    tmp_max  rank
0           80.0       19.0 2015-05-29  51.560001     1
1           47.0       31.0 2015-07-30  51.380001     1
2           46.0       33.0 2015-08-01  51.250000     1
3           47.0       32.0 2015-07-30  51.250000     1
4           81.0       19.0 2015-05-29  51.250000     1
...          ...        ...        ...        ...   ...
1708       122.0      -21.0 2015-01-22  45.000000     1
1709       -51.0      -10.0 2015-10-05  45.000000     1
1710       143.0      -34.0 2016-01-13  45.000000     1
1711       -53.0      -13.0 2015-10-04  45.000000     1
1712       133.0      -16.0 2015-11-29  45.000000     1

[1713 rows x 5 columns]
Query 'compare_regions_over_time' execution time: 0.05s
            day              region  tmp_avg
0    2015-01-15              europe     3.49
1    2015-01-15  global_land_approx     3.95
2    2015-01-15       north_america     2.18
3    2015-01-16              europe     3.92
4    2015-01-16  global_land_approx     4.04
...         ...                 ...      ...
1078 2016-01-14  global_land_approx     5.13
1079 2016-01-14       north_america     2.85
1080 2016-01-15              europe     0.17
1081 2016-01-15  global_land_approx     5.11
1082 2016-01-15       north_america     2.86

[1083 rows x 3 columns]
Query '7d_rolling_average' execution time: 0.04s
                  region        day  tmp_mean  tmp_avg_rolling_7d
0                 europe 2015-01-15      3.49                3.49
1          north_america 2015-01-15      2.18                2.18
2     global_land_approx 2015-01-15      3.95                3.95
3                 europe 2015-01-16      3.92                3.71
4          north_america 2015-01-16      2.57                2.37
...                  ...        ...       ...                 ...
1078       north_america 2016-01-14      2.85                2.63
1079  global_land_approx 2016-01-14      5.13                5.04
1080              europe 2016-01-15      0.17                1.03
1081       north_america 2016-01-15      2.86                2.67
1082  global_land_approx 2016-01-15      5.11                5.06

[1083 rows x 4 columns]
Query '30d_rolling_average' execution time: 0.04s
                  region        day  tmp_mean  tmp_avg_rolling_30d
0     global_land_approx 2015-01-15      3.95                 3.95
1                 europe 2015-01-15      3.49                 3.49
2          north_america 2015-01-15      2.18                 2.18
3     global_land_approx 2015-01-16      4.04                 3.99
4                 europe 2015-01-16      3.92                 3.71
...                  ...        ...       ...                  ...
1078              europe 2016-01-14      0.62                 2.94
1079       north_america 2016-01-14      2.85                 3.33
1080  global_land_approx 2016-01-15      5.11                 4.81
1081              europe 2016-01-15      0.17                 2.79
1082       north_america 2016-01-15      2.86                 3.27

[1083 rows x 4 columns]
"""
