"""
main.py - entry point for ErFlasher MDM Tools
cross-platform (Windows & Linux)

github: https://github.com/Erzambayu/MDMPatcher-Enhanced
credit: Erzambayu
based on: MDMPatcher-Enhanced by fled-dev
"""

import sys
import os

# ensure project root is in sys.path so 'src' package is importable
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.gui.main_window import ErFlasherApp


def main():
    """launch ErFlasher MDM Tools."""
    app = ErFlasherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
