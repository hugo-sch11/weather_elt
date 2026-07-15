from time import time
import xarray
from src.config.settings import settings
from src.storage.paths import s3_path
import fsspec

start_time = time()
fs = fsspec.filesystem("s3", **settings.storage_options)
paths = fs.glob(s3_path(bucket=settings.BUCKET_NAME, path=f"bronze/date=*/dataset.zarr"))
datasets = [
    xarray.open_zarr(
        fs.get_mapper(path), 
        consolidated=True,
        zarr_format=2
    ) 
    for path in paths
]
dataset = xarray.concat(datasets, dim="time")

# print(dataset)
for var in dataset.data_vars:
    total_elements = dataset[var].size
    print(f"{var}, total_elements={total_elements}")
    non_null_count = int(dataset[var].count().compute())
    print(f"{var}, non_null_count={non_null_count}")
    null_percentage = (1.0 - (non_null_count / total_elements)) * 100
    print(f"{var}, {null_percentage:.2f}% null")

end_time = time()
print(f"Execution time: {end_time - start_time:.2f}s")

"""
--------------------------------------------------
precipitation_surface, total_elements=9119900160
precipitation_surface, non_null_count=0
precipitation_surface, 100.00% null
--------------------------------------------------
temperature_2m, total_elements=9119900160
temperature_2m, non_null_count=9032688000
temperature_2m, 0.96% null
--------------------------------------------------
wind_u_10m, total_elements=9119900160
wind_u_10m, non_null_count=9057605760
wind_u_10m, 0.68% null
--------------------------------------------------
wind_v_10m, total_elements=9119900160
wind_v_10m, non_null_count=9007770240
wind_v_10m, 1.23% null
--------------------------------------------------
Execution time: 661.87s
--------------------------------------------------
"""
