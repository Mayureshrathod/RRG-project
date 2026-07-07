"""
End-to-end diagnostic for the RRG data pipeline.
Tests: data fetching, engine computation, and store serialization.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date, timedelta
import numpy as np
import pandas as pd

from providers.yfinance_provider import YFinanceProvider
from providers.provider_manager import ProviderManager
from cache.cache_manager import CacheManager
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe, TIMEFRAME_WINDOWS
from config.indices import SECTOR_TICKERS, BENCHMARKS
from services.rrg_service import RRGService

print("=" * 70)
print("RRG PIPELINE DIAGNOSTIC")
print("=" * 70)

# Step 1: Test data fetching
print("\n[STEP 1] Testing YFinance data provider...")
provider = YFinanceProvider()
end_date = date.today()
start_date = end_date - timedelta(days=365 * 5)

benchmark_ticker = "NIFTY 50"
bench_df = provider.fetch_index_history(benchmark_ticker, start_date, end_date)
if bench_df is None or bench_df.empty:
    print(f"  CRITICAL: Failed to fetch benchmark {benchmark_ticker}")
    sys.exit(1)
print(f"  Benchmark '{benchmark_ticker}': {len(bench_df)} rows, range {bench_df.index[0]} to {bench_df.index[-1]}")
print(f"  Columns: {list(bench_df.columns)}")
print(f"  Close sample: {bench_df['Close'].tail(3).tolist()}")

# Fetch all sectors
sector_data = {}
for ticker in SECTOR_TICKERS:
    if ticker == benchmark_ticker:
        continue
    df = provider.fetch_index_history(ticker, start_date, end_date)
    if df is not None and not df.empty:
        sector_data[ticker] = df
        print(f"  {ticker}: {len(df)} rows OK")
    else:
        print(f"  {ticker}: FAILED")

print(f"\n  Total sectors loaded: {len(sector_data)}/{len(SECTOR_TICKERS)}")

# Step 2: Test engine computation
print("\n[STEP 2] Testing JdK Engine computation (weekly)...")
engine = JdKEngine()

for tf_name, tf in [("weekly", Timeframe.WEEKLY), ("daily", Timeframe.DAILY)]:
    print(f"\n  --- Timeframe: {tf_name} ---")
    result = engine.compute(
        sector_data=sector_data,
        benchmark_data=bench_df,
        timeframe=tf,
        benchmark_name=benchmark_ticker,
    )

    print(f"  Sectors computed: {len(result.sectors)}")
    print(f"  Common dates: {len(result.common_dates)}")

    if len(result.common_dates) > 0:
        print(f"  Date range: {result.common_dates[0]} to {result.common_dates[-1]}")
    else:
        print(f"  CRITICAL: No common dates!")
        continue

    # Check each sector
    for ticker, sr in result.sectors.items():
        rsr = sr.rs_ratio
        rsm = sr.rs_momentum
        n_nan_rsr = np.sum(np.isnan(rsr))
        n_nan_rsm = np.sum(np.isnan(rsm))
        n_inf_rsr = np.sum(np.isinf(rsr))
        n_inf_rsm = np.sum(np.isinf(rsm))
        rsr_range = (np.nanmin(rsr), np.nanmax(rsr))
        rsm_range = (np.nanmin(rsm), np.nanmax(rsm))

        issues = []
        if n_nan_rsr > 0: issues.append(f"RSR has {n_nan_rsr} NaN")
        if n_nan_rsm > 0: issues.append(f"RSM has {n_nan_rsm} NaN")
        if n_inf_rsr > 0: issues.append(f"RSR has {n_inf_rsr} Inf")
        if n_inf_rsm > 0: issues.append(f"RSM has {n_inf_rsm} Inf")
        if rsr_range[0] < 80 or rsr_range[1] > 120:
            issues.append(f"RSR range extreme: {rsr_range}")
        if rsm_range[0] < 80 or rsm_range[1] > 120:
            issues.append(f"RSM range extreme: {rsm_range}")

        # Check length matches
        if len(rsr) != len(result.common_dates):
            issues.append(f"RSR length {len(rsr)} != dates {len(result.common_dates)}")
        if len(rsm) != len(result.common_dates):
            issues.append(f"RSM length {len(rsm)} != dates {len(result.common_dates)}")
        if len(sr.quadrants) != len(result.common_dates):
            issues.append(f"Quadrants length {len(sr.quadrants)} != dates {len(result.common_dates)}")
        if len(sr.velocity) != len(result.common_dates):
            issues.append(f"Velocity length {len(sr.velocity)} != dates {len(result.common_dates)}")
        if len(sr.direction) != len(result.common_dates):
            issues.append(f"Direction length {len(sr.direction)} != dates {len(result.common_dates)}")
        if len(sr.rank) != len(result.common_dates):
            issues.append(f"Rank length {len(sr.rank)} != dates {len(result.common_dates)}")

        # Check quadrant distribution
        quad_counts = {}
        for q in sr.quadrants:
            quad_counts[q] = quad_counts.get(q, 0) + 1

        status = "ISSUES" if issues else "OK"
        print(f"  {ticker:30s} RSR[{rsr_range[0]:.2f},{rsr_range[1]:.2f}] RSM[{rsm_range[0]:.2f},{rsm_range[1]:.2f}] pts={len(rsr)} quads={quad_counts} [{status}]")
        for issue in issues:
            print(f"    !! {issue}")

# Step 3: Test serialization (what the dashboard receives)
print("\n[STEP 3] Testing RRG Service serialization...")
pm = ProviderManager(primary=provider, fallbacks=[])
cm = CacheManager(providers=[pm])
service = RRGService(cm, engine)

data_dict, max_idx = service.get_frame_store("NIFTY 50", "weekly")

print(f"  max_idx (slider max): {max_idx}")
print(f"  dates count: {len(data_dict.get('dates', []))}")
print(f"  sectors in store: {list(data_dict.get('sectors', {}).keys())}")

if data_dict.get('sectors'):
    for ticker, sd in data_dict['sectors'].items():
        rsr = sd['rsr']
        rsm = sd['rsm']
        n_null_rsr = sum(1 for x in rsr if x is None)
        n_null_rsm = sum(1 for x in rsm if x is None)
        valid_rsr = [x for x in rsr if x is not None]
        valid_rsm = [x for x in rsm if x is not None]
        
        issues = []
        if n_null_rsr > 0: issues.append(f"{n_null_rsr} null RSR values")
        if n_null_rsm > 0: issues.append(f"{n_null_rsm} null RSM values")
        if len(rsr) != len(data_dict['dates']):
            issues.append(f"RSR len {len(rsr)} != dates {len(data_dict['dates'])}")

        # Check quadrant distribution
        quad_counts = {}
        for q in sd['quadrant']:
            quad_counts[q] = quad_counts.get(q, 0) + 1
            
        status = "ISSUES" if issues else "OK"
        rsr_min = min(valid_rsr) if valid_rsr else 'N/A'
        rsr_max = max(valid_rsr) if valid_rsr else 'N/A'
        rsm_min = min(valid_rsm) if valid_rsm else 'N/A'
        rsm_max = max(valid_rsm) if valid_rsm else 'N/A'
        print(f"  {ticker:30s} rsr[{rsr_min:.2f},{rsr_max:.2f}] rsm[{rsm_min:.2f},{rsm_max:.2f}] len={len(rsr)} [{status}]")
        for issue in issues:
            print(f"    !! {issue}")

    # Show last frame values (what graph shows at max slider)
    print(f"\n  Last frame data (frame={max_idx}):")
    for ticker, sd in data_dict['sectors'].items():
        last_rsr = sd['rsr'][max_idx] if max_idx < len(sd['rsr']) else 'OOB'
        last_rsm = sd['rsm'][max_idx] if max_idx < len(sd['rsm']) else 'OOB'
        last_quad = sd['quadrant'][max_idx] if max_idx < len(sd['quadrant']) else 'OOB'
        print(f"    {ticker:30s} RSR={last_rsr}  RSM={last_rsm}  Quad={last_quad}")
else:
    print("  CRITICAL: No sectors in store data!")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
