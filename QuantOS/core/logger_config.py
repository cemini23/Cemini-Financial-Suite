import logging
import sys
from datetime import datetime
from collections import deque

# Global buffer for UI to fetch recent activity (Thread-safe, O(1) operations)
UI_LOGS = deque(maxlen=50)

class UIConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "msg": self.format(record)
        }
        UI_LOGS.append(log_entry)

def get_logger(name="QuantOS"):
    """
    Sets up a safe, standard logger that works on all Python versions.
    Replaces the complex logger to prevent startup crashes.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate logs if function is called twice
    if logger.hasHandlers():
        return logger

    # Create UI and Console Handler
    handler = UIConsoleHandler(sys.stdout)
    
    # Create Simple Formatter
    formatter = logging.Formatter(
        '%(message)s'
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Ensure logs don't bubble up to the root logger
    logger.propagate = False
    
    return logger

# Alias for compatibility if needed
setup_logger = get_logger
