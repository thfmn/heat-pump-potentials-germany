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
        response = requests.get(url)
        response.raise_for_status()
        logger.info("API request successful, status code: %d", response.status_code)
        return response.json()
    except requests.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return None

def preprocess_data_germany(raw_json):
    """Preprocess raw JSON from the FfE API into a cleaned pandas DataFrame.

    Transforms the raw API response by extracting the data payload, removing
    unnecessary columns, renaming columns to standard names, and cleaning up
    region identifiers.

    Args:
        raw_json: The raw JSON response from the FfE API, expected to be a list
            where the first element contains a 'data' key with the actual records.

    Returns:
        A pandas DataFrame with columns: region, building_type, heat_source, value.
        The DataFrame is ready for further processing or category mapping.
    """
    data = raw_json[0]["data"]
    df = pd.DataFrame(data).dropna(axis=1, how='all')
    drop_cols = ['id_opendata', 'id_region_type', 'region_type', 'year', 'internal_id']
    df.drop(drop_cols, axis=1, inplace=True)
    df.rename(
        columns={'internal_id_1': 'building_type', 'internal_id_2': 'heat_source'}, inplace=True
    )
    df['region'].replace(dict(zip(df['id_region'], df['region'])), inplace=True)
    df.drop(['id_region'], axis=1, inplace=True)
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
    df['building_type'].replace(BUILDING_TYPE_MAPPING, inplace=True)
    df['heat_source'].replace(HEAT_SOURCE_MAPPING, inplace=True)

def get_result_df(selected_state, selected_building_type, selected_heat_source):
    """Query the in-memory DuckDB database for filtered heat pump suitability data.

    Filters the data based on user selections and returns matching records.
    Uses parameterized queries to prevent SQL injection. All inputs are validated
    against allowed values before query execution.

    Args:
        selected_state: The federal state to filter by, or "(Deutschland)" for
            nationwide data (all states).
        selected_building_type: The building type category to filter by
            (e.g., "Einfamilienhaus", "Mehrfamilienhaus 3-6 WE").
        selected_heat_source: The heat pump type to filter by
            (e.g., "Luft", "Erdsonde", "Erdkollektor").

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

    # Connect to temp DuckDB database
    conn = duckdb.connect(database=':memory:', read_only=False)

    # Check if table exists. If not, create table
    tables = conn.execute("SHOW TABLES").fetchall()
    if('data',) not in tables:
        create_table_query = "CREATE TABLE data AS SELECT * FROM df"
        conn.execute(create_table_query)

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
