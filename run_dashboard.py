"""
RRG Dashboard — Entry Point
"""

import sys
import os
import time
from datetime import datetime

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from cache.cache_manager import CacheManager
from engine.jdk_engine import JdKEngine
from dashboard.app import create_app
from utils.logger import get_logger
from config.indices import SECTOR_TICKERS, BENCHMARKS

logger = get_logger(__name__)

def validate_startup(cache_manager: CacheManager) -> None:
    """Run comprehensive startup validation."""
    logger.info("=" * 60)
    logger.info("STARTUP VALIDATION REPORT")
    logger.info("=" * 60)
    
    # 1. Timezone Check
    tz = time.tzname
    logger.info(f"[TIMEZONE] Local Timezone: {tz}")
    
    # 2. Duplicate Symbol Check
    all_tickers = list(SECTOR_TICKERS.keys()) + list(BENCHMARKS.keys())
    duplicates = set([x for x in all_tickers if all_tickers.count(x) > 1])
    if duplicates:
        logger.warning(f"[SYMBOLS] Duplicate tickers found: {duplicates}")
    else:
        logger.info("[SYMBOLS] No duplicate tickers found.")

    # 3. YFinance Provider Check (also checks delisted/invalid)
    from providers.yfinance_provider import validate_symbols
    validate_symbols()
    
    # 4. Cache Check
    stats = cache_manager.get_cache_stats()
    if stats["cached_tickers"] == 0:
        logger.warning("[CACHE] Cache is MISSING or empty. Data will be fetched on demand.")
    else:
        logger.info(f"[CACHE] Found {stats['cached_tickers']} daily tickers ({stats['total_size_mb']:.2f} MB)")
    
    logger.info("=" * 60)

def main() -> None:
    """Launch the RRG Dashboard."""
    logger.info("Starting RRG Dashboard...")
    
    # Initialize components
    from providers.yfinance_provider import YFinanceProvider
    from providers.bhavcopy_provider import BhavCopyProvider
    from providers.provider_manager import ProviderManager
    from services.rrg_service import RRGService
    
    provider_manager = ProviderManager(
        primary=BhavCopyProvider(),
        fallbacks=[YFinanceProvider()]
    )
    cache_manager = CacheManager(providers=[provider_manager])
    
    # Run Validation
    validate_startup(cache_manager)
    
    engine = JdKEngine()
    rrg_service = RRGService(cache_manager, engine)
    
    # Create Dash app
    app = create_app(rrg_service)
    
    # Run server
    logger.info("Server starting on port 8050...")
    logger.info("Local access: http://127.0.0.1:8050")
    logger.info("Network access: http://<YOUR_COMPUTER_IP>:8050 (for your team to access)")
    app.run(host='0.0.0.0', debug=True, port=8050)

if __name__ == "__main__":
    main()
