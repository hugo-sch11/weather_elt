"""
Helper functions.
"""
import io
import xarray
from typing import Hashable
import fsspec
from datetime import datetime, timedelta
from xarray.core.dataset import Dataset

def bytes_to_highest_unit(nbytes, pten=0):
    """
    Parameters:
        `nbytes` (int|float): The number of bytes to convert.
        `p` (int, optional): The current power of 10 representing the unit scale.
            Defaults to 0.

    Returns:
        tuple[int,int]: A tuple containing the scaled number of bytes and the
        corresponding power of 10 (0, 3, 6, 9, 12, or 15).
    """
    if (nbytes % 1024) == nbytes or pten == 15:
        return nbytes, pten
    else:
        return bytes_to_highest_unit(nbytes / 1024, pten+3)


def power_of_ten_to_literal(p:int) -> str:
    """Converts a power of ten to its corresponding metric prefix literal.

    Parameters:
        `p` (int): The power of ten. Must be one of 0, 3, 6, 9, 12, or 15.

    Returns:
        str: The matching metric prefix ("", "Kilo", "Mega", "Giga", "Tera",
        or "Peta").

    Raises:
        ValueError: If `p` is not a valid power of 10 (0, 3, 6, 9, 12, 15).
    """
    match p:
        case 0:
            return ""
        case 3:
            return "K" # Kilo
        case 6:
            return "M" # Mega
        case 9:
            return "G" # Giga
        case 12:
            return "T" # Tera
        case 15:
            return "P" # Peta
        case _:
            raise ValueError("p must be 0, 3, 6, 9, 12 or 15")

def bytes_to_highest_unit_literal(nbytes) -> str:
    """Converts a number of bytes to a human-readable string with a metric prefix.

    Parameters:
        `nbytes` (int|float): The number of bytes to convert.

    Returns:
        str: A formatted string combining the scaled bit count and its metric
        prefix (e.g., "1500KiloBits").
    """
    nbytes, pten = bytes_to_highest_unit(nbytes)
    return f"{nbytes:.2f}{power_of_ten_to_literal(pten)}B" # Bytes


def get_next_day(date: str) -> str:
    """
    Parameters:
        `date` (str): The date in ISO 8601 (YYYY-MM-DD).
    Returns:
        str: The ISO 8601 date (YYYY-MM-DD) that is the day after `date`.
    """
    return (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


def get_date_list(date: str, duration: int) -> list[str]:
    """
    Parameters:
        `date` (str): The start date in ISO 8601 (YYYY-MM-DD).
        `duration` (int): The number of days to include (`date`+`duration`).
    Returns:
        list[str]: All the days from `date` to `date` + `duration` in ISO 8601 (YYYY-MM-DD).
    Example:
        >>> get_date_list("2025-01-01", 3)
        ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04']
    """
    date_datetime = datetime.strptime(date, "%Y-%m-%d")
    return [
        (date_datetime + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(duration+1)
    ]


def get_delta_two_dates(date1: str, date2: str) -> int:
    """Returns number of days separating two str dates(YYYY-MM-DD)"""
    date1_datetime = datetime.strptime(date1, "%Y-%m-%d")
    date2_datetime = datetime.strptime(date2, "%Y-%m-%d")
    return (date2_datetime - date1_datetime).days


def dataset_to_bytes(dataset: Dataset) -> bytes:
    buffer = io.BytesIO()
    dataset.to_netcdf(buffer)
    return buffer.getvalue()


def bytes_to_dataset(bytes_data: bytes) -> Dataset:
    buffer = io.BytesIO(bytes_data)
    return xarray.open_dataset(buffer)


def is_null_variable_percentage(dataset: xarray.Dataset, var_name: Hashable, threshold_percentage: float = 10.00) -> bool:
    """Checks whether a variable is null up to the `threshold` percentage in a dataset."""
    total_elements = dataset[var_name].size
    if total_elements == 0:
        return True
    non_null_count = int(dataset[var_name].count().compute())
    null_percentage = (1.0 - (non_null_count / total_elements)) * 100
    return null_percentage >= threshold_percentage


def main():
    test_bytes = 10000000000000 # 10*10**12
    print(f"{test_bytes}Bytes = {bytes_to_highest_unit_literal(test_bytes)}")
    test_date = "2026-06-30"
    print(f"One day : {test_date}, and its next day : {get_next_day(test_date)}")
    print(f"One day and its 3 next days : {get_date_list(test_date, 3)}")
    print(f"365days of 800MB/days = {bytes_to_highest_unit_literal((800*10**6)*365)}")
    test_dates = ("2025-01-01", "2025-01-13")
    print(f"{test_dates}, gap : {get_delta_two_dates(*test_dates)} days")


if __name__ == "__main__":
    main()
