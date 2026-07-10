import logging
import xarray

from src.quality.schema import DatasetSchema

logger = logging.getLogger(__name__)

class DataQualityError(Exception):
    """Raised when a dataset fails quality validation."""
    pass

def validate_dataset(dataset: xarray.Dataset, schema: DatasetSchema) -> None:
    """
    Validates an xarray Dataset against a defined schema.
    Uses lazy evaluation (Dask) under the hood to avoid loading full arrays into RAM.

    Raises:
        DataQualityError: If any validation check fails.
    """
    errors = []
    logger.info(f"Starting quality validation for schema '{schema.name}'...")

    # Validate Coordinates
    for coord_name, spec in schema.required_coordinates.items():
        if coord_name not in dataset.coords:
            errors.append(f"Missing coordinate: '{coord_name}'")
            continue

        # Check physical bounds
        if spec.min_val is not None or spec.max_val is not None:
            # .compute() triggers the Dask graph for this specific coordinate
            coord_min = float(dataset[coord_name].min(skipna=True).compute())
            coord_max = float(dataset[coord_name].max(skipna=True).compute())

            if spec.min_val is not None and coord_min < spec.min_val:
                errors.append(f"Coordinate '{coord_name}' min value {coord_min} is below {spec.min_val}")
            if spec.max_val is not None and coord_max > spec.max_val:
                errors.append(f"Coordinate '{coord_name}' max value {coord_max} is above {spec.max_val}")

    # Validate Variables
    for var_name, spec in schema.required_variables.items():
        if var_name not in dataset.data_vars:
            errors.append(f"Missing variable: '{var_name}'")
            continue

        var = dataset[var_name]

        # Check Physical Bounds (Lazy evaluation)
        if spec.min_val is not None or spec.max_val is not None:
            var_min = float(var.min(skipna=True).compute())
            var_max = float(var.max(skipna=True).compute())

            if spec.min_val is not None and var_min < spec.min_val:
                errors.append(f"Variable '{var_name}' min value {var_min} is below {spec.min_val}")
            if spec.max_val is not None and var_max > spec.max_val:
                errors.append(f"Variable '{var_name}' max value {var_max} is above {spec.max_val}")

    # Validate Time Continuity / Completeness
    if schema.expected_time_steps is not None:
        if "time" not in dataset.dims:
            errors.append("Missing 'time' dimension.")
        else:
            actual_steps = dataset.sizes["time"]
            if actual_steps != schema.expected_time_steps:
                errors.append(f"Expected {schema.expected_time_steps} time steps, but found {actual_steps}")

    # Raise Exception if any errors were found
    if errors:
        error_msg = "Data Quality Validation Failed:\n" + "\n".join(f"- {e}" for e in errors)
        logger.error(error_msg)
        raise DataQualityError(error_msg)

    logger.info(f"Dataset successfully passed all quality checks for schema '{schema.name}'.")
