"""
Z-score normalization centered at 100.

Used for both RS-Ratio and RS-Momentum normalization.
Formula: 100 + (value - rolling_mean) / rolling_std
"""

import numpy as np

from config.engine import EPSILON
from utils.logger import get_logger

logger = get_logger(__name__)


def normalize_zscore(
    values: np.ndarray,
    window: int,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """
    Apply rolling z-score normalization centered at 100.

    Formula: 100 + (value - rolling_mean) / (rolling_std + epsilon)

    Uses pure NumPy for performance. NaN-safe: periods with
    insufficient data return NaN.

    Args:
        values:  1D array of raw values.
        window:  Rolling window size.
        epsilon: Small constant for numerical stability in std division.

    Returns:
        1D array of normalized values centered at 100.
    """
    n = len(values)
    result = np.full(n, np.nan)

    if n < window:
        logger.warning(
            f"Insufficient data for normalization: {n} < {window}"
        )
        return result

    # Compute rolling mean and std using a sliding window
    # This is faster than pandas rolling for pure numeric arrays
    for i in range(window - 1, n):
        win_slice = values[i - window + 1 : i + 1]

        # Skip if any NaN in window
        if np.any(np.isnan(win_slice)):
            continue

        mean = np.mean(win_slice)
        std = np.std(win_slice, ddof=1)  # Sample std

        result[i] = 100.0 + (values[i] - mean) / (std + epsilon)

    return result


def normalize_zscore_vectorized(
    values: np.ndarray,
    window: int,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """
    Vectorized rolling z-score normalization using cumulative sums.

    Significantly faster for large arrays (>1000 elements).
    Falls back to loop-based for small arrays.

    Args:
        values:  1D array of raw values.
        window:  Rolling window size.
        epsilon: Small constant for numerical stability.

    Returns:
        1D array of normalized values centered at 100.
    """
    n = len(values)
    if n < window:
        return np.full(n, np.nan)

    # For small arrays, use the simple loop (less overhead)
    if n < 200:
        return normalize_zscore(values, window, epsilon)

    # Vectorized using pandas-style rolling (via stride tricks)
    import pandas as pd

    s = pd.Series(values)
    rolling = s.rolling(window=window, min_periods=window)
    r_mean = rolling.mean().values
    r_std = rolling.std(ddof=1).values

    result = 100.0 + (values - r_mean) / (r_std + epsilon)

    # NaN out the warm-up period
    result[:window - 1] = np.nan

    return result
