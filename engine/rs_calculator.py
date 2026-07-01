"""
Raw Relative Strength calculator.

Computes the raw RS as the price ratio of sector vs benchmark.
This is the foundation for both RSR and RSM.
"""

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def compute_raw_rs(
    sector_close: np.ndarray,
    benchmark_close: np.ndarray,
) -> np.ndarray:
    """
    Compute raw Relative Strength as sector/benchmark price ratio.

    Args:
        sector_close:    1D array of sector closing prices.
        benchmark_close: 1D array of benchmark closing prices (same length).

    Returns:
        1D array of raw RS values. NaN where benchmark is zero.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        raw_rs = np.where(
            benchmark_close != 0,
            sector_close / benchmark_close,
            np.nan,
        )
    return raw_rs


def align_and_compute_raw_rs(
    sector_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Align sector and benchmark data, then compute raw RS.

    Both DataFrames must have a DatetimeIndex and a 'Close' column.
    The output DataFrame has columns: Sector_Close, Benchmark_Close, Raw_RS.

    Args:
        sector_df:    Sector OHLC DataFrame.
        benchmark_df: Benchmark OHLC DataFrame.

    Returns:
        Aligned DataFrame with Raw_RS column.
    """
    # Inner join on date to get common trading days
    aligned = pd.DataFrame(
        {
            "Sector_Close": sector_df["Close"],
            "Benchmark_Close": benchmark_df["Close"],
        }
    ).dropna()

    if aligned.empty:
        logger.warning("No overlapping dates between sector and benchmark")
        return aligned

    aligned["Raw_RS"] = compute_raw_rs(
        aligned["Sector_Close"].values,
        aligned["Benchmark_Close"].values,
    )

    return aligned
