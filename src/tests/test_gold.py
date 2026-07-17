import pandas
import time
from typing import Hashable
from src.config.settings import settings
from src.storage.paths import s3_path


def dataframe_null_check(dataframe: pandas.DataFrame) -> dict[Hashable, tuple[int,int]]:
    """Returns: { series_name, (series.size, series.count()) }"""
    d = {}
    # alternative = int(series.isnull().sum())
    for name, series in dataframe.items():
        if name not in ['latitude', 'longitude', 'spatial_ref', 'date']:
            d[name] = (series.size, int(series.count()))
    return d

def main() -> None:
    print("########## TEST GOLD ##########\n")
    start_time = time.time()

    # Extract daily global dataframe partition
    missing_daily_global_partition = []
    null_dict_daily_global = {}
    print("########## [Daily Global] ########## ")
    for days in settings.DAYS_TO_INGEST:
        try:
            partition_daily_global_dataframe = pandas.read_parquet(
                s3_path(path=f"gold/daily_global/date={days}/data.parquet"), 
                storage_options=settings.storage_options
            )
            # NULL CHECK (long execution: )
            d = dataframe_null_check(partition_daily_global_dataframe)
            for key in d.keys():
                null_dict_daily_global[key] = tuple(map(lambda x, y: x + y, null_dict_daily_global.get(key, (0,0)), d[key]))
        except FileNotFoundError:
            missing_daily_global_partition.append(days)

    print(f"Missing daily global partitions: {missing_daily_global_partition}")
    for key in null_dict_daily_global.keys():
        size, non_null = null_dict_daily_global[key]
        null_percentage = (1.0 - (non_null / size)) * 100
        print(f"{key}: null_percentage={null_percentage}%")

    ### # Extract daily regional dataframe partition
    #
    
    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    main()


