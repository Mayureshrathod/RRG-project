import os

replacements = {
    "test_engine.py": [("from config import Timeframe", "from config.engine import Timeframe")],
    "tests/validate_real_world.py": [("from config import Timeframe, EPSILON", "from config.engine import Timeframe, EPSILON")],
    "tests/test_timeframe.py": [("from config import Timeframe", "from config.engine import Timeframe")],
    "tests/test_numerical_stability.py": [("from config import Timeframe", "from config.engine import Timeframe")],
    "tests/test_jdk_engine.py": [("from config import Timeframe", "from config.engine import Timeframe")],
    "services/rrg_service.py": [
        ("from config import Timeframe, SECTOR_TICKERS, CACHE_FRESHNESS_HOURS", 
         "from config.engine import Timeframe\nfrom config.indices import SECTOR_TICKERS\nfrom config.cache import CACHE_FRESHNESS_HOURS")
    ],
    "engine/timeframe.py": [("from config import Timeframe, TIMEFRAME_WINDOWS", "from config.engine import Timeframe, TIMEFRAME_WINDOWS")],
    "engine/normalization.py": [("from config import EPSILON", "from config.engine import EPSILON")],
    "engine/momentum.py": [("from config import EPSILON, MOMENTUM_SMOOTHING", "from config.engine import EPSILON, MOMENTUM_SMOOTHING")],
    "engine/jdk_engine.py": [("from config import Timeframe, TIMEFRAME_WINDOWS, EPSILON", "from config.engine import Timeframe, TIMEFRAME_WINDOWS, EPSILON")],
    "engine/base.py": [("from config import Timeframe", "from config.engine import Timeframe")],
    "dashboard/styles.py": [("from config import QUADRANT_COLORS", "from config.ui import QUADRANT_COLORS")],
    "dashboard/layout.py": [
        ("from config import Timeframe, BENCHMARKS", 
         "from config.engine import Timeframe\nfrom config.indices import BENCHMARKS")
    ],
    "dashboard/animation.py": [("from config import QUADRANT_COLORS, QUADRANT_BG_OPACITY", "from config.ui import QUADRANT_COLORS, QUADRANT_BG_OPACITY")],
    "benchmark.py": [("from config import BENCHMARKS, Timeframe", "from config.indices import BENCHMARKS\nfrom config.engine import Timeframe")]
}

for filepath, reps in replacements.items():
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        for old, new in reps:
            content = content.replace(old, new)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")
