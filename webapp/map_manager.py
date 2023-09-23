import plotly.express as px
from config import STATE_GEOJSON_URL, DISTRICT_GEOJSON_URL, STATE_GEO_VALUES

# Set longitude and latitude (center) and zoom for each state selection
def set_geographical_values(selected_state):
    return STATE_GEO_VALUES.get(selected_state, STATE_GEO_VALUES["(Deutschland)"])

# Create and display map with choropleth layer
def create_map(result_df, selected_state, selected_building_type, selected_heat_source, GEOJSON_URL):
    lat, lon, zoom = set_geographical_values(selected_state)  # pass the selected_state

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