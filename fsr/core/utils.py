"""
Utility functions for the Congregation Reporter project.
"""
from fsr.core.constants import (
    ROLE_NON_PIONEER, ROLE_AUXILIARY_PIONEER, ROLE_REGULAR_PIONEER, ROLE_SPECIAL_PIONEER,
    PIONEER_KEYWORD_AUXILIARY, PIONEER_KEYWORD_REGULAR, PIONEER_KEYWORD_SPECIAL
)

def get_publisher_role(report_pioneer_field: str | None) -> str:
    """
    Determines the publisher's role based on the 'pioneer' field from a report.

    Args:
        report_pioneer_field: The value of the 'pioneer' field (e.g., "Auxiliary", "Regular").
                              Can be None or an empty string.

    Returns:
        A string identifying the role: ROLE_NON_PIONEER, ROLE_AUXILIARY_PIONEER,
        ROLE_REGULAR_PIONEER, or ROLE_SPECIAL_PIONEER.
    """
    if not report_pioneer_field:
        return ROLE_NON_PIONEER

    field_lower = report_pioneer_field.lower()

    if PIONEER_KEYWORD_AUXILIARY in field_lower:
        return ROLE_AUXILIARY_PIONEER
    elif PIONEER_KEYWORD_REGULAR in field_lower:
        return ROLE_REGULAR_PIONEER
    elif PIONEER_KEYWORD_SPECIAL in field_lower:
        return ROLE_SPECIAL_PIONEER
    else:
        return ROLE_NON_PIONEER


def format_minutes_to_hr_min(minutes: int | None) -> str:
    """
    Formats a duration in minutes to a string "Xh YYm".

    Args:
        minutes: An integer representing the total minutes. Can be None.

    Returns:
        A string formatted as "Xh YYm" (e.g., 90 minutes -> "1h 30m").
        Returns "N/A" if the input is None or not an integer.
        Returns "0h 00m" if the input is 0.
    """
    if minutes is None:
        return "N/A"
    if not isinstance(minutes, int):
        return "N/A"
    if minutes == 0:
        return "0h 00m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours}h {remaining_minutes:02d}m"


def parse_year_month(year_month_str: str) -> tuple[int, int]:
    """
    Parses a "YYYY-MM" string into a tuple of integers (year, month).

    Args:
        year_month_str: A string in the format "YYYY-MM".

    Returns:
        A tuple (year, month) as integers.

    Raises:
        ValueError: If the input string is not in the "YYYY-MM" format
                    or if year/month are not valid integers.
    """
    if not isinstance(year_month_str, str):
        raise ValueError("Input must be a string.")

    parts = year_month_str.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid format: '{year_month_str}'. Expected 'YYYY-MM'.")

    year_str, month_str = parts
    if not (len(year_str) == 4 and year_str.isdigit() and \
            len(month_str) == 2 and month_str.isdigit()):
        raise ValueError(f"Invalid format: '{year_month_str}'. Expected 'YYYY-MM' with numeric parts.")

    try:
        year = int(year_str)
        month = int(month_str)
    except ValueError:
        # This case should ideally be caught by the isdigit checks, but as a safeguard:
        raise ValueError(f"Invalid numeric values in '{year_month_str}'. Year and month must be integers.")

    if not (1 <= month <= 12):
        raise ValueError(f"Month '{month}' out of range (1-12) in '{year_month_str}'.")

    # Assuming a reasonable range for years, e.g., not allowing year 0000.
    if year < 1000 or year > 9999: # Basic sanity check for year
        raise ValueError(f"Year '{year}' out of reasonable range in '{year_month_str}'.")

    return year, month
