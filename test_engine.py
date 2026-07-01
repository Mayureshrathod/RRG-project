"""Verify RRG Engine accuracy: NIFTY BANK vs NIFTY 50, weekly, 1 year."""
from datetime import date, timedelta
from cache.cache_manager import CacheManager
from providers.yfinance_provider import YFinanceProvider
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe

cm = CacheManager(providers=[YFinanceProvider()])
engine = JdKEngine()

end = date.today()
start = end - timedelta(days=365)

# Fetch data
print("Fetching NIFTY 50 and NIFTY BANK...")
bench_df = cm.get_or_fetch("NIFTY 50", start, end)
bank_df = cm.get_or_fetch("NIFTY BANK", start, end)
print(f"  Benchmark: {len(bench_df)} rows")
print(f"  NIFTY BANK: {len(bank_df)} rows")

# Compute
sector_data = {"NIFTY BANK": bank_df}
result = engine.compute(sector_data, bench_df, Timeframe.WEEKLY, "NIFTY 50")

bank = result.sectors["NIFTY BANK"]

print(f"\nDates: {len(bank.dates)} weekly periods")
print(f"Final RSR: {bank.rs_ratio[-1]:.4f}")
print(f"Final RSM: {bank.rs_momentum[-1]:.4f}")
print(f"Final Quadrant: {bank.quadrants[-1]}")
print(f"Final Direction: {bank.direction[-1]:.2f} deg")
print(f"Final Velocity: {bank.velocity[-1]:.4f}")

# Sanity checks
rsr_final = bank.rs_ratio[-1]
rsm_final = bank.rs_momentum[-1]

print(f"\n--- SANITY CHECKS ---")
print(f"RSR in range 90-110: {90 < rsr_final < 110} (value: {rsr_final:.4f})")
print(f"RSM in range 90-110: {90 < rsm_final < 110} (value: {rsm_final:.4f})")
print(f"RSR != RSM: {abs(rsr_final - rsm_final) > 0.01} (diff: {abs(rsr_final - rsm_final):.4f})")

# Show last 5 data points
print(f"\nLast 5 data points:")
print(f"{'Date':<12} {'RSR':>8} {'RSM':>8} {'Quadrant':<12}")
for i in range(-5, 0):
    d = str(bank.dates[i])[:10]
    print(f"{d:<12} {bank.rs_ratio[i]:>8.3f} {bank.rs_momentum[i]:>8.3f} {bank.quadrants[i]:<12}")
