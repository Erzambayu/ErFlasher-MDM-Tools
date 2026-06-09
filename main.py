"""
main.py - entry point for ErFlasher MDM Tools
cross-platform (Windows & Linux)

github: https://github.com/Erzambayu/ErFlasher-MDM-Tools
credit: Erzambayu
based on: MDMPatcher-Enhanced by fled-dev
"""

import sys
import os
import logging
from datetime import datetime

# ensure project root is in sys.path so 'src' package is importable
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def setup_logging():
    """configure logging to file + console for error reporting."""
    # log file next to executable (or in project root during dev)
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = _project_root
    
    log_file = os.path.join(log_dir, "erflasher.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    logger = logging.getLogger("erflasher")
    logger.info(f"ErFlasher MDM Tools v2.0.0 starting")
    logger.info(f"platform: {sys.platform}, python: {sys.version}")
    logger.info(f"log file: {log_file}")
    
    return logger


from src.gui.main_window import ErFlasherApp


def main():
    """launch ErFlasher MDM Tools."""
    logger = setup_logging()
    
    try:
        app = ErFlasherApp()
        app.mainloop()
    except Exception as e:
        logger.critical(f"fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
