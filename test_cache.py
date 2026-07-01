from datetime import date, timedelta
from cache.cache_manager import CacheManager
from providers.yfinance_provider import YFinanceProvider
import time

cm = CacheManager(providers=[YFinanceProvider()])
end = date.today()
start = end - timedelta(days=365*5)

# Clear old cache first
print("0. Clearing old cache...")
cleared = cm.clear_cache()
print(f"   Cleared {cleared} files")

# Fetch (should block, save, and populate SQLite)
print("1. Fetching NIFTY 50 (cold)...")
df = cm.get_or_fetch("NIFTY 50", start, end)
print(f"   Got {len(df)} rows")

# Check stale (should be fresh now)
stale = cm.is_stale("NIFTY 50")
print(f"2. is_stale: {stale}  (expected: False)")

# Load from cache (should be cache hit)
print("3. Loading from cache...")
df2 = cm.load("NIFTY 50")
print(f"   Got {len(df2)} rows from cache")

# Second get_or_fetch (should be cache hit, no network)
print("4. Second get_or_fetch (should be instant)...")
t0 = time.time()
df3 = cm.get_or_fetch("NIFTY 50", start, end)
elapsed = time.time() - t0
print(f"   Got {len(df3)} rows in {elapsed:.3f}s (expected < 0.1s)")

# Stats
stats = cm.get_cache_stats()
print(f"5. Stats: {stats}")
print("DONE")
