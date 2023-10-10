import requests
import pandas as pd
import duckdb
import json
from config import BUILDING_TYPE_MAPPING, HEAT_SOURCE_MAPPING

# Fetch data from API
def fetch_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
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
    # Connect to temp DuckDB database
    conn = duckdb.connect(database=':memory:', read_only=False)

    # Check if table exists. If not, create table
    tables = conn.execute("SHOW TABLES").fetchall()
    if('data',) not in tables:
        create_table_query = "CREATE TABLE data AS SELECT * FROM df"
        conn.execute(create_table_query)

    if selected_state == "(Deutschland)":
        # Create query
        select_data_query = f"""
        SELECT * FROM data
        WHERE building_type = '{selected_building_type}'
        AND heat_source = '{selected_heat_source}'
        """
    else:
        select_data_query = f"""
        SELECT * FROM data
        WHERE building_type = '{selected_building_type}'
        AND heat_source = '{selected_heat_source}'
        AND federal_state = '{selected_state}'
        """
    
    # Fetch DataFrame
    result_df = conn.execute(select_data_query).fetchdf()

    # Close DuckDB connection
    conn.close()

    return result_df
