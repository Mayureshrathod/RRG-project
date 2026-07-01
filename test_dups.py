import numpy as np
import pandas as pd
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe

engine = JdKEngine()
dates = pd.DatetimeIndex(["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03", "2020-01-04"])
bench = pd.Series([100, 101, 102, 103, 104], index=dates)
sector = pd.DataFrame({"Close": [50, 51, 52, 53, 54]}, index=dates)

res = engine._compute_sector("TEST", sector, bench, Timeframe.DAILY, 2, 2)
print("Before trim:")
print(f"dates: {len(res.dates)}")

engine._trim_to_common_dates({"TEST": res}, np.array(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"], dtype="datetime64[ns]"))

print("After trim:")
print(f"dates: {len(res.dates)}")
