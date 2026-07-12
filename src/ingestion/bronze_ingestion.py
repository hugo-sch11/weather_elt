import logging
import xarray as xr
#import argparse

from src.config.settings import settings
from src.storage.minio import MinioClient
from src.storage.metadata import build_ingestion_metadata, metadata_to_bytes
from src.storage.paths import dataset_path, metadata_path, s3_path, success_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

## # backfill idea
## def parse_args():
##     parser = argparse.ArgumentParser(description="NOAA GFS ingestion pipeline")
##     group = parser.add_mutually_exclusive_group(required=True)
##     group.add_argument("--date", help="Single day (YYYY-MM-DD)")
##     group.add_argument("--start", help="Range start (YYYY-MM-DD)")
##     #parser.add_argument("--numberdays", help="Number of days (integer), from --start exclusive")
##     parser.add_argument("--end", help="Range end (YYYY-MM-DD), required with --start")
##     return parser.parse_args()
"""
usage in main:
    args = parse_args()
    if args.date:
        dates = [args.date]
    else:
        if not args.end:
            raise SystemExit("--end is required when using --start")
        n_days = get_delta_two_dates(args.start, args.end)
        # n_days = args.numberdays
        dates = get_date_list(args.start, n_days)
"""
class BronzeIngestion:

    def __init__(self, minio_client: MinioClient) -> None:
        self.minio_client = minio_client

    def ingest_partition(self, partition_date: str, dataset: xr.Dataset) -> None:
        """Handles the full lifecycle of a single partition."""
        # Idempotency Check (Marker File)
        marker_path = success_path(settings.BRONZE_PREFIX, partition_date)
        if self.minio_client.object_exists(settings.BUCKET_NAME, marker_path):
            logger.info(f"Skipping {partition_date}, already done.")
            return

        try:
            # Define paths
            ds_path = dataset_path(settings.BRONZE_PREFIX, partition_date)
            md_path = metadata_path(settings.BRONZE_PREFIX, partition_date)

            # Rechunking for optimal daily reads, default is (160, 145, 144), -> (24,145,144)
            # (one week, full latitude, full longitude) -> (one day, full latitude, full longitude)
            dataset = dataset.chunk({"time": 24, "latitude": -1, "longitude": -1})

            # Save dataset
            dataset.to_zarr(
                s3_path(path=ds_path),
                mode='w',
                consolidated=True,
                storage_options=settings.storage_options, 
                zarr_format=2
            )

            # Build Metadata
            metadata = build_ingestion_metadata(
                dataset,
                source=settings.SOURCE_NAME,
                partition_date=partition_date
            )
            # Save metadata
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

            logger.info(f"Successfully ingested Bronze partition: {partition_date}")

        except Exception as e:
            logger.error(f"Bronze Ingestion failed for {partition_date}: {e}")
            raise

