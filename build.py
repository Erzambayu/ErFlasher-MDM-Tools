"""
build.py - PyInstaller build script for ErFlasher MDM Tools
produces standalone .exe (Windows) or binary (Linux).
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
RESOURCES_DIR = SRC_DIR / "resources"


def clean_build():
    """clean previous builds."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for d in dirs_to_clean:
        path = PROJECT_ROOT / d
        if path.exists():
            shutil.rmtree(path)
            print(f"[build] cleaned: {path}")
    
    # clean __pycache__ recursively
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"[build] cleaned: {pycache}")


def build():
    """run PyInstaller to create standalone executable."""
    print("[build] starting PyInstaller build...")
    
    # determine platform-specific settings
    is_windows = sys.platform == "win32"
    separator = ";" if is_windows else ":"
    ext = ".exe" if is_windows else ""
    
    # resource files to bundle
    resource_files = []
    if RESOURCES_DIR.exists():
        for f in RESOURCES_DIR.iterdir():
            if f.is_file():
                dest = os.path.join("resources", f.name)
                resource_files.append(f"{f}{separator}{dest}")
    
    add_data_arg = []
    for rf in resource_files:
        add_data_arg.extend(["--add-data", rf])
    
    # build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ErFlasher-MDM-Tools",
        "--onefile",            # single .exe
        "--windowed",           # no console window (Windows)
        "--clean",
        "--noconfirm",
        *add_data_arg,
        str(PROJECT_ROOT / "main.py"),
    ]
    
    # on linux, also add icon if available
    if not is_windows:
        # prevent GUI warnings about missing display
        cmd.insert(2, "--console")  # linux: keep console for debugging
        pass
    
    print(f"[build] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    
    if result.returncode == 0:
        output = PROJECT_ROOT / "dist" / f"ErFlasher-MDM-Tools{ext}"
        print(f"\n[build] SUCCESS! output: {output}")
    else:
        print(f"\n[build] FAILED with code {result.returncode}")
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build ErFlasher MDM Tools")
    parser.add_argument("--clean", action="store_true", help="clean before build")
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    
    sys.exit(build())
