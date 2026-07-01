"""
Timeframe resampling and window scaling.

Fetch daily once → resample to Weekly / Monthly locally.
Forward-fill before resampling to avoid phantom gaps from
holidays and trading halts.
"""

import pandas as pd

from config.engine import Timeframe, TIMEFRAME_WINDOWS
from utils.logger import get_logger

logger = get_logger(__name__)

# Pandas resample rules
_RESAMPLE_RULES = {
    Timeframe.DAILY: None,      # No resampling needed
    Timeframe.WEEKLY: "W",      # Weekly (Friday close)
    Timeframe.MONTHLY: "ME",    # Month-end
}


def resample_ohlc(
    df: pd.DataFrame,
    timeframe: Timeframe,
) -> pd.DataFrame:
    """
    Resample daily OHLC data to the target timeframe.

    Steps:
      1. Forward-fill to handle holidays / trading halts
      2. Resample using pandas OHLC aggregation rules
      3. Drop any resulting NaN rows

    Args:
        df:        Daily OHLC DataFrame with DatetimeIndex.
        timeframe: Target timeframe.

    Returns:
        Resampled DataFrame (or original if DAILY).
    """
    if timeframe == Timeframe.DAILY:
        return df.copy()

    rule = _RESAMPLE_RULES[timeframe]

    # Forward-fill BEFORE resampling to prevent phantom gaps
    filled = df.ffill()

    resampled = filled.resample(rule).agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
        }
    ).dropna()

    logger.debug(
        f"Resampled {len(df)} daily → {len(resampled)} {timeframe.value} rows"
    )
    return resampled


def get_windows(timeframe: Timeframe) -> dict:
    """
    Get RSR and RSM window sizes for a timeframe.

    Returns dict with keys 'rsr' and 'rsm'.
    """
    return TIMEFRAME_WINDOWS[timeframe]


def resample_close_series(
    close: pd.Series,
    timeframe: Timeframe,
) -> pd.Series:
    """
    Resample a close price series to the target timeframe.

    Simpler version for when we only need Close prices.

    Args:
        close:     Daily close prices as Series with DatetimeIndex.
        timeframe: Target timeframe.

    Returns:
        Resampled close price Series.
    """
    if timeframe == Timeframe.DAILY:
        return close.copy()

    rule = _RESAMPLE_RULES[timeframe]
    return close.ffill().resample(rule).last().dropna()
