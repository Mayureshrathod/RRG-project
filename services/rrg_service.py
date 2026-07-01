"""
Service Layer for RRG computations.

Coordinates the CacheManager (data fetching/storage) and JdKEngine (calculations).
Ensures that the Dashboard Controller only receives pre-calculated UI-ready data.
"""

import threading
import time
from datetime import date, timedelta
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd

from config.engine import Timeframe
from config.indices import SECTOR_TICKERS
from config.cache import CACHE_FRESHNESS_HOURS
from engine.base import RRGComputationResult
from engine.jdk_engine import JdKEngine
from cache.cache_manager import CacheManager
from utils.logger import get_logger

logger = get_logger(__name__)


class RRGService:
    """Service layer bridging dashboard, cache, and engine."""

    def __init__(self, cache_manager: CacheManager, engine: JdKEngine):
        self.cache_manager = cache_manager
        self.engine = engine

    def get_rrg_data(
        self, benchmark_ticker: str, timeframe_val: str
    ) -> RRGComputationResult:
        """Load daily data from cache, run RRG computation, return RRGResult."""
        logger.info(
            f"RRGService: Computing RRG for {benchmark_ticker}, {timeframe_val}"
        )
        timeframe = Timeframe(timeframe_val)

        end_date = date.today()
        start_date = end_date - timedelta(days=365 * 5)

        # Load benchmark
        benchmark_df = self.cache_manager.get_or_fetch(
            benchmark_ticker, start_date, end_date
        )
        if benchmark_df is None or benchmark_df.empty:
            logger.error(f"Failed to load benchmark data for {benchmark_ticker}")
            return RRGComputationResult(
                benchmark=benchmark_ticker,
                timeframe=timeframe,
                sectors={},
                common_dates=np.array([], dtype="datetime64[ns]"),
            )

        # Load all sectors
        sector_data = {}
        for ticker in SECTOR_TICKERS:
            if ticker == benchmark_ticker:
                continue
            df = self.cache_manager.get_or_fetch(ticker, start_date, end_date)
            if df is not None and not df.empty:
                sector_data[ticker] = df
            else:
                logger.warning(f"Skipping {ticker}: no data available")

        if not sector_data:
            logger.error("Failed to load any sector data")
            return RRGComputationResult(
                benchmark=benchmark_ticker,
                timeframe=timeframe,
                sectors={},
                common_dates=np.array([], dtype="datetime64[ns]"),
            )

        # Compute RRG
        try:
            result = self.engine.compute(
                sector_data=sector_data,
                benchmark_data=benchmark_df,
                timeframe=timeframe,
                benchmark_name=benchmark_ticker,
            )
        except Exception as e:
            logger.error(f"Error computing RRG: {e}")
            return RRGComputationResult(
                benchmark=benchmark_ticker,
                timeframe=timeframe,
                sectors={},
                common_dates=np.array([], dtype="datetime64[ns]"),
            )

        return result

    def get_frame_store(
        self, benchmark_ticker: str, timeframe_val: str
    ) -> Tuple[Dict[str, Any], int]:
        """Pre-serialize all frame data for dcc.Store.

        Returns (data_dict, max_idx) where data_dict is JSON-serializable.
        """
        result = self.get_rrg_data(benchmark_ticker, timeframe_val)

        if not result.sectors:
            return {}, 0

        def _clean(arr: np.ndarray) -> list:
            """Convert numpy array to JSON-safe list."""
            return [
                None if (x is None or np.isnan(x) or np.isinf(x)) else round(float(x), 4)
                for x in arr
            ]

        sectors_dict = {}
        for ticker, sr in result.sectors.items():
            sectors_dict[ticker] = {
                "rsr": _clean(sr.rs_ratio),
                "rsm": _clean(sr.rs_momentum),
                "quadrant": sr.quadrants.tolist(),
                "velocity": _clean(sr.velocity),
                "direction": _clean(sr.direction),
                "rank": _clean(sr.rank),
            }

        dates_list = [
            pd.Timestamp(d).strftime("%Y-%m-%d") if pd.notnull(d) else None
            for d in result.common_dates
        ]

        data_dict = {
            "benchmark": result.benchmark,
            "timeframe": result.timeframe.value,
            "dates": dates_list,
            "sectors": sectors_dict,
        }

        max_idx = max(0, len(dates_list) - 1)
        return data_dict, max_idx

    def refresh_stale_tickers(self) -> None:
        """Check all tickers for staleness and refresh in background threads."""
        end_date = date.today()
        start_date = end_date - timedelta(days=365 * 5)
        all_tickers = list(SECTOR_TICKERS.keys())

        stale_tickers = [
            t for t in all_tickers if self.cache_manager.is_stale(t)
        ]

        if not stale_tickers:
            logger.info("All tickers are fresh, no refresh needed")
            return

        logger.info(f"Refreshing {len(stale_tickers)} stale tickers: {stale_tickers}")

        for ticker in stale_tickers:
            thread = threading.Thread(
                target=self._refresh_ticker,
                args=(ticker, start_date, end_date),
                daemon=True,
            )
            thread.start()

    def _refresh_ticker(self, ticker: str, start_date: date, end_date: date) -> None:
        """Refresh a single ticker's cache data."""
        t0 = time.time()
        try:
            df = self.cache_manager.get_or_fetch(ticker, start_date, end_date)
            elapsed = time.time() - t0
            if df is not None:
                logger.info(f"Refreshed {ticker}: {len(df)} rows ({elapsed:.1f}s)")
            else:
                logger.warning(f"Refresh failed for {ticker} ({elapsed:.1f}s)")
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"Refresh error for {ticker}: {e} ({elapsed:.1f}s)")
