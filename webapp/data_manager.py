import requests
import pandas as pd
import duckdb
import json
from config import STATE_DATA_URL, DISTRICT_DATA_URL, BUILDING_TYPE_MAPPING, HEAT_SOURCE_MAPPING

# Fetch data from API
def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        return None

# Data preprocessing
def preprocess_data(raw_json):
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
def get_result_df(selected_building_type, selected_heat_source):
    # Connect to temp DuckDB database
    conn = duckdb.connect(database=':memory:', read_only=False)

    # Check if table exists. If not, create table
    tables = conn.execute("SHOW TABLES").fetchall()
    if('data',) not in tables:
        conn.execute("CREATE TABLE data AS SELECT * FROM df")

    # Create query
    sql_query = f"""
    SELECT * FROM data
    WHERE building_type = '{selected_building_type}'
    AND heat_source = '{selected_heat_source}'
    """
    # Fetch DataFrame
    result_df = conn.execute(sql_query).fetchdf()

    # Close DuckDB connection
    conn.close()

    return result_df

