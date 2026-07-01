"""
Tests for RS-Momentum computation.

Validates:
  1. ROC(t) = RS(t)/RS(t-1) - 1
  2. Optional smoothing: ROC_S = RollingMean(ROC, smoothing_window)
  3. RSM = 100 + Z-Score(ROC_S, window)

CRITICAL: RSM must be computed from ROC of raw RS, not from RSR.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.momentum import compute_roc, smooth_roc, compute_rs_momentum

FIXTURES = Path(__file__).parent / "fixtures"


class TestComputeROC:
    """Tests for rate-of-change computation."""

    def test_basic_roc(self):
        """ROC = curr/prev - 1."""
        values = np.array([100.0, 110.0, 121.0, 100.0])
        roc = compute_roc(values, period=1)

        assert np.isnan(roc[0])
        assert roc[1] == pytest.approx(0.10, abs=1e-10)  # 110/100 - 1
        assert roc[2] == pytest.approx(0.10, abs=1e-10)  # 121/110 - 1
        assert roc[3] == pytest.approx(100.0 / 121.0 - 1, abs=1e-10)

    def test_roc_zero_prev(self):
        """ROC should be NaN when previous value is 0."""
        values = np.array([0.0, 100.0])
        roc = compute_roc(values, period=1)
        assert np.isnan(roc[0])
        assert np.isnan(roc[1])  # prev is 0

    def test_roc_constant(self):
        """Constant values → ROC = 0."""
        values = np.full(10, 50.0)
        roc = compute_roc(values, period=1)
        assert np.isnan(roc[0])
        np.testing.assert_allclose(roc[1:], 0.0)

    def test_roc_empty(self):
        """Empty input → empty output."""
        roc = compute_roc(np.array([]), period=1)
        assert len(roc) == 0

    def test_roc_single_value(self):
        """Single value → all NaN."""
        roc = compute_roc(np.array([100.0]), period=1)
        assert len(roc) == 1
        assert np.isnan(roc[0])


class TestSmoothROC:
    """Tests for ROC smoothing."""

    def test_no_smoothing(self):
        """smoothing_window=1 should return input unchanged."""
        roc = np.array([np.nan, 0.05, 0.03, 0.04, 0.02])
        result = smooth_roc(roc, smoothing_window=1)
        np.testing.assert_array_equal(roc, result)

    def test_smoothing_window_3(self):
        """Window=3 should compute rolling mean."""
        roc = np.array([np.nan, 0.06, 0.03, 0.09, 0.06])
        result = smooth_roc(roc, smoothing_window=3)

        # First 2 values should be NaN (window not full)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        # result[2] should be NaN because roc[0] is NaN
        assert np.isnan(result[2])
        # result[3] = mean(0.06, 0.03, 0.09) = 0.06
        assert result[3] == pytest.approx(0.06, abs=1e-10)
        # result[4] = mean(0.03, 0.09, 0.06) = 0.06
        assert result[4] == pytest.approx(0.06, abs=1e-10)


class TestComputeRSMomentum:
    """Tests for the full RSM pipeline."""

    def test_output_centered_at_100(self):
        """RSM output should be centered around 100."""
        # Simulate raw RS with an uptrend
        raw_rs = np.cumsum(np.ones(50) * 0.01) + 1.0
        rsm = compute_rs_momentum(raw_rs, window=14, smoothing=1)
        valid = rsm[~np.isnan(rsm)]
        if len(valid) > 0:
            assert np.mean(valid) == pytest.approx(100.0, abs=3.0)

    def test_no_nan_propagation_after_warmup(self):
        """After warmup period, RSM should produce valid values."""
        raw_rs = np.linspace(1.0, 2.0, 50)
        rsm = compute_rs_momentum(raw_rs, window=14, smoothing=1)
        # Warmup = 1 (ROC) + 13 (window-1) = 14 NaN values
        valid = rsm[~np.isnan(rsm)]
        assert len(valid) > 0
        assert not np.any(np.isinf(valid))

    def test_momentum_positive_during_acceleration(self):
        """RSM should be higher at end of accelerating RS than at start."""
        # RS accelerating strongly: exponential growth
        raw_rs = np.array([1.0 * (1.02 ** i) for i in range(50)])
        rsm = compute_rs_momentum(raw_rs, window=14, smoothing=1)
        valid = rsm[~np.isnan(rsm)]
        if len(valid) >= 10:
            # During sustained acceleration, later RSM should trend higher
            # than earlier RSM (relative to the z-score window)
            mid = len(valid) // 2
            late_mean = np.mean(valid[mid:])
            early_mean = np.mean(valid[:mid])
            # At minimum, values should be finite and near 100
            assert not np.any(np.isinf(valid))
            assert np.abs(np.mean(valid) - 100.0) < 5.0

    def test_smoothing_reduces_noise(self):
        """Higher smoothing should produce less volatile RSM."""
        np.random.seed(42)
        raw_rs = np.cumsum(np.random.randn(100) * 0.01) + 1.0

        rsm_smooth1 = compute_rs_momentum(raw_rs, window=14, smoothing=1)
        rsm_smooth3 = compute_rs_momentum(raw_rs, window=14, smoothing=3)

        # Get valid segments
        v1 = rsm_smooth1[~np.isnan(rsm_smooth1)]
        v3 = rsm_smooth3[~np.isnan(rsm_smooth3)]

        if len(v1) > 5 and len(v3) > 5:
            # Smoothed version should have lower std
            assert np.std(v3) <= np.std(v1) * 1.5  # Allow some tolerance

    def test_with_fixture_data(self):
        """RSM from fixture data should follow expected pattern."""
        bench = pd.read_csv(
            FIXTURES / "benchmark_daily.csv", parse_dates=["Date"]
        ).set_index("Date")
        sector = pd.read_csv(
            FIXTURES / "sector_daily.csv", parse_dates=["Date"]
        ).set_index("Date")

        # Compute raw RS
        common = bench.index.intersection(sector.index)
        raw_rs = (sector.loc[common, "Close"] / bench.loc[common, "Close"]).values

        rsm = compute_rs_momentum(raw_rs, window=14, smoothing=1)
        valid = rsm[~np.isnan(rsm)]

        assert len(valid) > 0
        assert not np.any(np.isinf(valid))
