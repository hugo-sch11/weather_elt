from dataclasses import dataclass
from datetime import datetime, timezone, date
import dataclasses
import json
import xarray as xr
from typing import Any, Hashable

@dataclass
class IngestionMetadata:
    source: str
    partition_date: str
    ingestion_timestamp: str
    start_time: str
    end_time: str
    variable_count: int
    variables: list[str]
    dataset_size_bytes: int

def build_ingestion_metadata(
    dataset: xr.Dataset,
    source: str,
    partition_date: str
) -> IngestionMetadata:

    return IngestionMetadata(
        source=source,
        partition_date=partition_date,
        ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
        start_time=str(dataset.time.min().values),
        end_time=str(dataset.time.max().values),
        variable_count=len(dataset.data_vars),
        variables=list(dataset.data_vars), # type: ignore[arg-type]
        dataset_size_bytes=dataset.nbytes
    )

@dataclass
class SilverMetadata:
    layer: str
    source: str
    partition_date: str
    variables_kept: list[str]
    variables_dropped: list[Hashable]
    variables_derived: list[Hashable]
    start_time: str
    end_time: str
    ingestion_timestamp: str
    execution_duration_seconds: float
    dataset_size_bytes: int

def build_silver_metadata(
    dataset: xr.Dataset,
    source: str,
    partition_date: str,
    vars_dropped: list[Hashable],
    vars_derived: list[Hashable],
    execution_time: float
) -> SilverMetadata:
    return SilverMetadata(
        layer="silver",
        source=source,
        partition_date=partition_date,
        variables_kept=list(dataset.data_vars), # type: ignore[arg-type]
        variables_dropped=vars_dropped,
        variables_derived=vars_derived,
        start_time=str(dataset.time.min().values),
        end_time=str(dataset.time.max().values),
        ingestion_timestamp=datetime.now(timezone.utc).isoformat(),
        execution_duration_seconds=round(execution_time, 2),
        dataset_size_bytes=dataset.nbytes
    )

@dataclass
class GoldMetadata:
    layer: str
    source: str
    partition_date: str
    transformation_name: str
    aggregation_logic: str | dict[str,Any] 
    spatial_bounds: str | dict[str,Any]
    row_count: int
    file_size_bytes: int
    ingestion_timestamp: str
    execution_duration_seconds: float

def build_gold_metadata(
    row_count: int,
    source: str,
    partition_date: str,
    transformation_name: str,
    aggregation_logic: str | dict[str, Any],
    spatial_bounds: str | dict[str, Any],
    file_size_bytes: int,
    execution_time: float,
) -> GoldMetadata:
    return GoldMetadata(
        row_count=row_count,
        source=source,
        partition_date=partition_date,
        transformation_name=transformation_name,
        aggregation_logic=aggregation_logic,
        spatial_bounds=spatial_bounds,
        file_size_bytes=file_size_bytes,
        execution_duration_seconds=round(execution_time, 2),
        layer="gold",
        ingestion_timestamp=datetime.now(timezone.utc).isoformat()
    )

def metadata_to_bytes(metadata_obj) -> bytes:
    """
    Converts a dataclass to JSON bytes, safely handling datetimes.
    """
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, slice):
            return {"start": obj.start, "stop": obj.stop, "step": obj.step}
        raise TypeError(f"Type {type(obj)} not serializable")

    metadata_dict = dataclasses.asdict(metadata_obj)
    json_str = json.dumps(metadata_dict, indent=2, default=json_serial)
    return json_str.encode("utf-8")
