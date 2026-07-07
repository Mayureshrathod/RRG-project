"""
NSE Bhavcopy data provider.

Downloads official daily CSVs from NSE archives, caches them locally,
and extracts index OHLC history.
"""

from datetime import date, timedelta
from typing import Dict, Optional
import time
import requests
import io
from pathlib import Path

import pandas as pd

from providers.provider_interface import IDataProvider
from utils.logger import get_logger
from config.cache import DATA_DIR

logger = get_logger(__name__)

# Directory for caching raw downloaded CSVs from NSE
BHAVCOPY_CACHE_DIR = DATA_DIR / "bhavcopy_raw"
BHAVCOPY_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# NSE index key → exact string in the Bhavcopy CSV
_BHAVCOPY_TICKER_MAP: Dict[str, str] = {
    # Benchmarks
    "NIFTY 50": "Nifty 50",
    "NIFTY 500": "Nifty 500",
    "NIFTY TOTAL MARKET": "Nifty Total Market",
    # Sectors
    "NIFTY BANK": "Nifty Bank",
    "NIFTY AUTO": "Nifty Auto",
    "NIFTY ENERGY": "Nifty Energy",
    "NIFTY PSU BANK": "Nifty PSU Bank",
    "NIFTY INFRA": "Nifty Infrastructure",
    "NIFTY MEDIA": "Nifty Media",
    "NIFTY METAL": "Nifty Metal",
    "NIFTY REALTY": "Nifty Realty",
    "NIFTY PHARMA": "Nifty Pharma",
    "NIFTY IT": "Nifty IT",
    "NIFTY FMCG": "Nifty FMCG",
    "NIFTY SERVICES SECTOR": "Nifty Services Sector",
    "NIFTY CONSUMPTION": "Nifty India Consumption",
}


class BhavCopyProvider(IDataProvider):
    """Data provider using NSE Bhavcopy direct archives."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://www.nseindia.com/"
        })

    @property
    def name(self) -> str:
        return "bhavcopy"

    def _get_csv_path(self, d: date) -> Path:
        """Get the local cache path for a specific day's CSV."""
        return BHAVCOPY_CACHE_DIR / f"ind_close_all_{d.strftime('%d%m%Y')}.csv"

    def _fetch_day_csv(self, d: date) -> Optional[pd.DataFrame]:
        """Fetch a single day's CSV, from local cache if exists, else from NSE."""
        # Skip weekends completely
        if d.weekday() >= 5:
            return None

        path = self._get_csv_path(d)
        
        # Load from cache if we have it
        if path.exists():
            try:
                df = pd.read_csv(path)
                return df
            except Exception as e:
                logger.warning(f"Corrupt cached CSV for {d}: {e}. Redownloading...")
                path.unlink(missing_ok=True)
        
        # Download from NSE
        date_str = d.strftime('%d%m%Y')
        url = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{date_str}.csv"
        
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 404:
                # Market holiday, expected.
                # Let's create an empty file to indicate 'holiday/no data' to avoid 404ing repeatedly.
                path.write_text("HOLIDAY")
                return None
            
            if r.status_code != 200:
                logger.debug(f"NSE returned {r.status_code} for {url}")
                return None
                
            if "<html" in r.text[:200].lower():
                logger.error("Blocked by Cloudflare/HTML response received.")
                return None
            
            # Save raw text to cache
            path.write_text(r.text, encoding='utf-8')
            
            df = pd.read_csv(io.StringIO(r.text))
            return df
            
        except requests.RequestException as e:
            logger.debug(f"Request failed for {d}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Parse failed for {d}: {e}")
            return None

    def fetch_index_history(
        self,
        ticker: str,
        start: date,
        end: date,
    ) -> Optional[pd.DataFrame]:
        """Fetch index history by iterating over dates and parsing CSVs."""
        csv_name = _BHAVCOPY_TICKER_MAP.get(ticker)
        if not csv_name:
            logger.warning(f"No Bhavcopy mapping for '{ticker}'.")
            return None
            
        logger.info(f"Fetching {ticker} ({csv_name}) from Bhavcopy ({start} to {end})")
        t0 = time.time()
        
        rows = []
        
        # Iterate over all days in the range
        delta = end - start
        
        # To avoid bombarding the server if cache is empty, we add a tiny sleep for actual downloads.
        for i in range(delta.days + 1):
            d = start + timedelta(days=i)
            
            # Weekend check is already in _fetch_day_csv
            if d.weekday() >= 5:
                continue
                
            path = self._get_csv_path(d)
            was_cached = path.exists()
            
            # 404 cache check
            if was_cached and path.stat().st_size < 20: # "HOLIDAY" is small
                with open(path, 'r') as f:
                    if f.read().strip() == "HOLIDAY":
                        continue
            
            df_day = self._fetch_day_csv(d)
            
            if df_day is not None and not df_day.empty:
                # Find the row for this specific index
                row = df_day[df_day["Index Name"] == csv_name]
                if not row.empty:
                    # Append it as a dictionary so we can construct a DataFrame later
                    r = row.iloc[0]
                    rows.append({
                        "Date": pd.to_datetime(r["Index Date"], format="%d-%m-%Y"),
                        "Open": float(r["Open Index Value"]),
                        "High": float(r["High Index Value"]),
                        "Low": float(r["Low Index Value"]),
                        "Close": float(r["Closing Index Value"]),
                    })
                    
            if not was_cached:
                # Be polite to NSE if we just downloaded
                time.sleep(0.1)
                
        elapsed = time.time() - t0
        
        if not rows:
            logger.warning(f"Empty result for {ticker} from Bhavcopy ({elapsed:.1f}s)")
            return None
            
        # Build DataFrame
        df = pd.DataFrame(rows)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        
        logger.info(f"Fetched {ticker}: {len(df)} rows from Bhavcopy ({elapsed:.1f}s)")
        return df
