from dotenv import load_dotenv
from dataclasses import dataclass
import os

from src.utils.util import get_date_list


load_dotenv()

@dataclass(frozen=True)
class Settings:
    NOAA_GFS_URL = (
        "https://data.dynamical.org/noaa/gfs/analysis-hourly/latest.zarr"
    )
    SOURCE_NAME = "NOAA_GFS"

    MINIO_ENDPOINT = "localhost:9000"
    MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

    BUCKET_NAME = "weather-data-bucket"

    BRONZE_PREFIX = "bronze"
    SILVER_PREFIX = "silver"
    GOLD_PREFIX = "gold"

    LAYER_PREFIX = frozenset(
        {BRONZE_PREFIX, SILVER_PREFIX, GOLD_PREFIX}
    )

    # TO MODIFY! (this dataset date only go from 2015-01-15 to 2024-06-30)
    DAYS_TO_INGEST = get_date_list("2015-01-15", 365) # done with 365, replace with 0 for quickstart

    storage_options = {
        "key": MINIO_ROOT_USER,
        "secret": MINIO_ROOT_PASSWORD,
        "client_kwargs": {"endpoint_url": f"http://{MINIO_ENDPOINT}"}
    }

settings = Settings()
