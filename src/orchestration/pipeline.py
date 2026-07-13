import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import xarray

from src.ingestion.bronze_ingestion import BronzeIngestion
from src.transformations.bronze_to_silver import BronzeToSilverTransformer
from src.config.settings import settings
from src.storage.minio import MinioClient
from src.storage.log_handler import MinioLogHandler
from src.transformations.silver_to_gold import SilverToGoldTransformer

logger = logging.getLogger(__name__)

def process_partition(
    target_day: str,
    lazy_dataset,
    ingestion: BronzeIngestion,
    transformer_silver: BronzeToSilverTransformer, 
    transformer_gold: SilverToGoldTransformer
) -> None:
    """Handles the full ELT lifecycle for a single partition."""
    # Extract and Load Bronze
    ingestion.ingest_partition(target_day, lazy_dataset)

    # Transform to Silver
    transformer_silver.transform_and_save(target_day)

    # Transform to Gold
    transformer_gold.process_partition(target_day)


def main():
    start_execution_time = time.time()

    # Initialize
    minio_client = MinioClient()
    ingestion = BronzeIngestion(minio_client)
    transformer_silver = BronzeToSilverTransformer(minio_client)
    transformer_gold = SilverToGoldTransformer(minio_client)

    # Log both console and MinIO
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # MinIO Log Handler
    log_handler = MinioLogHandler(minio_client)
    log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
    root_logger.addHandler(log_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))
    root_logger.addHandler(console_handler)

    # Track failures
    failed_days = []

    try:
        source_dataset = xarray.open_zarr(settings.NOAA_GFS_URL, chunks={}) # type: ignore[arg-type]

        logger.info(f"Orchestrating pipeline for {len(settings.DAYS_TO_INGEST)} days...")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for day in settings.DAYS_TO_INGEST:
                day_dataset = source_dataset.sel(time=day)

                future = executor.submit(
                    process_partition,
                    day,
                    day_dataset,
                    ingestion,
                    transformer_silver,
                    transformer_gold
                )
                futures[future] = day

            for future in as_completed(futures):
                day = futures[future]
                try:
                    future.result()
                except Exception:
                    # already logged, just collect for summary
                    failed_days.append(day)
                    #raise #Debug

    finally:
        # Cleanup Log Handlers
        log_handler.flush()
        root_logger.removeHandler(log_handler)
        root_logger.removeHandler(console_handler)

    end_execution_time = time.time()
    print(f"Total Pipeline Execution time: {end_execution_time-start_execution_time:.2f}s")

    if failed_days:
        print(f"{len(failed_days)} days failed processing: {failed_days}")
        # sys.exit(1)
    else:
        print("All partitions processed successfully!")

if __name__ == "__main__":
    main()
