# Screenshots Directory

This directory should contain screenshots of the Heat Pump Potentials Germany application for documentation purposes.

## Required Screenshots

To complete the README documentation, capture the following views:

### 1. `germany_map.png`
- **View**: Explorer tab at Germany level
- **Settings**: State = "(Deutschland)", Building Type = "Total", Heat Source = "Total"
- **Shows**: Choropleth map of all 16 federal states with Viridis color scale

### 2. `state_map.png`
- **View**: Explorer tab at state level (after clicking a state)
- **Settings**: Select any state (e.g., "Bayern"), Building Type = "Total", Heat Source = "Air"
- **Shows**: District-level choropleth map with breadcrumb navigation visible

### 3. `district_detail.png`
- **View**: District detail view (after clicking a district)
- **Shows**: Building type breakdown chart, heat source breakdown chart, metadata, and "Back to State" button

### 4. `compare_view.png`
- **View**: Compare tab with 3-4 states selected
- **Settings**: Select states like "Bayern", "Nordrhein-Westfalen", "Baden-Württemberg"
- **Shows**: Side-by-side state maps with comparison metrics table below

### 5. `statistics_panel.png`
- **View**: Explorer tab showing statistics section
- **Shows**: Metric cards, Top 10 table, Bottom 10 table, and Building Type breakdown chart

## How to Capture

1. Start the application: `uv run streamlit run webapp/app.py`
2. Open browser at `http://localhost:8501`
3. Navigate to each view described above
4. Use browser screenshot tool or OS screenshot tool
5. Save images as PNG with descriptive names
6. Recommended resolution: 1200x800 pixels or higher

## Image Guidelines

- Use PNG format for crisp text
- Capture at high resolution for retina displays
- Crop to show relevant content without excessive whitespace
- Ensure data is visible and readable
