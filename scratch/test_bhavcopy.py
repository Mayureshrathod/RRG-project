import sys
from pathlib import Path
from datetime import date, timedelta
import logging

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from providers.bhavcopy_provider import BhavCopyProvider
from config.indices import SECTOR_TICKERS, BENCHMARKS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_bhavcopy():
    provider = BhavCopyProvider()
    
    # Representative historical period (e.g., last 30 days)
    end_date = date(2025, 6, 20) # Using the known valid date we tested earlier
    start_date = end_date - timedelta(days=30)
    
    all_indices = list(BENCHMARKS.keys()) + list(SECTOR_TICKERS.keys())
    
    print(f"Testing {len(all_indices)} indices from {start_date} to {end_date}...\n")
    
    for idx in all_indices:
        print(f"--- {idx} ---")
        df = provider.fetch_index_history(idx, start_date, end_date)
        if df is not None and not df.empty:
            print(f"Success! Retrieved {len(df)} rows.")
            print("Head:")
            print(df.head(2))
            print("Tail:")
            print(df.tail(2))
        else:
            print(f"FAILED to retrieve data for {idx}")
        print("\n")

if __name__ == "__main__":
    test_bhavcopy()
