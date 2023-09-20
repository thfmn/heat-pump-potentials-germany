import streamlit as st
import pandas as pd
import json
import requests
import plotly.express as px

# Set the layout configuration of the Streamlit app
st.set_page_config(layout="wide")

# URL constants
DATA_URL = "https://opendata.ffe.de/api/od/v_opendata?id_opendata=eq.87"
GEOJSON_URL = 'https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/2_hoch.geo.json'

# Initialize session states
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = "(Deutschland)"

if 'selected_building_type' not in st.session_state:
    st.session_state.selected_building_type = "Total"

if 'selected_heat_source' not in st.session_state:
    st.session_state.selected_heat_source = "Total"

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

# Create and display map with choropleth layer using Plotly
def create_map(df):
    fig = px.choropleth_mapbox(df.query("building_type == 'Total' & heat_source == 'Total'"), 
                               geojson=GEOJSON_URL, 
                               locations='region', 
                               color='value',
                               featureidkey="properties.name",
                               color_continuous_scale="RdYlGn",
                               mapbox_style="carto-darkmatter",
                               opacity=0.7)
    fig.update_geos(fitbounds="locations")
    fig.update_layout(
        mapbox_zoom=5,
        mapbox_center={"lat": 51.1657, "lon": 10.4515},
        autosize=False,
        width=800, 
        height=800
    )
    st.plotly_chart(fig, use_container_width=True)


# Fetch and preprocess data
raw_json = fetch_data(DATA_URL)
if raw_json:
    df = preprocess_data(raw_json)
    update_df_categories(df)
else:
    st.error("Failed to fetch data")

# Generate unique federal states for selection
federal_states = df['region'].unique()

# Create Streamlit frontend
st.title("Heatpump Potentials in Germany")
st.divider()

# Layout columns
col_state, col_building, col_heat = st.columns(3)
col_map, col_stats = st.columns([0.7, 0.3])

# State selection
with col_state:
    selected_state = st.selectbox("Select federal state", 
                                  options=["(Deutschland)"] + sorted(federal_states),
                                  key="selected_federal_state"
                                  )


# Building type selection
with col_building:
    selected_building = st.radio("Select building type", 
                                 options=df['building_type'].unique(),
                                 key="selected_building_type"
                                 )

# Heat source selection
with col_heat:
    selected_heat = st.radio("Select heat source", 
                             options=df['heat_source'].unique(),
                             key="selected_heat_source"
                             )

# Display map
with col_map:
    create_map(df)

# Display statistics
with col_stats:
    st.subheader("Stats")
    st.bar_chart({'Data': [1, 2, 3, 7, 5]}) # Dummy stats for now
