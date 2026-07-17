import xarray
import time
import fsspec
from src.config.settings import settings

def get_global_dataset(glob_path: str) -> xarray.Dataset:
    """Concat all partition dataset from a global path (e.g."bronze/date=*/dataset.zarr")"""
    fs = fsspec.filesystem("s3", **settings.storage_options)
    paths = fs.glob(f"{settings.BUCKET_NAME}/{glob_path}")
    datasets = [
        xarray.open_zarr(
            fs.get_mapper(path), 
            consolidated=True,
            zarr_format=2
        ) 
        for path in paths
    ]
    return xarray.concat(datasets, dim="time")

def dataset_null_check(dataset: xarray.Dataset) -> None:
    print("========== NULL CHECK ==========")
    # alternative = int(dataset[var].isnull().sum().compute())
    for var in dataset.data_vars:
        total_elements = dataset[var].size
        print(f"{var}, total_elements={total_elements}")
        non_null_count = int(dataset[var].count().compute())
        print(f"{var}, non_null_count={non_null_count}")
        null_percentage = (1.0 - (non_null_count / total_elements)) * 100
        print(f"{var}, null_percentage={null_percentage:.2f}%")

def dataset_days_check(dataset: xarray.Dataset) -> None:
    print("========== DAYS CHECK ==========")
    print(f"Dates supposed to be ingested ({len(settings.DAYS_TO_INGEST)}days*24hours): {len(settings.DAYS_TO_INGEST)*24}")
    print(f"Dates ingested: {dataset["time"].size}")
    dates = [date.strftime("%Y-%m-%d") for date in dataset.groupby("time.date").groups.keys()]
    same_days_ingested = dates == settings.DAYS_TO_INGEST
    print(f"Same days ingested as planned (no miss): {same_days_ingested}")
    if not same_days_ingested:
        differing_elements = list(set(dates) ^ set(settings.DAYS_TO_INGEST))
        print(f"Missing days: {differing_elements}")
    print(f"Duplicates dates: {dataset["time"].drop_duplicates("time").size != dataset["time"].size}")

def main() -> None:
    print("########## TEST BRONZE ##########\n")
    start_time = time.time()

    # Extract global dataset
    #dataset = get_global_dataset("bronze/date=*/dataset.zarr")
    #print(dataset)
    # NULL CHECK (long execution: 10min)
    #dataset_null_check(dataset)
    # CHECKING NUMBER OF DAYS INGESTED
    #dataset_days_check(dataset)

    print("########## TEST SILVER ##########\n")
    # Extract global dataset
    dataset = get_global_dataset("silver/date=*/dataset.zarr")
    #print(dataset)
    # NULL CHECK (long execution: 20min)
    #dataset_null_check(dataset)
    # CHECKING NUMBER OF DAYS INGESTED
    dataset_days_check(dataset)

    end_time = time.time()
    print(f"\nExecution time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    main()

"""
########## TEST BRONZE ##########
============================================================================================================================
<xarray.Dataset> Size: 146GB
Dimensions:                (time: 8784, latitude: 721, longitude: 1440)
Coordinates:
  * time                   (time) datetime64[ns] 70kB 2015-01-15 ... 2016-01-...
  * latitude               (latitude) float64 6kB 90.0 89.75 ... -89.75 -90.0
  * longitude              (longitude) float64 12kB -180.0 -179.8 ... 179.8
    spatial_ref            int64 8B 0
Data variables:
    precipitation_surface  (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    temperature_2m         (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_u_10m             (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_v_10m             (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
Attributes:
    attribution:         NOAA NCEP GFS data processed by dynamical.org from N...
    description:         Historical weather data from the Global Forecast Sys...
    id:                  noaa-gfs-analysis-hourly
    name:                NOAA GFS analysis, hourly
    spatial_domain:      Global
    spatial_resolution:  0.25 degrees (~20km)
    time_domain:         2015-01-15 00:00:00 UTC to 2024-07-01 00:00:00 UTC
    time_resolution:     1 hour
============================================================================================================================
========== NULL CHECK ==========
precipitation_surface, total_elements=9119900160
precipitation_surface, non_null_count=0
precipitation_surface, null_percentage=100.00%
--------------------------------------------------
temperature_2m, total_elements=9119900160
temperature_2m, non_null_count=9032688000
temperature_2m, null_percentage=0.96%
--------------------------------------------------
wind_u_10m, total_elements=9119900160
wind_u_10m, non_null_count=9057605760
wind_u_10m, null_percentage=0.68%
--------------------------------------------------
wind_v_10m, total_elements=9119900160
wind_v_10m, non_null_count=9007770240
wind_v_10m, null_percentage=1.23%
--------------------------------------------------
========== DAYS CHECK ==========
Dates supposed to be ingested (366days*24hours): 8784
Dates ingested: 8784
Same days ingested as planned (no miss): True
Duplicates dates: False
--------------------------------------------------
Execution time: 673.37s


########## TEST SILVER ##########
============================================================================================================================
<xarray.Dataset> Size: 180GB
Dimensions:             (time: 8664, latitude: 721, longitude: 1440)
Coordinates:
  * time                (time) datetime64[ns] 69kB 2015-01-15 ... 2016-01-15T...
  * latitude            (latitude) float64 6kB 90.0 89.75 89.5 ... -89.75 -90.0
  * longitude           (longitude) float64 12kB -180.0 -179.8 ... 179.5 179.8
    spatial_ref         int64 8B 0
Data variables:
    temperature_2m      (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_direction_10m  (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_speed_10m      (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_u_10m          (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
    wind_v_10m          (time, latitude, longitude) float32 36GB dask.array<chunksize=(24, 145, 144), meta=np.ndarray>
Attributes:
    attribution:         NOAA NCEP GFS data processed by dynamical.org from N...
    description:         Historical weather data from the Global Forecast Sys...
    id:                  noaa-gfs-analysis-hourly
    name:                NOAA GFS analysis, hourly
    spatial_domain:      Global
    spatial_resolution:  0.25 degrees (~20km)
    time_domain:         2015-01-15 00:00:00 UTC to 2024-07-01 00:00:00 UTC
    time_resolution:     1 hour
============================================================================================================================
========== NULL CHECK ==========
temperature_2m, total_elements=8995311360
temperature_2m, non_null_count=8982852480
temperature_2m, null_percentage=0.14%
-
wind_direction_10m, total_elements=8995311360
wind_direction_10m, non_null_count=8982852480
wind_direction_10m, null_percentage=0.14%
-
wind_speed_10m, total_elements=8995311360
wind_speed_10m, non_null_count=8982852480
wind_speed_10m, null_percentage=0.14%
-
wind_u_10m, total_elements=8995311360
wind_u_10m, non_null_count=8982852480
wind_u_10m, null_percentage=0.14%
-
wind_v_10m, total_elements=8995311360
wind_v_10m, non_null_count=8982852480
wind_v_10m, null_percentage=0.14%
========== DAYS CHECK ==========
Dates supposed to be ingested (366days*24hours): 8784
Dates ingested: 8664
Same days ingested as planned (no miss): False
Missing days: ['2015-11-23', '2015-10-15', '2015-11-07', '2015-05-13', '2015-09-25']
Duplicates dates: False

Execution time: 1430.97s
"""
