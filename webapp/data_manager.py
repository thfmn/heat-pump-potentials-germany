import requests
import pandas as pd
import duckdb
import json
from config import STATE_DATA_URL, DISTRICT_DATA_URL


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
    building_type_dict = {
        1: 'One- and Two-family Houses',
        6: 'Apartment Buildings (3-6)',
        9: 'Row Houses',
        11: 'Semi-detached Houses',
        38: 'Apartment Buildings: 7 and More Apartments',
        100: 'Total'
    }
    heat_source_dict = {
        0: 'Total',
        1: 'Air',
        2: 'Ground Probe',
        3: 'Ground Collector',
        4: 'Solar-Thermal Energy and Ice Storage'
    }
    df['building_type'].replace(building_type_dict, inplace=True)
    df['heat_source'].replace(heat_source_dict, inplace=True)

# Query data based upon user selections
def get_result_df(selected_building_type, selected_heat_source):
    # Connect to temp DuckDB database
    conn = duckdb.connect(database=':memory:', read_only=False)

    # Check if table exists. If not, create table
    tables = conn.execute("SHOW TABLES").fetchall()
    if('data',) not in tables:
        conn.execute("CREATE TABLE data AS SELECT * FROM df")


    sql_query = f"""
    SELECT * FROM data
    WHERE building_type = '{selected_building_type}'
    AND heat_source = '{selected_heat_source}'
    """
    result_df = conn.execute(sql_query).fetchdf()
    conn.close()
    return result_df
