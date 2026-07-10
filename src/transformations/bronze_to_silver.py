import logging
import numpy as np
import xarray as xr
from typing import Hashable
import time

from src.config.settings import settings
from src.storage.paths import dataset_path, metadata_path, s3_path, success_path
from src.storage.metadata import build_silver_metadata, metadata_to_bytes
from src.storage.minio import MinioClient
from src.quality.validation import validate_dataset
from src.quality.schema import NOAA_GFS_BRONZE_SCHEMA

logger = logging.getLogger(__name__)

class BronzeToSilverTransformer:

    def __init__(self, minio_client: MinioClient):
        self.minio_client = minio_client

    def _load_bronze(self, partition_date: str) -> xr.Dataset:
        """Loads a Bronze partition from MinIO as a lazy, Dask-backed xarray Dataset."""
        bronze_dataset_path = dataset_path(settings.BRONZE_PREFIX, partition_date)
        s3_url = s3_path(path=bronze_dataset_path)
        return xr.open_zarr(s3_url, storage_options=settings.storage_options, zarr_format=2)

    ### Maybe move it to utils
    @staticmethod
    def null_variable(dataset: xr.Dataset, var_name: Hashable, threshold: float = 0.99) -> bool:
        """Checks whether a variable is completely or mostly null in a dataset."""
        total_elements = dataset[var_name].size
        if total_elements == 0:
            return True
        non_null_count = int(dataset[var_name].count().compute())
        null_ratio = 1.0 - (non_null_count / total_elements)
        return null_ratio >= threshold

    def _apply_transformations(self, dataset: xr.Dataset) -> tuple[xr.Dataset,list[Hashable],list[Hashable]]:
        """
        Applies domain-specific transformations to create the Silver layer.
        Domain-specific: wind speed, wind_direction
        All operations are lazy (Dask-backed) and will only execute when saving.
        """
        logger.info("Applying derived metric transformations...")

        # Drop null variable
        vars_to_drop = [var for var in dataset.data_vars if self.null_variable(dataset, var)]
        if vars_to_drop:
            logger.warning(f"Dropping variables due to null values: {vars_to_drop}")
            dataset = dataset.drop_vars(vars_to_drop)

        vars_derived = []

        if "wind_u_10m" in dataset and "wind_v_10m" in dataset:
            u = dataset["wind_u_10m"]
            v = dataset["wind_v_10m"]

            # Wind Speed
            dataset["wind_speed_10m"] = np.sqrt(u**2 + v**2)
            dataset["wind_speed_10m"].attrs.update({
                "units": "m/s",
                "long_name": "Wind Speed 10 meters above earth surface",
                "description": "Derived from u and v components."
            })
            vars_derived.append("wind_speed_10m")

            # Wind Direction: Meteorological direction
            rad2deg = 180.0 / np.pi
            wind_dir = xr.apply_ufunc(
                lambda v_arr, u_arr: (270.0 - rad2deg * np.arctan2(v_arr, u_arr)) % 360.0,
                v, u,
                dask="parallelized",
                output_dtypes=[u.dtype]
            )
            dataset["wind_direction_10m"] = wind_dir
            dataset["wind_direction_10m"].attrs.update({
                "units": "degrees",
                "long_name": "10m Meteorological Wind Direction",
                "description": "Direction the wind is coming from (0=North, 90=East, 180=South, 270=West)."
            })
            vars_derived.append("wind_direction_10m")
        else:
            logger.warning("Wind components missing. Skipping wind derivations.")

        # Precipitation: kg/m^2/s to mm/h
        # 1 kg/m^2 of water = 1 mm depth.
        if "precipitation_surface" in dataset:
            dataset["precipitation_mm_per_hour"] = dataset["precipitation_surface"] * 3600.0
            dataset["precipitation_mm_per_hour"].attrs.update({
                "units": "mm/h",
                "long_name": "Hourly Precipitation Accumulation",
                "description": "Derived assuming surface precipitation rate is in kg/m^2/s."
            })
            vars_derived.append("precipitation_mm_per_hour")
        else:
            logger.warning("Precipitation components missing. Skipping precipitation derivations.")

        return (dataset, vars_to_drop, vars_derived)

    def transform_and_save(self, partition_date: str) -> None:
        """Orchestrates the loading, validating, transforming, and saving of a single partition."""
        # Idempotency Check (Marker File)
        marker_path = success_path(settings.SILVER_PREFIX, partition_date)
        if self.minio_client.object_exists(settings.BUCKET_NAME, marker_path):
            logger.info(f"Skipping {partition_date}, already done.")
            return

        try:
            start = time.time()
            # Load
            dataset = self._load_bronze(partition_date)

            # Quality
            validate_dataset(dataset, NOAA_GFS_BRONZE_SCHEMA)

            # Transform
            dataset_silver, vars_dropped, vars_derived = self._apply_transformations(dataset)

            # Save to MinIO
            silver_path = dataset_path(settings.SILVER_PREFIX, partition_date)
            s3_url = s3_path(path=silver_path)

            dataset_silver.to_zarr(
                s3_url,
                mode='w',
                consolidated=True,
                storage_options=settings.storage_options,
                zarr_format=2
            )

            # Build Metadata
            metadata = build_silver_metadata(
                dataset_silver,
                source=settings.SOURCE_NAME,
                partition_date=partition_date,
                vars_dropped=vars_dropped, 
                vars_derived=vars_derived, 
                execution_time=(time.time()-start)
            )
            md_path = metadata_path(settings.SILVER_PREFIX, partition_date)
            # Save Metadata
            self.minio_client.put_bytes(
                bucket_name=settings.BUCKET_NAME,
                object_name=md_path,
                data=metadata_to_bytes(metadata), 
                content_type="application/json"
            )

            # Write Marker File
            self.minio_client.put_bytes(
                bucket_name=settings.BUCKET_NAME, 
                object_name=marker_path, 
                data=b"", 
                content_type="text/plain"
            )

            logger.info(f"Successfully processed Silver partition: {partition_date}")

        except Exception as e:
            logger.error(f"Bronze to Silver transformation failed for {partition_date}: {e}")
            raise

