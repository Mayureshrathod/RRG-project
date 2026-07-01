"""
BUG 1 deeper diagnosis -- compare different RSM approaches.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from datetime import date, timedelta

from cache.cache_manager import CacheManager
from providers.yfinance_provider import YFinanceProvider
from config.engine import Timeframe, TIMEFRAME_WINDOWS, EPSILON

provider = YFinanceProvider()
cache = CacheManager(providers=[provider])

end_date = date.today()
start_date = end_date - timedelta(days=365 * 5)

bench_df = cache.get_or_fetch("NIFTY 50", start_date, end_date)
sector_df = cache.get_or_fetch("NIFTY BANK", start_date, end_date)

# Resample to weekly
bench_close = bench_df.ffill()["Close"].resample("W").last().dropna()
sector_close = sector_df.ffill()["Close"].resample("W").last().dropna()

# Align
aligned = pd.concat([sector_close.rename("sector"), bench_close.rename("bench")], axis=1, join="inner").dropna()
print(f"Aligned rows: {len(aligned)}")

raw_rs = aligned["sector"] / aligned["bench"]
rsr_window = 10
rsm_window = 14

# Current RSR
rs_mean = raw_rs.rolling(window=rsr_window).mean()
rs_std = raw_rs.rolling(window=rsr_window).std(ddof=0)
rsr = 100.0 + (raw_rs - rs_mean) / (rs_std + EPSILON)

# Current RSM (from raw_rs.pct_change)
roc = raw_rs.pct_change(1)
roc_mean = roc.rolling(window=rsm_window).mean()
roc_std = roc.rolling(window=rsm_window).std(ddof=0)
rsm_current = 100.0 + (roc - roc_mean) / (roc_std + EPSILON)

# WRONG RSM (from rsr.pct_change -- double normalization)
roc_wrong = rsr.pct_change(1)
roc_wrong_mean = roc_wrong.rolling(window=rsm_window).mean()
roc_wrong_std = roc_wrong.rolling(window=rsm_window).std(ddof=0)
rsm_wrong = 100.0 + (roc_wrong - roc_wrong_mean) / (roc_wrong_std + EPSILON)

valid = rsr.notna() & rsm_current.notna() & rsm_wrong.notna()

print("\n== NIFTY BANK last 10 dates ==")
print(f"{'Date':>12} {'RSR':>8} {'RSM(correct)':>13} {'RSM(wrong)':>13}")
for d, r, m_c, m_w in zip(
    aligned.index[valid][-10:],
    rsr[valid][-10:],
    rsm_current[valid][-10:],
    rsm_wrong[valid][-10:]
):
    print(f"{str(d.date()):>12} {r:8.2f} {m_c:13.2f} {m_w:13.2f}")

rsr_clean = rsr[valid].values
rsm_c_clean = rsm_current[valid].values
rsm_w_clean = rsm_wrong[valid].values

print(f"\nRSR     range: {rsr_clean.min():.2f} - {rsr_clean.max():.2f}, std={rsr_clean.std():.4f}")
print(f"RSM(ok) range: {rsm_c_clean.min():.2f} - {rsm_c_clean.max():.2f}, std={rsm_c_clean.std():.4f}")
print(f"RSM(bad)range: {rsm_w_clean.min():.2f} - {rsm_w_clean.max():.2f}, std={rsm_w_clean.std():.4f}")

# Check: are they effectively identical? 
corr = np.corrcoef(rsm_c_clean, rsm_w_clean)[0, 1]
print(f"\nCorrelation between correct and wrong RSM: {corr:.6f}")
print(f"Mean absolute difference: {np.mean(np.abs(rsm_c_clean - rsm_w_clean)):.6f}")
