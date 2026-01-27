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
import plotly.express as px
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
from stats_manager import (
    calculate_summary_stats,
    get_building_type_breakdown,
    get_top_bottom_districts,
)

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
    # Create navigation tabs
    tab_explorer, tab_compare, tab_insights = st.tabs(["Explorer", "Compare", "Insights"])

    with tab_explorer:
        render_explorer_tab()

    with tab_compare:
        render_compare_tab()

    with tab_insights:
        st.info("Insights tab - implementation pending (ML-3)")


def render_explorer_tab():
    """Render the Explorer tab with map and statistics."""
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

        # Calculate summary statistics from the loaded dataframe
        stats = calculate_summary_stats(df, selected_building_type, selected_heat_source)
        top_districts, bottom_districts = get_top_bottom_districts(
            df, selected_building_type, selected_heat_source, n=10
        )

        # Metric cards using st.columns(4) layout
        metric_col1, metric_col2 = st.columns(2)
        metric_col3, metric_col4 = st.columns(2)

        with metric_col1:
            st.metric(
                label="Average Suitability",
                value=f"{stats['mean']:.1f}%",
                help="Mean suitability percentage across all districts/regions"
            )

        with metric_col2:
            st.metric(
                label="Coverage",
                value=f"{stats['count']}",
                help="Number of districts/regions in the current selection"
            )

        with metric_col3:
            top_name = top_districts.iloc[0]['district'] if not top_districts.empty else "N/A"
            top_val = top_districts.iloc[0]['value'] if not top_districts.empty else 0
            st.metric(
                label="Top District",
                value=f"{top_val:.1f}%" if not top_districts.empty else "N/A",
                help=f"Highest: {top_name}"
            )

        with metric_col4:
            bottom_name = (
                bottom_districts.iloc[0]['district'] if not bottom_districts.empty else "N/A"
            )
            bottom_val = bottom_districts.iloc[0]['value'] if not bottom_districts.empty else 0
            st.metric(
                label="Bottom District",
                value=f"{bottom_val:.1f}%" if not bottom_districts.empty else "N/A",
                help=f"Lowest: {bottom_name}"
            )

        # Top 10 / Bottom 10 tables
        st.subheader("Top 10 Districts")
        if not top_districts.empty:
            st.dataframe(
                top_districts,
                column_config={
                    "rank": st.column_config.NumberColumn("Rank", width="small"),
                    "district": st.column_config.TextColumn("District", width="medium"),
                    "federal_state": st.column_config.TextColumn("State", width="medium"),
                    "value": st.column_config.NumberColumn(
                        "Suitability (%)",
                        format="%.1f%%",
                        width="small",
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No data available for the current selection.")

        st.subheader("Bottom 10 Districts")
        if not bottom_districts.empty:
            st.dataframe(
                bottom_districts,
                column_config={
                    "rank": st.column_config.NumberColumn("Rank", width="small"),
                    "district": st.column_config.TextColumn("District", width="medium"),
                    "federal_state": st.column_config.TextColumn("State", width="medium"),
                    "value": st.column_config.NumberColumn(
                        "Suitability (%)",
                        format="%.1f%%",
                        width="small",
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No data available for the current selection.")

        # Building type breakdown chart
        st.subheader("Suitability by Building Type")
        building_breakdown = get_building_type_breakdown(
            df, selected_heat_source, state=selected_state
        )

        if not building_breakdown.empty:
            # Define consistent colors for building types (green shades for suitability theme)
            color_sequence = ['#2ecc71', '#27ae60', '#1abc9c', '#16a085', '#3498db']

            fig_building = px.bar(
                building_breakdown,
                x='avg_value',
                y='building_type',
                orientation='h',
                color_discrete_sequence=color_sequence,
                labels={
                    'avg_value': 'Average Suitability (%)',
                    'building_type': 'Building Type',
                },
                text='avg_value',
            )

            # Format text labels on bars
            fig_building.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside',
            )

            # Update layout for clean appearance
            fig_building.update_layout(
                xaxis_title='Average Suitability (%)',
                yaxis_title='',
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(range=[0, 100]),
                height=250,
            )

            st.plotly_chart(fig_building, use_container_width=True)
        else:
            st.info("No building type data available for the current selection.")


def render_compare_tab():
    """Render the Compare tab for comparing multiple states side-by-side."""
    st.header("Compare States")
    st.markdown("Select 2-4 states to compare their heat pump suitability side-by-side.")

    # Filters row
    col_select, col_building, col_heat = st.columns([2, 1, 1])

    with col_select:
        selected_states = st.multiselect(
            "Select states to compare (2-4)",
            options=sorted(FEDERAL_STATES),
            default=[],
            max_selections=4,
            help="Select 2 to 4 states to compare their heat pump suitability.",
            key="compare_selected_states",
        )

    with col_building:
        compare_building_type = st.radio(
            "Building type",
            options=["Total", "One- and Two-family Houses", "Row Houses",
                     "Semi-detached Houses", "Apartments (3-6 units)",
                     "Apartments (7+ units)"],
            key="compare_building_type",
            horizontal=False,
        )

    with col_heat:
        compare_heat_source = st.radio(
            "Heat source",
            options=["Total", "Air", "Ground Probe", "Ground Collector", "Solar-thermal"],
            key="compare_heat_source",
            horizontal=False,
        )

    # Validate selection count
    if len(selected_states) < 2:
        st.warning("Please select at least 2 states to compare.")
        return

    # Load data for selected states
    state_data = {}
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with st.spinner("Loading state data..."):
        for state in selected_states:
            try:
                filename = DISTRICT_DATA_SELECTION.get(state)
                data_path = os.path.join(dir_path, f"data/districts/{filename}")
                df = pd.read_csv(data_path)
                update_df_categories(df)
                df['geometry'] = df['geometry'].apply(wkt.loads)
                gdf = gpd.GeoDataFrame(df, geometry='geometry')
                state_data[state] = gdf
            except FileNotFoundError:
                st.error(f"Data file not found for {state}.")
                return
            except Exception as e:
                st.error(f"Failed to load data for {state}: {e}")
                return

    # Render side-by-side maps in responsive grid
    st.subheader("Side-by-Side Comparison")
    render_comparison_maps(
        state_data, selected_states, compare_building_type, compare_heat_source
    )

    # Render comparison metrics table
    st.subheader("Comparison Metrics")
    render_comparison_table(
        state_data, selected_states, compare_building_type, compare_heat_source
    )


def render_comparison_maps(state_data, selected_states, building_type, heat_source):
    """Render side-by-side maps for the selected states.

    Uses responsive grid layout:
    - 2 states: 2 columns (1x2)
    - 3 states: 3 columns (1x3)
    - 4 states: 2x2 grid
    """
    num_states = len(selected_states)

    if num_states == 2:
        cols = st.columns(2)
    elif num_states == 3:
        cols = st.columns(3)
    else:  # 4 states
        # First row of 2
        cols_row1 = st.columns(2)
        cols_row2 = st.columns(2)
        cols = cols_row1 + cols_row2

    for idx, state in enumerate(selected_states):
        gdf = state_data[state]
        with cols[idx]:
            st.markdown(f"**{state}**")
            try:
                fig = create_state_map(gdf, state, building_type, heat_source)
                # Adjust map size for comparison view
                fig.update_layout(
                    width=None,
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0),
                    coloraxis_showscale=(idx == 0),  # Only show color scale on first map
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to render map for {state}: {e}")


def render_comparison_table(state_data, selected_states, building_type, heat_source):
    """Render a comparison metrics table for selected states.

    Shows metrics for each state including:
    - Average Suitability
    - Best District
    - Worst District
    - Standard Deviation
    """
    metrics_data = []

    for state in selected_states:
        gdf = state_data[state]
        stats = calculate_summary_stats(gdf, building_type, heat_source)
        top_districts, bottom_districts = get_top_bottom_districts(
            gdf, building_type, heat_source, n=1
        )

        best_district = (
            f"{top_districts.iloc[0]['district']} ({top_districts.iloc[0]['value']:.1f}%)"
            if not top_districts.empty else "N/A"
        )
        worst_district = (
            f"{bottom_districts.iloc[0]['district']} ({bottom_districts.iloc[0]['value']:.1f}%)"
            if not bottom_districts.empty else "N/A"
        )

        metrics_data.append({
            'State': state,
            'Avg Suitability (%)': f"{stats['mean']:.1f}",
            'Best District': best_district,
            'Worst District': worst_district,
            'Std Dev (%)': f"{stats['std']:.1f}",
            'Districts': stats['count'],
        })

    # Create comparison DataFrame
    comparison_df = pd.DataFrame(metrics_data)

    # Determine rankings for each numeric metric
    comparison_df['_avg_val'] = comparison_df['Avg Suitability (%)'].astype(float)
    comparison_df['_std_val'] = comparison_df['Std Dev (%)'].astype(float)

    # Sort to find rankings
    sorted_by_avg = comparison_df.sort_values('_avg_val', ascending=False)
    rank_map_avg = {
        state: idx + 1 for idx, state in enumerate(sorted_by_avg['State'].values)
    }

    # Add rank suffixes to average suitability
    def add_rank_indicator(row):
        rank = rank_map_avg[row['State']]
        if rank == 1:
            return f"{row['Avg Suitability (%)']} 🥇"
        elif rank == 2:
            return f"{row['Avg Suitability (%)']} 🥈"
        elif rank == 3:
            return f"{row['Avg Suitability (%)']} 🥉"
        else:
            return row['Avg Suitability (%)']

    comparison_df['Avg Suitability (%)'] = comparison_df.apply(add_rank_indicator, axis=1)

    # Drop temporary columns
    comparison_df = comparison_df.drop(columns=['_avg_val', '_std_val'])

    # Display table
    st.dataframe(
        comparison_df,
        column_config={
            'State': st.column_config.TextColumn('State', width='medium'),
            'Avg Suitability (%)': st.column_config.TextColumn(
                'Avg Suitability (%)', width='small'
            ),
            'Best District': st.column_config.TextColumn('Best District', width='large'),
            'Worst District': st.column_config.TextColumn('Worst District', width='large'),
            'Std Dev (%)': st.column_config.TextColumn('Std Dev (%)', width='small'),
            'Districts': st.column_config.NumberColumn('Districts', width='small'),
        },
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
