import streamlit as st
import plotly.express as px
from config import STATE_GEOJSON_URL, DISTRICT_GEOJSON_URL

# Set longitude and latitude (center) and zoom for each state selection
def set_geographical_values(selected_state):
    if selected_state == "Baden-Württemberg":
        lat, lon = 48.6616, 9.3501
        zoom = 8
    elif selected_state == "Bayern":
        lat, lon = 48.7904, 11.4979
        zoom = 8
    elif selected_state == "Brandenburg":
        lat, lon = 52.4125, 12.5316
        zoom = 8
    elif selected_state == "Bremen":
        lat, lon = 53.0793, 8.8017 # anpassen auf Bremerhaven
        zoom = 8
    elif selected_state == "Hamburg":
        lat, lon = 53.5488, 9.9872
        zoom = 8
    elif selected_state == "Hessen":
        lat, lon = 50.6521, 9.1624
        zoom = 8
    elif selected_state == "Mecklenburg-Vorpommern":
        lat, lon = 53.6127, 12.4296
        zoom = 8
    elif selected_state == "Niedersachsen":
        lat, lon = 52.6367, 9.8451
        zoom = 8
    elif selected_state == "Nordrhein-Westfalen":
        lat, lon = 51.4332, 7.6616
        zoom = 8
    elif selected_state == "Rheinland-Pfalz":
        lat, lon = 50.1183, 7.3090
        zoom = 8
    elif selected_state == "Saarland":
        lat, lon = 49.3964, 7.0230
        zoom = 8
    elif selected_state == "Sachsen":
        lat, lon = 51.1045, 13.2017
        zoom = 8
    elif selected_state == "Sachsen-Anhalt":
        lat, lon = 51.9503, 11.6923
        zoom = 8
    elif selected_state == "Schleswig-Holstein":
        lat, lon = 54.5250, 9.5608
        zoom = 8
    elif selected_state == "Thüringen":
        lat, lon = 51.0110, 10.8453
        zoom = 8
    else:
        lat, lon = 51.1657, 10.4515
        zoom = 5
    return lat, lon, zoom

# Create and display map with choropleth layer
def create_map(result_df, selected_state, selected_building_type, selected_heat_source, GEOJSON_URL):
    lat, lon, zoom = set_geographical_values(selected_state)  # pass the selected_state

    fig = px.choropleth_mapbox(result_df.query(f"building_type == '{selected_building_type}' & heat_source == '{selected_heat_source}'"), 
                               geojson=GEOJSON_URL, 
                               locations='region', 
                               color='value',
                               featureidkey="properties.name",
                               color_continuous_scale="RdYlGn",
                               mapbox_style="carto-darkmatter",
                               opacity=0.7)
    fig.update_geos(fitbounds="locations")
    fig.update_layout(
        mapbox_zoom=zoom,
        mapbox_center={"lat": lat, "lon": lon},
        autosize=False,
        width=800, 
        height=800
    )
    st.plotly_chart(fig, use_container_width=True)