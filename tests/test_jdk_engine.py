"""
Tests for JdK RRG Engine.

Validates the full pipeline execution and RRGComputationResult.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.jdk_engine import JdKEngine
from config.engine import Timeframe

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def benchmark_df():
    df = pd.read_csv(FIXTURES / "benchmark_daily.csv", parse_dates=["Date"])
    return df.set_index("Date")


@pytest.fixture
def sector_df():
    df = pd.read_csv(FIXTURES / "sector_daily.csv", parse_dates=["Date"])
    return df.set_index("Date")


class TestJdKEngine:
    """Tests for the JdKEngine class."""

    def test_compute_pipeline(self, sector_df, benchmark_df):
        """Full pipeline execution should return RRGComputationResult."""
        engine = JdKEngine()
        
        sector_data = {
            "TEST1": sector_df,
            "TEST2": sector_df * 1.01  # Slightly offset
        }
        
        result = engine.compute(
            sector_data=sector_data,
            benchmark_data=benchmark_df,
            timeframe=Timeframe.WEEKLY,
            benchmark_name="NIFTY 50",
        )
        
        # Check result structure
        assert result.benchmark == "NIFTY 50"
        assert result.timeframe == Timeframe.WEEKLY
        assert result.num_sectors == 2
        assert len(result.common_dates) > 0
        
        # Check SectorResult contents
        s1 = result.sectors["TEST1"]
        assert s1.ticker == "TEST1"
        assert len(s1.dates) == result.num_dates
        assert len(s1.rs_ratio) == result.num_dates
        assert len(s1.rs_momentum) == result.num_dates
        assert len(s1.quadrants) == result.num_dates
        assert len(s1.velocity) == result.num_dates
        assert len(s1.direction) == result.num_dates
        

        
    def test_empty_sector_data(self, benchmark_df):
        """Empty sector data dictionary."""
        engine = JdKEngine()
        result = engine.compute(
            sector_data={},
            benchmark_data=benchmark_df,
            timeframe=Timeframe.DAILY,
        )
        assert result.num_sectors == 0
        
    def test_one_empty_sector_dataframe(self, sector_df, benchmark_df):
        """One sector has empty dataframe."""
        engine = JdKEngine()
        
        sector_data = {
            "GOOD": sector_df,
            "BAD": pd.DataFrame()
        }
        
        result = engine.compute(
            sector_data=sector_data,
            benchmark_data=benchmark_df,
            timeframe=Timeframe.DAILY,
        )
        assert result.num_sectors == 1
        assert "GOOD" in result.sectors
        assert "BAD" not in result.sectors
