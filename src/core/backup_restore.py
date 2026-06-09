"""
backup_restore.py - restore patched backup to iOS device

ported dari idevicebackup2.c mainLOL() function.
uses idevicebackup2 CLI tool on Linux/Windows.
"""

import os
import sys
import subprocess
import shutil
import time
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("erflasher.restore")


# ---------------------------------------------------------------------------
# CLI tool discovery
# ---------------------------------------------------------------------------

def _find_idevicebackup2() -> Optional[str]:
    """cari binary idevicebackup2 di system PATH atau lokasi umum."""
    tool_names = ["idevicebackup2", "idevicebackup2.exe"]
    
    # check PATH
    for name in tool_names:
        for path in os.environ.get("PATH", "").split(os.pathsep):
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    
    # linux common paths
    for base in ["/usr/bin", "/usr/local/bin", "/opt/homebrew/bin", "/usr/lib/libimobiledevice"]:
        for name in tool_names:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate):
                return candidate
    
    # windows — check bundled
    if sys.platform == "win32":
        for name in tool_names:
            bundled = os.path.join(os.path.dirname(__file__), "..", "bin", name)
            if os.path.isfile(bundled):
                return bundled
    
    return None


def is_idevicebackup2_available() -> bool:
    """check apakah idevicebackup2 tersedia."""
    return _find_idevicebackup2() is not None


# ---------------------------------------------------------------------------
# backup restore operations
# ---------------------------------------------------------------------------

def prepare_backup_for_restore(temp_dir: str, device_udid: str) -> str:
    """
    prepare backup directory structure untuk restore.
    
    standard idevicebackup2 expects: <backup_dir>/<udid>/Info.plist
    but our patched backup uses: <backup_dir>/MDMB/Info.plist
    
    jadi kita rename MDMB -> UDID (atau symlink).
    """
    mdmb_path = os.path.join(temp_dir, "MDMB")
    udid_path = os.path.join(temp_dir, device_udid)
    
    if not os.path.isdir(mdmb_path):
        raise FileNotFoundError(f"MDMB directory not found: {mdmb_path}")
    
    # kalau udah ada UDID path, hapus dulu
    if os.path.exists(udid_path):
        if os.path.isdir(udid_path):
            shutil.rmtree(udid_path)
        else:
            os.remove(udid_path)
    
    # rename MDMB -> UDID
    os.rename(mdmb_path, udid_path)
    print(f"[restore] renamed MDMB -> {device_udid}")
    logger.info(f"renamed MDMB -> {device_udid}")
    
    # verify Info.plist exists
    info_plist = os.path.join(udid_path, "Info.plist")
    manifest_plist = os.path.join(udid_path, "Manifest.plist")
    
    if not os.path.isfile(info_plist):
        raise FileNotFoundError(f"Info.plist not found after rename: {info_plist}")
    if not os.path.isfile(manifest_plist):
        print(f"[restore] warning: Manifest.plist not found: {manifest_plist}")
    
    return udid_path


def restore_backup(
    backup_dir: str,
    device_udid: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    restore patched backup ke iOS device via idevicebackup2 CLI.
    
    equivalent to: mainLOL(path, uuid) returning 0 on success.
    
    args:
        backup_dir: path ke directory yang mengandung <UDID>/Info.plist
        device_udid: UDID device target (optional, auto-detect)
        progress_callback: function(line: str) dipanggil per line output
    
    returns: (success: bool, message: str)
    """
    binary = _find_idevicebackup2()
    if not binary:
        return False, "idevicebackup2 not found. install libimobiledevice:\n" \
                      "  Linux: sudo apt install libimobiledevice-utils\n" \
                      "  Windows: install via MSYS2 or download libimobiledevice-win32"
    
    # build command
    # idevicebackup2 restore flags:
    #   --system   = restore system files
    #   --settings = restore settings (MDM config lives here)
    #   -u <udid>  = target device
    cmd = [
        binary,
        "restore",
        "--system",        # restore system files
        "--settings",      # restore settings (MDM config lives here)
        backup_dir
    ]
    
    if device_udid:
        cmd.extend(["--udid", device_udid])
    
    print(f"[restore] running: {' '.join(cmd)}")
    logger.info(f"running: {' '.join(cmd)}")
    
    try:
        # run with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        
        for line in process.stdout:
            line = line.rstrip()
            output_lines.append(line)
            print(f"[restore] {line}")
            logger.debug(f"idevicebackup2: {line}")
            
            if progress_callback:
                progress_callback(line)
        
        process.wait(timeout=300)  # 5 menit timeout
        
        success = process.returncode == 0
        
        if success:
            logger.info("restore completed successfully")
            return True, "MDM patched successfully! device will reboot."
        else:
            error_msg = f"Restore failed with exit code {process.returncode}"
            logger.error(f"restore failed: exit code {process.returncode}")
            # extract error dari output
            for line in output_lines:
                if "ERROR" in line or "error" in line.lower():
                    error_msg += f"\n  {line}"
            return False, error_msg
    
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)  # reap zombie process
        return False, "Restore timed out (5 minutes). device may be unresponsive."
    except FileNotFoundError:
        return False, f"idevicebackup2 binary not found at: {binary}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def restore_backup_pymd3(
    backup_dir: str,
    device_udid: str,
    progress_callback: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    alternative: restore using pymobiledevice3 (pure Python, cross-platform).
    
    uses Mobilebackup2Service to send the restore request directly.
    """
    try:
        from pymobiledevice3.lockdown import LockdownClient
        from pymobiledevice3.services.mobilebackup2 import Mobilebackup2Service
        
        # connect to device
        lockdown = LockdownClient(device_udid, autopair=False)
        
        # start mobilebackup2 service
        backup_service = Mobilebackup2Service(lockdown)
        
        # send restore request
        # this is a simplified version - the full DLMessage protocol
        # is handled by Mobilebackup2Service internally
        
        if progress_callback:
            progress_callback("Starting restore via pymobiledevice3...")
        
        # construct the restore options
        # equivalent to cmd_flags in the C code
        backup_service.restore(
            backup_directory=backup_dir,
            system_files=True,
            settings=True,
            remove_items=False,
            password=None,
        )
        
        if progress_callback:
            progress_callback("Restore completed successfully!")
        
        return True, "MDM patched successfully via pymobiledevice3!"
    
    except ImportError:
        return False, "pymobiledevice3 not installed. pip install pymobiledevice3"
    except Exception as e:
        return False, f"pymobiledevice3 restore failed: {e}"


# ---------------------------------------------------------------------------
# full restore workflow
# ---------------------------------------------------------------------------

def execute_full_restore(
    temp_dir: str,
    device_udid: str,
    progress_callback: Optional[callable] = None
) -> Tuple[bool, str]:
    """
    full restore pipeline:
    1. prepare backup directory (rename MDMB -> UDID)
    2. execute the restore via CLI or pymobiledevice3
    
    returns: (success, message)
    """
    # step 1: prepare directory
    if progress_callback:
        progress_callback("Preparing backup directory...")
    
    prepare_backup_for_restore(temp_dir, device_udid)
    
    # step 2: try restore
    if progress_callback:
        progress_callback("Starting backup restore to device...")
    
    # try CLI first (more reliable)
    if is_idevicebackup2_available():
        logger.info("using idevicebackup2 CLI")
        print("[restore] using idevicebackup2 CLI")
        return restore_backup(temp_dir, device_udid, progress_callback)
    
    # fallback to pymobiledevice3
    logger.info("trying pymobiledevice3 fallback...")
    print("[restore] trying pymobiledevice3...")
    success, msg = restore_backup_pymd3(temp_dir, device_udid, progress_callback)
    if success:
        return success, msg
    
    # both failed
    return False, (
        "No restore backend available.\n\n"
        "Please install one of:\n"
        "  Linux:   sudo apt install libimobiledevice-utils\n"
        "  Windows: download libimobiledevice-win32\n"
        "  Cross:   pip install pymobiledevice3"
    )
