"""
Tests for timeframe resampling.

Validates:
  - Forward-fill before resampling
  - Weekly and monthly aggregation rules
  - Window size scaling per timeframe
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.timeframe import resample_ohlc, resample_close_series, get_windows
from config.engine import Timeframe

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def daily_df():
    df = pd.read_csv(FIXTURES / "benchmark_daily.csv", parse_dates=["Date"])
    return df.set_index("Date")


class TestResampleOHLC:
    """Tests for OHLC resampling."""

    def test_daily_returns_copy(self, daily_df):
        """Daily timeframe should return a copy, not modify original."""
        result = resample_ohlc(daily_df, Timeframe.DAILY)
        assert len(result) == len(daily_df)
        assert result is not daily_df

    def test_weekly_reduces_rows(self, daily_df):
        """Weekly resampling should have fewer rows than daily."""
        result = resample_ohlc(daily_df, Timeframe.WEEKLY)
        assert len(result) < len(daily_df)
        # ~100 trading days ≈ 20 weeks
        assert 15 <= len(result) <= 25

    def test_monthly_reduces_more(self, daily_df):
        """Monthly should have fewer rows than weekly."""
        weekly = resample_ohlc(daily_df, Timeframe.WEEKLY)
        monthly = resample_ohlc(daily_df, Timeframe.MONTHLY)
        assert len(monthly) < len(weekly)

    def test_weekly_ohlc_rules(self, daily_df):
        """Weekly: Open=first, High=max, Low=min, Close=last."""
        result = resample_ohlc(daily_df, Timeframe.WEEKLY)

        assert "Open" in result.columns
        assert "High" in result.columns
        assert "Low" in result.columns
        assert "Close" in result.columns

        # High should always >= Open, Close, Low
        assert (result["High"] >= result["Open"]).all()
        assert (result["High"] >= result["Close"]).all()
        assert (result["High"] >= result["Low"]).all()

    def test_no_nan_after_resample(self, daily_df):
        """Resampled output should have no NaN."""
        weekly = resample_ohlc(daily_df, Timeframe.WEEKLY)
        assert weekly.isna().sum().sum() == 0

    def test_ffill_handles_gaps(self):
        """Forward-fill should handle missing days correctly."""
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-05"])
        df = pd.DataFrame(
            {
                "Open": [100, 110, 130],
                "High": [105, 115, 135],
                "Low": [95, 105, 125],
                "Close": [102, 112, 132],
            },
            index=dates,
        )
        result = resample_ohlc(df, Timeframe.WEEKLY)
        assert result.isna().sum().sum() == 0


class TestResampleCloseSeries:
    """Tests for close-only resampling."""

    def test_daily_unchanged(self, daily_df):
        close = daily_df["Close"]
        result = resample_close_series(close, Timeframe.DAILY)
        assert len(result) == len(close)

    def test_weekly_close_matches_ohlc(self, daily_df):
        """Weekly close from series should match weekly close from OHLC."""
        close_series = resample_close_series(daily_df["Close"], Timeframe.WEEKLY)
        ohlc_result = resample_ohlc(daily_df, Timeframe.WEEKLY)

        # Align indices
        common = close_series.index.intersection(ohlc_result.index)
        np.testing.assert_allclose(
            close_series.loc[common].values,
            ohlc_result.loc[common, "Close"].values,
        )


class TestGetWindows:
    """Tests for window size retrieval."""

    def test_weekly_canonical(self):
        w = get_windows(Timeframe.WEEKLY)
        assert w["rsr"] == 10
        assert w["rsm"] == 14

    def test_daily_scaled(self):
        w = get_windows(Timeframe.DAILY)
        assert w["rsr"] == 52
        assert w["rsm"] == 70

    def test_monthly_short(self):
        w = get_windows(Timeframe.MONTHLY)
        assert w["rsr"] == 3
        assert w["rsm"] == 4
