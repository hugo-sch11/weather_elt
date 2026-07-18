import logging
import threading

from datetime import date
from src.storage.minio import MinioClient
from src.config.settings import settings
from src.storage.paths import log_path


class MinioLogHandler(logging.Handler):
    """
    Buffers log records in memory and flushes them to a single
    MinIO object per partition date (one file per day).
    """
    def __init__(self, minio_client: MinioClient):
        super().__init__()
        self.minio_client = minio_client
        self.object_name = log_path(date.today().isoformat())
        self._buffer: list[str] = []
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        with self._lock:
            self._buffer.append(self.format(record) + "\n")

    def flush(self) -> None:
        with self._lock:
            data = "".join(self._buffer).encode("utf-8")
            self.minio_client.put_bytes(
                bucket_name=settings.BUCKET_NAME,
                object_name=self.object_name,
                data=data,
                content_type="text/plain",
            )


    def get_log_content(self, name: str = "") -> str:
        """
        Fetch the log content as a string.
        Parameter:
            name (str): is the name of the log, advise to use log_path function from src/storage/paths, see example.
        Example:
        >>>minio_client = MinioClient()
        >>>log_handler = MinioLogHandler(minio_client)
        >>>log = log_handler.get_log_content(log_path("2026-06-25"))
        """
        with self._lock:
            return self.minio_client.get_bytes(
                bucket_name=settings.BUCKET_NAME, 
                object_name=name if name != "" else self.object_name
            ).decode("utf-8")

