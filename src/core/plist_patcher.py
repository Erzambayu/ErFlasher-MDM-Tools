"""
plist_patcher.py - orchestrates the full backup patching workflow

ported dari ViewController.swift Patch() IBAction flow:
  1. decrypt + extract backup ZIP (patchFile3)
  2. decrypt + patch Info.plist (patchFile1)
  3. decrypt + patch Manifest.plist (patchFile2)
  4. call backup restore engine
"""

import os
import io
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Tuple, Optional

from .crypto_utils import (
    decrypt_resource,
    patch_info_plist,
    patch_manifest_plist,
    calculate_password,
)
from .device_info import DeviceInfo


# resource filenames (identik dengan Swift bundle resources)
RESOURCE_EXT1 = "extension1.pdf"         # encrypted Info.plist
RESOURCE_EXT2 = "extension2.pdf"         # encrypted Manifest.plist
RESOURCE_DYLIB = "libiMobileeDevice.dylib"  # encrypted backup ZIP

# nama subdirectory backup (hardcoded "MDMB" dari Swift)
BACKUP_SUBDIR = "MDMB"


def _get_resource_path(filename: str) -> str:
    """cari resource file, cek berbagai kemungkinan lokasi."""
    # 1. development: src/resources/
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "resources", filename),
        os.path.join(os.path.dirname(__file__), "..", "..", "resources", filename),
    ]
    
    # 2. bundled (PyInstaller)
    import sys
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        candidates.insert(0, os.path.join(base, "resources", filename))
        candidates.insert(1, os.path.join(base, filename))
    
    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)
    
    raise FileNotFoundError(
        f"resource '{filename}' not found. searched: {candidates}"
    )


def _read_resource_bytes(filename: str) -> bytes:
    """baca resource file sebagai bytes."""
    path = _get_resource_path(filename)
    with open(path, "rb") as f:
        return f.read()


def decrypt_and_extract_backup(output_dir: str) -> str:
    """
    decrypt libiMobileeDevice.dylib dan extract ZIP ke output_dir.
    identik dengan patchFile3() di Swift.
    
    returns: path ke subdirectory MDMB/ di dalam output_dir
    """
    print("[patcher] decrypting backup archive...")
    
    # baca + decrypt
    encrypted = _read_resource_bytes(RESOURCE_DYLIB)
    decrypted = decrypt_resource(encrypted)
    
    # extract ZIP dari memory
    print(f"[patcher] extracting backup archive ({len(decrypted)} bytes)...")
    zip_buffer = io.BytesIO(decrypted)
    
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        zf.extractall(output_dir)
    
    # verify MDMB/ directory exists
    mdmb_path = os.path.join(output_dir, BACKUP_SUBDIR)
    if not os.path.isdir(mdmb_path):
        raise FileNotFoundError(
            f"extracted archive doesn't contain '{BACKUP_SUBDIR}/' directory"
        )
    
    print(f"[patcher] backup extracted to: {mdmb_path}")
    return mdmb_path


def decrypt_and_patch_plist(
    resource_name: str,
    device: DeviceInfo,
    output_path: str,
    is_info_plist: bool = True
) -> str:
    """
    decrypt resource plist dan patch dengan info device.
    
    returns: content string dari plist yang udah di-patch.
    """
    print(f"[patcher] patching {resource_name} -> {output_path}")
    
    # baca + decrypt
    encrypted = _read_resource_bytes(resource_name)
    decrypted = decrypt_resource(encrypted)
    
    # convert ke string
    plist_str = decrypted.decode("utf-8")
    
    # patch with device info
    if is_info_plist:
        patched = patch_info_plist(
            plist_str,
            build_id=device.build_version,
            imei=device.imei,
            product_type=device.product_type,
            sn=device.serial_number,
            udid=device.udid,
        )
    else:
        patched = patch_manifest_plist(
            plist_str,
            build_id=device.build_version,
            imei=device.imei,
            product_type=device.product_type,
            sn=device.serial_number,
            udid=device.udid,
        )
    
    # tulis ke file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(patched)
    
    return patched


# ---------------------------------------------------------------------------
# main patching workflow
# ---------------------------------------------------------------------------

class BackupPatcher:
    """
    orchestrates the full MDM patching workflow.
    """
    
    def __init__(self, device: DeviceInfo):
        self.device = device
        self._temp_dir: Optional[str] = None
        self._mdmb_path: Optional[str] = None
    
    @property
    def temp_dir(self) -> str:
        if not self._temp_dir:
            raise RuntimeError("patcher not started — call prepare() first")
        return self._temp_dir
    
    @property
    def mdmb_path(self) -> str:
        if not self._mdmb_path:
            raise RuntimeError("patcher not started — call prepare() first")
        return self._mdmb_path
    
    def prepare(self) -> Tuple[str, str]:
        """
        step 1-3: decrypt resources, create patched backup.
        
        returns: (temp_dir, mdmb_path) — paths untuk backup restore engine.
        """
        # create temp directory
        self._temp_dir = tempfile.mkdtemp(prefix="erflasher_")
        print(f"[patcher] temp dir: {self._temp_dir}")
        
        # step 1: decrypt + extract backup ZIP
        self._mdmb_path = decrypt_and_extract_backup(self._temp_dir)
        
        # step 2: decrypt + patch Info.plist
        info_output = os.path.join(self._mdmb_path, "Info.plist")
        decrypt_and_patch_plist(
            RESOURCE_EXT1, self.device, info_output, is_info_plist=True
        )
        
        # step 3: decrypt + patch Manifest.plist
        manifest_output = os.path.join(self._mdmb_path, "Manifest.plist")
        decrypt_and_patch_plist(
            RESOURCE_EXT2, self.device, manifest_output, is_info_plist=False
        )
        
        print("[patcher] preparation complete!")
        return self._temp_dir, self._mdmb_path
    
    def cleanup(self):
        """hapus temporary directory."""
        if self._temp_dir and os.path.isdir(self._temp_dir):
            print(f"[patcher] cleaning up: {self._temp_dir}")
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None
            self._mdmb_path = None
