import streamlit as st
from config import FEDERAL_STATES, STATE_GEOJSON_URL, DISTRICT_GEOJSON_URL, STATE_DATA_URL, DISTRICT_DATA_URL
from data_manager import fetch_data, preprocess_data, update_df_categories, get_result_df
from map_manager import create_map, set_geographical_values
import duckdb

# Set the layout configuration of the Streamlit app
st.set_page_config(layout="wide")

# Initialize session states

if 'selected_state' not in st.session_state:
    st.session_state.selected_state = "(Deutschland)"

if 'selected_building_type' not in st.session_state:
    st.session_state.selected_building_type = "Total"

if 'selected_heat_source' not in st.session_state:
    st.session_state.selected_heat_source = "Total"


def main():


    # ------------- DEBUG---------------
    st.write(st.session_state)
    # ------------- /DEBUG---------------

    selected_state = st.session_state.selected_state
    selected_building_type = st.session_state.selected_building_type
    selected_heat_source = st.session_state.selected_heat_source

    if st.session_state.selected_state == "(Deutschland)":
        raw_json = fetch_data(STATE_DATA_URL)
    else:
        raw_json = fetch_data(DISTRICT_DATA_URL)
    df = preprocess_data(raw_json)
    update_df_categories(df)

    result_df = get_result_df(selected_building_type, selected_heat_source)

    # ------------- DEBUG---------------
    st.dataframe(result_df)
    # ------------- /DEBUG---------------

    # Create Streamlit frontend
    st.title("Heatpump Potentials in Germany")
    st.divider()

    # Layout columns
    col_state, col_building, col_heat = st.columns(3)
    col_map, col_stats = st.columns([0.7, 0.3])

    # State selection
    with col_state:
        selected_state = st.selectbox("Select federal state", 
                                    options=["(Deutschland)"] + sorted(FEDERAL_STATES),
                                    key="selected_state"
                                    )
        
        if st.session_state.selected_state == "(Deutschland)":
            GEOJSON_URL = STATE_GEOJSON_URL
        else:
            GEOJSON_URL = DISTRICT_GEOJSON_URL

        lat, lon, zoom = set_geographical_values(selected_state)
        


    # Building type selection
    with col_building:
        selected_building = st.selectbox("Select building type", 
                                    options=df['building_type'].unique(),
                                    key="selected_building_type"
                                    )

    # Heat source selection
    with col_heat:
        selected_heat = st.selectbox("Select heat source", 
                                options=df['heat_source'].unique(),
                                key="selected_heat_source"
                                )

    # Display map
    with col_map:
        create_map(result_df, selected_state, selected_building_type, selected_heat_source, GEOJSON_URL)

    # Display statistics
    with col_stats:
        st.subheader("Stats")
        st.bar_chart({'Data': [1, 2, 3, 7, 5]}) # Dummy stats for now

if __name__ == "__main__":
    main()

