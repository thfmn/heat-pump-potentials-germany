"""Unit tests for SQL injection prevention in data_manager.py."""
import sys
from pathlib import Path

import pytest

# Add webapp to path so we can import data_manager
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "webapp"))

from data_manager import InputValidationError, validate_inputs


class TestSQLInjectionPrevention:
    """Tests to verify SQL injection attempts are blocked by input validation."""

    def test_sql_injection_in_building_type_is_blocked(self):
        """SQL injection attempt in building_type should raise InputValidationError."""
        injection_payloads = [
            "'; DROP TABLE data; --",
            "Total' OR '1'='1",
            "Total'; DELETE FROM data; --",
            "Total UNION SELECT * FROM users --",
            "1 OR 1=1",
        ]

        for payload in injection_payloads:
            with pytest.raises(InputValidationError) as exc_info:
                validate_inputs(
                    building_type=payload,
                    heat_source="Total",
                    selected_state="(Deutschland)"
                )
            assert "Invalid building type" in str(exc_info.value)

    def test_sql_injection_in_heat_source_is_blocked(self):
        """SQL injection attempt in heat_source should raise InputValidationError."""
        injection_payloads = [
            "'; DROP TABLE data; --",
            "Air' OR '1'='1",
            "Air'; DELETE FROM data; --",
            "Air UNION SELECT * FROM users --",
        ]

        for payload in injection_payloads:
            with pytest.raises(InputValidationError) as exc_info:
                validate_inputs(
                    building_type="Total",
                    heat_source=payload,
                    selected_state="(Deutschland)"
                )
            assert "Invalid heat source" in str(exc_info.value)

    def test_sql_injection_in_state_is_blocked(self):
        """SQL injection attempt in selected_state should raise InputValidationError."""
        injection_payloads = [
            "'; DROP TABLE data; --",
            "Bayern' OR '1'='1",
            "Bayern'; DELETE FROM data; --",
            "Bayern UNION SELECT * FROM users --",
        ]

        for payload in injection_payloads:
            with pytest.raises(InputValidationError) as exc_info:
                validate_inputs(
                    building_type="Total",
                    heat_source="Total",
                    selected_state=payload
                )
            assert "Invalid state" in str(exc_info.value)

    def test_valid_inputs_pass_validation(self):
        """Valid inputs should not raise any exception."""
        # This should not raise any exception
        validate_inputs(
            building_type="Total",
            heat_source="Air",
            selected_state="Bayern"
        )

        validate_inputs(
            building_type="One- and Two-family Houses",
            heat_source="Ground Probe",
            selected_state="(Deutschland)"
        )
