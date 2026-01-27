"""Main Streamlit application for the Heat Pump Potentials Germany dashboard.

This module provides the user interface for visualizing heat pump suitability
data across Germany at both state and district levels. Users can filter data
by federal state, building type, and heat pump technology to explore which
regions are most suitable for different heat pump installations.

The application displays an interactive choropleth map and statistics panel,
with data sourced from the FfE Open Data Portal (2022 dataset).
"""
import os

import geopandas as gpd
import pandas as pd
import streamlit as st
from config import (
    DISTRICT_DATA_SELECTION,
    DISTRICT_GEOJSON_URL,
    FEDERAL_STATES,
    STATE_DATA_URL,
    STATE_GEOJSON_URL,
)
from data_manager import fetch_data, get_result_df, preprocess_data_germany, update_df_categories
from logging_config import setup_logging
from map_manager import create_germany_map, create_state_map, set_geographical_values
from shapely import wkt

# Initialize logging
logger = setup_logging()

# Set the layout configuration of the Streamlit app
st.set_page_config(layout="wide")

# DEBUG DataFrame Conversion
pd.set_option('io.parquet.engine', 'pyarrow')

# Initialize session states
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = "(Deutschland)"

if 'selected_building_type' not in st.session_state:
    st.session_state.selected_building_type = "Total"

if 'selected_heat_source' not in st.session_state:
    st.session_state.selected_heat_source = "Total"


def main():
    selected_state = st.session_state.selected_state
    selected_building_type = st.session_state.selected_building_type
    selected_heat_source = st.session_state.selected_heat_source

    try:
        if st.session_state.selected_state == "(Deutschland)":
            # API call for full country scope
            logger.info("Loading Germany-level data from API")
            with st.spinner("Loading Germany data from API..."):
                raw_json = fetch_data(STATE_DATA_URL)
                df = preprocess_data_germany(raw_json)
                update_df_categories(df)
                result_df = get_result_df(
                    selected_state, selected_building_type, selected_heat_source
                )
        else:
            # Get the absolute path of the directory where app.py is located
            dir_path = os.path.dirname(os.path.realpath(__file__))
            # Construct the absolute path to the data file
            filename = DISTRICT_DATA_SELECTION.get(selected_state)
            data_path = os.path.join(dir_path, f"data/districts/{filename}")

            # Choose and process correct local data depending on state_selection from data/districts
            logger.info("Loading state data from CSV: %s", selected_state)
            with st.spinner("Loading state data..."):
                df = pd.read_csv(data_path)
                update_df_categories(df)
                df['geometry'] = df['geometry'].apply(wkt.loads)
                gdf = gpd.GeoDataFrame(df, geometry='geometry')
                result_df = gdf
    except FileNotFoundError:
        logger.error("Data file not found for state: %s", selected_state)
        st.error(
            f"Data file not found for {selected_state}. "
            "Please check if the data files are available."
        )
        return
    except Exception as e:
        logger.exception("Failed to load data: %s", str(e))
        st.error(f"Failed to load data: {str(e)}")
        return

    # Layout columns
    col_state, col_building, col_heat = st.columns(3)
    col_map, col_stats = st.columns([0.7, 0.3])

    # -- Populate columns --
    # State selection
    with col_state:
        selected_state = st.selectbox("Select federal state",
                                    options=["(Deutschland)"] + sorted(FEDERAL_STATES),
                                    key="selected_state"
                                    )

        if st.session_state.selected_state == "(Deutschland)":
            geojson_url = STATE_GEOJSON_URL
        else:
            geojson_url = DISTRICT_GEOJSON_URL

        # Set zoom
        lat, lon, zoom = set_geographical_values(selected_state)

    # Building type selection
    with col_building:
        st.radio("Select building type",
                 options=df['building_type'].unique(),
                 key="selected_building_type"
                 )

    # Heat source selection
    with col_heat:
        st.radio("Select heat source",
                 options=df['heat_source'].unique(),
                 key="selected_heat_source"
                 )

    # Display map
    with col_map:
        try:
            if selected_state == '(Deutschland)':
                fig = create_germany_map(
                    result_df, selected_building_type, selected_heat_source, geojson_url
                )
            else:
                fig = create_state_map(
                    result_df, selected_state, selected_building_type, selected_heat_source
                )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.exception("Failed to render map: %s", str(e))
            st.error(f"Failed to render map: {str(e)}")

    # Display statistics
    with col_stats:
        st.subheader("Statistics")
        st.info("Statistics panel - implementation pending")

if __name__ == "__main__":
    main()
