"""Unit tests for the stats_manager module."""

import pandas as pd
import pytest

from webapp.stats_manager import (
    calculate_summary_stats,
    get_building_type_breakdown,
    get_top_bottom_districts,
)


@pytest.fixture
def sample_stats_df():
    """Create a sample DataFrame for stats testing."""
    return pd.DataFrame({
        'district': ['Munich', 'Augsburg', 'Nuremberg', 'Regensburg', 'Wurzburg'],
        'building_type': [
            'One- and Two-family Houses',
            'One- and Two-family Houses',
            'Apartment Buildings (3-6)',
            'Apartment Buildings (3-6)',
            'Total',
        ],
        'heat_source': ['Air', 'Air', 'Air', 'Ground Probe', 'Air'],
        'value': [0.75, 0.82, 0.45, 0.61, 0.55],
        'federal_state': ['Bayern', 'Bayern', 'Bayern', 'Bayern', 'Bayern'],
        'district_type': ['City', 'City', 'City', 'City', 'City'],
    })


class TestCalculateSummaryStats:
    """Tests for calculate_summary_stats function."""

    def test_returns_correct_mean(self, sample_stats_df):
        """Test that mean is calculated correctly."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
        )
        # (0.75 + 0.82) / 2 = 0.785, * 100 = 78.5
        assert abs(stats['mean'] - 78.5) < 0.01

    def test_returns_correct_count(self, sample_stats_df):
        """Test that count is correct."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
        )
        assert stats['count'] == 2

    def test_returns_correct_median(self, sample_stats_df):
        """Test that median is calculated correctly."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
        )
        # median of [0.75, 0.82] = 0.785, * 100 = 78.5
        assert abs(stats['median'] - 78.5) < 0.01

    def test_returns_min_max(self, sample_stats_df):
        """Test that min and max are correct."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
        )
        assert abs(stats['min'] - 75.0) < 0.01
        assert abs(stats['max'] - 82.0) < 0.01

    def test_empty_filter_returns_zeros(self, sample_stats_df):
        """Test that empty filter results return zeros."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'Nonexistent Type',
            'Air',
        )
        assert stats['count'] == 0
        assert stats['mean'] == 0.0
        assert stats['median'] == 0.0

    def test_includes_filter_info(self, sample_stats_df):
        """Test that filter info is included in result."""
        stats = calculate_summary_stats(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
        )
        assert stats['building_type'] == 'One- and Two-family Houses'
        assert stats['heat_source'] == 'Air'


class TestGetTopBottomDistricts:
    """Tests for get_top_bottom_districts function."""

    def test_returns_tuple_of_dataframes(self, sample_stats_df):
        """Test that function returns tuple of DataFrames."""
        top, bottom = get_top_bottom_districts(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
            n=5,
        )
        assert isinstance(top, pd.DataFrame)
        assert isinstance(bottom, pd.DataFrame)

    def test_top_districts_sorted_descending(self, sample_stats_df):
        """Test that top districts are sorted by value descending."""
        top, _ = get_top_bottom_districts(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
            n=5,
        )
        assert top.iloc[0]['district'] == 'Augsburg'  # 0.82 is highest
        assert top.iloc[0]['value'] == 82.0

    def test_bottom_districts_sorted_descending(self, sample_stats_df):
        """Test that bottom districts are sorted by value descending (worst at bottom)."""
        _, bottom = get_top_bottom_districts(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
            n=5,
        )
        # Worst (lowest value) should be at bottom of the table
        assert bottom.iloc[-1]['district'] == 'Munich'  # 0.75 is lowest of the two
        assert bottom.iloc[-1]['value'] == 75.0

    def test_has_required_columns(self, sample_stats_df):
        """Test that result has required columns."""
        top, bottom = get_top_bottom_districts(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
            n=5,
        )
        required_cols = ['rank', 'district', 'federal_state', 'value']
        for col in required_cols:
            assert col in top.columns
            assert col in bottom.columns

    def test_rank_values(self, sample_stats_df):
        """Test that top rank starts at 1 and bottom rank reflects actual position."""
        top, bottom = get_top_bottom_districts(
            sample_stats_df,
            'One- and Two-family Houses',
            'Air',
            n=5,
        )
        # Top districts rank 1, 2, 3...
        assert top.iloc[0]['rank'] == 1
        # Bottom districts rank reflects actual position (worst at bottom has highest rank)
        # With 2 matching records, last row should have rank 2 (the worst)
        assert bottom.iloc[-1]['rank'] == len(bottom)

    def test_empty_filter_returns_empty_dataframes(self, sample_stats_df):
        """Test that empty filter returns empty DataFrames."""
        top, bottom = get_top_bottom_districts(
            sample_stats_df,
            'Nonexistent Type',
            'Air',
            n=5,
        )
        assert len(top) == 0
        assert len(bottom) == 0


class TestGetBuildingTypeBreakdown:
    """Tests for get_building_type_breakdown function."""

    def test_returns_dataframe(self, sample_stats_df):
        """Test that function returns a DataFrame."""
        result = get_building_type_breakdown(sample_stats_df, 'Air')
        assert isinstance(result, pd.DataFrame)

    def test_aggregates_by_building_type(self, sample_stats_df):
        """Test that data is aggregated by building type."""
        result = get_building_type_breakdown(sample_stats_df, 'Air')
        # Should have building types that appear with 'Air' heat source
        # Excluding 'Total' category
        assert len(result) >= 1

    def test_excludes_total_category(self, sample_stats_df):
        """Test that 'Total' building type is excluded."""
        result = get_building_type_breakdown(sample_stats_df, 'Air')
        assert 'Total' not in result['building_type'].values

    def test_has_required_columns(self, sample_stats_df):
        """Test that result has required columns."""
        result = get_building_type_breakdown(sample_stats_df, 'Air')
        required_cols = ['building_type', 'avg_value', 'count']
        for col in required_cols:
            assert col in result.columns

    def test_values_are_percentages(self, sample_stats_df):
        """Test that values are converted to percentages (0-100 scale)."""
        result = get_building_type_breakdown(sample_stats_df, 'Air')
        # All values should be in 0-100 range since we multiply by 100
        assert all(result['avg_value'] >= 0)
        assert all(result['avg_value'] <= 100)

    def test_empty_filter_returns_empty_dataframe(self, sample_stats_df):
        """Test that empty filter returns empty DataFrame."""
        result = get_building_type_breakdown(sample_stats_df, 'Nonexistent Source')
        assert len(result) == 0
