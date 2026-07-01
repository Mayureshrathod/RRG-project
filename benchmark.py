import time
import logging
from config.indices import BENCHMARKS
from config.engine import Timeframe
from providers.yfinance_provider import YFinanceProvider
from cache.cache_manager import CacheManager
from engine.jdk_engine import JdKEngine
from services.rrg_service import RRGService

logging.basicConfig(level=logging.ERROR)

def run_benchmark():
    providers = [YFinanceProvider()]
    cache_manager = CacheManager(providers=providers)
    engine = JdKEngine()
    service = RRGService(cache_manager, engine)
    
    # Pre-fetch data into cache so we only measure engine performance, not network
    print("Pre-fetching data to warm up cache...")
    service.get_rrg_data("NIFTY 50", "weekly")
    time.sleep(3) # allow background threads to finish if they started
    
    # Now benchmark
    iterations = 10
    total_time = 0
    
    print(f"\nRunning {iterations} iterations of engine calculation...")
    
    for i in range(iterations):
        start = time.perf_counter()
        data, max_idx = service.get_rrg_data("NIFTY 50", "weekly")
        end = time.perf_counter()
        total_time += (end - start)
        
    avg_time = total_time / iterations
    print(f"Average execution time: {avg_time:.4f} seconds ({avg_time*1000:.2f} ms)")
    print(f"Number of points calculated per sector: {max_idx}")

if __name__ == "__main__":
    run_benchmark()
