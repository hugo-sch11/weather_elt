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

""" Test gold with DuckDB"""
# import duckdb
# from src.config.settings import settings
# 
# con = duckdb.connect()
# 
# # Install & Load S3 extension
# con.execute("INSTALL httpfs; LOAD httpfs;")
# 
# # Configure credentials
# con.execute(f"SET s3_endpoint='{settings.MINIO_ENDPOINT}';")
# con.execute(f"SET s3_access_key_id='{settings.MINIO_ROOT_USER}';")
# con.execute(f"SET s3_secret_access_key='{settings.MINIO_ROOT_PASSWORD}';")
# con.execute("SET s3_region='eu-west-3';")
# con.execute("SET s3_use_ssl=false;")
# con.execute("SET s3_url_style='path';")
# 
# query1 = """
#     SELECT latitude, longitude, temperature_2m_min AS MinTmp, temperature_2m_mean AS MeanTmp, temperature_2m_max AS MaxTmp
#     FROM read_parquet('s3://weather-data-bucket/gold/daily_global/**/*.parquet')
#     WHERE date = '2015-08-15' 
#         AND latitude BETWEEN 25 AND 60 
#         AND temperature_2m_max - temperature_2m_min > 20
# """
# 
# query2 = """
#     DESCRIBE SELECT *
#     FROM read_parquet('s3://weather-data-bucket/gold/daily_global/**/*.parquet')
# """
# # Output:
# """
#            column_name column_type null   key default extra
# 0             latitude      DOUBLE  YES  None    None  None
# 1            longitude      DOUBLE  YES  None    None  None
# 2          spatial_ref      BIGINT  YES  None    None  None
# 3  temperature_2m_mean       FLOAT  YES  None    None  None
# 4   temperature_2m_min       FLOAT  YES  None    None  None
# 5   temperature_2m_max       FLOAT  YES  None    None  None
# 6  wind_speed_10m_mean       FLOAT  YES  None    None  None
# 7   wind_speed_10m_max       FLOAT  YES  None    None  None
# 8                 date        DATE  YES  None    None  None
# """
# 
# df = con.execute(query1).df()
# print(df)
