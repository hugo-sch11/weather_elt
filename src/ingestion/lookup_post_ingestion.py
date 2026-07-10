from time import time
import xarray
from src.config.settings import settings
from src.storage.paths import root_path, s3_path
import fsspec

start_time = time()
fs = fsspec.filesystem("s3", **settings.storage_options)
prefix = root_path(settings.BRONZE_PREFIX)
paths = fs.glob(s3_path(path=f"{prefix}date=*/dataset.zarr"))
datasets = [
    xarray.open_zarr(
        fs.get_mapper(path), 
        consolidated=True,
        zarr_format=2
    ) 
    for path in paths
]
dataset = xarray.concat(datasets, dim="time")
print(dataset)
# print(dataset["precipitation_surface"])
# print(dataset["temperature_2m"])
# print(dataset["wind_u_10m"])
# print(dataset["wind_v_10m"])
end_time = time()
print(f"Execution time: {end_time - start_time:.2f}s")

"""
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
Execution time: 11.61s


+ ["precipitation_surface"] + ["temperature_2m"] + ["wind_u_10m"] + ["wind_v_10m"] :

<xarray.DataArray 'precipitation_surface' (time: 8784, latitude: 721,
                                           longitude: 1440)> Size: 36GB
dask.array<concatenate, shape=(8784, 721, 1440), dtype=float32, chunksize=(24, 145, 144), chunktype=numpy.ndarray>
Coordinates:
  * time         (time) datetime64[ns] 70kB 2015-01-15 ... 2016-01-15T23:00:00
  * latitude     (latitude) float64 6kB 90.0 89.75 89.5 ... -89.5 -89.75 -90.0
  * longitude    (longitude) float64 12kB -180.0 -179.8 -179.5 ... 179.5 179.8
    spatial_ref  int64 8B 0
Attributes:
    grid_mapping:            spatial_ref
    long_name:               Precipitation rate at earth surface
    statistics_approximate:  {'max': 0.04474, 'mean': 2.911e-05, 'min': 0.0}
    units:                   kg/(m^2 s)
<xarray.DataArray 'temperature_2m' (time: 8784, latitude: 721, longitude: 1440)> Size: 36GB
dask.array<concatenate, shape=(8784, 721, 1440), dtype=float32, chunksize=(24, 145, 144), chunktype=numpy.ndarray>
Coordinates:
  * time         (time) datetime64[ns] 70kB 2015-01-15 ... 2016-01-15T23:00:00
  * latitude     (latitude) float64 6kB 90.0 89.75 89.5 ... -89.5 -89.75 -90.0
  * longitude    (longitude) float64 12kB -180.0 -179.8 -179.5 ... 179.5 179.8
    spatial_ref  int64 8B 0
Attributes:
    grid_mapping:            spatial_ref
    long_name:               Temperature 2 meters above earth surface
    statistics_approximate:  {'max': 53.25, 'mean': 6.041, 'min': -79.5}
    units:                   C
<xarray.DataArray 'wind_u_10m' (time: 8784, latitude: 721, longitude: 1440)> Size: 36GB
dask.array<concatenate, shape=(8784, 721, 1440), dtype=float32, chunksize=(24, 145, 144), chunktype=numpy.ndarray>
Coordinates:
  * time         (time) datetime64[ns] 70kB 2015-01-15 ... 2016-01-15T23:00:00
  * latitude     (latitude) float64 6kB 90.0 89.75 89.5 ... -89.5 -89.75 -90.0
  * longitude    (longitude) float64 12kB -180.0 -179.8 -179.5 ... 179.5 179.8
    spatial_ref  int64 8B 0
Attributes:
    grid_mapping:            spatial_ref
    long_name:               Wind speed u-component 10 meters above earth sur...
    statistics_approximate:  {'max': 87.5, 'mean': -0.00644, 'min': -96.88}
    units:                   m/s
<xarray.DataArray 'wind_v_10m' (time: 8784, latitude: 721, longitude: 1440)> Size: 36GB
dask.array<concatenate, shape=(8784, 721, 1440), dtype=float32, chunksize=(24, 145, 144), chunktype=numpy.ndarray>
Coordinates:
  * time         (time) datetime64[ns] 70kB 2015-01-15 ... 2016-01-15T23:00:00
  * latitude     (latitude) float64 6kB 90.0 89.75 89.5 ... -89.5 -89.75 -90.0
  * longitude    (longitude) float64 12kB -180.0 -179.8 -179.5 ... 179.5 179.8
    spatial_ref  int64 8B 0
Attributes:
    grid_mapping:            spatial_ref
    long_name:               Wind speed v-component 10 meters above earth sur...
    statistics_approximate:  {'max': 89.0, 'mean': 0.1571, 'min': -87.88}
    units:                   m/s
"""
