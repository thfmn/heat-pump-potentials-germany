import plotly.express as px
import streamlit as st
import json
import requests
import re
from shapely.geometry import mapping, shape, Polygon
from config import STATE_GEO_VALUES

# Set longitude and latitude (center) and zoom for each state selection
def set_geographical_values(selected_state):
    return STATE_GEO_VALUES.get(selected_state, STATE_GEO_VALUES["(Deutschland)"])

# Create and display map with choropleth layer
def create_germany_map(result_df, selected_building_type, selected_heat_source, GEOJSON_URL):
    lat, lon, zoom = 51.1657, 10.4515, 5
    
    fig = px.choropleth_mapbox(result_df.query(f"building_type == '{selected_building_type}' & heat_source == '{selected_heat_source}'"), 
                            geojson=GEOJSON_URL, 
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
        x=0.5,  # Centers the colorbar horizontally
        y=0,  # Positions the colorbar above the plot
        xanchor='center',  # Ensures the colorbar is centered at the x position
        orientation='h',  # Makes the colorbar horizontal
        len=0.7  # Adjusts the length of the colorbar
        )
    )

    return fig

    
def create_state_map(state_df, selected_state, selected_building_type, selected_heat_source):
    lat, lon, zoom = set_geographical_values(selected_state)
    
    filtered_df = state_df.query(f"building_type == '{selected_building_type}' & heat_source == '{selected_heat_source}' & federal_state == '{selected_state}'")
    
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
        x=0.5,  # Centers the colorbar horizontally
        y=0,  # Positions the colorbar above the plot
        xanchor='center',  # Ensures the colorbar is centered at the x position
        orientation='h',  # Makes the colorbar horizontal
        len=0.7 # Adjusts the length of the colorbar
        )
    )

    return fig
    
