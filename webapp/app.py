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
    CHART_COLORS_GREEN,
    CHART_COLORS_HEAT,
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

# Initialize session states
if 'selected_state' not in st.session_state:
    st.session_state.selected_state = "(Deutschland)"

if 'selected_building_type' not in st.session_state:
    st.session_state.selected_building_type = "Total"

if 'selected_heat_source' not in st.session_state:
    st.session_state.selected_heat_source = "Total"

# Navigation state for drill-down hierarchy (VIZ-3)
if 'nav_current_level' not in st.session_state:
    st.session_state.nav_current_level = "germany"  # "germany" | "state" | "district"

if 'nav_selected_state' not in st.session_state:
    st.session_state.nav_selected_state = None  # None | state name

if 'nav_selected_district' not in st.session_state:
    st.session_state.nav_selected_district = None  # None | district name

# Pending state for map click navigation (applied BEFORE widget instantiation)
# This pattern avoids "cannot modify session_state after widget instantiation" error
if 'pending_state_navigation' not in st.session_state:
    st.session_state.pending_state_navigation = None  # None | state name to navigate to

# Apply pending navigation BEFORE any widgets are instantiated
if st.session_state.pending_state_navigation is not None:
    st.session_state.selected_state = st.session_state.pending_state_navigation
    st.session_state.pending_state_navigation = None


# Navigation helper functions for drill-down hierarchy (VIZ-3)
def navigate_to_germany():
    """Navigate to Germany-level view (top level)."""
    st.session_state.nav_current_level = "germany"
    st.session_state.nav_selected_state = None
    st.session_state.nav_selected_district = None


def navigate_to_state(state_name: str):
    """Navigate to state-level view.

    Args:
        state_name: Name of the state to navigate to.
    """
    st.session_state.nav_current_level = "state"
    st.session_state.nav_selected_state = state_name
    st.session_state.nav_selected_district = None


def navigate_to_district(state_name: str, district_name: str):
    """Navigate to district-level detail view.

    Args:
        state_name: Name of the state containing the district.
        district_name: Name of the district to navigate to.
    """
    st.session_state.nav_current_level = "district"
    st.session_state.nav_selected_state = state_name
    st.session_state.nav_selected_district = district_name


def render_breadcrumb():
    """Render breadcrumb navigation for drill-down hierarchy.

    Displays clickable breadcrumb trail showing current location:
    - Germany (always shown, clickable to return to top level)
    - > {State} (shown when state selected)
    - > {District} (shown when district selected)

    Uses st.button() for each level to enable navigation.
    """
    current_level = st.session_state.nav_current_level
    selected_state = st.session_state.nav_selected_state
    selected_district = st.session_state.nav_selected_district

    # Create horizontal container for breadcrumb buttons
    breadcrumb_cols = st.columns([1, 0.2, 2, 0.2, 3, 5])

    with breadcrumb_cols[0]:
        # Germany button - always visible, clickable when not at germany level
        if current_level == "germany":
            st.markdown("**Germany**")
        else:
            if st.button("Germany", key="breadcrumb_germany", type="secondary"):
                navigate_to_germany()
                st.rerun()

    # Show separator and state if at state or district level
    if current_level in ["state", "district"] and selected_state:
        with breadcrumb_cols[1]:
            st.markdown("**>**")

        with breadcrumb_cols[2]:
            if current_level == "state":
                st.markdown(f"**{selected_state}**")
            else:
                # At district level, state is clickable
                if st.button(selected_state, key="breadcrumb_state", type="secondary"):
                    navigate_to_state(selected_state)
                    st.rerun()

    # Show separator and district if at district level
    if current_level == "district" and selected_district:
        with breadcrumb_cols[3]:
            st.markdown("**>**")

        with breadcrumb_cols[4]:
            st.markdown(f"**{selected_district}**")


def main():
    # Professional header
    st.title("Heat Pump Potential Atlas")
    st.markdown("*An interactive analysis of heat pump suitability across Germany*")

    # About section - collapsible for clean interface
    with st.expander("ℹ️ About this tool — What the data shows and how to use it"):
        st.markdown("""
        ### Germany's Path to Climate-Neutral Heating

        As Germany pursues its ambitious goal of carbon neutrality by 2045, the building
        sector, responsible for nearly 30% of the nation's energy consumption, faces a
        fundamental transformation. Heat pumps have emerged as the cornerstone technology
        for decarbonizing residential heating, but their viability varies dramatically
        across regions, building types, and installation methods.

        This interactive atlas, built on 2022 research data from the
        [Forschungsstelle für Energiewirtschaft (FfE)](https://opendata.ffe.de/),
        visualizes the technical potential for heat pump adoption across Germany's
        16 federal states and approximately 400 districts.

        ---

        ### Understanding "Suitability"

        **The percentage shown for each region represents the share of buildings that
        could technically accommodate a heat pump installation** - based on factors
        including building age, insulation levels, available outdoor space, and
        compatibility with existing heating infrastructure.

        | Suitability | Interpretation |
        |-------------|----------------|
        | **75-100%** | Excellent potential - most buildings are suitable |
        | **50-75%** | Good potential - majority could install heat pumps |
        | **25-50%** | Moderate potential - significant barriers exist for many buildings |
        | **0-25%** | Limited potential - few buildings meet technical requirements |

        *Important: Technical suitability does not account for economic feasibility,
        homeowner preferences, or local grid capacity constraints.*

        ---

        ### How to Use This Tool

        **Explorer Tab**
        - Select a **federal state** or view all of Germany
        - Filter by **building type** (single-family homes, apartments, etc.)
        - Filter by **heat pump technology** (air-source, ground probe, etc.)
        - Click any region on the map to drill down to district-level detail

        **Compare Tab**
        - Select 2-4 states for side-by-side comparison
        - Identify regional leaders and understand geographic patterns

        ---

        ### Data Source

        All data originates from the FfE "Wärmepumpen-Ampel" project, which employed
        bottom-up modeling of Germany's building stock. The analysis evaluates individual
        buildings based on structural characteristics, site conditions, and technical
        requirements for each heat pump type.

        **Reference year:** 2022 · **Coverage:** ~400 districts · **License:** FfE Open Data
        """)

    st.divider()

    # Create navigation tabs
    tab_explorer, tab_compare = st.tabs(["Explorer", "Compare"])

    with tab_explorer:
        render_explorer_tab()

    with tab_compare:
        render_compare_tab()


def render_explorer_tab():
    """Render the Explorer tab with map and statistics."""
    # Render breadcrumb navigation for drill-down hierarchy
    render_breadcrumb()
    st.divider()

    # Check if at district level - show district detail view
    if st.session_state.nav_current_level == "district":
        nav_state = st.session_state.nav_selected_state
        nav_district = st.session_state.nav_selected_district
        if nav_state and nav_district:
            # Load state data for district view
            try:
                dir_path = os.path.dirname(os.path.realpath(__file__))
                filename = DISTRICT_DATA_SELECTION.get(nav_state)
                data_path = os.path.join(dir_path, f"data/districts/{filename}")
                df = pd.read_csv(data_path)
                update_df_categories(df)
                render_district_detail_view(df, nav_state, nav_district)
                return
            except FileNotFoundError:
                st.error(f"Data file not found for {nav_state}.")
                return
            except Exception as e:
                st.error(f"Failed to load data: {e}")
                return

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
                    df, selected_state, selected_building_type, selected_heat_source
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

    # Display map with click handling for drill-down navigation
    with col_map:
        try:
            if selected_state == '(Deutschland)':
                fig = create_germany_map(
                    result_df, selected_building_type, selected_heat_source, geojson_url
                )
                # Enable click events on Germany map for state navigation
                # Config removes Plotly logo from modebar
                event = st.plotly_chart(
                    fig,
                    width="stretch",
                    key="germany_map",
                    on_select="rerun",
                    selection_mode=["points"],
                    config={"displaylogo": False},
                )
                # Handle click event - navigate to clicked state
                if event and event.selection and event.selection.points:
                    clicked_point = event.selection.points[0]
                    # The 'location' field contains the region name (state name)
                    clicked_state = clicked_point.get("location")
                    if clicked_state and clicked_state in FEDERAL_STATES:
                        # Use pending state pattern to avoid "cannot modify after widget" error
                        # The pending state is applied BEFORE widget instantiation on next rerun
                        st.session_state.pending_state_navigation = clicked_state
                        navigate_to_state(clicked_state)
                        st.rerun()
            else:
                fig = create_state_map(
                    result_df, selected_state, selected_building_type, selected_heat_source
                )

                # Enable click events on state map for district navigation
                # Config removes Plotly logo from modebar
                event = st.plotly_chart(
                    fig,
                    width="stretch",
                    key="state_map",
                    on_select="rerun",
                    selection_mode=["points"],
                    config={"displaylogo": False},
                )
                # Handle click event - navigate to clicked district
                if event and event.selection and event.selection.points:
                    clicked_point = event.selection.points[0]
                    # The 'location' field contains the district name
                    clicked_district = clicked_point.get("location")
                    if clicked_district:
                        # Get the list of valid district names from the current data
                        valid_districts = result_df['district'].unique().tolist()
                        if clicked_district in valid_districts:
                            navigate_to_district(selected_state, clicked_district)
                            st.rerun()
        except Exception as e:
            logger.exception("Failed to render map: %s", str(e))
            st.error(f"Failed to render map: {str(e)}")

        # Data attribution footer
        st.caption("Data: [FfE Open Data Portal](https://opendata.ffe.de/) (2022)")
        st.caption("Visualization: Heat Pump Potentials Germany")

        # Export buttons
        st.divider()
        export_col1, export_col2 = st.columns(2)

        with export_col1:
            # Download Map as PNG button
            try:
                png_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
                filename_png = f"heat_pump_map_{selected_state}_{selected_building_type}.png"
                filename_png = filename_png.replace(" ", "_").replace("(", "").replace(")", "")
                st.download_button(
                    label="Download Map (PNG)",
                    data=png_bytes,
                    file_name=filename_png,
                    mime="image/png",
                    key="download_map_png",
                )
            except Exception as e:
                logger.warning("Failed to generate PNG export: %s", str(e))
                st.warning("PNG export not available")

        with export_col2:
            # Download Data as CSV button
            # Filter data to current selection
            filtered_df = df[
                (df['building_type'] == selected_building_type) &
                (df['heat_source'] == selected_heat_source)
            ].copy()

            # Remove geometry column for cleaner export (if present)
            export_cols = [c for c in filtered_df.columns if c != 'geometry']
            export_df = filtered_df[export_cols]

            csv_data = export_df.to_csv(index=False)
            filename_csv = f"heat_pump_data_{selected_state}_{selected_building_type}.csv"
            filename_csv = filename_csv.replace(" ", "_").replace("(", "").replace(")", "")
            st.download_button(
                label="Download Data (CSV)",
                data=csv_data,
                file_name=filename_csv,
                mime="text/csv",
                key="download_data_csv",
            )

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

        # Building type breakdown chart
        st.subheader("Suitability by Building Type")
        building_breakdown = get_building_type_breakdown(
            df, selected_heat_source, state=selected_state
        )

        if not building_breakdown.empty:
            # Sort by value descending so highest suitability appears at top
            building_breakdown = building_breakdown.sort_values('avg_value', ascending=True)
            fig_building = px.bar(
                building_breakdown,
                x='avg_value',
                y='building_type',
                orientation='h',
                color_discrete_sequence=CHART_COLORS_GREEN,
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

            st.plotly_chart(fig_building, width="stretch")
        else:
            st.info("No building type data available for the current selection.")

    # Top 10 / Bottom 10 tables - only show at state level (not Germany level)
    # At Germany level there are only 16 states, making top/bottom 10 redundant
    if selected_state != "(Deutschland)":
        st.divider()
        table_col1, table_col2 = st.columns(2)

        with table_col1:
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
                    width="stretch",
                )
            else:
                st.info("No data available for the current selection.")

        with table_col2:
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
                    width="stretch",
                )
            else:
                st.info("No data available for the current selection.")
    else:
        # Germany level - show full state ranking (all 16 states)
        st.divider()
        st.subheader("State Ranking")

        # Combine top and bottom to get full ranking, or use top_districts with n=16
        full_ranking = get_top_bottom_districts(
            df, selected_building_type, selected_heat_source, n=16
        )[0]  # Get top 16 (all states)

        if not full_ranking.empty:
            # Rename 'district' column to 'state' for clarity at Germany level
            display_df = full_ranking.rename(columns={'district': 'state'})
            # Drop federal_state column as it's redundant at Germany level
            if 'federal_state' in display_df.columns:
                display_df = display_df.drop(columns=['federal_state'])

            st.dataframe(
                display_df,
                column_config={
                    "rank": st.column_config.NumberColumn("Rank", width="small"),
                    "state": st.column_config.TextColumn("Federal State", width="large"),
                    "value": st.column_config.NumberColumn(
                        "Suitability (%)",
                        format="%.1f%%",
                        width="medium",
                    ),
                },
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("No ranking data available for the current selection.")


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
                # Get current zoom and reduce it for smaller comparison view
                current_zoom = fig.layout.mapbox.zoom
                # Adjust map size for comparison view
                fig.update_layout(
                    width=None,
                    height=400,
                    margin=dict(l=0, r=0, t=0, b=0),
                    coloraxis_showscale=(idx == 0),  # Only show color scale on first map
                    mapbox_zoom=current_zoom - 0.7,  # Zoom out for smaller container
                )
                st.plotly_chart(
                    fig, width="stretch", config={"displaylogo": False}
                )
            except Exception as e:
                st.error(f"Failed to render map for {state}: {e}")


def render_district_detail_view(df, state_name, district_name):
    """Render detailed view for a single district.

    Shows breakdown of suitability by building type and heat source,
    plus district metadata and navigation back to state view.

    Args:
        df: DataFrame containing all district data for the state.
        state_name: Name of the state containing this district.
        district_name: Name of the district to display.
    """
    # Filter data for this district
    district_df = df[df['district'] == district_name].copy()

    if district_df.empty:
        st.error(f"No data found for district: {district_name}")
        return

    # Get district metadata from first row
    if 'district_type' in district_df.columns:
        district_type = district_df['district_type'].iloc[0]
    else:
        district_type = "Unknown"

    # Header with district name and metadata
    st.header(f"{district_name}")

    # Metadata section
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.metric("State", state_name)
    with col_meta2:
        st.metric("District Type", district_type)
    with col_meta3:
        # Count unique combinations
        num_building_types = district_df['building_type'].nunique()
        st.metric("Building Types", num_building_types)

    st.divider()

    # Create two columns for the charts
    col_building, col_heat = st.columns(2)

    # Building type breakdown chart
    with col_building:
        st.subheader("Suitability by Building Type")

        # Filter to Total heat source (code 0) for building type comparison
        building_data = district_df[district_df['heat_source'] == 'Total'].copy()

        if not building_data.empty:
            # Sort by value descending
            building_data = building_data.sort_values('value', ascending=True)
            # Convert to percentage
            building_data['value_pct'] = building_data['value'] * 100

            fig_building = px.bar(
                building_data,
                x='value_pct',
                y='building_type',
                orientation='h',
                color_discrete_sequence=CHART_COLORS_GREEN,
                labels={
                    'value_pct': 'Suitability (%)',
                    'building_type': 'Building Type',
                },
                text='value_pct',
            )

            fig_building.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside',
            )

            fig_building.update_layout(
                xaxis_title='Suitability (%)',
                yaxis_title='',
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(range=[0, 100]),
                height=300,
            )

            st.plotly_chart(fig_building, width="stretch")
        else:
            st.info("No building type data available for this district.")

    # Heat source breakdown chart
    with col_heat:
        st.subheader("Suitability by Heat Source")

        # Filter to Total building type (code 100) for heat source comparison
        heat_data = district_df[district_df['building_type'] == 'Total'].copy()

        if not heat_data.empty:
            # Sort by value descending
            heat_data = heat_data.sort_values('value', ascending=True)
            # Convert to percentage
            heat_data['value_pct'] = heat_data['value'] * 100

            fig_heat = px.bar(
                heat_data,
                x='value_pct',
                y='heat_source',
                orientation='h',
                color_discrete_sequence=CHART_COLORS_HEAT,
                labels={
                    'value_pct': 'Suitability (%)',
                    'heat_source': 'Heat Source',
                },
                text='value_pct',
            )

            fig_heat.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside',
            )

            fig_heat.update_layout(
                xaxis_title='Suitability (%)',
                yaxis_title='',
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(range=[0, 100]),
                height=300,
            )

            st.plotly_chart(fig_heat, width="stretch")
        else:
            st.info("No heat source data available for this district.")

    st.divider()

    # Back to State button
    if st.button(f"← Back to {state_name}", key="back_to_state", type="primary"):
        navigate_to_state(state_name)
        st.rerun()


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
        width="stretch",
    )


if __name__ == "__main__":
    main()
