"""
Structured logging for the RRG Dashboard.

Logs cache hits, API failures, fetch durations, and animation FPS
to specific module logs in logs/: provider.log, cache.log, engine.log, dashboard.log.
"""

import logging
import sys
from pathlib import Path

# Resolve log directory relative to project root
_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Shared formatter
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

# Keep track of configured loggers to avoid duplicate handlers
_configured_loggers = set()

def _get_log_file(name: str) -> Path:
    """Map module name to specific log file."""
    if "provider" in name:
        return _LOG_DIR / "provider.log"
    elif "cache" in name:
        return _LOG_DIR / "cache.log"
    elif "engine" in name:
        return _LOG_DIR / "engine.log"
    elif "dashboard" in name or "main" in name:
        return _LOG_DIR / "dashboard.log"
    else:
        return _LOG_DIR / "system.log"


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that routes to the appropriate file based on module name.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)

    Args:
        name: Module name (typically __name__).

    Returns:
        Configured Logger instance.
    """
    logger_name = f"rrg.{name}"
    logger = logging.getLogger(logger_name)
    
    if logger_name in _configured_loggers:
        return logger

    logger.setLevel(logging.DEBUG)
    
    # Prevent propagation to root logger to avoid duplicate console prints
    logger.propagate = False

    # File handler — DEBUG and above, specific to module
    log_file = _get_log_file(name)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_formatter)
    logger.addHandler(fh)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(_formatter)
    logger.addHandler(ch)

    _configured_loggers.add(logger_name)
    return logger
