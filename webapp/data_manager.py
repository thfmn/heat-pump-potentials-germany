"""Data management module for fetching, preprocessing, and querying heat pump data.

This module handles all data operations including:
- Fetching raw data from the FfE Open Data Portal API
- Preprocessing and transforming API responses into clean DataFrames
- Converting numeric category codes to human-readable labels
- Executing filtered queries using DuckDB with parameterized SQL

All database queries use parameterized placeholders to prevent SQL injection,
and all user inputs are validated against allowed values before execution.
"""
import logging

import duckdb
import pandas as pd
import requests
from config import BUILDING_TYPE_MAPPING, HEAT_SOURCE_MAPPING
from utils import validate_inputs

# Get logger instance
logger = logging.getLogger("heat_pump_webapp")


def fetch_data(url):
    """Fetch JSON data from the FfE Open Data Portal API.

    Makes an HTTP GET request to the specified URL and returns the parsed JSON response.
    Logs the request status and handles network errors gracefully.

    Args:
        url: The full API endpoint URL to fetch data from.

    Returns:
        The parsed JSON response as a Python dictionary/list, or None if the request fails.

    Raises:
        No exceptions are raised; errors are logged and None is returned.
    """
    logger.info("Fetching data from API: %s", url)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logger.info("API request successful, status code: %d", response.status_code)
        return response.json()
    except requests.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return None

# Region ID to name mapping (from FfE API v_region_simple endpoint)
REGION_ID_MAPPING = {
    1: 'Schleswig-Holstein',
    2: 'Hamburg',
    3: 'Niedersachsen',
    4: 'Bremen',
    5: 'Nordrhein-Westfalen',
    6: 'Hessen',
    7: 'Rheinland-Pfalz',
    8: 'Baden-Württemberg',
    9: 'Bayern',
    10: 'Saarland',
    11: 'Berlin',
    12: 'Brandenburg',
    13: 'Mecklenburg-Vorpommern',
    14: 'Sachsen',
    15: 'Sachsen-Anhalt',
    16: 'Thüringen'
}


def preprocess_data_germany(raw_json):
    """Preprocess raw JSON from the FfE API into a cleaned pandas DataFrame.

    Transforms the raw API response by extracting the data payload, removing
    unnecessary columns, renaming columns to standard names, and mapping
    region identifiers to names.

    Args:
        raw_json: The raw JSON response from the FfE API, expected to be a dict
            containing a 'data' key with the actual records. Each record has an
            'internal_id' array [building_type, heat_source] and 'id_region'.

    Returns:
        A pandas DataFrame with columns: region, building_type, heat_source, value.
        The DataFrame is ready for further processing or category mapping.
    """
    if raw_json is None:
        raise ValueError("API returned no data")

    data = raw_json["data"]
    df = pd.DataFrame(data)

    # Extract building_type and heat_source from internal_id array
    df['building_type'] = df['internal_id'].apply(lambda x: x[0] if isinstance(x, list) else None)
    df['heat_source'] = df['internal_id'].apply(lambda x: x[1] if isinstance(x, list) else None)

    # Map region IDs to names
    df['region'] = df['id_region'].map(REGION_ID_MAPPING)

    # Keep only required columns
    df = df[['region', 'building_type', 'heat_source', 'value']]

    return df

def update_df_categories(df):
    """Replace numeric category codes with human-readable labels.

    Converts the building_type and heat_source columns from internal numeric
    identifiers to user-friendly text labels using the mappings defined in config.py.

    Args:
        df: A pandas DataFrame containing 'building_type' and 'heat_source' columns
            with numeric category codes.

    Returns:
        None. The DataFrame is modified in place.
    """
    df['building_type'] = df['building_type'].replace(BUILDING_TYPE_MAPPING)
    df['heat_source'] = df['heat_source'].replace(HEAT_SOURCE_MAPPING)

def get_result_df(df, selected_state, selected_building_type, selected_heat_source):
    """Query heat pump suitability data using DuckDB for efficient filtering.

    Filters the provided DataFrame based on user selections and returns matching records.
    Uses parameterized queries to prevent SQL injection. All inputs are validated
    against allowed values before query execution.

    Args:
        df: The pandas DataFrame containing heat pump suitability data.
        selected_state: The federal state to filter by, or "(Deutschland)" for
            nationwide data (all states).
        selected_building_type: The building type category to filter by
            (e.g., "One- and Two-family Houses", "Total").
        selected_heat_source: The heat pump type to filter by
            (e.g., "Air", "Ground Probe", "Total").

    Returns:
        A pandas DataFrame containing the filtered records with columns matching
        the source data schema.

    Raises:
        InputValidationError: If any input value is not in the allowed set of values.
    """
    logger.debug("Query requested - state: %s, building: %s, heat: %s",
                 selected_state, selected_building_type, selected_heat_source)
    # Validate all inputs against allowed values before executing any query
    validate_inputs(selected_building_type, selected_heat_source, selected_state)

    # Connect to temp DuckDB database and register the DataFrame
    conn = duckdb.connect(database=':memory:', read_only=False)
    conn.register('data', df)

    if selected_state == "(Deutschland)":
        # Create query with parameterized placeholders to prevent SQL injection
        select_data_query = """
        SELECT * FROM data
        WHERE building_type = ?
        AND heat_source = ?
        """
        params = [selected_building_type, selected_heat_source]
        result_df = conn.execute(select_data_query, params).fetchdf()
    else:
        select_data_query = """
        SELECT * FROM data
        WHERE building_type = ?
        AND heat_source = ?
        AND federal_state = ?
        """
        params = [selected_building_type, selected_heat_source, selected_state]
        result_df = conn.execute(select_data_query, params).fetchdf()

    # Close DuckDB connection
    conn.close()

    return result_df
