import pandas as pd
import numpy as np
from datetime import date, timedelta
from cache.cache_manager import CacheManager
from providers.yfinance_provider import YFinanceProvider
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe
from config.indices import SECTOR_TICKERS

def run():
    print("Fetching data and running engine...")
    providers = [YFinanceProvider()]
    c = CacheManager(providers=providers)
    e = JdKEngine()
    
    ed = date.today()
    sd = ed - timedelta(days=365*5)
    
    bench = c.get_or_fetch("NIFTY 50", sd, ed)
    sect = {}
    for t in SECTOR_TICKERS:
        if t != "NIFTY 50":
            df = c.get_or_fetch(t, sd, ed)
            if df is not None: 
                sect[t] = df
    
    result = e.compute(sect, bench, Timeframe.WEEKLY, "NIFTY 50")
    
    realty = result.sectors["NIFTY REALTY"]
    rsr_series = realty._rsr_series
    rsm_series = realty._rsm_series
    
    print("\n" + "="*50)
    print("STEP 1: PRE-SMOOTHED DIAGNOSTIC OUTPUT")
    print("="*50)
    print(f"rsr_series index sample: {rsr_series.index[70:80].tolist()}")
    print(f"rsm_series index sample: {rsm_series.index[70:80].tolist()}")
    print(f"Are these equal? {rsr_series.index[70:80].equals(rsm_series.index[70:80])}")
    
    print("\nIndex | Date       | RSR    | RSM")
    for i in range(70, min(80, len(realty.rs_ratio))):
        d_str = str(realty.dates[i])[:10]
        print(f"{i:5d} | {d_str} | {realty.rs_ratio[i]:.3f} | {realty.rs_momentum[i]:.3f}")
    
    print("\n" + "="*50)
    print("VERIFICATION SCRIPT COMPLETED.")

if __name__ == "__main__":
    run()
