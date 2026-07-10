from dataclasses import dataclass

# bounds according to src/ingestion/lookup_post_ingestion.py
@dataclass(frozen=True)
class CoordinateSpec:
    """Defines constraints for coordinate."""
    dtype: str
    min_val: float | None = None
    max_val: float | None = None

@dataclass(frozen=True)
class VariableSpec:
    """Defines constraints for data variable."""
    dtype: str
    min_val: float | None = None
    max_val: float | None = None

@dataclass(frozen=True)
class DatasetSchema:
    """The complete schema definition for an xarray Dataset."""
    name: str
    required_variables: dict[str, VariableSpec]
    required_coordinates: dict[str, CoordinateSpec]
    expected_time_steps: int | None = None

# --- Specific Schema for NOAA GFS Bronze Layer ---
# GFS standard units: Temp = C, Wind = m/s, Precip = kg/m^2/s (>= 0)
NOAA_GFS_BRONZE_SCHEMA = DatasetSchema(
    name="noaa_gfs_bronze",
    expected_time_steps=24,
    required_coordinates={
        "time": CoordinateSpec(dtype="datetime64[ns]"),
        "latitude": CoordinateSpec(dtype="float64", min_val=-90.0, max_val=90.0),
        "longitude": CoordinateSpec(dtype="float64", min_val=-180.0, max_val=180.0),
    },
    required_variables={
        "precipitation_surface": VariableSpec(dtype="float32", min_val=0.0, max_val=1.0),
        "temperature_2m": VariableSpec(dtype="float64", min_val=-80.0, max_val=54.0),
        "wind_u_10m": VariableSpec(dtype="float64", min_val=-97.0, max_val=88.0),
        "wind_v_10m": VariableSpec(dtype="float64", min_val=-88.0, max_val=89.0),
    }
)
