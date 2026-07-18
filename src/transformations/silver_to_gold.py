import io
import logging
import xarray as xr
import pandas as pd
import time

from src.config.settings import settings
from src.storage.paths import dataset_path, s3_path, gold_path
from src.storage.minio import MinioClient
from src.storage.metadata import build_gold_metadata, metadata_to_bytes


logger = logging.getLogger(__name__)

# geographical bounds for spatial aggregation (high to low)
REGIONS = {
    "europe": {"lat_slice": slice(70.0, 35.0), "lon_slice": slice(-10.0, 40.0)},
    "north_america": {"lat_slice": slice(70.0, 15.0), "lon_slice": slice(-160.0, -50.0)},
    "global_land_approx": {"lat_slice": slice(90.0, -90.0), "lon_slice": slice(-180.0, 180.0)}
}


class SilverToGoldTransformer:

    def __init__(self, minio_client: MinioClient):
        self.minio_client = minio_client

    def _load_silver(self, partition_date: str) -> xr.Dataset:
        """Loads a Silver partition from MinIO as a lazy, Dask-backed xarray Dataset."""
        silver_dataset_path = dataset_path(settings.SILVER_PREFIX, partition_date)
        s3_url = s3_path(path=silver_dataset_path)
        return xr.open_zarr(s3_url, storage_options=settings.storage_options, zarr_format=2)

    def _write_parquet_to_minio(self, df: pd.DataFrame, transfo_name: str, partition_date: str, filename: str = "data.parquet") -> int:
        """Helper to flatten, convert to Parquet in memory, and upload to MinIO."""
        object_name = gold_path(transfo_name, partition_date) + filename

        # Pandas DataFrame to Parquet bytes in memory
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        buffer.seek(0)

        # Write Parquet
        self.minio_client.put_bytes(
            bucket_name=settings.BUCKET_NAME,
            object_name=object_name,
            data=buffer.getvalue(),
            content_type="application/vnd.apache.parquet"
        )
        return len(buffer.getvalue())


    def transform_to_hourly_parquet(self) -> None:
        """Direct Copy to Parquet (Chunks the multidimensional array)"""
        # Defusing the operation, too much space use (300Gb, woud take me 50+hours).
        pass


    def transform_to_daily_parquet(self, ds: xr.Dataset, partition_date: str) -> None:
        """Temporal Rollup (Hourly -> Daily Min/Max/Mean)"""
        transformation_name = "daily_global"
        currpath = gold_path(transformation_name, partition_date)
        # Idempotency Check (Marker File)
        marker_path = currpath + "_SUCCESS"
        if self.minio_client.object_exists(settings.BUCKET_NAME, marker_path):
            logger.info(f"Skipping [Gold - Daily] {partition_date}, already done.")
            return

        try:
            start = time.time()
            # Transformation
            daily_ds = xr.Dataset({
                "temperature_2m_mean": ds["temperature_2m"].mean(dim="time"),
                "temperature_2m_min": ds["temperature_2m"].min(dim="time"),
                "temperature_2m_max": ds["temperature_2m"].max(dim="time"),
                "wind_speed_10m_mean": ds["wind_speed_10m"].mean(dim="time"),
                "wind_speed_10m_max": ds["wind_speed_10m"].max(dim="time")
            })
            dataframe = daily_ds.compute().to_dataframe().reset_index()
            file_size_bytes = self._write_parquet_to_minio(dataframe, transformation_name, partition_date)

            # Build Metadata
            metadata = build_gold_metadata(
                row_count=len(dataframe),
                source=settings.SOURCE_NAME, 
                partition_date=partition_date, 
                transformation_name=transformation_name, 
                aggregation_logic={"time":"1D","metrics":["mean","min","max"]}, 
                spatial_bounds="Global", 
                file_size_bytes=file_size_bytes, 
                execution_time=(time.time()-start)
            )
            md_path = currpath + "metadata.json"
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
            logger.info(f"Successfully transformed [Gold - Daily] for {partition_date}")
        except Exception as e:
            logger.error(f"Failed [Gold - Daily] transformation for {partition_date}: {e}")
            raise


    def transform_to_regional_parquet(self, ds: xr.Dataset, partition_date: str) -> None:
        """Spatial Aggregation (Grid -> Regions) + Temporal Rollup"""
        transfo_name = "daily_regional"
        currpath = gold_path(transfo_name, partition_date)
        # Idempotency Check (Marker File)
        marker_path = currpath + "_SUCCESS"
        if self.minio_client.object_exists(settings.BUCKET_NAME, marker_path):
            logger.info(f"Skipping [Gold - Regional] {partition_date}, already done.")
            return
        try:
            start = time.time()
            # Transformation
            region_rows = []
            for region_name, bounds in REGIONS.items():
                # Slice the global grid to the specific region
                ds_region = ds.sel(
                    latitude=bounds["lat_slice"], 
                    longitude=bounds["lon_slice"]
                )
                # Calculate the spatial and temporal average for this region for the day
                region_agg = ds_region.mean(dim=["time", "latitude", "longitude"]).compute()
                # Extract the scalar values
                region_rows.append({
                    "date": partition_date,
                    "region": region_name,
                    "temp_mean": float(region_agg["temperature_2m"].values),
                    "temp_max": float(ds_region["temperature_2m"].max().compute().values),
                    "wind_speed_mean": float(region_agg["wind_speed_10m"].values),
                    "wind_speed_max": float(ds_region["wind_speed_10m"].max().compute().values)
                })

            # Create a summary dataframe and write to parquet
            dataframe = pd.DataFrame(region_rows)
            file_size_bytes = self._write_parquet_to_minio(dataframe, transfo_name, partition_date)

            # Build Metadata
            metadata = build_gold_metadata(
                row_count=len(dataframe),
                source=settings.SOURCE_NAME, 
                partition_date=partition_date, 
                transformation_name=transfo_name, 
                aggregation_logic={"time":"1D","metrics":["mean","min","max"]}, 
                spatial_bounds=REGIONS, 
                file_size_bytes=file_size_bytes, 
                execution_time=(time.time()-start)
            )
            md_path = currpath + "metadata.json"
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
            logger.info(f"Successfully transformed [Gold - Regional] for {partition_date}")
        except Exception as e:
            logger.error(f"Failed [Gold - Regional] transformation for {partition_date}: {e}")
            raise


    def process_partition(self, partition_date: str) -> None:
        """Orchestrates the 3 Gold transformations for a single day."""
        all_done = all([
            self.minio_client.object_exists(settings.BUCKET_NAME, gold_path("hourly_global", partition_date) + "_SUCCESS"),
            self.minio_client.object_exists(settings.BUCKET_NAME, gold_path("daily_global", partition_date) + "_SUCCESS"),
            self.minio_client.object_exists(settings.BUCKET_NAME, gold_path("daily_regional", partition_date) + "_SUCCESS")
        ])
        if all_done:
            logger.info(f"Skipping [Gold] {partition_date}, all 3 operations already done.")
            return
        dataset = self._load_silver(partition_date)
        #self.transform_to_hourly_parquet()
        self.transform_to_daily_parquet(dataset, partition_date)
        self.transform_to_regional_parquet(dataset, partition_date)

