"""Map generation module for creating interactive choropleth visualizations.

This module provides functions for creating Plotly choropleth maps that
display heat pump suitability data across Germany. It supports two map types:
- Germany-wide maps showing state-level aggregations
- State-level maps showing district-level detail

Maps use a red-yellow-green color scale where green indicates higher
suitability proportions. Geographic coordinates and zoom levels are
configured per state for optimal visualization.
"""
import plotly.express as px
from config import STATE_GEO_VALUES
from shapely.geometry import mapping


def set_geographical_values(selected_state):
    """Get geographic coordinates and zoom level for a selected state.

    Retrieves the latitude, longitude, and zoom level for centering the map
    on the specified German state. Falls back to Germany-wide coordinates
    if the state is not found in the configuration.

    Args:
        selected_state: Name of the German federal state (e.g., "Bayern",
            "Nordrhein-Westfalen") or "(Deutschland)" for the whole country.

    Returns:
        A tuple of (latitude, longitude, zoom) where:
            - latitude: Float for map center latitude
            - longitude: Float for map center longitude
            - zoom: Integer zoom level for the map display
    """
    return STATE_GEO_VALUES.get(selected_state, STATE_GEO_VALUES["(Deutschland)"])

def create_germany_map(result_df, selected_building_type, selected_heat_source, geojson_url):
    """Create a choropleth map of Germany showing heat pump suitability by state.

    Generates an interactive Plotly choropleth map displaying the proportion
    of buildings suitable for the selected heat pump type across all German
    federal states. The map uses a red-yellow-green color scale where green
    indicates higher suitability.

    Args:
        result_df: pandas DataFrame containing the state-level data with columns:
            - region: State name matching GeoJSON feature names
            - building_type: Building category (e.g., "Gesamt", "Ein- und Zweifamilienhaus")
            - heat_source: Heat pump type (e.g., "Gesamt", "Luft")
            - value: Suitability proportion (0.0-1.0)
        selected_building_type: Building type to filter and display.
        selected_heat_source: Heat source type to filter and display.
        geojson_url: URL to the GeoJSON file containing Germany state boundaries.

    Returns:
        A plotly.graph_objects.Figure containing the configured choropleth map
        with hover tooltips showing state names and suitability percentages.
    """
    lat, lon, zoom = 51.1657, 10.4515, 5

    query_str = (
        f"building_type == '{selected_building_type}' "
        f"& heat_source == '{selected_heat_source}'"
    )
    fig = px.choropleth_mapbox(result_df.query(query_str),
                            geojson=geojson_url,
                            locations='region',
                            color='value',
                            featureidkey="properties.name",
                            color_continuous_scale='RdYlGn',
                            range_color=[0,1],
                            mapbox_style="carto-darkmatter",
                            opacity=1,
                            hover_data={'value': True},
                            hover_name=result_df['region']
                            )
    fig.update_traces(hovertemplate='%{hovertext}<br>%{z:.1%}')
    fig.update_geos(fitbounds="locations")
    fig.update_layout(
        mapbox_zoom=zoom,
        mapbox_center={"lat": lat, "lon": lon},
        autosize=False,
        width=800,
        height=800,
        coloraxis_colorbar=dict(
        title="Anteil in %",
        tickvals=[0, 0.25, 0.5, 0.75, 1],
        ticktext=['0%', '25%', '50%', '75%', '100%'],
        x=0.5,
        y=0,
        xanchor='center',
        orientation='h',
        len=0.7
        )
    )

    return fig


def create_state_map(state_df, selected_state, selected_building_type, selected_heat_source):
    """Create a choropleth map of a German state showing heat pump suitability by district.

    Generates an interactive Plotly choropleth map displaying the proportion
    of buildings suitable for the selected heat pump type across all districts
    (Kreise and kreisfreie Städte) within the specified German federal state.
    The map uses a red-yellow-green color scale where green indicates higher
    suitability.

    The function dynamically creates GeoJSON features from the WKT geometry
    stored in the DataFrame, allowing district-level visualization without
    requiring external GeoJSON files for each state.

    Args:
        state_df: GeoDataFrame containing district-level data with columns:
            - district: District name (Kreis or kreisfreie Stadt)
            - district_type: Type of district ("Kreis", "Kreisfreie Stadt", etc.)
            - building_type: Building category
            - heat_source: Heat pump type
            - value: Suitability proportion (0.0-1.0)
            - federal_state: Name of the federal state
            - geometry: Shapely geometry object (parsed from WKT)
        selected_state: Name of the German federal state to display.
        selected_building_type: Building type to filter and display.
        selected_heat_source: Heat source type to filter and display.

    Returns:
        A plotly.graph_objects.Figure containing the configured choropleth map
        with hover tooltips showing district names and suitability percentages.
    """
    lat, lon, zoom = set_geographical_values(selected_state)

    query_str = (
        f"building_type == '{selected_building_type}' "
        f"& heat_source == '{selected_heat_source}' "
        f"& federal_state == '{selected_state}'"
    )
    filtered_df = state_df.query(query_str)

    geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"district": row.district, "district_type": row.district_type},
            "geometry": mapping(row.geometry)
        }
        for idx, row in filtered_df.iterrows()
    ]
    }

    fig = px.choropleth_mapbox(filtered_df,
                            geojson=geojson,
                            locations='district',
                            featureidkey="properties.district",
                            color='value',
                            color_continuous_scale='RdYlGn',
                            range_color=[0, 1],
                            mapbox_style="carto-darkmatter",
                            opacity=1,
                            hover_name=filtered_df['district'],
                            hover_data={'value': True}
                           )

    fig.update_traces(hovertemplate='%{hovertext}<br>%{z:.1%}')
    fig.update_geos(fitbounds="locations")
    fig.update_layout(
        mapbox_zoom=zoom,
        mapbox_center={"lat": lat, "lon": lon},
        autosize=False,
        width=800,
        height=800,
        coloraxis_colorbar=dict(
        title="Anteil in %",
        tickvals=[0, 0.25, 0.5, 0.75, 1],
        ticktext=['0%', '25%', '50%', '75%', '100%'],
        x=0.5,
        y=0,
        xanchor='center',
        orientation='h',
        len=0.7
        )
    )

    return fig

