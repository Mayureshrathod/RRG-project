"""Verify RRG Service Layer."""
import json
from cache.cache_manager import CacheManager
from providers.yfinance_provider import YFinanceProvider
from engine.jdk_engine import JdKEngine
from services.rrg_service import RRGService

cm = CacheManager(providers=[YFinanceProvider()])
engine = JdKEngine()
service = RRGService(cm, engine)

print("Calling get_frame_store('NIFTY 50', 'weekly')...")
data_dict, max_idx = service.get_frame_store("NIFTY 50", "weekly")

# Test JSON serializable
try:
    json_str = json.dumps(data_dict)
    print(f"JSON serializable: YES ({len(json_str)} bytes)")
except Exception as e:
    print(f"JSON serializable: NO ({e})")

# Check structure
print(f"Benchmark: {data_dict['benchmark']}")
print(f"Timeframe: {data_dict['timeframe']}")
print(f"Dates count: {len(data_dict['dates'])}")
print(f"Max slider idx: {max_idx}")
print(f"Sectors: {list(data_dict['sectors'].keys())}")

# Verify lengths match
dates_len = len(data_dict["dates"])
all_ok = True
for ticker, sdata in data_dict["sectors"].items():
    rsr_len = len(sdata["rsr"])
    rsm_len = len(sdata["rsm"])
    if rsr_len != dates_len or rsm_len != dates_len:
        print(f"  MISMATCH: {ticker} rsr={rsr_len} rsm={rsm_len} dates={dates_len}")
        all_ok = False

if all_ok:
    print(f"Length check: ALL {len(data_dict['sectors'])} sectors match dates length ({dates_len})")

print("DONE")
