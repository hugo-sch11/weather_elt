from src.config.settings import settings


def s3_path(bucket: str=settings.BUCKET_NAME, path: str="") -> str:
    """
    s3://{bucket}/{path}
    """
    return f"s3://{bucket}/{path}"


def root_path(layer: str) -> str:
    """
    {layer}/
    """
    layer = layer.lower()
    if layer not in settings.LAYER_PREFIX:
        raise ValueError(f"The layer must in {settings.LAYER_PREFIX}.")
    return f"{layer}/"


def partition_path(layer: str, partition: str) -> str:
    """
    {layer}/date={partition}/
    """
    return (
        root_path(layer)
        + f"date={partition}/"
    )


def dataset_path(layer: str, partition: str) -> str:
    """
    {layer}/date={partition}/dataset.zarr
    """
    return (
        partition_path(layer, partition)
        + "dataset.zarr"
    )


def metadata_path(layer: str, partition: str) -> str:
    """
    {layer}/date={partition}/metadata.json
    """
    return (
        partition_path(layer, partition)
        + "metadata.json"
    )


def log_path(date: str) -> str:
    """
    log/ingestion{date}.log
    """
    return f"log/ingestion{date}.log"


def success_path(layer: str, partition: str) -> str:
    """
    {layer}/date={partition}/_SUCCESS
    """
    return (
        partition_path(layer, partition)
        + "_SUCCESS"
    )


# Includes transformations name (specific to gold)
def gold_path(transformation_name: str, partition_date: str) -> str:
    """
    f"{settings.GOLD_PREFIX}/{transfo_name}/date={partition_date}/"
    """
    return f"{settings.GOLD_PREFIX}/{transformation_name}/date={partition_date}/"

