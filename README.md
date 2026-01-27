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

## Installation

```bash
# Clone repository
git clone https://github.com/your-username/heat-pump-potentials-germany.git
cd heat-pump-potentials-germany

# Install dependencies (requires uv - https://docs.astral.sh/uv/)
uv sync

# Run application
uv run streamlit run webapp/app.py
```

The application will be available at `http://localhost:8501`.

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Alternative Installation with pip

If you prefer using pip:

```bash
pip install -e .
streamlit run webapp/app.py
```

## Usage Guide

### Navigation

When you launch the application, you'll see an interactive map of Germany with three filter controls at the top:

1. **State Selection** (left dropdown)
   - Select `(Deutschland)` to view the entire country at the state level
   - Select any of the 16 federal states to drill down to district-level data
   - The map automatically zooms and centers on your selection

2. **Building Type** (center radio buttons)
   - **Total** - All building types combined
   - **One- and Two-family Houses** - Single-family detached homes
   - **Row Houses** - Terraced housing
   - **Semi-detached Houses** - Houses sharing a wall with one neighbor
   - **Apartment Buildings (3-6)** - Small multi-family buildings
   - **Apartment Buildings: 7 and More Apartments** - Larger multi-family buildings

3. **Heat Source** (right radio buttons)
   - **Total** - All heat pump types combined
   - **Air** - Air-source heat pumps (most common, easiest to install)
   - **Ground Probe** - Vertical borehole geothermal systems
   - **Ground Collector** - Horizontal ground loop systems
   - **Solar-Thermal Energy and Ice Storage** - Combined solar-thermal and heat pump systems

### Interpreting the Map

- **Color scale**: The Viridis colorblind-friendly scale is used - purple/blue indicates low suitability (~0%), yellow indicates high suitability (~100%)
- **Hover information**: Move your mouse over any region to see detailed suitability percentages
- **Values shown**: The percentage represents the proportion of buildings in that region that are suitable for the selected heat pump type

### Example Workflows

**Compare states for air-source heat pumps:**
1. Keep `(Deutschland)` selected in the state dropdown
2. Select "Air" as the heat source
3. Select "Total" for building type
4. Observe which states have the highest air-source heat pump potential

**Analyze apartment building potential in a specific state:**
1. Select a state (e.g., "Bayern") from the dropdown
2. Select "Apartment Buildings (3-6)" as the building type
3. Compare different heat sources to see which type works best
4. Hover over districts to identify areas with highest potential

## Data Sources

### FfE Open Data Portal

All heat pump suitability data used in this application comes from the **Forschungsstelle für Energiewirtschaft e.V. (FfE)** Open Data Portal:

- **Portal URL**: [https://opendata.ffe.de/](https://opendata.ffe.de/)
- **Data Year**: **2022** (latest available dataset)
- **Dataset**: Heat pump suitability analysis for German buildings
- **License**: Data is provided under FfE Open Data terms - see portal for current licensing

The FfE is a non-profit research organization focused on energy economics and technology. Their heat pump potential analysis evaluates building characteristics across Germany to determine suitability for various heat pump types.

### Data Coverage

| Level | Coverage | Records |
|-------|----------|---------|
| State (Bundesland) | All 16 federal states | ~16 regions |
| District (Landkreis/Kreisfreie Stadt) | ~400 districts | ~400 regions |

### Geographic Data

District and state boundary geometries are sourced from publicly available GeoJSON files maintained by German government agencies. Geometries are stored in WKT (Well-Known Text) format in the district CSV files.

### Data Refresh

The current dataset reflects 2022 building stock assessments. Data updates depend on FfE publishing new analyses. Check the [FfE Open Data Portal](https://opendata.ffe.de/) for the latest available datasets.

## Architecture

For a detailed technical overview of the system architecture, including data flow diagrams, module descriptions, and security considerations, see the [Architecture Documentation](docs/ARCHITECTURE.md).

The documentation covers:
- System overview with component diagrams
- Data flow for Germany-level and state-level views
- Module responsibilities and interactions
- File structure organization
- Security measures including SQL injection prevention

## Technology Stack
- **Streamlit**: Provides the framework for developing the interactive web interface.
- **Pandas**: Used for data processing and analysis.
- **Plotly**: Responsible for creating the interactive and geographical visualizations presented in the app.
- **DuckDB**: Operates as an in-memory SQL database (OLAP), allowing effective data management and queries.

## Contributing

We welcome contributions to improve this project. Please follow these guidelines:

### Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/heat-pump-potentials-germany.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `uv sync --all-extras`

### Development Workflow

1. Make your changes in the feature branch
2. Run linting: `uv run ruff check webapp/ tests/`
3. Run type checking: `uv run mypy webapp/`
4. Run tests: `uv run pytest`
5. Commit with clear, descriptive messages
6. Push to your fork and submit a pull request

### Code Standards

- Follow PEP 8 style guidelines (enforced by ruff)
- Add type hints for new functions
- Write unit tests for new functionality
- Use parameterized queries for any database operations (no string interpolation)
- Update documentation for user-facing changes

### Pull Request Process

1. Ensure all tests pass and linting is clean
2. Update the README.md if you change user-facing functionality
3. Reference any related issues in your PR description
4. Request review from maintainers

### Reporting Issues

When reporting bugs, please include:
- Python version and operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages or logs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Data

The heat pump suitability data used in this application is sourced from the [FfE Open Data Portal](https://opendata.ffe.de/). Please refer to the FfE Open Data Portal for the specific terms and conditions governing the use of their data.
