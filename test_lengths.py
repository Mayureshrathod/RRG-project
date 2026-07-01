import os
import sys
import pandas as pd
from engine.jdk_engine import JdKEngine
from config.engine import Timeframe
from cache.cache_manager import CacheManager
from datetime import date, timedelta
from services.rrg_service import RRGService

cache = CacheManager()
engine = JdKEngine()
service = RRGService(cache, engine)

res, max_idx = service.get_frame_store("^NSEI", "daily")

print(f"Global dates count: {len(res['dates'])}")
for ticker, data in res["sectors"].items():
    print(f"  {ticker}: rsr={len(data['rsr'])}, rsm={len(data['rsm'])}")
