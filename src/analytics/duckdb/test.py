import duckdb
import time
from src.config.settings import settings


LOCAL_DB_PATH = "/mnt/storage/container/weather_analytics.duckdb"

queries = {
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
##    """
#     "monthly_regional_averages": f"""
#         SELECT 
#             region,
#             date_trunc('month', date) AS month,
#             ROUND(AVG(temp_mean),2) AS avg_tmp
#         FROM daily_regional
#         GROUP BY region, month
#         ORDER BY month, avg_tmp
#     """
    "hottest_days_per_region": f"""
        SELECT
            region,
            date_trunc('day', date) AS day,
            ROUND(MAX(temp_max),2) AS tmp_max,
        FROM daily_regional
        --WHERE region NOT LIKE 'global%'
        GROUP BY region, day
        ORDER BY tmp_max DESC
        LIMIT 20
    """
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
Query 'describe_view_dg' execution time: 0.34s
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

Query 'describe_view_dr' execution time: 0.73s
       column_name column_type null   key default extra
0             date        DATE  YES  None    None  None
1           region     VARCHAR  YES  None    None  None
2        temp_mean      DOUBLE  YES  None    None  None
3         temp_max      DOUBLE  YES  None    None  None
4  wind_speed_mean      DOUBLE  YES  None    None  None
5   wind_speed_max      DOUBLE  YES  None    None  None

Query 'summarize_view_dg' execution time: 73.90s
           column_name column_type          min         max  approx_unique                         avg                 std                  q25                    q50                 q75      count  null_percentage
0             latitude      DOUBLE        -90.0        90.0            823                         0.0  52.033643032391524   -45.12294157887524  0.0028764791329579198    44.9887378191618  374804640              0.0
1            longitude      DOUBLE       -180.0      179.75           1694                      -0.125  103.92302353415772   -90.08214237102229    -0.1355726338737292   89.88251756132071  374804640              0.0
2          spatial_ref      BIGINT            0           0              1                         0.0                 0.0                    0                      0                   0  374804640              0.0
3  temperature_2m_mean       FLOAT    -72.99479   45.619793        5385185           6.025190778845839   21.16059573650807   -4.075513442488709     10.969064117911879  23.902046781906183  374804640              0.0
4   temperature_2m_min       FLOAT       -78.25     40.4375           9207          3.9920016395114977  21.844894595920113   -6.769936645334608       9.07663533546294   22.08415891049233  374804640              0.0
5   temperature_2m_max       FLOAT      -72.125     51.5625           8538           8.141876339937413  20.831755924687794  -1.5859640972398226     12.722708114873182   25.48628147982158  374804640              0.0
6  wind_speed_10m_mean       FLOAT  0.104329586    41.88106       31693506           6.289519933066487  3.5013237652573554   3.5879267552869267      5.786951733110303   8.360524821517586  374804640              0.0
7   wind_speed_10m_max       FLOAT   0.20241103    78.27458        2171103            8.25075654025085   4.286923330698452    5.112828357575534      7.514771304819389  10.533590145310324  374804640              0.0
8                 date        DATE   2015-01-15  2016-01-15            337  2015-07-15 13:25:45.706371                None           2015-04-15             2015-07-15          2015-10-15  374804640              0.0
Query 'summarize_view_dr' execution time: 0.75s
       column_name column_type                 min                max  approx_unique                         avg                 std                q25                 q50                q75  count  null_percentage
0             date        DATE          2015-01-15         2016-01-15            337  2015-07-15 13:25:45.706371                None         2015-04-14          2015-07-15         2015-10-14   1083              0.0
1           region     VARCHAR              europe      north_america              3                        None                None               None                None               None   1083              0.0
2        temp_mean      DOUBLE  -1.118711233139038  20.10315704345703            971           8.855037207583642  5.4584343353692715  4.800659633412654   7.524873383729929  13.14976278251531   1083              0.0
3         temp_max      DOUBLE            17.71875            51.5625            395           39.99521006463527   8.051511115342889  36.86099102437417   42.05666089965398         46.0234375   1083              0.0
4  wind_speed_mean      DOUBLE  3.2711615562438965  8.140768051147461           1036          5.6372824435088775  0.8090202525093209  4.945010517055827   5.831348370283077  6.282701173607184   1083              0.0
5   wind_speed_max      DOUBLE  14.038158416748047  78.27458190917969           1040          28.943160914758344   10.33960863532158  21.48852153572012  26.306735404332475  33.72743545259748   1083              0.0

Query 'monthly_regional_averages' execution time: 0.10s
                region      month  avg_tmp
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

"""
