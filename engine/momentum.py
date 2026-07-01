"""
RS-Momentum computation.

CRITICAL: RSM is computed from the rate-of-change of RAW RS,
NOT from the already-normalized RS-Ratio. Computing ROC on
a z-score creates a double-normalization artifact.

Pipeline:
  Raw RS → ROC(1) → optional smoothing → z-score normalize → RS-Momentum

Smoothing is configurable via MOMENTUM_SMOOTHING in config.py:
  1 = no smoothing (raw ROC)
  3 = light smoothing
  5 = stronger smoothing
"""

import numpy as np

from engine.normalization import normalize_zscore_vectorized
from config.engine import EPSILON, MOMENTUM_SMOOTHING
from utils.logger import get_logger

logger = get_logger(__name__)


def compute_roc(values: np.ndarray, period: int = 1) -> np.ndarray:
    """
    Compute rate-of-change: ROC(t) = (RS(t) / RS(t-1)) - 1

    Args:
        values: 1D array.
        period: Lookback period (default 1).

    Returns:
        1D array of ROC values. First `period` values are NaN.
    """
    n = len(values)
    result = np.full(n, np.nan)

    if n <= period:
        return result

    prev = values[:-period]
    curr = values[period:]

    with np.errstate(divide="ignore", invalid="ignore"):
        roc = np.where(prev != 0, (curr / prev) - 1.0, np.nan)

    result[period:] = roc
    return result


def smooth_roc(
    roc: np.ndarray,
    smoothing_window: int = MOMENTUM_SMOOTHING,
) -> np.ndarray:
    """
    Apply rolling mean smoothing to ROC values.

    ROC_S(t) = (1/s) * sum(ROC(t-i) for i in 0..s-1)

    Args:
        roc:              1D array of ROC values (may contain NaN).
        smoothing_window: Number of periods to average.
                          1 = no smoothing (returns input unchanged).

    Returns:
        1D array of smoothed ROC values.
    """
    if smoothing_window <= 1:
        return roc.copy()

    n = len(roc)
    result = np.full(n, np.nan)

    if n < smoothing_window:
        logger.warning(
            f"ROC series ({n}) shorter than smoothing window ({smoothing_window})"
        )
        return result

    # Use cumsum for O(n) rolling mean (NaN-aware)
    import pandas as pd

    s = pd.Series(roc)
    smoothed = s.rolling(window=smoothing_window, min_periods=smoothing_window).mean()
    result = smoothed.values

    return result


def compute_rs_momentum(
    raw_rs: np.ndarray,
    window: int,
    smoothing: int = MOMENTUM_SMOOTHING,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """
    Compute RS-Momentum from raw RS values.

    Steps:
      1. ROC of raw RS: ROC(t) = RS(t)/RS(t-1) - 1
      2. Optional smoothing: ROC_S = RollingMean(ROC, smoothing)
      3. Normalize: RSM = 100 + Z-Score(ROC_S, window)

    This is the CORRECT JdK-inspired methodology: momentum is
    derived from the raw RS, not from the normalized RS-Ratio.

    Args:
        raw_rs:    1D array of raw relative strength values.
        window:    Rolling window for z-score normalization (rsm window).
        smoothing: ROC smoothing window (1 = no smoothing).
        epsilon:   Numerical stability constant.

    Returns:
        1D array of RS-Momentum values centered at 100.
    """
    # Step 1: Rate of change of raw RS
    roc = compute_roc(raw_rs, period=1)

    # Step 2: Optional smoothing
    roc_s = smooth_roc(roc, smoothing_window=smoothing)

    # Step 3: Normalize the (optionally smoothed) ROC
    rsm = normalize_zscore_vectorized(roc_s, window=window, epsilon=epsilon)

    return rsm
