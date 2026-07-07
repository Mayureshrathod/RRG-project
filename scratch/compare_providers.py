import sys
from pathlib import Path
from datetime import date, timedelta
import logging
import pandas as pd
import numpy as np

# Ensure project root is in PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from providers.bhavcopy_provider import BhavCopyProvider
from providers.yfinance_provider import YFinanceProvider
from config.indices import BENCHMARKS, SECTOR_TICKERS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def compare_providers():
    b_prov = BhavCopyProvider()
    y_prov = YFinanceProvider()
    
    end_date = date(2025, 6, 20)
    start_date = end_date - timedelta(days=30)
    
    # Let's test a few diverse indices
    test_indices = ["NIFTY 50", "NIFTY BANK", "NIFTY IT"]
    
    for idx in test_indices:
        print(f"--- Comparing {idx} ---")
        
        b_df = b_prov.fetch_index_history(idx, start_date, end_date)
        y_df = y_prov.fetch_index_history(idx, start_date, end_date)
        
        if b_df is None or b_df.empty:
            print(f"Failed to fetch {idx} from Bhavcopy")
            continue
            
        if y_df is None or y_df.empty:
            print(f"Failed to fetch {idx} from Yahoo Finance")
            continue
            
        # Align index (dates might have time components from Yahoo, ensure they are just dates)
        y_df.index = pd.to_datetime(y_df.index).normalize()
        b_df.index = pd.to_datetime(b_df.index).normalize()
        
        # Merge on Date
        merged = pd.merge(b_df[['Close']], y_df[['Close']], left_index=True, right_index=True, suffixes=('_Bhavcopy', '_Yahoo'))
        
        if merged.empty:
            print("No overlapping dates found!")
            continue
            
        # Calculate percentage difference
        merged['Diff_Pct'] = (merged['Close_Bhavcopy'] - merged['Close_Yahoo']) / merged['Close_Yahoo'] * 100
        
        print(f"Overlapping rows: {len(merged)}")
        print(f"Max difference: {merged['Diff_Pct'].abs().max():.4f}%")
        print(f"Mean difference: {merged['Diff_Pct'].abs().mean():.4f}%")
        
        if merged['Diff_Pct'].abs().max() < 1.0:
            print("Verdict: Providers MATCH (differences are well within expected adjusted close variance).")
        else:
            print("Verdict: Providers DIVERGE significantly.")
            print("Sample data:")
            print(merged.head())
        print("\n")

if __name__ == "__main__":
    compare_providers()
