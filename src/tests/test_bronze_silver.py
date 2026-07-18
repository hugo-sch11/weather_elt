import xarray
import time
import fsspec
import pandas

from src.config.settings import settings


def get_global_dataset(glob_path: str) -> xarray.Dataset:
    """Concat all partition dataset from a global path (e.g."bronze/date=*/dataset.zarr")"""
    fs = fsspec.filesystem("s3", **settings.storage_options)
    paths = sorted(fs.glob(f"{settings.BUCKET_NAME}/{glob_path}"))
    datasets = [
        xarray.open_zarr(
            f"s3://{path}", 
            storage_options=settings.storage_options, 
            consolidated=True,
            zarr_format=2
        ) 
        for path in paths
    ]
    return xarray.concat(datasets, dim="time")


def dataset_null_check(dataset: xarray.Dataset) -> None:
    print("========== NULL CHECK ==========")
    counts = dataset.count().compute()
    for var in dataset.data_vars:
        total_elements = dataset[var].size
        non_null_count = int(counts[var].values)
        null_percentage = (1.0 - (non_null_count / total_elements)) * 100
        print(f"{var}, total_elements={total_elements}, non_null_count={non_null_count}, null_percentage={null_percentage:.2f}%")


def dataset_days_check(dataset: xarray.Dataset, expected_days: list[str]) -> None:
    print("========== DAYS CHECK ==========")
    expected_hours = len(expected_days) * 24
    print(f"Expected hours: {expected_hours:,}")
    print(f"Ingested hours: {dataset["time"].size:,}")
    print(f"Hours equal: {expected_hours==dataset["time"].size}")
    time_index = pandas.to_datetime(dataset["time"].values)
    ingested_days = set(time_index.strftime("%Y-%m-%d").unique())
    expected_set = set(expected_days)
    missing_days = expected_set - ingested_days
    extra_days = ingested_days - expected_set
    if missing_days:
        print(f"Missig days: {sorted(list(missing_days))}")
    if extra_days:
        print(f"Extra days: {sorted(list(extra_days))}")
    if not missing_days and not extra_days:
        print("All expected days are present.")
    has_duplicates = len(time_index) != len(time_index.unique())
    print(f"Duplicate timestamps: {has_duplicates}")


def main() -> None:
    start_time = time.time()

    for layer in [settings.BRONZE_PREFIX, settings.SILVER_PREFIX]:
        print(f"########## TEST {layer.upper()} ##########")
        try:
            dataset = get_global_dataset(f"{layer}/date=*/dataset.zarr")
            #print(dataset)
            dataset_null_check(dataset)
            dataset_days_check(dataset, settings.DAYS_TO_INGEST)
        except Exception as e:
            print(f"Error testing {layer}: {e}")

    end_time = time.time()
    print(f"\nTotal Execution time: {end_time - start_time:.2f}s")


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
precipitation_surface, total_elements=9119900160, non_null_count=0, null_percentage=100.00%
temperature_2m, total_elements=9119900160, non_null_count=9032688000, null_percentage=0.96%
wind_u_10m, total_elements=9119900160, non_null_count=9057605760, null_percentage=0.68%
wind_v_10m, total_elements=9119900160, non_null_count=9007770240, null_percentage=1.23%
========== DAYS CHECK ==========
Expected hours: 8,784
Ingested hours: 8,784
Hours equal: True
All expected days are present.
Duplicate timestamps: False

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
temperature_2m, total_elements=8995311360, non_null_count=8982852480, null_percentage=0.14%
wind_direction_10m, total_elements=8995311360, non_null_count=8982852480, null_percentage=0.14%
wind_speed_10m, total_elements=8995311360, non_null_count=8982852480, null_percentage=0.14%
wind_u_10m, total_elements=8995311360, non_null_count=8982852480, null_percentage=0.14%
wind_v_10m, total_elements=8995311360, non_null_count=8982852480, null_percentage=0.14%
========== DAYS CHECK ==========
Expected hours: 8,784
Ingested hours: 8,664
Hours equal: False
Missig days: ['2015-05-13', '2015-09-25', '2015-10-15', '2015-11-07', '2015-11-23']
Duplicate timestamps: False

==================================================

Total Execution time: 2125.57s
"""
