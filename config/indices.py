"""
Index and Sector tickers configuration.
"""
from typing import Dict
from config.engine import Timeframe

SECTOR_TICKERS: Dict[str, str] = {
    "NIFTY BANK": "Nifty Bank",
    "NIFTY AUTO": "Nifty Auto",
    "NIFTY ENERGY": "Nifty Energy",
    "NIFTY PSU BANK": "Nifty PSU Bank",
    "NIFTY INFRA": "Nifty Infra",
    "NIFTY MEDIA": "Nifty Media",
    "NIFTY METAL": "Nifty Metal",
    "NIFTY REALTY": "Nifty Realty",
    "NIFTY PHARMA": "Nifty Pharma",
    "NIFTY IT": "Nifty IT",
    "NIFTY FMCG": "Nifty FMCG",
    "NIFTY SERVICES SECTOR": "Nifty Services",
    "NIFTY CONSUMPTION": "Nifty Consumption",
}

BENCHMARKS: Dict[str, str] = {
    "NIFTY 50": "Nifty 50",
    "NIFTY 500": "Nifty 500",
    "NIFTY TOTAL MARKET": "Nifty Total Market",
}

DEFAULT_BENCHMARK = "NIFTY 50"
DEFAULT_TIMEFRAME = Timeframe.WEEKLY
