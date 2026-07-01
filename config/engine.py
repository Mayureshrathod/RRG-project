"""
RRG Engine math and timeframe configuration.
"""
from enum import Enum
from typing import Dict

class Timeframe(Enum):
    """Supported analysis timeframes."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# JdK RS-Ratio and RS-Momentum window sizes per timeframe.
TIMEFRAME_WINDOWS: Dict[Timeframe, Dict[str, int]] = {
    Timeframe.DAILY:   {"rsr": 52, "rsm": 70},
    Timeframe.WEEKLY:  {"rsr": 10, "rsm": 14},   # Canonical JdK
    Timeframe.MONTHLY: {"rsr":  3, "rsm":  4},
}

EPSILON = 1e-6  # Numerical stability for std division

MOMENTUM_SMOOTHING = 1  # 1 = no smoothing (raw ROC, purest JdK approximation)
