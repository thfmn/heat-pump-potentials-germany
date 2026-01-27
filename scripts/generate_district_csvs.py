#!/usr/bin/env python3
"""Generate district-level CSV files from raw FfE JSON data.

This script transforms raw JSON data fetched from the FfE Open Data Portal
into CSV files with WKT geometry for use in the Heat Pump Potentials Germany
web application.

The transformation process includes:
- Parsing the FfE API JSON response
- Filtering by federal state
- Merging with district geometry (from existing CSVs or GeoJSON)
- Validating output schema
- Saving to CSV format

Usage:
    python scripts/generate_district_csvs.py --input-dir ./data/raw \\
        --output-dir ./webapp/data/districts
    python scripts/generate_district_csvs.py --input-dir ./data/raw \\
        --output-dir ./output --state Bayern
    python scripts/generate_district_csvs.py --help

Example:
    # Transform all states
    python scripts/generate_district_csvs.py --input-dir data/raw --output-dir webapp/data/districts

    # Transform a specific state
    python scripts/generate_district_csvs.py --input-dir data/raw \\
        --output-dir output --state "Baden-Württemberg"
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("generate_district_csvs")

# Valid German federal states and their CSV filename abbreviations
STATE_TO_ABBREV = {
    "Baden-Württemberg": "bw",
    "Bayern": "by",
    "Brandenburg": "bb",
    "Bremen": "hb",
    "Hamburg": "hh",
    "Hessen": "he",
    "Mecklenburg-Vorpommern": "mv",
    "Niedersachsen": "ni",
    "Nordrhein-Westfalen": "nw",
    "Rheinland-Pfalz": "rp",
    "Saarland": "sl",
    "Sachsen": "sn",
    "Sachsen-Anhalt": "st",
    "Schleswig-Holstein": "sh",
    "Thüringen": "th",
}

# Expected CSV columns in the correct order
EXPECTED_COLUMNS = [
    "district",
    "building_type",
    "heat_source",
    "value",
    "federal_state",
    "district_type",
    "geometry",
]


def find_latest_json(input_dir: Path, state: str | None = None) -> Path | None:
    """Find the most recent FfE JSON file in the input directory.

    Args:
        input_dir: Directory containing raw JSON files.
        state: Optional state name to filter for.

    Returns:
        Path to the most recent JSON file, or None if not found.
    """
    pattern = "ffe_district_data_*.json"
    json_files = sorted(input_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if not json_files:
        logger.error("No FfE JSON files found in %s", input_dir)
        return None

    # Return most recent file
    return json_files[0]


def load_json_data(json_path: Path) -> list | None:
    """Load and parse the raw FfE JSON data.

    Args:
        json_path: Path to the JSON file.

    Returns:
        The data records from the JSON, or None if loading fails.
    """
    logger.info("Loading JSON data from: %s", json_path)

    try:
        with open(json_path, encoding="utf-8") as f:
            raw_data = json.load(f)

        # Validate structure
        if not isinstance(raw_data, list) or len(raw_data) == 0:
            logger.error("Unexpected JSON format: expected non-empty list")
            return None

        if "data" not in raw_data[0]:
            logger.error("JSON missing 'data' key in first element")
            return None

        data_records = raw_data[0]["data"]
        logger.info("Loaded %d data records from JSON", len(data_records))
        return data_records

    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON: %s", str(e))
        return None
    except OSError as e:
        logger.error("Failed to read file: %s", str(e))
        return None


def transform_to_dataframe(data_records: list) -> pd.DataFrame:
    """Transform raw data records into a pandas DataFrame.

    Cleans column names and extracts relevant fields from the FfE API response.

    Args:
        data_records: List of data dictionaries from the FfE API.

    Returns:
        Cleaned DataFrame with standardized columns.
    """
    df = pd.DataFrame(data_records)

    # Drop columns that are all null
    df = df.dropna(axis=1, how="all")

    # Drop metadata columns
    drop_cols = ["id_opendata", "id_region_type", "region_type", "year", "internal_id"]
    existing_drop_cols = [c for c in drop_cols if c in df.columns]
    df = df.drop(columns=existing_drop_cols)

    # Rename columns to match expected schema
    rename_map = {
        "internal_id_1": "building_type",
        "internal_id_2": "heat_source",
        "region": "district",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop id_region if present (replaced by district name)
    if "id_region" in df.columns:
        df = df.drop(columns=["id_region"])

    logger.info("Transformed DataFrame: %d rows, columns: %s", len(df), list(df.columns))
    return df


def extract_state_from_district(district_name: str) -> str | None:
    """Extract federal state from district name if embedded.

    The FfE data sometimes includes state info in the district name.
    This is a fallback method for state identification.

    Args:
        district_name: The district name string.

    Returns:
        State name if found, None otherwise.
    """
    # This is a simplified approach - the actual mapping requires
    # external data (AGS codes or geography database)
    return None


def load_geometry_from_existing_csv(
    csv_dir: Path, state: str, state_abbrev: str
) -> pd.DataFrame | None:
    """Load geometry data from existing CSV files.

    The existing CSVs contain pre-processed WKT geometry from the notebook's
    complex GeoJSON merging process with manual corrections.

    Args:
        csv_dir: Directory containing existing CSV files.
        state: State name for logging.
        state_abbrev: State abbreviation for filename.

    Returns:
        DataFrame with district, district_type, geometry columns, or None if not found.
    """
    csv_path = csv_dir / f"{state_abbrev}_full_data.csv"

    if not csv_path.exists():
        logger.warning("Existing CSV not found for geometry: %s", csv_path)
        return None

    try:
        # Read only the columns we need for geometry
        df = pd.read_csv(csv_path, usecols=["district", "district_type", "geometry"])

        # Get unique district geometries (they repeat for each building_type/heat_source combo)
        geometry_df = df.drop_duplicates(subset=["district"]).reset_index(drop=True)

        logger.info("Loaded geometry for %d districts from %s", len(geometry_df), csv_path)
        return geometry_df

    except (pd.errors.EmptyDataError, KeyError) as e:
        logger.error("Failed to load geometry from %s: %s", csv_path, str(e))
        return None


def validate_output_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate that the output DataFrame has the expected schema.

    Args:
        df: DataFrame to validate.

    Returns:
        Tuple of (is_valid, list of issues found).
    """
    issues = []

    # Check required columns
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")

    # Check value ranges
    if "value" in df.columns:
        if df["value"].min() < 0.0:
            issues.append(f"Value column has negative values: min={df['value'].min()}")
        if df["value"].max() > 1.0:
            issues.append(f"Value column exceeds 1.0: max={df['value'].max()}")

    # Check for null geometries
    if "geometry" in df.columns:
        null_geom_count = df["geometry"].isna().sum()
        if null_geom_count > 0:
            issues.append(f"Found {null_geom_count} null geometry values")

    # Check building_type values
    valid_building_types = {1, 6, 9, 11, 38, 100}
    if "building_type" in df.columns:
        invalid_bt = set(df["building_type"].unique()) - valid_building_types
        if invalid_bt:
            issues.append(f"Invalid building_type values: {invalid_bt}")

    # Check heat_source values
    valid_heat_sources = {0, 1, 2, 3, 4}
    if "heat_source" in df.columns:
        invalid_hs = set(df["heat_source"].unique()) - valid_heat_sources
        if invalid_hs:
            issues.append(f"Invalid heat_source values: {invalid_hs}")

    is_valid = len(issues) == 0
    return is_valid, issues


def generate_csv_for_state(
    df: pd.DataFrame,
    state: str,
    state_abbrev: str,
    output_dir: Path,
    geometry_source_dir: Path | None = None,
) -> bool:
    """Generate CSV file for a single state.

    Args:
        df: Full DataFrame with all data records.
        state: State name to filter for.
        state_abbrev: State abbreviation for output filename.
        output_dir: Directory to save the CSV.
        geometry_source_dir: Directory with existing CSVs for geometry lookup.

    Returns:
        True if CSV was generated successfully, False otherwise.
    """
    logger.info("Generating CSV for state: %s", state)

    # Filter data for this state
    # Note: The FfE API data doesn't include explicit state column in the raw data
    # State information needs to be derived from district-to-state mapping
    # For now, we'll use the existing CSV approach with geometry

    # Load geometry from existing CSV
    if geometry_source_dir:
        geometry_df = load_geometry_from_existing_csv(geometry_source_dir, state, state_abbrev)
        if geometry_df is None:
            logger.error("Cannot generate CSV without geometry data for %s", state)
            return False

        # Get list of districts in this state from geometry
        state_districts = set(geometry_df["district"].unique())

        # Filter main data to only include districts in this state
        state_df = df[df["district"].isin(state_districts)].copy()

        if len(state_df) == 0:
            logger.warning("No matching data records found for state: %s", state)
            return False

        # Merge geometry
        state_df = state_df.merge(geometry_df, on="district", how="left")

        # Add federal_state column
        state_df["federal_state"] = state

    else:
        logger.error("Geometry source directory required for CSV generation")
        return False

    # Validate output schema
    is_valid, issues = validate_output_schema(state_df)
    if not is_valid:
        logger.error("Schema validation failed for %s:", state)
        for issue in issues:
            logger.error("  - %s", issue)
        return False

    # Reorder columns to match expected schema
    state_df = state_df[EXPECTED_COLUMNS]

    # Save to CSV
    output_path = output_dir / f"{state_abbrev}_full_data.csv"
    try:
        state_df.to_csv(output_path, index=True)
        logger.info("Saved CSV: %s (%d rows)", output_path, len(state_df))
        return True
    except OSError as e:
        logger.error("Failed to save CSV: %s", str(e))
        return False


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="generate_district_csvs",
        description=(
            "Generate district-level CSV files from raw FfE JSON data. "
            "Transforms API responses into the format required by the "
            "Heat Pump Potentials Germany web application."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s --input-dir ./data/raw --output-dir ./webapp/data/districts\n"
            "  %(prog)s --input-dir ./data/raw --output-dir ./output --state Bayern\n"
            "\n"
            "Note: This script requires existing CSV files with geometry data\n"
            "to merge WKT polygons. The geometry was originally processed from\n"
            "GeoJSON with manual corrections in the district_map_generation notebook."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing raw FfE JSON file(s) from fetch_ffe_data.py.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save generated CSV files.",
    )

    parser.add_argument(
        "--state",
        type=str,
        choices=list(STATE_TO_ABBREV.keys()),
        default=None,
        help="Generate CSV for a specific state only. If not specified, generates all states.",
    )

    parser.add_argument(
        "--geometry-dir",
        type=str,
        default=None,
        help=(
            "Directory containing existing CSVs with WKT geometry. "
            "Defaults to --output-dir if not specified."
        ),
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    args = parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("=" * 60)
    logger.info("Generate District CSVs - Heat Pump Potentials Germany")
    logger.info("=" * 60)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    geometry_dir = Path(args.geometry_dir) if args.geometry_dir else output_dir

    # Validate input directory
    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return 1

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find and load JSON data
    json_path = find_latest_json(input_dir)
    if json_path is None:
        return 1

    data_records = load_json_data(json_path)
    if data_records is None:
        return 1

    # Transform to DataFrame
    df = transform_to_dataframe(data_records)

    # Determine which states to process
    if args.state:
        states_to_process = [(args.state, STATE_TO_ABBREV[args.state])]
    else:
        states_to_process = list(STATE_TO_ABBREV.items())

    logger.info("Processing %d state(s)", len(states_to_process))

    # Process each state with progress bar
    success_count = 0
    failed_states = []

    for state, abbrev in tqdm(states_to_process, desc="Generating CSVs", unit="state"):
        if generate_csv_for_state(df, state, abbrev, output_dir, geometry_dir):
            success_count += 1
        else:
            failed_states.append(state)

    # Summary
    logger.info("=" * 60)
    total_states = len(states_to_process)
    logger.info("Generation complete: %d/%d states successful", success_count, total_states)
    if failed_states:
        logger.warning("Failed states: %s", ", ".join(failed_states))
        return 1

    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
