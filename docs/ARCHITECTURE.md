# Architecture Overview

This document describes the system architecture of the Heat Pump Potentials Germany application.

## System Overview Diagram

```mermaid
flowchart TB
    subgraph External["External Data Sources"]
        FFE["FfE Open Data Portal API"]
        GeoJSON["GitHub GeoJSON Repository"]
    end

    subgraph Webapp["Streamlit Web Application"]
        subgraph UI["User Interface Layer"]
            App["app.py<br/>Main Application"]
            Filters["Filter Controls<br/>(State, Building Type, Heat Source)"]
            MapDisplay["Map Display<br/>(Plotly Choropleth)"]
            Stats["Statistics Panel"]
        end

        subgraph Core["Core Business Logic"]
            DataMgr["data_manager.py<br/>Data Fetching & Queries"]
            MapMgr["map_manager.py<br/>Map Generation"]
            Config["config.py<br/>Configuration & Constants"]
            Utils["utils.py<br/>Validation & Utilities"]
            Logging["logging_config.py<br/>Logging Setup"]
        end

        subgraph Data["Data Layer"]
            DuckDB["DuckDB<br/>(In-Memory)"]
            CSVFiles["CSV Files<br/>(District Data)"]
        end
    end

    %% External connections
    FFE -->|"REST API<br/>(id_opendata=87)"| DataMgr
    GeoJSON -->|"State Boundaries"| MapMgr

    %% Internal connections
    App --> Filters
    App --> MapDisplay
    App --> Stats
    App --> DataMgr
    App --> MapMgr
    App --> Config
    App --> Logging

    DataMgr --> Config
    DataMgr --> Utils
    DataMgr --> DuckDB
    DataMgr --> CSVFiles

    MapMgr --> Config

    Filters -->|"User Selection"| DataMgr
    DataMgr -->|"Filtered DataFrame"| MapMgr
    MapMgr -->|"Plotly Figure"| MapDisplay
```

## Data Flow

The application supports two primary data flows depending on the user's geographic selection:

### Germany-Level View (Deutschland)

```mermaid
sequenceDiagram
    participant User
    participant App as app.py
    participant DM as data_manager.py
    participant API as FfE API
    participant DB as DuckDB
    participant MM as map_manager.py
    participant UI as Streamlit UI

    User->>App: Select "(Deutschland)"
    App->>DM: fetch_data(STATE_DATA_URL)
    DM->>API: GET /api/od/v_opendata?id_opendata=eq.87
    API-->>DM: JSON response
    DM->>DM: preprocess_data_germany()
    DM->>DM: update_df_categories()
    DM->>DB: CREATE TABLE data
    App->>DM: get_result_df(state, building_type, heat_source)
    DM->>DM: validate_inputs()
    DM->>DB: SELECT * FROM data WHERE ...
    DB-->>DM: Filtered DataFrame
    DM-->>App: result_df
    App->>MM: create_germany_map(result_df, ...)
    MM->>MM: Build Plotly choropleth
    MM-->>App: Plotly Figure
    App->>UI: st.plotly_chart(fig)
    UI-->>User: Display choropleth map
```

### State-Level View (Individual State)

```mermaid
sequenceDiagram
    participant User
    participant App as app.py
    participant DM as data_manager.py
    participant CSV as CSV Files
    participant MM as map_manager.py
    participant UI as Streamlit UI

    User->>App: Select specific state (e.g., "Bayern")
    App->>App: Look up filename in DISTRICT_DATA_SELECTION
    App->>CSV: pd.read_csv(by_full_data.csv)
    CSV-->>App: Raw DataFrame
    App->>DM: update_df_categories(df)
    App->>App: Parse WKT geometry
    App->>App: Create GeoDataFrame
    App->>MM: create_state_map(gdf, state, building_type, heat_source)
    MM->>MM: Filter by query string
    MM->>MM: Convert geometry to GeoJSON
    MM->>MM: Build Plotly choropleth
    MM-->>App: Plotly Figure
    App->>UI: st.plotly_chart(fig)
    UI-->>User: Display district-level map
```

## Module Descriptions

### `webapp/app.py`
Main Streamlit application entry point. Responsibilities:
- Initialize session state for filter selections
- Orchestrate data loading based on geographic scope
- Render the three-column filter layout
- Display the choropleth map and statistics panel
- Handle errors with user-friendly messages

### `webapp/config.py`
Central configuration module. Contains:
- API endpoint URLs (FfE Open Data Portal)
- GeoJSON source URLs (state and district boundaries)
- List of 15 German federal states
- File path mappings for district CSV files
- Geographic center coordinates and zoom levels per state
- Category mappings (building types, heat sources)

### `webapp/data_manager.py`
Data fetching and query module. Provides:
- `fetch_data(url)`: Fetch JSON from FfE API
- `preprocess_data_germany(raw_json)`: Transform API response to DataFrame
- `update_df_categories(df)`: Apply human-readable category labels
- `get_result_df(state, building_type, heat_source)`: Query filtered data via DuckDB

### `webapp/map_manager.py`
Map generation module. Provides:
- `set_geographical_values(selected_state)`: Get lat/lon/zoom for state
- `create_germany_map(...)`: Generate state-level choropleth
- `create_state_map(...)`: Generate district-level choropleth

### `webapp/utils.py`
Shared utility functions. Contains:
- Input validation against allowed values
- `InputValidationError` exception class
- `validate_inputs()`: Validates building type, heat source, and state

### `webapp/logging_config.py`
Logging configuration module. Provides:
- `setup_logging()`: Configure logger with console handler
- Timestamp formatting for log messages
- Handler deduplication for Streamlit reruns

## File Structure

```
heat-pump-potentials-germany/
├── webapp/
│   ├── app.py              # Main Streamlit application
│   ├── config.py           # Configuration and constants
│   ├── data_manager.py     # Data fetching and DuckDB queries
│   ├── map_manager.py      # Plotly map generation
│   ├── utils.py            # Validation utilities
│   ├── logging_config.py   # Logging setup
│   └── data/
│       └── districts/      # Pre-computed CSV files (16 states)
│           ├── bw_full_data.csv
│           ├── by_full_data.csv
│           └── ...
├── tests/
│   ├── __init__.py
│   └── unit/
│       ├── __init__.py
│       └── test_sql_injection.py
├── notebooks/
│   └── district_map_generation.ipynb
├── docs/
│   └── ARCHITECTURE.md     # This file
├── pyproject.toml          # Project dependencies and tool config
└── README.md               # Project documentation
```

## Security Considerations

1. **SQL Injection Prevention**: All database queries use parameterized placeholders (`?`) instead of string interpolation. User inputs are validated against allowed values before query execution.

2. **Input Validation**: The `validate_inputs()` function checks all user-provided values against predefined allowed lists before any database operation.

3. **Error Handling**: Exceptions are caught and logged, with user-friendly error messages displayed via `st.error()`.

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | Streamlit | Interactive UI |
| Data Processing | Pandas, GeoPandas | DataFrame operations |
| Database | DuckDB (in-memory) | Fast analytical queries |
| Visualization | Plotly Express | Choropleth maps |
| Geometry | Shapely | WKT parsing |
| HTTP Client | Requests | API calls |
| Testing | pytest | Unit tests |
| Linting | ruff | Code quality |
| Type Checking | mypy | Static analysis |
