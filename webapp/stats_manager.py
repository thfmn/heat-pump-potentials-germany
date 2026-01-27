"""Statistics calculation module for the Heat Pump Potentials Germany dashboard.

This module provides functions for calculating summary statistics, identifying
top and bottom performing districts, and generating building type breakdowns
for heat pump suitability data visualization.

Functions:
    calculate_summary_stats: Compute summary statistics for filtered data.
    get_top_bottom_districts: Get top N and bottom N districts by suitability.
    get_building_type_breakdown: Aggregate data by building type for charts.
"""

from typing import Any

import pandas as pd
from config import BUILDING_TYPE_MAPPING


def calculate_summary_stats(
    df: pd.DataFrame,
    building_type: str,
    heat_source: str,
) -> dict[str, Any]:
    """Calculate summary statistics for heat pump suitability data.

    Computes aggregate statistics for the suitability values in the filtered
    DataFrame, including mean, median, standard deviation, and total count.

    Args:
        df: DataFrame containing heat pump suitability data with columns
            'district', 'building_type', 'heat_source', 'value', 'federal_state'.
        building_type: The building type filter (e.g., 'Total', 'One- and Two-family Houses').
        heat_source: The heat source filter (e.g., 'Total', 'Air', 'Ground Probe').

    Returns:
        Dictionary containing:
            - 'count': Number of districts/regions in the filtered data.
            - 'mean': Average suitability percentage (0-100 scale).
            - 'median': Median suitability percentage (0-100 scale).
            - 'std': Standard deviation of suitability (0-100 scale).
            - 'min': Minimum suitability value (0-100 scale).
            - 'max': Maximum suitability value (0-100 scale).
            - 'total_value': Sum of all suitability values.
            - 'building_type': The building type filter used.
            - 'heat_source': The heat source filter used.

    Example:
        >>> stats = calculate_summary_stats(df, 'Total', 'Air')
        >>> print(f"Average suitability: {stats['mean']:.1f}%")
    """
    # Filter data by building type and heat source
    filtered_df = df[
        (df['building_type'] == building_type) & (df['heat_source'] == heat_source)
    ]

    if filtered_df.empty:
        return {
            'count': 0,
            'mean': 0.0,
            'median': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0,
            'total_value': 0.0,
            'building_type': building_type,
            'heat_source': heat_source,
        }

    values = filtered_df['value']

    # Convert proportions (0-1) to percentages (0-100) for display
    return {
        'count': len(filtered_df),
        'mean': float(values.mean() * 100),
        'median': float(values.median() * 100),
        'std': float(values.std() * 100) if len(values) > 1 else 0.0,
        'min': float(values.min() * 100),
        'max': float(values.max() * 100),
        'total_value': float(values.sum()),
        'building_type': building_type,
        'heat_source': heat_source,
    }


def get_top_bottom_districts(
    df: pd.DataFrame,
    building_type: str,
    heat_source: str,
    n: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Get the top N and bottom N districts by suitability value.

    Identifies the districts with the highest and lowest heat pump suitability
    values for the specified building type and heat source combination.

    Args:
        df: DataFrame containing heat pump suitability data with columns
            'district', 'building_type', 'heat_source', 'value', 'federal_state'.
        building_type: The building type filter (e.g., 'Total', 'One- and Two-family Houses').
        heat_source: The heat source filter (e.g., 'Total', 'Air', 'Ground Probe').
        n: Number of top/bottom districts to return. Defaults to 10.

    Returns:
        Tuple of (top_df, bottom_df) where each DataFrame contains columns:
            - 'rank': 1-indexed rank (1 is best for top, 1 is worst for bottom).
            - 'district': District name.
            - 'federal_state': State name (or 'region' for Germany-level data).
            - 'value': Suitability percentage (0-100 scale).

    Example:
        >>> top, bottom = get_top_bottom_districts(df, 'Total', 'Air', n=5)
        >>> print(f"Best district: {top.iloc[0]['district']}")
    """
    # Filter data by building type and heat source
    filtered_df = df[
        (df['building_type'] == building_type) & (df['heat_source'] == heat_source)
    ].copy()

    if filtered_df.empty:
        empty_df = pd.DataFrame(columns=['rank', 'district', 'federal_state', 'value'])
        return empty_df, empty_df

    # Determine the region column name (differs between Germany and state level)
    region_col = 'federal_state' if 'federal_state' in filtered_df.columns else 'region'
    district_col = 'district' if 'district' in filtered_df.columns else 'region'

    # Sort by value descending for top districts
    sorted_df = filtered_df.sort_values('value', ascending=False)

    # Create top N dataframe
    top_n = sorted_df.head(n).reset_index(drop=True)
    top_state_vals = (
        top_n[region_col].values if region_col in top_n.columns else [''] * len(top_n)
    )
    top_df = pd.DataFrame({
        'rank': range(1, len(top_n) + 1),
        'district': top_n[district_col].values,
        'federal_state': top_state_vals,
        'value': (top_n['value'] * 100).round(1).values,
    })

    # Create bottom N dataframe (sorted descending, so worst at bottom)
    # Ranks reflect actual position: if 45 total, bottom 10 shows ranks 36, 37...45
    total_count = len(sorted_df)
    bottom_n = sorted_df.tail(n).sort_values('value', ascending=False).reset_index(drop=True)
    bottom_state_vals = (
        bottom_n[region_col].values if region_col in bottom_n.columns else [''] * len(bottom_n)
    )
    # Calculate actual ranks (starts at total-n+1, ends at total for worst)
    actual_ranks = list(range(total_count - len(bottom_n) + 1, total_count + 1))
    bottom_df = pd.DataFrame({
        'rank': actual_ranks,
        'district': bottom_n[district_col].values,
        'federal_state': bottom_state_vals,
        'value': (bottom_n['value'] * 100).round(1).values,
    })

    return top_df, bottom_df


def get_building_type_breakdown(
    df: pd.DataFrame,
    heat_source: str,
    state: str | None = None,
) -> pd.DataFrame:
    """Aggregate suitability data by building type for visualization.

    Computes the average suitability for each building type, suitable for
    creating pie charts or bar charts showing the distribution of heat pump
    potential across different building categories.

    Args:
        df: DataFrame containing heat pump suitability data with columns
            'district', 'building_type', 'heat_source', 'value', 'federal_state'.
        heat_source: The heat source filter (e.g., 'Total', 'Air', 'Ground Probe').
        state: Optional state name to filter by. If None, uses all data.

    Returns:
        DataFrame with columns:
            - 'building_type': Building type label.
            - 'avg_value': Average suitability percentage (0-100 scale).
            - 'count': Number of districts/regions for this building type.
            - 'building_type_code': Original building type code for sorting.

    Example:
        >>> breakdown = get_building_type_breakdown(df, 'Air', state='Bayern')
        >>> print(breakdown[['building_type', 'avg_value']])
    """
    # Filter by heat source
    filtered_df = df[df['heat_source'] == heat_source].copy()

    # Filter by state if specified
    if state and state != "(Deutschland)":
        state_col = 'federal_state' if 'federal_state' in filtered_df.columns else 'region'
        filtered_df = filtered_df[filtered_df[state_col] == state]

    if filtered_df.empty:
        return pd.DataFrame(columns=['building_type', 'avg_value', 'count', 'building_type_code'])

    # Group by building type and calculate mean
    # First, we need to reverse-map labels back to codes for proper ordering
    label_to_code = {v: k for k, v in BUILDING_TYPE_MAPPING.items()}

    # Aggregate by building type
    aggregated = filtered_df.groupby('building_type').agg(
        avg_value=('value', 'mean'),
        count=('value', 'count'),
    ).reset_index()

    # Add building type code for sorting
    aggregated['building_type_code'] = aggregated['building_type'].map(
        lambda x: label_to_code.get(x, 999)
    )

    # Convert to percentage
    aggregated['avg_value'] = (aggregated['avg_value'] * 100).round(1)

    # Sort by code (keeps 'Total' (100) at end)
    aggregated = aggregated.sort_values('building_type_code')

    # Exclude 'Total' row for breakdown charts (it's a summary, not a category)
    aggregated = aggregated[aggregated['building_type'] != 'Total']

    return aggregated.reset_index(drop=True)
