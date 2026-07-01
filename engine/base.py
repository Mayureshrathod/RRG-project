"""
Abstract base and data classes for the RRG engine.

Defines IRRGEngine interface and RRGResult dataclass so that
future engines (Mansfield, Custom) can be swapped without
touching the dashboard.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config.engine import Timeframe


@dataclass
class SectorResult:
    """RRG computation result for a single sector."""

    ticker: str
    display_name: str
    dates: np.ndarray           # datetime64 array
    raw_rs: np.ndarray          # Raw relative strength (price ratio)
    rs_ratio: np.ndarray        # Normalized RS-Ratio (centered at 100)
    rs_momentum: np.ndarray     # Normalized RS-Momentum (centered at 100)
    quadrants: np.ndarray       # Quadrant label per date (str array)
    velocity: np.ndarray        # Movement magnitude per step
    direction: np.ndarray       # Direction angle in degrees per step
    rank: np.ndarray            # Composite rank score


@dataclass
class RRGComputationResult:
    """Full RRG computation result for all sectors against one benchmark."""

    benchmark: str
    timeframe: Timeframe
    sectors: Dict[str, SectorResult]
    common_dates: np.ndarray
    computed_at: str = field(default_factory=lambda: str(np.datetime64("now")))

    @property
    def num_sectors(self) -> int:
        return len(self.sectors)

    @property
    def num_dates(self) -> int:
        return len(self.common_dates)


class IRRGEngine(ABC):
    """Abstract interface for RRG computation engines."""

    @abstractmethod
    def compute(
        self,
        sector_data: Dict[str, pd.DataFrame],
        benchmark_data: pd.DataFrame,
        timeframe: Timeframe,
        benchmark_name: str = "",
    ) -> RRGComputationResult:
        """Compute RRG positions for all sectors against a benchmark."""
        ...
