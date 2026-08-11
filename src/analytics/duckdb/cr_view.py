import duckdb
import logging
import time
from src.storage.log_handler import MinioLogHandler
from src.config.settings import settings
from src.storage.paths import s3_path
from src.storage.minio import MinioClient


logger = logging.getLogger(__name__)

def main() -> None:
    LOCAL_DB_PATH = "/mnt/storage/container/weather_analytics.duckdb"
    GPFX = settings.GOLD_PREFIX
    S3GPTH = s3_path(path=f"{GPFX}")
    TDGPFX = settings.TRANSFORMATION_DAILY_GLOBAL
    TDRPFX = settings.TRANSFORMATION_DAILY_REGIONAL
    TDG = s3_path(path=f"{GPFX}/{TDGPFX}/**/*.parquet")
    TDR = s3_path(path=f"{GPFX}/{TDRPFX}/**/*.parquet")

    queries = {
        "daily_global_aggregate_view" : f"""
            CREATE OR REPLACE VIEW daily_global AS
            SELECT *
            FROM read_parquet('{TDG}')
        """,

        "daily_regional_view" : f"""
            CREATE OR REPLACE VIEW daily_regional AS
            SELECT *
            FROM read_parquet('{TDR}')
        """
    }

    # Initialize MinIO
    minio_client = MinioClient()
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

    # Execute DuckDB
    try:
        with duckdb.connect(LOCAL_DB_PATH) as con:
            # Credentials
            con.execute("INSTALL httpfs; LOAD httpfs;")
            con.execute(f"SET s3_endpoint='{settings.MINIO_ENDPOINT}';")
            con.execute(f"SET s3_access_key_id='{settings.MINIO_ROOT_USER}';")
            con.execute(f"SET s3_secret_access_key='{settings.MINIO_ROOT_PASSWORD}';")
            con.execute("SET s3_region='eu-west-3';")
            con.execute("SET s3_use_ssl=false;")
            con.execute("SET s3_url_style='path';")
            # Execute Queries
            for name, query in queries.items():
                start = time.time()
                logger.info(f"Executing query: {name}")
                con.execute(query)
                logger.info(f"Query '{name}' execution time: {time.time() - start:.2f}s")
    except Exception as e:
        logger.error(f"Failure: {e}")
        raise
    finally:
        log_handler.flush()
        root_logger.removeHandler(log_handler)
        root_logger.removeHandler(console_handler)

if __name__ == "__main__":
    main()
