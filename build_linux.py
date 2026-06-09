#!/usr/bin/env python3
"""
build_linux.py - Linux-specific build script for ErFlasher MDM Tools
creates a standalone binary using PyInstaller.

usage:
  python build_linux.py --clean
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.resolve()
SRC_DIR = PROJECT_ROOT / "src"
RESOURCES_DIR = SRC_DIR / "resources"

# explicit resource allowlist for bundle
RESOURCE_BUNDLE = [
    "extension1.pdf",
    "extension2.pdf",
    "libiMobileeDevice.dylib",
]


def check_dependencies():
    """verify all system dependencies are installed."""
    print("[linux] checking dependencies...")
    
    # check libimobiledevice
    tools = ["ideviceinfo", "idevicebackup2", "idevice_id"]
    for tool in tools:
        result = subprocess.run(["which", tool], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  [WARN] {tool} not found — install with:")
            print(f"         sudo apt install libimobiledevice-utils")
        else:
            print(f"  [OK] {tool} found: {result.stdout.strip()}")
    
    # check usbmuxd
    result = subprocess.run(["which", "usbmuxd"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [WARN] usbmuxd not found — install with:")
        print(f"         sudo apt install usbmuxd")
    else:
        print(f"  [OK] usbmuxd found")
    
    print()


def clean_build():
    """clean previous builds."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for d in dirs_to_clean:
        path = PROJECT_ROOT / d
        if path.exists():
            shutil.rmtree(path)
            print(f"[linux] cleaned: {path}")
    
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache)
    print()
    
    # clean .spec file
    spec = PROJECT_ROOT / "ErFlasher-MDM-Tools.spec"
    if spec.exists():
        spec.unlink()
        print(f"[linux] cleaned spec: {spec}")


def build():
    """run PyInstaller to create Linux standalone binary."""
    print("[linux] starting PyInstaller build...")
    print(f"[linux] platform: {sys.platform}")
    print(f"[linux] python: {sys.version}")
    print()
    
    # resource files — Linux uses : as separator
    separator = ":"
    add_data_args = []
    
    for name in RESOURCE_BUNDLE:
        f = RESOURCES_DIR / name
        if f.is_file():
            dest = os.path.join("resources", f.name)
            add_data_args.extend(["--add-data", f"{f}{separator}{dest}"])
            print(f"[linux] bundling: {f.name} -> {dest}")
        else:
            print(f"[linux] skipped missing resource: {f}")
    
    print()
    
    # PyInstaller command
    # --console keeps terminal output visible (useful for debugging on Linux)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ErFlasher-MDM-Tools",
        "--onefile",              # single binary
        "--console",              # keep terminal (debugging)
        "--clean",
        "--noconfirm",
        "--strip",                # strip debug symbols (smaller binary)
        *add_data_args,
        str(PROJECT_ROOT / "main.py"),
    ]
    
    print(f"[linux] running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    
    if result.returncode == 0:
        output_path = PROJECT_ROOT / "dist" / "ErFlasher-MDM-Tools"
        size_mb = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0
        print(f"\n[linux] =========================================")
        print(f"[linux] BUILD SUCCESS!")
        print(f"[linux] output: {output_path}")
        print(f"[linux] size: {size_mb:.1f} MB")
        print(f"[linux] =========================================")
        print()
        print(f"run with: {output_path}")
        print(f"  or:     sudo {output_path}  (if usbmuxd needs root)")
    else:
        print(f"\n[linux] BUILD FAILED with code {result.returncode}")
    
    return result.returncode


def install_system_deps():
    """print instructions for installing system dependencies."""
    print("""
[linux] =========================================
[linux] SYSTEM DEPENDENCIES SETUP
[linux] =========================================

# Ubuntu/Debian:
sudo apt update
sudo apt install -y libimobiledevice-utils usbmuxd python3-pip python3-tk

# Fedora:
sudo dnf install -y libimobiledevice usbmuxd python3-pip python3-tkinter

# Arch:
sudo pacman -S libimobiledevice usbmuxd python-pip tk

# start usbmuxd service:
sudo systemctl start usbmuxd
sudo systemctl enable usbmuxd   # auto-start on boot

# python dependencies:
pip install -r requirements.txt

[linux] =========================================
""")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Build ErFlasher MDM Tools for Linux"
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="clean previous build artifacts before building"
    )
    parser.add_argument(
        "--check-deps", action="store_true",
        help="check system dependencies"
    )
    parser.add_argument(
        "--install-deps", action="store_true",
        help="show system dependency install instructions"
    )
    args = parser.parse_args()
    
    if args.install_deps:
        install_system_deps()
        sys.exit(0)
    
    if args.check_deps:
        check_dependencies()
    
    if args.clean:
        clean_build()
    
    sys.exit(build())
