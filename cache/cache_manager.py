import sqlite3
import time
from datetime import date
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from config.cache import CACHE_DAILY_DIR, CACHE_FRESHNESS_HOURS, DATA_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Manages downloading, caching, and serving financial data."""
    
    def __init__(self, providers: List[Any], cache_dir=None):
        self.providers = providers
        self.db_path = DATA_DIR / "cache_metadata.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    ticker       TEXT PRIMARY KEY,
                    last_fetched REAL NOT NULL,
                    start_date   TEXT NOT NULL,
                    end_date     TEXT NOT NULL,
                    row_count    INTEGER NOT NULL
                )
            ''')
            conn.commit()

    def _sanitize_ticker(self, ticker: str) -> str:
        return ticker.lower().replace(" ", "_").replace("^", "")

    def _get_parquet_path(self, ticker: str) -> Path:
        sanitized = self._sanitize_ticker(ticker)
        return CACHE_DAILY_DIR / f"{sanitized}.parquet"

    def clear_cache(self) -> int:
        """Clear all cached files and metadata."""
        count = 0
        for p in CACHE_DAILY_DIR.glob("*.parquet"):
            p.unlink()
            count += 1
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("DELETE FROM cache_metadata")
            conn.commit()
        return count

    def get_or_fetch(self, ticker: str, start: date, end: date) -> Optional[pd.DataFrame]:
        """Get data from cache if fresh, otherwise fetch from providers."""
        if not self.is_stale(ticker):
            df = self.load(ticker)
            if df is not None and not df.empty:
                return df

        for provider in self.providers:
            df = provider.fetch_index_history(ticker, start, end)
            if df is not None and not df.empty:
                self._save(ticker, df, start, end)
                return df

        return None

    def is_stale(self, ticker: str) -> bool:
        """Check if the cache for the given ticker is stale or missing."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_fetched FROM cache_metadata WHERE ticker = ?", (ticker,))
            row = cursor.fetchone()
            
        if not row:
            return True
            
        last_fetched = row[0]
        hours_since_fetch = (time.time() - last_fetched) / 3600.0
        if hours_since_fetch > CACHE_FRESHNESS_HOURS:
            return True
            
        if not self._get_parquet_path(ticker).exists():
            return True
            
        return False

    def load(self, ticker: str) -> Optional[pd.DataFrame]:
        """Load data from parquet cache file without checking staleness."""
        path = self._get_parquet_path(ticker)
        if path.exists():
            try:
                return pd.read_parquet(path)
            except Exception as e:
                logger.error(f"Failed to read parquet for {ticker}: {e}")
        return None

    def _save(self, ticker: str, df: pd.DataFrame, start: date, end: date):
        """Save data to parquet and update metadata in SQLite."""
        path = self._get_parquet_path(ticker)
        try:
            df.to_parquet(path)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO cache_metadata 
                    (ticker, last_fetched, start_date, end_date, row_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ticker, time.time(), start.isoformat(), end.isoformat(), len(df)))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save cache for {ticker}: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return statistics about the cache."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cache_metadata")
            count = cursor.fetchone()[0]
            
        size_bytes = sum(f.stat().st_size for f in CACHE_DAILY_DIR.glob('*.parquet') if f.is_file())
        
        return {
            "cached_tickers": count,
            "total_size_mb": size_bytes / (1024 * 1024)
        }
