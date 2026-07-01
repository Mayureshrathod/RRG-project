"""
Cache and Data Provider configuration.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DAILY_DIR = DATA_DIR / "daily"
CACHE_WEEKLY_DIR = DATA_DIR / "weekly"
CACHE_MONTHLY_DIR = DATA_DIR / "monthly"
LOG_DIR = PROJECT_ROOT / "logs"

# Auto-create directories
for _dir in [CACHE_DAILY_DIR, CACHE_WEEKLY_DIR, CACHE_MONTHLY_DIR, LOG_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# Data Fetching
PERIOD_DAYS = 730  # History window in calendar days
CACHE_FRESHNESS_HOURS = 6  # Re-fetch if cache older than this
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # Exponential backoff base (seconds)

DATA_PROVIDER = "yfinance"
