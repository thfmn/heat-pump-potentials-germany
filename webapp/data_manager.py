import logging
import requests
import pandas as pd
import duckdb
from config import BUILDING_TYPE_MAPPING, HEAT_SOURCE_MAPPING
from utils import validate_inputs, InputValidationError

# Get logger instance
logger = logging.getLogger("heat_pump_webapp")


# Fetch data from API
def fetch_data(url):
    logger.info("Fetching data from API: %s", url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.info("API request successful, status code: %d", response.status_code)
        return response.json()
    except requests.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return None

# Data preprocessing
def preprocess_data_germany(raw_json):
    data = raw_json[0]["data"]
    df = pd.DataFrame(data).dropna(axis=1, how='all')
    drop_cols = ['id_opendata', 'id_region_type', 'region_type', 'year', 'internal_id']
    df.drop(drop_cols, axis=1, inplace=True)
    df.rename(columns={'internal_id_1': 'building_type', 'internal_id_2': 'heat_source'}, inplace=True)
    df['region'].replace(dict(zip(df['id_region'], df['region'])), inplace=True)
    df.drop(['id_region'], axis=1, inplace=True)
    return df

# Update data frame with human-readable categories
def update_df_categories(df):
    df['building_type'].replace(BUILDING_TYPE_MAPPING, inplace=True)
    df['heat_source'].replace(HEAT_SOURCE_MAPPING, inplace=True)

# Query data based upon user selections
def get_result_df(selected_state, selected_building_type, selected_heat_source):
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
        result_df = conn.execute(select_data_query, [selected_building_type, selected_heat_source]).fetchdf()
    else:
        select_data_query = """
        SELECT * FROM data
        WHERE building_type = ?
        AND heat_source = ?
        AND federal_state = ?
        """
        result_df = conn.execute(select_data_query, [selected_building_type, selected_heat_source, selected_state]).fetchdf()

    # Close DuckDB connection
    conn.close()

    return result_df
