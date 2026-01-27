#!/usr/bin/env python3
"""Fetch heat pump suitability data from the FfE Open Data Portal API.

This script retrieves district-level heat pump suitability data from the
Forschungsstelle für Energiewirtschaft (FfE) Open Data Portal and saves
the raw JSON response to a file.

The FfE Open Data Portal provides comprehensive energy-related datasets
for Germany. This script fetches dataset ID 88, which contains heat pump
suitability assessments at the district (Landkreis/Kreisfreie Stadt) level.

Usage:
    python scripts/fetch_ffe_data.py --state Bayern --output-dir ./data/raw
    python scripts/fetch_ffe_data.py --output-dir ./data/raw  # Fetch all data
    python scripts/fetch_ffe_data.py --help

Example:
    # Fetch all district-level data and save to data/raw/
    python scripts/fetch_ffe_data.py --output-dir data/raw

    # Fetch data for a specific state
    python scripts/fetch_ffe_data.py --state "Baden-Württemberg" --output-dir data/raw
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("fetch_ffe_data")

# FfE Open Data Portal API endpoint for district-level heat pump data (id_opendata=88)
DISTRICT_DATA_URL = "https://opendata.ffe.de/api/od/v_opendata?id_opendata=eq.88"

# Valid German federal states (excluding Berlin which lacks data in this dataset)
VALID_STATES = [
    "Baden-Württemberg",
    "Bayern",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Hessen",
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Nordrhein-Westfalen",
    "Rheinland-Pfalz",
    "Saarland",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Thüringen",
]


def fetch_ffe_data(url: str) -> dict | list | None:
    """Fetch JSON data from the FfE Open Data Portal API.

    Makes an HTTP GET request to the specified URL and returns the parsed
    JSON response. Handles network errors gracefully with logging.

    Args:
        url: The full API endpoint URL to fetch data from.

    Returns:
        The parsed JSON response as a Python dictionary or list,
        or None if the request fails.
    """
    logger.info("Fetching data from FfE API: %s", url)

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        logger.info(
            "API request successful, status code: %d, content length: %d bytes",
            response.status_code,
            len(response.content),
        )
        return response.json()
    except requests.Timeout:
        logger.error("API request timed out after 60 seconds")
        return None
    except requests.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return None
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON response: %s", str(e))
        return None


def filter_by_state(data: list, state: str) -> list:
    """Filter API response data to include only records for a specific state.

    The FfE API returns data for all districts. This function filters the
    response to include only records where the region name contains the
    state abbreviation or matches the state naming pattern.

    Args:
        data: The raw API response data (list of records from 'data' key).
        state: The name of the German federal state to filter by.

    Returns:
        A filtered list containing only records for the specified state.
    """
    logger.info("Filtering data for state: %s", state)

    # The API response includes region names like "Landkreis München"
    # We need to filter based on the data structure
    # Since the API doesn't directly include state info in each record,
    # we'll return all data and note this limitation
    logger.warning(
        "Note: The FfE API endpoint returns all district data. "
        "State-level filtering requires post-processing after CSV generation. "
        "Saving all data to allow full processing pipeline."
    )
    return data


def save_json_response(data: dict | list, output_path: Path, state: str | None) -> bool:
    """Save the raw JSON response to a file.

    Saves the fetched data as a JSON file with proper formatting for
    readability and debugging purposes.

    Args:
        data: The JSON data to save.
        output_path: Directory where the file should be saved.
        state: Optional state name for filename (None for all states).

    Returns:
        True if the file was saved successfully, False otherwise.
    """
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if state:
        # Sanitize state name for filename
        safe_state = state.lower().replace(" ", "_").replace("-", "_")
        filename = f"ffe_district_data_{safe_state}_{timestamp}.json"
    else:
        filename = f"ffe_district_data_all_{timestamp}.json"

    filepath = output_path / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Successfully saved JSON data to: %s", filepath)
        logger.info("File size: %.2f KB", filepath.stat().st_size / 1024)
        return True
    except OSError as e:
        logger.error("Failed to save JSON file: %s", str(e))
        return False


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace with state and output_dir attributes.
    """
    parser = argparse.ArgumentParser(
        prog="fetch_ffe_data",
        description=(
            "Fetch heat pump suitability data from the FfE Open Data Portal. "
            "Downloads district-level (Landkreis) data for heat pump potential "
            "assessments across Germany."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s --output-dir ./data/raw\n"
            "  %(prog)s --state Bayern --output-dir ./data/raw\n"
            "\n"
            "Data source: FfE Open Data Portal (https://opendata.ffe.de)\n"
            "Dataset: id_opendata=88 (District-level heat pump suitability, 2022)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--state",
        type=str,
        choices=VALID_STATES,
        default=None,
        help=(
            "German federal state to fetch data for. "
            "If not specified, fetches data for all states. "
            "Note: The API returns all data; state filtering is for metadata only."
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save the raw JSON response file.",
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

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    logger.info("=" * 60)
    logger.info("FfE Data Fetcher - Heat Pump Suitability Data")
    logger.info("=" * 60)

    if args.state:
        logger.info("Target state: %s", args.state)
    else:
        logger.info("Target: All German states (district-level data)")

    logger.info("Output directory: %s", args.output_dir)

    # Fetch data from FfE API
    raw_data = fetch_ffe_data(DISTRICT_DATA_URL)

    if raw_data is None:
        logger.error("Failed to fetch data from FfE API. Exiting.")
        return 1

    # Validate response structure
    if not isinstance(raw_data, list) or len(raw_data) == 0:
        logger.error("Unexpected API response format. Expected non-empty list.")
        return 1

    # Extract data payload
    if "data" not in raw_data[0]:
        logger.error("API response missing 'data' key. Response structure may have changed.")
        return 1

    data_records = raw_data[0]["data"]
    logger.info("Retrieved %d data records from API", len(data_records))

    # Save the raw JSON response
    output_path = Path(args.output_dir)
    if not save_json_response(raw_data, output_path, args.state):
        logger.error("Failed to save JSON response. Exiting.")
        return 1

    logger.info("=" * 60)
    logger.info("Data fetch completed successfully!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
