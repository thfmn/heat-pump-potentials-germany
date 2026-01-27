"""Shared utility functions for the heat pump webapp."""

from config import BUILDING_TYPE_MAPPING, FEDERAL_STATES, HEAT_SOURCE_MAPPING

# Allowed values for input validation
ALLOWED_BUILDING_TYPES = set(BUILDING_TYPE_MAPPING.values())
ALLOWED_HEAT_SOURCES = set(HEAT_SOURCE_MAPPING.values())
ALLOWED_STATES = set(FEDERAL_STATES) | {"(Deutschland)"}


class InputValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_inputs(building_type: str, heat_source: str, selected_state: str) -> None:
    """
    Validate user inputs against allowed values from config.py.

    Args:
        building_type: The building type to validate.
        heat_source: The heat source to validate.
        selected_state: The state selection to validate.

    Raises:
        InputValidationError: If any input is not in the allowed values.
    """
    if building_type not in ALLOWED_BUILDING_TYPES:
        raise InputValidationError(
            f"Invalid building type: '{building_type}'. "
            f"Allowed values: {sorted(ALLOWED_BUILDING_TYPES)}"
        )

    if heat_source not in ALLOWED_HEAT_SOURCES:
        raise InputValidationError(
            f"Invalid heat source: '{heat_source}'. "
            f"Allowed values: {sorted(ALLOWED_HEAT_SOURCES)}"
        )

    if selected_state not in ALLOWED_STATES:
        raise InputValidationError(
            f"Invalid state: '{selected_state}'. "
            f"Allowed values: {sorted(ALLOWED_STATES)}"
        )
