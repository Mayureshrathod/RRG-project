"""
Provider Manager that orchestrates data fetching and enforces validation.
"""

from typing import List, Optional
from datetime import date
import pandas as pd
import numpy as np

from providers.provider_interface import IDataProvider
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when data fails validation checks."""
    pass


class ProviderManager(IDataProvider):
    """
    Orchestrates multiple data providers with strict fallback
    and automatic data validation.
    """

    def __init__(self, primary: IDataProvider, fallbacks: List[IDataProvider]):
        self.primary = primary
        self.fallbacks = fallbacks
        self.providers = [primary] + fallbacks

    @property
    def name(self) -> str:
        return "provider_manager"

    def fetch_index_history(self, symbol: str, start: date, end: date) -> Optional[pd.DataFrame]:
        """Fetch and validate OHLC data, falling back on errors."""
        for provider in self.providers:
            try:
                df = provider.fetch_index_history(symbol, start, end)
                
                if df is None or df.empty:
                    logger.warning(f"[{provider.name}] returned empty data for {symbol}")
                    continue
                    
                self._validate(df, symbol, provider.name)
                
                # If validation passes, return it
                return df
                
            except ValidationError as ve:
                logger.warning(f"[{provider.name}] validation failed for {symbol}: {ve}")
                continue
            except Exception as e:
                logger.warning(f"[{provider.name}] failed for {symbol}: {e}")
                continue
                
        logger.error(f"All providers failed to retrieve valid data for {symbol}.")
        return None

    def _validate(self, df: pd.DataFrame, symbol: str, provider_name: str) -> None:
        """Run strict data validation rules."""
        
        # 1. Schema validation
        required_cols = {"Open", "High", "Low", "Close"}
        if not required_cols.issubset(df.columns):
            raise ValidationError(f"Missing required columns. Found {list(df.columns)}")
            
        if df.index.name != "Date":
            raise ValidationError(f"Index must be named 'Date', got '{df.index.name}'")

        # 2. Duplicate check
        if df.index.has_duplicates:
            dups = df.index[df.index.duplicated()].tolist()
            raise ValidationError(f"Found {len(dups)} duplicate dates (e.g., {dups[0]})")

        # 3. OHLC bounds validation
        # High must be >= Low
        invalid_high_low = df[df["High"] < df["Low"]]
        if not invalid_high_low.empty:
            raise ValidationError(f"Found {len(invalid_high_low)} rows where High < Low")
            
        # Open must be between High and Low
        invalid_open = df[(df["Open"] > df["High"]) | (df["Open"] < df["Low"])]
        if not invalid_open.empty:
            # Allow for tiny floating point inaccuracies
            if (invalid_open["Open"] - invalid_open["High"]).max() > 0.01 or (invalid_open["Low"] - invalid_open["Open"]).max() > 0.01:
                raise ValidationError(f"Found {len(invalid_open)} rows where Open is outside High/Low bounds")

        # Close must be between High and Low
        invalid_close = df[(df["Close"] > df["High"]) | (df["Close"] < df["Low"])]
        if not invalid_close.empty:
             if (invalid_close["Close"] - invalid_close["High"]).max() > 0.01 or (invalid_close["Low"] - invalid_close["Close"]).max() > 0.01:
                raise ValidationError(f"Found {len(invalid_close)} rows where Close is outside High/Low bounds")

        logger.info(f"[{provider_name}] Validation PASSED for {symbol} ({len(df)} rows)")
