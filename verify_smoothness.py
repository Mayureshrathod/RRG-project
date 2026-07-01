import pandas as pd
import numpy as np
from datetime import date, timedelta
from cache.cache_manager import CacheManager
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe
from config.indices import SECTOR_TICKERS

def verify_smoothness():
    print("--- Verifying RRG Engine Smoothness ---")
    cache = CacheManager()
    engine = JdKEngine()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=365*5)
    
    benchmark = cache.get_or_fetch("NIFTY 50", start_date, end_date)
    sectors = {}
    for ticker in SECTOR_TICKERS:
        if ticker != "NIFTY 50":
            df = cache.get_or_fetch(ticker, start_date, end_date)
            if df is not None and not df.empty:
                sectors[ticker] = df
                
    result = engine.compute(sectors, benchmark, Timeframe.WEEKLY, "NIFTY 50")
    
    max_jump = 0
    max_jump_info = ""
    
    print(f"\nCommon Dates: {len(result.common_dates)}")
    for ticker, sr in result.sectors.items():
        if len(sr.dates) != len(result.common_dates):
            print(f"ERROR: {ticker} has {len(sr.dates)} dates, expected {len(result.common_dates)}")
            
        rsr = sr.rs_ratio
        rsm = sr.rs_momentum
        
        # Calculate step-by-step distances
        for i in range(1, len(rsr)):
            if np.isnan(rsr[i]) or np.isnan(rsr[i-1]):
                continue
                
            dist = np.sqrt((rsr[i] - rsr[i-1])**2 + (rsm[i] - rsm[i-1])**2)
            if dist > max_jump:
                max_jump = dist
                max_jump_info = f"{ticker} on {sr.dates[i]} (dist: {dist:.2f})"
                
    print(f"\nMaximum frame-to-frame jump observed: {max_jump:.2f} ({max_jump_info})")
    if max_jump < 10:
        print("VERDICT: SUCCESS. The trails are smooth and indices are perfectly aligned.")
    else:
        print("VERDICT: WARNING. A large jump was observed, indicating a potential index mismatch.")

if __name__ == "__main__":
    verify_smoothness()
