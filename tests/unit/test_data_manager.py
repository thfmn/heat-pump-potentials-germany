"""Unit tests for webapp/data_manager.py module.

Tests cover:
- fetch_data() with mocked HTTP requests
- preprocess_data_germany() transformation logic
- update_df_categories() mapping functionality
- get_result_df() query logic with DuckDB
- SQL injection prevention
- Invalid input handling
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Add webapp to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "webapp"))

from data_manager import (
    fetch_data,
    get_result_df,
    preprocess_data_germany,
    update_df_categories,
)
from utils import InputValidationError


class TestFetchData:
    """Tests for the fetch_data() function."""

    def test_fetch_data_success(self):
        """fetch_data returns JSON on successful request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}

        with patch("data_manager.requests.get", return_value=mock_response):
            result = fetch_data("https://example.com/api")

        assert result == {"test": "data"}
        mock_response.raise_for_status.assert_called_once()

    def test_fetch_data_failure_returns_none(self):
        """fetch_data returns None on request failure."""
        import requests

        with patch("data_manager.requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection failed")
            result = fetch_data("https://example.com/api")

        assert result is None

    def test_fetch_data_http_error_returns_none(self):
        """fetch_data returns None on HTTP error status."""
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("data_manager.requests.get", return_value=mock_response):
            result = fetch_data("https://example.com/api")

        assert result is None


class TestPreprocessDataGermany:
    """Tests for the preprocess_data_germany() function."""

    def test_preprocess_extracts_data_correctly(self, mock_api_response):
        """preprocess_data_germany extracts and renames columns correctly."""
        result = preprocess_data_germany(mock_api_response)

        # Check expected columns exist
        assert "region" in result.columns
        assert "building_type" in result.columns
        assert "heat_source" in result.columns
        assert "value" in result.columns

        # Check dropped columns are gone
        assert "id_opendata" not in result.columns
        assert "id_region_type" not in result.columns
        assert "region_type" not in result.columns
        assert "year" not in result.columns
        assert "internal_id" not in result.columns
        assert "id_region" not in result.columns

    def test_preprocess_renames_internal_ids(self, mock_api_response):
        """preprocess_data_germany renames internal_id columns."""
        result = preprocess_data_germany(mock_api_response)

        # internal_id_1 should become building_type
        assert "internal_id_1" not in result.columns
        assert "building_type" in result.columns

        # internal_id_2 should become heat_source
        assert "internal_id_2" not in result.columns
        assert "heat_source" in result.columns

    def test_preprocess_preserves_values(self, mock_api_response):
        """preprocess_data_germany preserves value data."""
        result = preprocess_data_germany(mock_api_response)

        values = result["value"].tolist()
        assert 0.6543 in values
        assert 0.4321 in values
        assert 0.7890 in values


class TestUpdateDfCategories:
    """Tests for the update_df_categories() function."""

    def test_update_categories_maps_building_types(self, sample_district_df):
        """update_df_categories maps building_type codes to labels."""
        df = sample_district_df.copy()
        update_df_categories(df)

        # Check that numeric codes are replaced with labels
        assert df["building_type"].iloc[0] == "One- and Two-family Houses"  # was 1
        assert df["building_type"].iloc[2] == "Apartment Buildings (3-6)"   # was 6

    def test_update_categories_maps_heat_sources(self, sample_district_df):
        """update_df_categories maps heat_source codes to labels."""
        df = sample_district_df.copy()
        update_df_categories(df)

        # Check that numeric codes are replaced with labels
        assert df["heat_source"].iloc[0] == "Air"             # was 1
        assert df["heat_source"].iloc[1] == "Ground Probe"    # was 2
        assert df["heat_source"].iloc[3] == "Ground Collector"  # was 3

    def test_update_categories_modifies_in_place(self, sample_district_df):
        """update_df_categories modifies DataFrame in place."""
        df = sample_district_df.copy()
        original_id = id(df)

        result = update_df_categories(df)

        # Should return None (modifies in place)
        assert result is None
        # Should be the same object
        assert id(df) == original_id


class TestGetResultDf:
    """Tests for the get_result_df() function."""

    def test_get_result_df_with_valid_germany_selection(self, sample_district_df_with_labels):
        """get_result_df returns filtered data for Deutschland selection."""
        # Need to make data available as global 'df' for DuckDB
        import data_manager

        try:
            # Inject df into the module's namespace for DuckDB
            data_manager.df = sample_district_df_with_labels

            result = get_result_df(
                selected_state="(Deutschland)",
                selected_building_type="One- and Two-family Houses",
                selected_heat_source="Air"
            )

            assert isinstance(result, pd.DataFrame)
            # Should only have rows matching the filters
            if len(result) > 0:
                assert all(result["building_type"] == "One- and Two-family Houses")
                assert all(result["heat_source"] == "Air")
        finally:
            # Cleanup
            if "df" in data_manager.__dict__:
                del data_manager.df

    def test_get_result_df_with_valid_state_selection(self, sample_district_df_with_labels):
        """get_result_df returns filtered data for specific state selection."""
        import data_manager

        try:
            data_manager.df = sample_district_df_with_labels

            result = get_result_df(
                selected_state="Bayern",
                selected_building_type="One- and Two-family Houses",
                selected_heat_source="Air"
            )

            assert isinstance(result, pd.DataFrame)
            if len(result) > 0:
                assert all(result["building_type"] == "One- and Two-family Houses")
                assert all(result["heat_source"] == "Air")
                assert all(result["federal_state"] == "Bayern")
        finally:
            if "df" in data_manager.__dict__:
                del data_manager.df

    def test_get_result_df_invalid_building_type_raises(self):
        """get_result_df raises InputValidationError for invalid building_type."""
        with pytest.raises(InputValidationError) as exc_info:
            get_result_df(
                selected_state="Bayern",
                selected_building_type="Invalid Type",
                selected_heat_source="Air"
            )
        assert "Invalid building type" in str(exc_info.value)

    def test_get_result_df_invalid_heat_source_raises(self):
        """get_result_df raises InputValidationError for invalid heat_source."""
        with pytest.raises(InputValidationError) as exc_info:
            get_result_df(
                selected_state="Bayern",
                selected_building_type="Total",
                selected_heat_source="Invalid Source"
            )
        assert "Invalid heat source" in str(exc_info.value)

    def test_get_result_df_invalid_state_raises(self):
        """get_result_df raises InputValidationError for invalid state."""
        with pytest.raises(InputValidationError) as exc_info:
            get_result_df(
                selected_state="Invalid State",
                selected_building_type="Total",
                selected_heat_source="Air"
            )
        assert "Invalid state" in str(exc_info.value)


class TestSQLInjectionPrevention:
    """Tests to verify SQL injection is blocked."""

    def test_sql_injection_building_type_blocked(self):
        """SQL injection in building_type is blocked by validation."""
        payloads = [
            "'; DROP TABLE data; --",
            "Total' OR '1'='1",
            "Total'; DELETE FROM data; --"
        ]

        for payload in payloads:
            with pytest.raises(InputValidationError):
                get_result_df("Bayern", payload, "Air")

    def test_sql_injection_heat_source_blocked(self):
        """SQL injection in heat_source is blocked by validation."""
        payloads = [
            "'; DROP TABLE data; --",
            "Air' OR '1'='1"
        ]

        for payload in payloads:
            with pytest.raises(InputValidationError):
                get_result_df("Bayern", "Total", payload)

    def test_sql_injection_state_blocked(self):
        """SQL injection in state is blocked by validation."""
        payloads = [
            "Bayern'; DROP TABLE data; --",
            "Bayern' OR '1'='1"
        ]

        for payload in payloads:
            with pytest.raises(InputValidationError):
                get_result_df(payload, "Total", "Air")


class TestInvalidInputHandling:
    """Tests for invalid input handling."""

    def test_empty_string_inputs_rejected(self):
        """Empty string inputs should be rejected."""
        with pytest.raises(InputValidationError):
            get_result_df("", "Total", "Air")

        with pytest.raises(InputValidationError):
            get_result_df("Bayern", "", "Air")

        with pytest.raises(InputValidationError):
            get_result_df("Bayern", "Total", "")

    def test_none_like_strings_rejected(self):
        """String values like 'None' or 'null' should be rejected."""
        with pytest.raises(InputValidationError):
            get_result_df("None", "Total", "Air")

        with pytest.raises(InputValidationError):
            get_result_df("Bayern", "null", "Air")

    def test_numeric_strings_rejected(self):
        """Numeric strings should be rejected (codes must be mapped)."""
        with pytest.raises(InputValidationError):
            get_result_df("Bayern", "1", "Air")  # Should be label, not code

        with pytest.raises(InputValidationError):
            get_result_df("Bayern", "Total", "1")  # Should be label, not code
