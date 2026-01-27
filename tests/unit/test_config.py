"""Unit tests for webapp/config.py module.

Tests cover:
- All states are defined
- All file mappings exist and are valid
- Coordinate mappings are valid
- Category mappings are complete
"""
import sys
from pathlib import Path

# Add webapp to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "webapp"))

from config import (
    BUILDING_TYPE_MAPPING,
    DISTRICT_DATA_SELECTION,
    DISTRICT_DATA_URL,
    DISTRICT_GEOJSON_URL,
    FEDERAL_STATES,
    HEAT_SOURCE_MAPPING,
    STATE_DATA_URL,
    STATE_GEO_VALUES,
    STATE_GEOJSON_URL,
)


class TestFederalStates:
    """Tests for FEDERAL_STATES configuration."""

    def test_federal_states_is_list(self):
        """FEDERAL_STATES should be a list."""
        assert isinstance(FEDERAL_STATES, list)

    def test_federal_states_has_expected_count(self):
        """FEDERAL_STATES should contain 15 states (Berlin excluded)."""
        # Berlin is excluded because it lacks district-level data
        assert len(FEDERAL_STATES) == 15

    def test_federal_states_contains_major_states(self):
        """FEDERAL_STATES should contain all major German states."""
        expected_states = [
            "Bayern",
            "Baden-Württemberg",
            "Nordrhein-Westfalen",
            "Niedersachsen",
            "Hessen"
        ]
        for state in expected_states:
            assert state in FEDERAL_STATES, f"Missing state: {state}"

    def test_federal_states_are_strings(self):
        """All entries in FEDERAL_STATES should be strings."""
        for state in FEDERAL_STATES:
            assert isinstance(state, str)
            assert len(state) > 0

    def test_federal_states_no_duplicates(self):
        """FEDERAL_STATES should not contain duplicates."""
        assert len(FEDERAL_STATES) == len(set(FEDERAL_STATES))


class TestDistrictDataSelection:
    """Tests for DISTRICT_DATA_SELECTION file mappings."""

    def test_all_states_have_file_mappings(self):
        """Every state in FEDERAL_STATES should have a file mapping."""
        for state in FEDERAL_STATES:
            assert state in DISTRICT_DATA_SELECTION, f"Missing file mapping for {state}"

    def test_file_mappings_are_csv_files(self):
        """All file mappings should end with .csv."""
        for state, filename in DISTRICT_DATA_SELECTION.items():
            assert filename.endswith(".csv"), f"Invalid filename for {state}: {filename}"

    def test_file_mappings_follow_naming_convention(self):
        """File mappings should follow the {abbrev}_full_data.csv pattern."""
        for state, filename in DISTRICT_DATA_SELECTION.items():
            assert filename.endswith("_full_data.csv"), \
                f"Unexpected pattern for {state}: {filename}"
            # Should be lowercase abbreviation
            abbrev = filename.replace("_full_data.csv", "")
            assert abbrev.islower(), f"Abbreviation should be lowercase: {abbrev}"
            assert len(abbrev) == 2, f"Abbreviation should be 2 chars: {abbrev}"

    def test_data_files_exist(self):
        """All referenced CSV files should exist in the data directory."""
        data_dir = Path(__file__).parent.parent.parent / "webapp" / "data" / "districts"

        for state, filename in DISTRICT_DATA_SELECTION.items():
            filepath = data_dir / filename
            assert filepath.exists(), f"Missing data file for {state}: {filepath}"


class TestStateGeoValues:
    """Tests for STATE_GEO_VALUES coordinate mappings."""

    def test_all_states_have_geo_values(self):
        """Every state in FEDERAL_STATES should have geographic coordinates."""
        for state in FEDERAL_STATES:
            assert state in STATE_GEO_VALUES, f"Missing geo values for {state}"

    def test_deutschland_has_geo_values(self):
        """Deutschland (Germany-wide) should have geographic coordinates."""
        assert "(Deutschland)" in STATE_GEO_VALUES

    def test_geo_values_are_valid_tuples(self):
        """Geographic values should be tuples of (lat, lon, zoom)."""
        for state, values in STATE_GEO_VALUES.items():
            assert isinstance(values, tuple), f"Geo values for {state} should be tuple"
            assert len(values) == 3, f"Geo values for {state} should have 3 elements"

    def test_latitude_in_valid_range(self):
        """Latitude values should be in valid range for Germany (~47-55)."""
        for state, (lat, lon, zoom) in STATE_GEO_VALUES.items():
            assert isinstance(lat, (int, float)), f"Latitude for {state} should be numeric"
            # Germany is roughly between 47 and 55 degrees latitude
            assert 47 <= lat <= 56, f"Invalid latitude for {state}: {lat}"

    def test_longitude_in_valid_range(self):
        """Longitude values should be in valid range for Germany (~5-15)."""
        for state, (lat, lon, zoom) in STATE_GEO_VALUES.items():
            assert isinstance(lon, (int, float)), f"Longitude for {state} should be numeric"
            # Germany is roughly between 5 and 16 degrees longitude
            assert 5 <= lon <= 16, f"Invalid longitude for {state}: {lon}"

    def test_zoom_level_in_valid_range(self):
        """Zoom levels should be reasonable (5-12 for state-level views)."""
        for state, (lat, lon, zoom) in STATE_GEO_VALUES.items():
            assert isinstance(zoom, (int, float)), f"Zoom for {state} should be numeric"
            assert 4 <= zoom <= 12, f"Invalid zoom level for {state}: {zoom}"


class TestBuildingTypeMapping:
    """Tests for BUILDING_TYPE_MAPPING category mapping."""

    def test_building_type_mapping_is_dict(self):
        """BUILDING_TYPE_MAPPING should be a dictionary."""
        assert isinstance(BUILDING_TYPE_MAPPING, dict)

    def test_building_type_mapping_has_all_types(self):
        """BUILDING_TYPE_MAPPING should contain all expected building types."""
        # Known building type codes from FfE data
        expected_codes = [1, 6, 9, 11, 38, 100]
        for code in expected_codes:
            assert code in BUILDING_TYPE_MAPPING, f"Missing building type code: {code}"

    def test_building_type_keys_are_integers(self):
        """Building type keys should be integers (FfE codes)."""
        for key in BUILDING_TYPE_MAPPING.keys():
            assert isinstance(key, int), f"Key should be int: {key}"

    def test_building_type_values_are_strings(self):
        """Building type values should be non-empty strings."""
        for code, label in BUILDING_TYPE_MAPPING.items():
            assert isinstance(label, str), f"Label for {code} should be string"
            assert len(label) > 0, f"Label for {code} should not be empty"

    def test_building_type_has_total(self):
        """BUILDING_TYPE_MAPPING should include a 'Total' category."""
        labels = list(BUILDING_TYPE_MAPPING.values())
        assert "Total" in labels, "Missing 'Total' building type"


class TestHeatSourceMapping:
    """Tests for HEAT_SOURCE_MAPPING category mapping."""

    def test_heat_source_mapping_is_dict(self):
        """HEAT_SOURCE_MAPPING should be a dictionary."""
        assert isinstance(HEAT_SOURCE_MAPPING, dict)

    def test_heat_source_mapping_has_all_types(self):
        """HEAT_SOURCE_MAPPING should contain all expected heat sources."""
        # Known heat source codes from FfE data
        expected_codes = [0, 1, 2, 3, 4]
        for code in expected_codes:
            assert code in HEAT_SOURCE_MAPPING, f"Missing heat source code: {code}"

    def test_heat_source_keys_are_integers(self):
        """Heat source keys should be integers (FfE codes)."""
        for key in HEAT_SOURCE_MAPPING.keys():
            assert isinstance(key, int), f"Key should be int: {key}"

    def test_heat_source_values_are_strings(self):
        """Heat source values should be non-empty strings."""
        for code, label in HEAT_SOURCE_MAPPING.items():
            assert isinstance(label, str), f"Label for {code} should be string"
            assert len(label) > 0, f"Label for {code} should not be empty"

    def test_heat_source_has_total(self):
        """HEAT_SOURCE_MAPPING should include a 'Total' category."""
        labels = list(HEAT_SOURCE_MAPPING.values())
        assert "Total" in labels, "Missing 'Total' heat source"

    def test_heat_source_has_air(self):
        """HEAT_SOURCE_MAPPING should include 'Air' (most common type)."""
        labels = list(HEAT_SOURCE_MAPPING.values())
        assert "Air" in labels, "Missing 'Air' heat source"


class TestURLConstants:
    """Tests for URL configuration constants."""

    def test_state_data_url_is_valid(self):
        """STATE_DATA_URL should be a valid HTTPS URL."""
        assert isinstance(STATE_DATA_URL, str)
        assert STATE_DATA_URL.startswith("https://")
        assert "opendata.ffe.de" in STATE_DATA_URL

    def test_district_data_url_is_valid(self):
        """DISTRICT_DATA_URL should be a valid HTTPS URL."""
        assert isinstance(DISTRICT_DATA_URL, str)
        assert DISTRICT_DATA_URL.startswith("https://")
        assert "opendata.ffe.de" in DISTRICT_DATA_URL

    def test_state_geojson_url_is_valid(self):
        """STATE_GEOJSON_URL should be a valid HTTPS URL to GeoJSON."""
        assert isinstance(STATE_GEOJSON_URL, str)
        assert STATE_GEOJSON_URL.startswith("https://")
        assert ".geo.json" in STATE_GEOJSON_URL

    def test_district_geojson_url_is_valid(self):
        """DISTRICT_GEOJSON_URL should be a valid HTTPS URL to GeoJSON."""
        assert isinstance(DISTRICT_GEOJSON_URL, str)
        assert DISTRICT_GEOJSON_URL.startswith("https://")
        assert ".geo.json" in DISTRICT_GEOJSON_URL

    def test_api_urls_contain_opendata_ids(self):
        """API URLs should contain the opendata ID parameter."""
        assert "id_opendata=eq.87" in STATE_DATA_URL  # State-level data
        assert "id_opendata=eq.88" in DISTRICT_DATA_URL  # District-level data
