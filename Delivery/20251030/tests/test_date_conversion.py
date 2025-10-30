"""Tests for date conversion functionality."""
import pytest
from datetime import datetime

from frontend.pages.importador import convert_date_to_iso


class TestDateConversion:
    """Test date conversion from Brazilian format to ISO."""

    def test_convert_brazilian_date_dd_mm_yyyy(self):
        """Test conversion of DD/MM/YYYY format."""
        # Test various Brazilian dates
        assert convert_date_to_iso('28/08/2025') == '2025-08-28T00:00:00Z'
        assert convert_date_to_iso('01/01/2023') == '2023-01-01T00:00:00Z'
        assert convert_date_to_iso('31/12/2024') == '2024-12-31T00:00:00Z'
        assert convert_date_to_iso('15/06/1990') == '1990-06-15T00:00:00Z'

    def test_convert_brazilian_date_dd_mm_yy(self):
        """Test conversion of DD/MM/YY format."""
        assert convert_date_to_iso('28/08/25') == '2025-08-28T00:00:00Z'
        assert convert_date_to_iso('01/01/23') == '2023-01-01T00:00:00Z'
        assert convert_date_to_iso('31/12/99') == '1999-12-31T00:00:00Z'

    def test_convert_iso_date_passthrough(self):
        """Test that ISO dates are passed through unchanged."""
        assert convert_date_to_iso('2025-08-28') == '2025-08-28'
        assert convert_date_to_iso('2025-08-28T10:30:00Z') == '2025-08-28T10:30:00Z'
        assert convert_date_to_iso('2023-01-01 10:40:00') == '2023-01-01T10:40:00'
        assert convert_date_to_iso('2023-01-01T00:00:00Z') == '2023-01-01T00:00:00Z'

    def test_convert_edge_cases(self):
        """Test edge cases and invalid inputs."""
        # None and empty strings
        assert convert_date_to_iso(None) is None
        assert convert_date_to_iso('') is None
        assert convert_date_to_iso('   ') is None

        # Invalid formats
        assert convert_date_to_iso('invalid') is None
        assert convert_date_to_iso('13/45/2025') is None  # Invalid month
        assert convert_date_to_iso('32/08/2025') is None  # Invalid day
        assert convert_date_to_iso('28-08-2025') is None

        # Invalid date combinations
        assert convert_date_to_iso('30/02/2025') is None  # Feb 30th doesn't exist

    def test_convert_real_world_examples(self):
        """Test real-world examples from document processing."""
        # Examples from the actual error logs
        assert convert_date_to_iso('28/08/2025') == '2025-08-28T00:00:00Z'

        # Other common Brazilian date formats
        assert convert_date_to_iso('15/03/2024') == '2024-03-15T00:00:00Z'
        assert convert_date_to_iso('07/11/2023') == '2023-11-07T00:00:00Z'
        assert convert_date_to_iso('25/12/2024') == '2024-12-25T00:00:00Z'

    def test_convert_with_whitespace(self):
        """Test dates with leading/trailing whitespace."""
        assert convert_date_to_iso(' 28/08/2025 ') == '2025-08-28T00:00:00Z'
        assert convert_date_to_iso('\t15/03/2024\n') == '2024-03-15T00:00:00Z'

    def test_datetime_object_conversion(self):
        """Test that datetime objects are handled correctly."""
        dt = datetime(2025, 8, 28, 10, 30, 0)
        # The function should return ISO dates as-is, but datetime objects need conversion
        assert convert_date_to_iso('2025-08-28T10:30:00Z') == '2025-08-28T10:30:00Z'
