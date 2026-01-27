#!/usr/bin/env python3
"""Validate district-level heat pump suitability CSV data files.

This script performs comprehensive data validation on the CSV files containing
heat pump suitability data for German districts. It checks for data quality
issues including schema compliance, value ranges, geometry completeness,
and state coverage.

Usage:
    python scripts/validate_data.py --data-dir ./webapp/data/districts
    python scripts/validate_data.py --data-dir ./webapp/data/districts --state Bayern
    python scripts/validate_data.py --help

Example:
    # Validate all district CSV files
    python scripts/validate_data.py --data-dir webapp/data/districts

    # Validate a specific state's data
    python scripts/validate_data.py --data-dir webapp/data/districts --state Bayern
"""

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("validate_data")

# Expected columns in the CSV files (excluding optional index column)
EXPECTED_COLUMNS = [
    "district",
    "building_type",
    "heat_source",
    "value",
    "federal_state",
    "district_type",
    "geometry",
]

# State to CSV filename mapping
STATE_FILE_MAPPING = {
    "Baden-Württemberg": "bw_full_data.csv",
    "Bayern": "by_full_data.csv",
    "Brandenburg": "bb_full_data.csv",
    "Bremen": "hb_full_data.csv",
    "Hamburg": "hh_full_data.csv",
    "Hessen": "he_full_data.csv",
    "Mecklenburg-Vorpommern": "mv_full_data.csv",
    "Niedersachsen": "ni_full_data.csv",
    "Nordrhein-Westfalen": "nw_full_data.csv",
    "Rheinland-Pfalz": "rp_full_data.csv",
    "Saarland": "sl_full_data.csv",
    "Sachsen": "sn_full_data.csv",
    "Sachsen-Anhalt": "st_full_data.csv",
    "Schleswig-Holstein": "sh_full_data.csv",
    "Thüringen": "th_full_data.csv",
}

# Valid building type codes
VALID_BUILDING_TYPES = {1, 6, 9, 11, 38, 100}

# Valid heat source codes
VALID_HEAT_SOURCES = {0, 1, 2, 3, 4}


@dataclass
class ValidationResult:
    """Container for validation results of a single file."""

    filename: str
    state: str
    is_valid: bool = True
    total_rows: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark validation as failed."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message (does not fail validation)."""
        self.warnings.append(message)


def check_columns_exist(df: pd.DataFrame, result: ValidationResult) -> bool:
    """Check if all expected columns exist in the DataFrame.

    Args:
        df: The DataFrame to validate.
        result: ValidationResult to record errors.

    Returns:
        True if all required columns exist, False otherwise.
    """
    # Get columns excluding unnamed index columns
    actual_columns = [c for c in df.columns if not c.startswith("Unnamed")]

    missing_columns = set(EXPECTED_COLUMNS) - set(actual_columns)
    if missing_columns:
        result.add_error(f"Missing columns: {sorted(missing_columns)}")
        return False

    extra_columns = set(actual_columns) - set(EXPECTED_COLUMNS)
    if extra_columns:
        # Extra columns are a warning, not an error
        result.add_warning(f"Extra columns found: {sorted(extra_columns)}")

    return True


def check_value_ranges(df: pd.DataFrame, result: ValidationResult) -> None:
    """Check that 'value' column contains valid proportions (0.0-1.0).

    Args:
        df: The DataFrame to validate.
        result: ValidationResult to record errors/warnings.
    """
    if "value" not in df.columns:
        return

    # Check for null values
    null_count = df["value"].isna().sum()
    if null_count > 0:
        result.add_error(f"Found {null_count} null values in 'value' column")

    # Filter out nulls for range checking
    valid_values = df["value"].dropna()

    if len(valid_values) == 0:
        result.add_error("No valid values in 'value' column")
        return

    min_val = valid_values.min()
    max_val = valid_values.max()

    if min_val < 0.0:
        result.add_error(f"Values below 0.0 found (min: {min_val:.4f})")

    if max_val > 1.0:
        result.add_error(f"Values above 1.0 found (max: {max_val:.4f})")

    # Report statistics as info
    logger.debug(
        "  Value stats - min: %.4f, max: %.4f, mean: %.4f, median: %.4f",
        min_val,
        max_val,
        valid_values.mean(),
        valid_values.median(),
    )


def check_no_null_geometries(df: pd.DataFrame, result: ValidationResult) -> None:
    """Check that no rows have null or empty geometry values.

    Args:
        df: The DataFrame to validate.
        result: ValidationResult to record errors.
    """
    if "geometry" not in df.columns:
        return

    # Check for null values
    null_count = df["geometry"].isna().sum()
    if null_count > 0:
        result.add_error(f"Found {null_count} rows with null geometry")

    # Check for empty strings
    empty_count = (df["geometry"] == "").sum()
    if empty_count > 0:
        result.add_error(f"Found {empty_count} rows with empty geometry string")

    # Check that geometries look like valid WKT (basic check)
    if "geometry" in df.columns:
        non_null_geom = df["geometry"].dropna()
        if len(non_null_geom) > 0:
            # Sample first few geometries to check WKT format
            sample = non_null_geom.head(5)
            invalid_format = sum(
                1
                for g in sample
                if not (str(g).startswith("POLYGON") or str(g).startswith("MULTI"))
            )
            if invalid_format > 0:
                result.add_warning(
                    "Some geometries may not be valid WKT "
                    "(expected POLYGON or MULTIPOLYGON prefix)"
                )


def check_building_types(df: pd.DataFrame, result: ValidationResult) -> None:
    """Check that building_type values are within expected codes.

    Args:
        df: The DataFrame to validate.
        result: ValidationResult to record errors/warnings.
    """
    if "building_type" not in df.columns:
        return

    unique_types = set(df["building_type"].dropna().unique())
    invalid_types = unique_types - VALID_BUILDING_TYPES

    if invalid_types:
        result.add_warning(f"Unexpected building_type codes: {sorted(invalid_types)}")

    missing_types = VALID_BUILDING_TYPES - unique_types
    if missing_types:
        result.add_warning(f"Missing building_type codes: {sorted(missing_types)}")


def check_heat_sources(df: pd.DataFrame, result: ValidationResult) -> None:
    """Check that heat_source values are within expected codes.

    Args:
        df: The DataFrame to validate.
        result: ValidationResult to record errors/warnings.
    """
    if "heat_source" not in df.columns:
        return

    unique_sources = set(df["heat_source"].dropna().unique())
    invalid_sources = unique_sources - VALID_HEAT_SOURCES

    if invalid_sources:
        result.add_warning(f"Unexpected heat_source codes: {sorted(invalid_sources)}")

    missing_sources = VALID_HEAT_SOURCES - unique_sources
    if missing_sources:
        result.add_warning(f"Missing heat_source codes: {sorted(missing_sources)}")


def check_federal_state_consistency(
    df: pd.DataFrame, expected_state: str, result: ValidationResult
) -> None:
    """Check that federal_state values are consistent with expected state.

    Args:
        df: The DataFrame to validate.
        expected_state: The expected state name based on filename.
        result: ValidationResult to record errors/warnings.
    """
    if "federal_state" not in df.columns:
        return

    unique_states = df["federal_state"].dropna().unique()
    if len(unique_states) == 0:
        result.add_error("No federal_state values found")
        return

    if len(unique_states) > 1:
        result.add_warning(f"Multiple federal_state values in file: {list(unique_states)}")

    # Check if the expected state is present
    if expected_state not in unique_states:
        result.add_warning(
            f"Expected state '{expected_state}' not found in data. "
            f"Found: {list(unique_states)}"
        )


def validate_csv_file(filepath: Path, state: str) -> ValidationResult:
    """Perform comprehensive validation on a single CSV file.

    Args:
        filepath: Path to the CSV file to validate.
        state: The expected state name for this file.

    Returns:
        ValidationResult with all errors and warnings.
    """
    result = ValidationResult(filename=filepath.name, state=state)
    logger.info("Validating: %s (%s)", filepath.name, state)

    # Check file exists
    if not filepath.exists():
        result.add_error(f"File not found: {filepath}")
        return result

    # Try to load the CSV
    try:
        df = pd.read_csv(filepath)
        result.total_rows = len(df)
        logger.debug("  Loaded %d rows", result.total_rows)
    except Exception as e:
        result.add_error(f"Failed to load CSV: {str(e)}")
        return result

    # Check for empty file
    if len(df) == 0:
        result.add_error("CSV file is empty (0 rows)")
        return result

    # Run all validation checks
    columns_ok = check_columns_exist(df, result)
    if columns_ok:
        check_value_ranges(df, result)
        check_no_null_geometries(df, result)
        check_building_types(df, result)
        check_heat_sources(df, result)
        check_federal_state_consistency(df, state, result)

    return result


def generate_validation_report(results: list[ValidationResult]) -> str:
    """Generate a human-readable validation report.

    Args:
        results: List of ValidationResult objects from all validated files.

    Returns:
        Formatted string containing the validation report.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("DATA VALIDATION REPORT")
    lines.append("Heat Pump Potentials Germany - District CSV Files")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    total_files = len(results)
    valid_files = sum(1 for r in results if r.is_valid)
    invalid_files = total_files - valid_files
    total_rows = sum(r.total_rows for r in results)

    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total files validated:  {total_files}")
    lines.append(f"  Files passing:          {valid_files}")
    lines.append(f"  Files with errors:      {invalid_files}")
    lines.append(f"  Total rows processed:   {total_rows:,}")
    lines.append("")

    # Overall status
    if invalid_files == 0:
        lines.append("OVERALL STATUS: PASS")
    else:
        lines.append("OVERALL STATUS: FAIL")
    lines.append("")

    # Detailed results per file
    lines.append("DETAILED RESULTS")
    lines.append("-" * 40)

    for result in results:
        status = "PASS" if result.is_valid else "FAIL"
        lines.append(f"\n{result.filename} ({result.state})")
        lines.append(f"  Status: {status}")
        lines.append(f"  Rows:   {result.total_rows:,}")

        if result.errors:
            lines.append("  Errors:")
            for error in result.errors:
                lines.append(f"    - {error}")

        if result.warnings:
            lines.append("  Warnings:")
            for warning in result.warnings:
                lines.append(f"    - {warning}")

        if not result.errors and not result.warnings:
            lines.append("  No issues found")

    lines.append("")
    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="validate_data",
        description=(
            "Validate heat pump suitability CSV data files. "
            "Checks for schema compliance, value ranges, geometry completeness, "
            "and state coverage."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s --data-dir webapp/data/districts\n"
            "  %(prog)s --data-dir webapp/data/districts --state Bayern\n"
            "\n"
            "Validation checks:\n"
            "  - All expected columns exist\n"
            "  - Value column in range [0.0, 1.0]\n"
            "  - No null or empty geometries\n"
            "  - Valid building_type and heat_source codes\n"
            "  - Consistent federal_state values\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing the district CSV files.",
    )

    parser.add_argument(
        "--state",
        type=str,
        choices=list(STATE_FILE_MAPPING.keys()),
        default=None,
        help="Validate only a specific state's data file.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Save validation report to file (default: print to stdout).",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code: 0 if all validations pass, 1 if any fail.
    """
    args = parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    data_dir = Path(args.data_dir)

    # Check data directory exists
    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
        return 1

    if not data_dir.is_dir():
        logger.error("Path is not a directory: %s", data_dir)
        return 1

    logger.info("=" * 60)
    logger.info("Data Validator - Heat Pump Suitability CSV Files")
    logger.info("=" * 60)
    logger.info("Data directory: %s", data_dir)

    # Determine which files to validate
    if args.state:
        # Validate single state
        states_to_validate = {args.state: STATE_FILE_MAPPING[args.state]}
        logger.info("Validating single state: %s", args.state)
    else:
        # Validate all states
        states_to_validate = STATE_FILE_MAPPING
        logger.info("Validating all %d states", len(states_to_validate))

    # Check that all expected files exist first
    missing_files = []
    for state, filename in states_to_validate.items():
        filepath = data_dir / filename
        if not filepath.exists():
            missing_files.append((state, filename))

    if missing_files:
        logger.warning("Missing files for states:")
        for state, filename in missing_files:
            logger.warning("  - %s: %s", state, filename)

    # Validate each file
    results = []
    for state, filename in states_to_validate.items():
        filepath = data_dir / filename
        result = validate_csv_file(filepath, state)
        results.append(result)

    # Generate and output report
    report = generate_validation_report(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Validation report saved to: %s", output_path)
    else:
        print(report)

    # Determine exit code
    all_valid = all(r.is_valid for r in results)
    if all_valid:
        logger.info("All validations passed!")
        return 0
    else:
        failed_count = sum(1 for r in results if not r.is_valid)
        logger.error("%d file(s) failed validation", failed_count)
        return 1


if __name__ == "__main__":
    sys.exit(main())
