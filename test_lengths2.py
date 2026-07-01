import os
import sys
from engine.jdk_engine import JdKEngine
from cache.cache_manager import CacheManager
from services.rrg_service import RRGService

cache = CacheManager()
engine = JdKEngine()
service = RRGService(cache, engine)

try:
    res, max_idx = service.get_frame_store("NIFTY 50", "weekly")
    print("SUCCESS: Engine computed successfully.")
except Exception as e:
    print(f"FAILED: {e}")
