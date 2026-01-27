# Heat Pump Potential Analysis in Germany

## Project Overview

### What It Does

This interactive web application visualizes heat pump suitability data across Germany at both state and district levels. Using 2022 data from the FfE Open Data Portal, the application displays what proportion of buildings in each region are suitable for different types of heat pumps, including:

- **Air-source heat pumps** - The most common type, extracting heat from outdoor air
- **Ground probe heat pumps** - Using vertical boreholes for geothermal energy
- **Ground collector heat pumps** - Using horizontal ground loops
- **Solar-thermal assisted systems** - Combining heat pumps with solar thermal collectors

Users can filter the data by building type (single-family homes, apartments, row houses, etc.) and heat source type, then explore an interactive choropleth map showing suitability percentages across Germany's 16 federal states and approximately 400 districts.

### Why It Matters

Germany has committed to ambitious climate targets, including carbon neutrality by 2045. Heat pumps are a critical technology for decarbonizing the building sector, which accounts for approximately 30% of Germany's energy consumption. This tool helps:

- **Policymakers** identify regions with high heat pump potential for targeted subsidy programs
- **Energy planners** understand geographic distribution of suitable building stock
- **Researchers** analyze patterns in heat pump suitability across different building types
- **Industry stakeholders** identify market opportunities for heat pump installations

By making this data accessible through an interactive visualization, the application enables data-driven decision-making for Germany's energy transition (Energiewende).

## Data Sources
The data is retrieved from dedicated API endpoints provided by the [FfE Open Data Portal](https://opendata.ffe.de/), containing detailed information on heat pump potentials at the state and district levels. The geographical information essential for visualization is obtained from publicly available GeoJSON files.

## Technology Stack
- **Streamlit**: Provides the framework for developing the interactive web interface.
- **Pandas**: Used for data processing and analysis.
- **Plotly**: Responsible for creating the interactive and geographical visualizations presented in the app.
- **DuckDB**: Operates as an in-memory SQL database (OLAP), allowing effective data management and queries.
