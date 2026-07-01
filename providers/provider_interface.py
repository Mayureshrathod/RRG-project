"""
Abstract interface for market data providers.

All providers must implement IDataProvider so that the Service Layer
and RRG Engine remain completely decoupled from the data source.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

import pandas as pd


class IDataProvider(ABC):
    """
    Interface for market data providers.

    Implementations must return a DataFrame with:
      - DatetimeIndex named 'Date'
      - Columns: Open, High, Low, Close (float64)
      - Sorted ascending by date
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging (e.g. 'yfinance')."""
        ...

    @abstractmethod
    def fetch_index_history(
        self,
        ticker: str,
        start: date,
        end: date,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data for an NSE index.

        Args:
            ticker: NSE index symbol (e.g. 'NIFTY BANK').
            start:  Start date (inclusive).
            end:    End date (inclusive).

        Returns:
            DataFrame with DatetimeIndex and OHLC columns,
            or None if the fetch failed entirely.
        """
        ...
