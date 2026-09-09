"""
Benchmark execution speed of the JdK RRG Engine.
"""
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
    
    # Pre-fetch data into cache so we only measure computation, not network latency
    print("Pre-fetching data to warm up cache...")
    result = service.get_rrg_data("NIFTY 50", "weekly")
    time.sleep(1)
    
    iterations = 10
    total_time = 0
    
    print(f"\nRunning {iterations} iterations of engine calculation...")
    
    for i in range(iterations):
        start = time.perf_counter()
        result = service.get_rrg_data("NIFTY 50", "weekly")
        end = time.perf_counter()
        total_time += (end - start)
        
    avg_time = total_time / iterations
    print(f"Average execution time: {avg_time:.4f} seconds ({avg_time*1000:.2f} ms)")
    print(f"Sectors computed: {result.num_sectors}")
    print(f"Number of dates calculated per sector: {result.num_dates}")


if __name__ == "__main__":
    run_benchmark()
