import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
from folium import Choropleth
from streamlit_folium import folium_static, st_folium
import json
import requests

st.set_page_config(layout="wide")

url = "https://opendata.ffe.de/api/od/v_opendata?id_opendata=eq.87"
federal_states_geojson_url = 'https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/2_hoch.geo.json'
# add communities url 

# Fetch data
response = requests.get(url)
gdf = gpd.read_file(federal_states_geojson_url)

# Check if request was successful
if response.status_code == 200:
    # parse json data
    raw_json = json.loads(response.text)
    print("Success")
else:
    print("Fail")

# Pre-Processing -> export
data = raw_json[0]["data"]
df = pd.DataFrame(data)
df = df.dropna(axis=1, how='all')
df = df.drop(['id_opendata', 'id_region_type', 'region_type', 'year', 'internal_id'], axis=1)
df = df.rename(columns={'internal_id_1': 'building_type', 'internal_id_2': 'heat_source'})

region_dict = dict(zip(df['id_region'], df['region']))
df = df.drop(['id_region'], axis=1)
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

federal_states = list(df['region'].unique())

# Rename df content
df['building_type'] = df['building_type'].replace(building_type_dict)
df['heat_source'] = df['heat_source'].replace(heat_source_dict)

#federal_states
#st.table(df)

# min_lat, max_lat = 46.1657, 56.1657
# min_lon, max_lon = 5.4515, 15.4515
# functions
def create_map():
    m = folium.Map(
        location=[51.1657, 10.4515],
        zoom_start=6,
        zoom_control=False,
        tiles="cartodbdark_matter",
    )
    folium.Choropleth(
        geo_data=federal_states_geojson_url,
        name='choropleth',
        data=df.query("building_type == 'Total' & heat_source == 'Total'"),
        columns=['region', 'value'],
        key_on='feature.properties.name',
        fill_color='RdYlGn',
        fill_opacity=1,
        line_opacity=0.2,
        legend_name='Share of Buildings Suited for Heat Pumps (%)'
    ).add_to(m)
    st_folium(m)

# Create frontend
# Set title
st.title("Heatpump Potentials in Germany")
st.divider()

# Set first row of columns
col_state_selection, col_building_type, col_heat_source = st.columns(3)
st.divider()
# Set map and stats column
col_map, col_stats = st.columns([0.7,0.3], gap="medium")


# Populate columns
with col_state_selection:
    selected_state = st.selectbox(
        "Select federal state", options=federal_states
        )

with col_building_type:
    selected_building_type = st.radio(
        "Select building type", options=df["building_type"].unique()
        )
with col_heat_source:
    selected_heat_source = st.radio(
        "Select heat source", options=df["heat_source"].unique()
        )

with col_map:
    create_map()

with col_stats:
    # st.success("")
    # Dummy stats
    st.subheader("Stats")
    st.bar_chart(dict(data=[1,2,3,7,5]))

