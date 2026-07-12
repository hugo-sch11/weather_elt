"""Temporary file to test things. Signicative work will be written to other file."""

"""Checking log"""
# from datetime import date
# from src.storage.minio import MinioClient
# from src.storage.log_handler import MinioLogHandler
# from src.storage.paths import log_path
# 
# minio_client = MinioClient()
# log_handler = MinioLogHandler(minio_client)
# today = date.today().strftime("%Y-%m-%d")
# #print(today, type(today))
# print(f"Log of {today}: \n{log_handler.get_log_content(log_path(today))}")

"""Checking number of days ingested"""
# from src.storage.minio import MinioClient
# from src.config.settings import settings
# 
# minio_client = MinioClient()
# 
# objects = minio_client.client.list_objects(
#     settings.BUCKET_NAME,
#     prefix=f"settings.BRONZE_PREFIX/"
# )
# l = []
# for obj in objects:
#     l.append(obj.object_name)
# nl = len(l)
# nd = len(settings.DAYS_TO_INGEST)
# print(f"Numbers of days ingested: {nl}")
# print(f"Numbers of days supposed to be ingested: {nd}")
# print(f"Days ingested equal days setup: {nl == nd}")

"""Checking dataset"""
# import fsspec
# import xarray
# from src.config.settings import settings

# fs = fsspec.filesystem("s3", **settings.storage_options)
# bucket = settings.BUCKET_NAME
# prefix = f"settings.BRONZE_PREFIX/"
# paths = fs.glob(f"s3://{bucket}/{prefix}date=*/dataset.zarr")
# datasets = [
#     xarray.open_zarr(
#         fs.get_mapper(path), 
#         consolidated=True,
#         zarr_format=2
#     ) 
#     for path in paths
# ]
# dataset = xarray.concat(datasets, dim="time")

# for var in dataset.data_vars:
#     #print(dataset[var].isnull().mean().compute())
#     print(dataset[var].count().compute())
#     print(dataset[var].min(skipna=True).compute())
#     print(dataset[var].max(skipna=True).compute())

"""Replacing registry by marker file"""
# import re
# from src.storage.minio import MinioClient
# from src.config.settings import settings
# from src.storage.paths import success_path
# 
# minio_client = MinioClient()
# LAYERS = (settings.BRONZE_PREFIX, settings.SILVER_PREFIX)
# 
# for layer in LAYERS:
#     objects = minio_client.client.list_objects(
#         settings.BUCKET_NAME, 
#         prefix=f"{layer}/"
#     )
#     for obj in objects:
#         registry_path = f"{obj.object_name}registry.json"
#         if minio_client.object_exists(settings.BUCKET_NAME, registry_path):
#             print(f"Removing: {registry_path}")
#             #minio_client.client.remove_object(settings.BUCKET_NAME, registry_path)
#         else:
#             print(f"No registry @ {obj.object_name}")
# 
#         extracted_date = re.search("20[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])", str(obj.object_name))
#         if extracted_date:
#             extracted_date = extracted_date.group(0)
#             print(f"Match! Parsed date: {extracted_date}")
#         else:
#             print("No match...")
#             continue
# 
#         marker_path = success_path(layer, extracted_date)
#         print(f"Writing Marker File: {marker_path}\n")
#         #minio_client.put_bytes(
#         #    bucket_name=settings.BUCKET_NAME, 
#         #    object_name=marker_path, 
#         #    data=b"", 
#         #    content_type="text/plain"
#         #)
#     input("Continue to next layer ?")
