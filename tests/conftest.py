"""Pytest fixtures for heat pump potentials tests.

This module provides shared test fixtures that can be used across all test modules.
Fixtures include sample data, mocked API responses, and configuration helpers.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add webapp to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp"))


@pytest.fixture
def sample_district_df():
    """Create a small DataFrame with test district data.

    Returns:
        pd.DataFrame with columns matching the district CSV schema:
        district, building_type, heat_source, value, federal_state, district_type, geometry
    """
    return pd.DataFrame({
        "district": ["München", "Augsburg", "Nürnberg", "Regensburg"],
        "building_type": [1, 1, 6, 6],  # Raw codes
        "heat_source": [1, 2, 1, 3],  # Raw codes
        "value": [0.75, 0.82, 0.45, 0.61],
        "federal_state": ["Bayern", "Bayern", "Bayern", "Bayern"],
        "district_type": [
            "Kreisfreie Stadt", "Kreisfreie Stadt", "Kreisfreie Stadt", "Kreisfreie Stadt"
        ],
        "geometry": [
            "POLYGON ((11.5 48.1, 11.6 48.1, 11.6 48.2, 11.5 48.2, 11.5 48.1))",
            "POLYGON ((10.8 48.3, 10.9 48.3, 10.9 48.4, 10.8 48.4, 10.8 48.3))",
            "POLYGON ((11.0 49.4, 11.1 49.4, 11.1 49.5, 11.0 49.5, 11.0 49.4))",
            "POLYGON ((12.0 49.0, 12.1 49.0, 12.1 49.1, 12.0 49.1, 12.0 49.0))"
        ]
    })


@pytest.fixture
def sample_district_df_with_labels():
    """Create a DataFrame with human-readable category labels.

    Returns:
        pd.DataFrame with building_type and heat_source as string labels
        matching the mapped values from config.py.
    """
    return pd.DataFrame({
        "district": ["München", "Augsburg", "Nürnberg", "Regensburg"],
        "building_type": [
            "One- and Two-family Houses",
            "One- and Two-family Houses",
            "Apartment Buildings (3-6)",
            "Apartment Buildings (3-6)"
        ],
        "heat_source": ["Air", "Ground Probe", "Air", "Ground Collector"],
        "value": [0.75, 0.82, 0.45, 0.61],
        "federal_state": ["Bayern", "Bayern", "Bayern", "Bayern"],
        "district_type": [
            "Kreisfreie Stadt", "Kreisfreie Stadt", "Kreisfreie Stadt", "Kreisfreie Stadt"
        ],
        "geometry": [
            "POLYGON ((11.5 48.1, 11.6 48.1, 11.6 48.2, 11.5 48.2, 11.5 48.1))",
            "POLYGON ((10.8 48.3, 10.9 48.3, 10.9 48.4, 10.8 48.4, 10.8 48.3))",
            "POLYGON ((11.0 49.4, 11.1 49.4, 11.1 49.5, 11.0 49.5, 11.0 49.4))",
            "POLYGON ((12.0 49.0, 12.1 49.0, 12.1 49.1, 12.0 49.1, 12.0 49.0))"
        ]
    })


@pytest.fixture
def mock_api_response():
    """Create a mocked FfE API response structure.

    Returns:
        list containing a dict with 'data' key holding sample API records.
        Structure matches the actual FfE Open Data Portal response format.
    """
    return [{
        "data": [
            {
                "id_opendata": 87,
                "id_region": "08",
                "id_region_type": 1,
                "region": "Baden-Württemberg",
                "region_type": "Bundesland",
                "year": 2022,
                "internal_id": "some_id",
                "internal_id_1": 1,  # building_type code
                "internal_id_2": 1,  # heat_source code
                "value": 0.6543
            },
            {
                "id_opendata": 87,
                "id_region": "08",
                "id_region_type": 1,
                "region": "Baden-Württemberg",
                "region_type": "Bundesland",
                "year": 2022,
                "internal_id": "some_id_2",
                "internal_id_1": 1,
                "internal_id_2": 2,
                "value": 0.4321
            },
            {
                "id_opendata": 87,
                "id_region": "09",
                "id_region_type": 1,
                "region": "Bayern",
                "region_type": "Bundesland",
                "year": 2022,
                "internal_id": "some_id_3",
                "internal_id_1": 100,  # Total building type
                "internal_id_2": 0,    # Total heat source
                "value": 0.7890
            }
        ]
    }]


@pytest.fixture
def sample_config():
    """Provide sample configuration values for testing.

    Returns:
        dict containing test configuration with subsets of real config values.
    """
    return {
        "federal_states": ["Bayern", "Baden-Württemberg", "Hessen"],
        "building_type_mapping": {
            1: "One- and Two-family Houses",
            6: "Apartment Buildings (3-6)",
            100: "Total"
        },
        "heat_source_mapping": {
            0: "Total",
            1: "Air",
            2: "Ground Probe"
        },
        "state_geo_values": {
            "Bayern": (48.90, 11.45, 6.3),
            "Baden-Württemberg": (48.6, 9.1, 6.85),
            "(Deutschland)": (51.1657, 10.4515, 5)
        }
    }


@pytest.fixture
def sample_state_level_df():
    """Create a DataFrame simulating state-level API data after preprocessing.

    Returns:
        pd.DataFrame with columns: region, building_type, heat_source, value
        Ready for use with create_germany_map() after category label mapping.
    """
    return pd.DataFrame({
        "region": [
            "Bayern", "Bayern", "Bayern",
            "Baden-Württemberg", "Baden-Württemberg", "Baden-Württemberg"
        ],
        "building_type": [
            "Total", "One- and Two-family Houses", "Apartment Buildings (3-6)",
            "Total", "One- and Two-family Houses", "Apartment Buildings (3-6)"
        ],
        "heat_source": [
            "Total", "Air", "Ground Probe",
            "Total", "Air", "Ground Probe"
        ],
        "value": [0.78, 0.82, 0.45, 0.65, 0.71, 0.39]
    })
