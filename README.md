# Heat Pump Potential Analysis in Germany

## Overview
This project will showcase an interactive web application that illustrates the proportion and distribution of buildings suitable for various types of heat pumps across Germany in 2022. Developed using Streamlit, this application aims to provide valuable insights and a comprehensive understanding of the heat pump market landscape and its potential in the country.

## Data Sources
The data is retrieved from dedicated API endpoints provided by the [FfE Open Data Portal](https://opendata.ffe.de/), containing detailed information on heat pump potentials at the state and district levels. The geographical information essential for visualization is obtained from publicly available GeoJSON files.

## Technology Stack
- **Streamlit**: Provides the framework for developing the interactive web interface.
- **Pandas**: Used for data processing and analysis.
- **Plotly**: Responsible for creating the interactive and geographical visualizations presented in the app.
- **DuckDB**: Operates as an in-memory SQL database (OLAP), allowing effective data management and queries.
