import plotly.express as px
import streamlit as st
import json
import requests
from config import STATE_GEOJSON_URL, STATE_GEO_VALUES, DISTRICT_GEOJSON_URL

# Set longitude and latitude (center) and zoom for each state selection
def set_geographical_values(selected_state):
    return STATE_GEO_VALUES.get(selected_state, STATE_GEO_VALUES["(Deutschland)"])

# Create and display map with choropleth layer
def create_map(result_df, selected_state, selected_building_type, selected_heat_source, GEOJSON_URL):
    lat, lon, zoom = set_geographical_values(selected_state)  # pass the selected_state

    if selected_state == "(Deutschland)":
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
                                hover_name=result_df['region'],
                                )
        fig.update_traces(hovertemplate='%{hovertext}<br>%{z:.1%}')
        fig.update_geos(fitbounds="locations")
        fig.update_layout(
            mapbox_zoom=zoom,
            mapbox_center={"lat": lat, "lon": lon},
            autosize=False,
            width=800, 
            height=800,
            coloraxis_showscale=False
        )

        return fig
    else:
        # Fetch GeoJSON and load it into a dictionary
        geojson_data = requests.get(DISTRICT_GEOJSON_URL).json()

        # Filter features based on the selected state
        filtered_features = [
        feature for feature in geojson_data['features']
        if feature['properties']['NAME_1'] == selected_state
        ]

        # Replace the features in GeoJSON data with the filtered ones
        geojson_data['features'] = filtered_features

        fig = px.choropleth_mapbox(result_df.query(f"building_type == '{selected_building_type}' & heat_source == '{selected_heat_source}' & federal_state == '{selected_state}'"), 
                                geojson=geojson_data, 
                                locations='district', 
                                color='value',
                                featureidkey="properties.NAME_3",
                                color_continuous_scale='RdYlGn',
                                range_color=[0,1],
                                mapbox_style="carto-darkmatter",
                                opacity=1,
                                hover_data={'value': True},
                                hover_name=result_df['district'],
                                )
        fig.update_traces(hovertemplate='%{hovertext}<br>%{z:.1%}')
        fig.update_geos(fitbounds="locations")
        fig.update_layout(
            mapbox_zoom=zoom,
            mapbox_center={"lat": lat, "lon": lon},
            autosize=False,
            width=800, 
            height=800,
            coloraxis_showscale=False
        )

        if selected_state != "(Deutschland)":
            st.write("Selected State: ", selected_state)
            st.write("Result DataFrame: ", result_df.head())
            #st.write("GeoJSON URL: ", GEOJSON_URL)
    # Further prints can be added to print specific parts of the GeoJSON or other relevant data.


        return fig