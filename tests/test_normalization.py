"""
Tests for z-score normalization.

Validates: result = 100 + (value - rolling_mean) / (rolling_std + epsilon)
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.normalization import normalize_zscore, normalize_zscore_vectorized


class TestNormalizeZscore:
    """Tests for both loop-based and vectorized normalization."""

    @pytest.fixture(params=[normalize_zscore, normalize_zscore_vectorized])
    def normalize_fn(self, request):
        """Run each test against both implementations."""
        return request.param

    def test_centered_at_100(self, normalize_fn):
        """Output should be centered around 100."""
        # Steady increase — last value above mean → result > 100
        values = np.arange(1.0, 21.0)
        result = normalize_fn(values, window=10)
        # The valid (non-NaN) values should be near 100
        valid = result[~np.isnan(result)]
        assert len(valid) > 0
        assert np.mean(valid) == pytest.approx(100.0, abs=2.0)

    def test_warmup_period_is_nan(self, normalize_fn):
        """First (window-1) values should be NaN."""
        values = np.arange(1.0, 21.0)
        result = normalize_fn(values, window=10)
        assert all(np.isnan(result[:9]))
        assert not np.isnan(result[9])

    def test_constant_values(self, normalize_fn):
        """Constant input: std=0, epsilon prevents division by zero."""
        values = np.full(20, 100.0)
        result = normalize_fn(values, window=10)
        valid = result[~np.isnan(result)]
        # With constant values, (value - mean) = 0, so result = 100.0
        np.testing.assert_allclose(valid, 100.0, atol=0.01)

    def test_insufficient_data(self, normalize_fn):
        """Fewer points than window → all NaN."""
        values = np.array([1.0, 2.0, 3.0])
        result = normalize_fn(values, window=10)
        assert all(np.isnan(result))

    def test_window_of_2(self, normalize_fn):
        """Smallest meaningful window."""
        values = np.array([10.0, 20.0, 30.0, 40.0])
        result = normalize_fn(values, window=2)
        assert np.isnan(result[0])
        assert not np.isnan(result[1])

    def test_no_inf_values(self, normalize_fn):
        """Output should never contain inf."""
        values = np.random.randn(100) * 0.001 + 100  # very low variance
        result = normalize_fn(values, window=10)
        valid = result[~np.isnan(result)]
        assert not np.any(np.isinf(valid))

    def test_above_100_when_above_mean(self, normalize_fn):
        """Value above rolling mean → result > 100."""
        # Linear ramp: last value is always above the rolling mean
        values = np.arange(1.0, 31.0)
        result = normalize_fn(values, window=10)
        # Last few values should be > 100 since they're above the mean
        assert result[-1] > 100.0

    def test_below_100_when_below_mean(self, normalize_fn):
        """Value below rolling mean → result < 100."""
        # Declining: last value is always below the rolling mean
        values = np.arange(30.0, 0.0, -1.0)
        result = normalize_fn(values, window=10)
        assert result[-1] < 100.0

    def test_both_implementations_agree(self):
        """Loop and vectorized should produce same results."""
        values = np.cumsum(np.random.randn(100)) + 100
        r_loop = normalize_zscore(values, window=10)
        r_vec = normalize_zscore_vectorized(values, window=10)

        # Compare only non-NaN positions
        mask = ~(np.isnan(r_loop) | np.isnan(r_vec))
        np.testing.assert_allclose(r_loop[mask], r_vec[mask], rtol=1e-10)
