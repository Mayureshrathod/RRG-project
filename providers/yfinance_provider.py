"""
Yahoo Finance data provider.

Uses yfinance for historical OHLC data.
Maps NSE index names to Yahoo Finance tickers.
"""

from datetime import date
from typing import Dict, Optional, List, Tuple
import time

import pandas as pd

from providers.provider_interface import IDataProvider
from utils.logger import get_logger

logger = get_logger(__name__)

# NSE index → Yahoo Finance ticker mapping
_YF_TICKER_MAP: Dict[str, str] = {
    # Benchmarks
    "NIFTY 50": "^NSEI",
    "NIFTY 500": "^CRSLDX",
    "NIFTY TOTAL MARKET": "^CNXTOTALMARKET",
    # Sectors
    "NIFTY BANK": "^NSEBANK",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "NIFTY INFRA": "^CNXINFRA",
    "NIFTY MEDIA": "^CNXMEDIA",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY IT": "^CNXIT",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY SERVICES SECTOR": "^CNXSERVICE",
    "NIFTY CONSUMPTION": "^CNXCONSUM",
}


def get_yf_symbol(ticker: str) -> Optional[str]:
    """Return the Yahoo Finance symbol for a given NSE index name."""
    return _YF_TICKER_MAP.get(ticker)


def validate_symbols() -> List[Tuple[str, str, bool]]:
    """Validate all mapped Yahoo Finance symbols at startup.
    
    Returns a list of (nse_name, yf_symbol, is_valid) tuples.
    Does not crash on failures — logs warnings instead.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed. Run: pip install yfinance")
        return [(k, v, False) for k, v in _YF_TICKER_MAP.items()]

    results = []
    logger.info("=" * 60)
    logger.info("SYMBOL VALIDATION -- Yahoo Finance")
    logger.info("=" * 60)

    for nse_name, yf_symbol in _YF_TICKER_MAP.items():
        try:
            ticker_obj = yf.Ticker(yf_symbol)
            info = ticker_obj.fast_info
            # Check if we can read a price
            last_price = getattr(info, "last_price", None)
            if last_price is not None and last_price > 0:
                logger.info(f"  OK     {nse_name:<25} -> {yf_symbol:<20} (price: {last_price:.2f})")
                results.append((nse_name, yf_symbol, True))
            else:
                logger.warning(f"  WARN   {nse_name:<25} -> {yf_symbol:<20} (no price returned)")
                results.append((nse_name, yf_symbol, False))
        except Exception as e:
            logger.warning(f"  FAIL   {nse_name:<25} -> {yf_symbol:<20} ({e})")
            results.append((nse_name, yf_symbol, False))

    ok_count = sum(1 for _, _, v in results if v)
    fail_count = len(results) - ok_count
    logger.info("-" * 60)
    logger.info(f"  Summary: {ok_count} OK, {fail_count} MISSING/FAILED")
    logger.info("=" * 60)

    return results


class YFinanceProvider(IDataProvider):
    """Data provider using yfinance (Yahoo Finance API)."""

    @property
    def name(self) -> str:
        return "yfinance"

    def fetch_index_history(
        self,
        ticker: str,
        start: date,
        end: date,
    ) -> Optional[pd.DataFrame]:
        """Fetch index history from Yahoo Finance."""
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance not installed. Run: pip install yfinance")
            return None

        yf_ticker = _YF_TICKER_MAP.get(ticker)
        if yf_ticker is None:
            logger.warning(
                f"No Yahoo Finance mapping for '{ticker}'. "
                f"Available: {list(_YF_TICKER_MAP.keys())}"
            )
            return None

        try:
            t0 = time.time()
            logger.info(f"Fetching {ticker} ({yf_ticker}) from Yahoo Finance")

            data = yf.download(
                yf_ticker,
                start=start.isoformat(),
                end=end.isoformat(),
                progress=False,
                auto_adjust=True,
            )

            elapsed = time.time() - t0

            if data is None or data.empty:
                logger.warning(f"Empty result for {ticker} from Yahoo ({elapsed:.1f}s)")
                return None

            # Flatten MultiIndex columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Standardize
            df = data[["Open", "High", "Low", "Close"]].copy()
            df.index.name = "Date"
            df = df.astype(float).dropna()

            logger.info(f"Fetched {ticker}: {len(df)} rows from Yahoo ({elapsed:.1f}s)")
            return df

        except Exception as e:
            logger.error(f"Yahoo Finance fetch failed for {ticker}: {e}")
            return None
