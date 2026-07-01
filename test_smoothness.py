import os
import sys
import numpy as np
from engine.jdk_engine import JdKEngine
from cache.cache_manager import CacheManager
from services.rrg_service import RRGService

cache = CacheManager()
engine = JdKEngine()
service = RRGService(cache, engine)

try:
    res, max_idx = service.get_frame_store("NIFTY 50", "weekly")
    print("SUCCESS: Engine computed successfully.")
    
    for ticker, data in res["sectors"].items():
        rsr = np.array(data["rsr"])
        rsm = np.array(data["rsm"])
        
        # Calculate frame-to-frame delta
        rsr_diff = np.abs(np.diff(rsr))
        rsm_diff = np.abs(np.diff(rsm))
        
        max_rsr_jump = np.nanmax(rsr_diff)
        max_rsm_jump = np.nanmax(rsm_diff)
        
        # Determine if it's smooth
        is_smooth = max_rsr_jump < 5.0 and max_rsm_jump < 5.0
        print(f"{ticker}: Max RSR jump={max_rsr_jump:.2f}, Max RSM jump={max_rsm_jump:.2f} -> Smooth: {is_smooth}")

except Exception as e:
    print(f"FAILED: {e}")
