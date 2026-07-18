import time
import pandas as pd
from collections import defaultdict

from src.config.settings import settings
from src.storage.paths import s3_path


def validate_gold_table(table_name: str, days: list[str]) -> None:
    """
    Reads Parquet partitions for a given Gold table, checks for missing 
    partitions, and calculates null percentages for each metric column.
    """
    print(f"########## [{table_name.replace('_', ' ').title()}] ##########")
    missing_partitions = []
    null_stats = defaultdict(lambda: {"size": 0, "non_null": 0})
    ignore_cols = {'latitude', 'longitude', 'spatial_ref', 'date'}
    # null checks
    for day in days:
        path = s3_path(path=f"gold/{table_name}/date={day}/data.parquet")
        try:
            df = pd.read_parquet(
                path, 
                storage_options=settings.storage_options,
                partitioning=None # important
            )
            cols = [c for c in df.columns if c not in ignore_cols]
            size = df.shape[0]
            non_nulls = df[cols].count()
            for col in cols:
                null_stats[col]["size"] += size
                null_stats[col]["non_null"] += int(non_nulls[col]) # type: ignore[args]
        except FileNotFoundError:
            missing_partitions.append(day)
    print(f"Missing partitions: {missing_partitions}")
    # null percentages
    for col, stats in null_stats.items():
        if stats["size"] > 0:
            null_percentage = (1.0 - (stats["non_null"] / stats["size"])) * 100
            print(f"{col}: null_percentage={null_percentage:.2f}%")
    print()


def main() -> None:
    print("########## TEST GOLD ##########\n")
    start_time = time.time()

    validate_gold_table("daily_global", settings.DAYS_TO_INGEST)
    validate_gold_table("daily_regional", settings.DAYS_TO_INGEST)

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    main()


"""
########## TEST GOLD ##########

########## [Daily Global] ##########
Missing partitions: ['2015-05-13', '2015-09-25', '2015-10-15', '2015-11-07', '2015-11-23']
temperature_2m_mean: null_percentage=0.00%
temperature_2m_min: null_percentage=0.00%
temperature_2m_max: null_percentage=0.00%
wind_speed_10m_mean: null_percentage=0.00%
wind_speed_10m_max: null_percentage=0.00%

########## [Daily Regional] ##########
Missing partitions: ['2015-05-13', '2015-09-25', '2015-10-15', '2015-11-07', '2015-11-23']
region: null_percentage=0.00%
temp_mean: null_percentage=0.00%
temp_max: null_percentage=0.00%
wind_speed_mean: null_percentage=0.00%
wind_speed_max: null_percentage=0.00%

Execution time: 18.85s
"""
