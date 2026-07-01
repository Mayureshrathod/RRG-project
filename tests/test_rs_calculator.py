"""
Tests for raw RS (Relative Strength) computation.

Validates: RS = SectorPrice / BenchmarkPrice
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.rs_calculator import compute_raw_rs, align_and_compute_raw_rs

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def benchmark_df():
    df = pd.read_csv(FIXTURES / "benchmark_daily.csv", parse_dates=["Date"])
    return df.set_index("Date")


@pytest.fixture
def sector_df():
    df = pd.read_csv(FIXTURES / "sector_daily.csv", parse_dates=["Date"])
    return df.set_index("Date")


class TestComputeRawRS:
    """Tests for compute_raw_rs()."""

    def test_basic_ratio(self):
        """RS = sector / benchmark for simple values."""
        sector = np.array([50.0, 60.0, 70.0])
        benchmark = np.array([100.0, 100.0, 100.0])
        rs = compute_raw_rs(sector, benchmark)
        np.testing.assert_allclose(rs, [0.5, 0.6, 0.7])

    def test_equal_prices(self):
        """RS = 1.0 when prices are equal."""
        prices = np.array([100.0, 200.0, 300.0])
        rs = compute_raw_rs(prices, prices)
        np.testing.assert_allclose(rs, [1.0, 1.0, 1.0])

    def test_zero_benchmark(self):
        """RS should be NaN when benchmark is zero."""
        sector = np.array([50.0, 60.0])
        benchmark = np.array([100.0, 0.0])
        rs = compute_raw_rs(sector, benchmark)
        assert rs[0] == 0.5
        assert np.isnan(rs[1])

    def test_empty_arrays(self):
        """Empty inputs should return empty output."""
        rs = compute_raw_rs(np.array([]), np.array([]))
        assert len(rs) == 0

    def test_single_value(self):
        """Single value should work."""
        rs = compute_raw_rs(np.array([50.0]), np.array([100.0]))
        np.testing.assert_allclose(rs, [0.5])


class TestAlignAndComputeRawRS:
    """Tests for align_and_compute_raw_rs()."""

    def test_with_fixtures(self, sector_df, benchmark_df):
        """RS from fixtures: sector starts at 5000, benchmark at 10000."""
        result = align_and_compute_raw_rs(sector_df, benchmark_df)

        assert not result.empty
        assert "Raw_RS" in result.columns
        assert "Sector_Close" in result.columns
        assert "Benchmark_Close" in result.columns

        # First row: sector=5000, benchmark=10000 → RS=0.5
        first_rs = result["Raw_RS"].iloc[0]
        assert abs(first_rs - 0.5) < 0.01

    def test_no_nan_in_output(self, sector_df, benchmark_df):
        """Aligned output should have no NaN in Raw_RS."""
        result = align_and_compute_raw_rs(sector_df, benchmark_df)
        assert result["Raw_RS"].isna().sum() == 0

    def test_alignment_drops_mismatched_dates(self):
        """Only common dates should appear in output."""
        dates_a = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        dates_b = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])

        sector = pd.DataFrame({"Close": [100, 110, 120]}, index=dates_a)
        benchmark = pd.DataFrame({"Close": [200, 210, 220]}, index=dates_b)

        result = align_and_compute_raw_rs(sector, benchmark)
        # Only 2024-01-02 and 2024-01-03 overlap
        assert len(result) == 2

    def test_rs_direction_matches_outperformance(self, sector_df, benchmark_df):
        """RS should increase when sector outperforms benchmark."""
        result = align_and_compute_raw_rs(sector_df, benchmark_df)
        rs = result["Raw_RS"].values

        # In the first ~30 days, sector outperforms → RS should be increasing
        early_rs = rs[:30]
        assert early_rs[-1] > early_rs[0], (
            "RS should increase during sector outperformance"
        )
