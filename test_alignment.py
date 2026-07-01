import os
import sys
import pandas as pd
import numpy as np
from datetime import date, timedelta
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe

engine = JdKEngine()

dates1 = pd.date_range("2020-01-01", periods=100)
# Sector has a gap of 5 days
dates2 = dates1.drop(dates1[15:20])

bench = pd.Series(np.random.rand(100) * 100 + 100, index=dates1)
bench_df = bench.to_frame(name="Close")
sector_df = pd.DataFrame({"Close": np.random.rand(95) * 100 + 100}, index=dates2)

print(f"Bench len: {len(bench_df)}, Sector len: {len(sector_df)}")

res = engine._compute_sector(
    "TEST", sector_df, engine._resample_close(bench_df, Timeframe.DAILY),
    Timeframe.DAILY, 10, 14
)

print(f"Valid points (res.dates): {len(res.dates)}")
print(f"RSR points: {len(res.rs_ratio)}")
print(f"RSM points: {len(res.rs_momentum)}")

print("\nRunning full engine compute...")
sector_data = {"TEST1": sector_df, "TEST2": pd.DataFrame({"Close": np.random.rand(100) * 100 + 100}, index=dates1)}
full_res = engine.compute(sector_data, bench_df, Timeframe.DAILY, "BENCH")

for tk, r in full_res.sectors.items():
    print(f"{tk} -> dates:{len(r.dates)}, rsr:{len(r.rs_ratio)}, rsm:{len(r.rs_momentum)}")

print(f"Common dates len: {len(full_res.common_dates)}")
