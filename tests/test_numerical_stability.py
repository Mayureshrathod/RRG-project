"""
Numerical stability tests.

These are MANDATORY edge-case tests that validate the engine
does not produce NaN, Inf, or crash under adversarial inputs.
EPSILON = 1e-6 alone is insufficient — each case must be tested.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.rs_calculator import compute_raw_rs, align_and_compute_raw_rs
from engine.normalization import normalize_zscore, normalize_zscore_vectorized
from engine.momentum import compute_roc, compute_rs_momentum
from engine.timeframe import resample_ohlc
from config.engine import Timeframe


class TestConstantPrices:
    """8.1: Constant prices — no division by zero, no NaN, no Inf."""

    def test_constant_rs(self):
        sector = np.full(100, 50.0)
        benchmark = np.full(100, 100.0)
        rs = compute_raw_rs(sector, benchmark)
        np.testing.assert_allclose(rs, 0.5)
        assert not np.any(np.isnan(rs))
        assert not np.any(np.isinf(rs))

    def test_constant_rsr(self):
        values = np.full(50, 0.5)  # constant RS
        result = normalize_zscore(values, window=10)
        valid = result[~np.isnan(result)]
        assert not np.any(np.isinf(valid))
        # Constant input: (val - mean) = 0 → result = 100
        np.testing.assert_allclose(valid, 100.0, atol=0.01)

    def test_constant_rsm(self):
        raw_rs = np.full(50, 0.5)
        rsm = compute_rs_momentum(raw_rs, window=14)
        valid = rsm[~np.isnan(rsm)]
        assert not np.any(np.isinf(valid))
        # ROC of constant = 0, normalized 0 → 100
        if len(valid) > 0:
            np.testing.assert_allclose(valid, 100.0, atol=0.01)


class TestVerySmallStdDev:
    """8.2: Very small standard deviation — epsilon must prevent blow-up."""

    def test_near_constant_normalization(self):
        # Values vary by < 0.01%
        values = np.full(50, 100.0)
        values += np.random.RandomState(42).randn(50) * 1e-8
        result = normalize_zscore(values, window=10)
        valid = result[~np.isnan(result)]
        assert not np.any(np.isinf(valid))
        assert np.all(np.abs(valid - 100.0) < 1e6)  # bounded

    def test_near_constant_vectorized(self):
        values = np.full(50, 100.0)
        values += np.random.RandomState(42).randn(50) * 1e-8
        result = normalize_zscore_vectorized(values, window=10)
        valid = result[~np.isnan(result)]
        assert not np.any(np.isinf(valid))


class TestVeryLargePrices:
    """8.3: Very large prices (10^9 scale) — no overflow."""

    def test_large_price_rs(self):
        sector = np.full(50, 5e9)
        benchmark = np.full(50, 10e9)
        rs = compute_raw_rs(sector, benchmark)
        np.testing.assert_allclose(rs, 0.5)
        assert not np.any(np.isinf(rs))

    def test_large_price_normalization(self):
        values = np.linspace(1e9, 1.1e9, 50)
        result = normalize_zscore_vectorized(values, window=10)
        valid = result[~np.isnan(result)]
        assert not np.any(np.isinf(valid))
        assert len(valid) > 0

    def test_large_price_momentum(self):
        raw_rs = np.linspace(0.5, 0.6, 50)  # RS is always ~0.5
        rsm = compute_rs_momentum(raw_rs, window=14)
        valid = rsm[~np.isnan(rsm)]
        assert not np.any(np.isinf(valid))


class TestMissingTradingDays:
    """8.4: Missing trading days — proper alignment."""

    def test_non_overlapping_dates(self):
        dates_a = pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-05"])
        dates_b = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
        sector = pd.DataFrame({"Close": [100, 110, 120]}, index=dates_a)
        benchmark = pd.DataFrame({"Close": [200, 210, 220]}, index=dates_b)

        result = align_and_compute_raw_rs(sector, benchmark)
        # Only 2024-01-03 is common
        assert len(result) == 1
        assert result["Raw_RS"].iloc[0] == pytest.approx(110.0 / 210.0)

    def test_completely_disjoint(self):
        dates_a = pd.to_datetime(["2024-01-01", "2024-01-02"])
        dates_b = pd.to_datetime(["2024-01-03", "2024-01-04"])
        sector = pd.DataFrame({"Close": [100, 110]}, index=dates_a)
        benchmark = pd.DataFrame({"Close": [200, 210]}, index=dates_b)

        result = align_and_compute_raw_rs(sector, benchmark)
        assert result.empty


class TestHolidayGaps:
    """8.5: Holiday gaps (3-5 consecutive missing days)."""

    def test_resample_with_holiday_gap(self):
        # Create data with a 5-day gap (Diwali-like)
        dates = pd.bdate_range("2024-01-01", periods=20)
        # Remove days 8-12 (5 consecutive business days)
        dates = dates.delete([7, 8, 9, 10, 11])
        df = pd.DataFrame(
            {
                "Open": np.linspace(100, 115, len(dates)),
                "High": np.linspace(105, 120, len(dates)),
                "Low": np.linspace(95, 110, len(dates)),
                "Close": np.linspace(102, 117, len(dates)),
            },
            index=dates,
        )

        result = resample_ohlc(df, Timeframe.WEEKLY)
        assert result.isna().sum().sum() == 0

    def test_ffill_across_gap(self):
        """Forward-fill should carry last value across gaps."""
        dates = pd.to_datetime(["2024-01-01", "2024-01-08"])  # 7-day gap
        df = pd.DataFrame(
            {
                "Open": [100, 110],
                "High": [105, 115],
                "Low": [95, 105],
                "Close": [102, 112],
            },
            index=dates,
        )
        # Weekly resample with ffill shouldn't crash
        result = resample_ohlc(df, Timeframe.WEEKLY)
        assert not result.empty


class TestDuplicateTimestamps:
    """8.6: Duplicate timestamps — must be handled deterministically."""

    def test_duplicate_dates_in_alignment(self):
        dates = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"])
        sector = pd.DataFrame({"Close": [100, 105, 110]}, index=dates)
        benchmark = pd.DataFrame({"Close": [200, 205, 210]}, index=dates)

        # Should not crash — duplicates handled by pandas join
        result = align_and_compute_raw_rs(sector, benchmark)
        assert not result.empty
        assert not np.any(np.isinf(result["Raw_RS"].values))


class TestMissingValues:
    """8.7: NaN in OHLC data — no silent propagation."""

    def test_nan_in_close(self):
        sector = np.array([100.0, np.nan, 120.0, 130.0])
        benchmark = np.array([200.0, 210.0, 220.0, 230.0])
        rs = compute_raw_rs(sector, benchmark)
        assert np.isnan(rs[1])  # NaN propagates to RS
        assert not np.isnan(rs[0])
        assert not np.isnan(rs[2])

    def test_nan_in_roc(self):
        values = np.array([100.0, np.nan, 120.0, 130.0, 140.0])
        roc = compute_roc(values, period=1)
        assert np.isnan(roc[0])  # first always NaN
        assert np.isnan(roc[1])  # NaN input
        assert np.isnan(roc[2])  # prev is NaN

    def test_nan_in_normalization(self):
        values = np.array([1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        result = normalize_zscore(values, window=5)
        # Should not crash, NaN windows produce NaN
        assert not np.any(np.isinf(result[~np.isnan(result)]))


class TestShortTimeSeries:
    """8.8: Fewer data points than rolling window."""

    def test_short_normalization(self):
        values = np.array([1.0, 2.0, 3.0])
        result = normalize_zscore(values, window=10)
        assert all(np.isnan(result))

    def test_short_momentum(self):
        raw_rs = np.array([0.5, 0.51, 0.52])
        rsm = compute_rs_momentum(raw_rs, window=14)
        assert all(np.isnan(rsm))

    def test_single_point(self):
        result = normalize_zscore(np.array([100.0]), window=10)
        assert len(result) == 1
        assert np.isnan(result[0])

    def test_empty_input(self):
        result = normalize_zscore(np.array([]), window=10)
        assert len(result) == 0

    def test_short_roc(self):
        roc = compute_roc(np.array([100.0]), period=1)
        assert len(roc) == 1
        assert np.isnan(roc[0])
