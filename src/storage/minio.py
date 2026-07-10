import io
import logging
from minio import Minio
from minio.error import S3Error

from src.config.settings import settings
from src.utils.util import bytes_to_highest_unit_literal

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        """Initializes the MinIO client using settings and ensures the bucket exists."""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
        self._ensure_bucket_exists(settings.BUCKET_NAME)

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Creates the bucket if it doesn't already exist."""
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")

    def put_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str
    ) -> None:
        """
        Writes bytes directly to MinIO using an in-memory stream.
        No local disk I/O is performed.
        """
        # Wrap the bytes in an in-memory binary stream
        stream = io.BytesIO(data)
        len_data = len(data)
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=stream,
            length=len_data,
            content_type=content_type
        )
        nbytes = bytes_to_highest_unit_literal(len_data)
        logger.debug(f"Successfully wrote {nbytes} to {bucket_name}/{object_name}")

    def get_bytes(self, bucket_name: str, object_name: str) -> bytes:
        """
        Reads an object from MinIO and returns it as bytes in memory.
        """
        response = None
        try:
            response = self.client.get_object(bucket_name, object_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to get object {bucket_name}/{object_name}: {e}")
            raise
        finally:
            # close and release the connection back to the pool
            if response:
                response.close()
                response.release_conn()

    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """Checks if an object exists in MinIO without downloading it."""
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise

    # Dangerous function `:)`
    # def cleanup_layer(self, path: str) -> None:
    #     """Delete recursively a layer after confirmation."""
    #     confirmation = input(f"Confirm deletion of {path}, type \"Confirmation\": ")

    #     if confirmation != "Confirmation":
    #         print("Cancelation of deletion.")
    #         exit()
    #     print("3 seconds before fetching and deletion...")
    #     time.sleep(3)

    #     objects = self.client.list_objects(
    #         settings.BUCKET_NAME, 
    #         prefix=path, 
    #         recursive=True
    #     )

    #     count = 0
    #     for obj in objects:
    #         print(f"Deleting object {obj.object_name}...")
    #         client.client.remove_object(settings.BUCKET_NAME, obj.object_name) # type: ignore
    #         count += 1

    #     print(f"Successfully deleted {count} objects from {path}.")

