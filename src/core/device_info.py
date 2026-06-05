"""
device_info.py - retrieve iOS device information
cross-platform wrapper: Linux via libimobiledevice CLI, Windows via bundled binaries.

strategi:
  1. coba pake pymobiledevice3 (pure Python, cross-platform)
  2. fallback ke ideviceinfo CLI
  3. fallback ke libimobiledevice-win32 (Windows)
"""

import subprocess
import plistlib
import os
import sys
import json
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# data models
# ---------------------------------------------------------------------------

@dataclass
class DeviceInfo:
    """info device iOS yang diperlukan buat patching."""
    udid: str = ""
    serial_number: str = ""
    product_type: str = ""       # e.g. "iPhone12,8"
    build_version: str = ""      # e.g. "18C66"
    product_version: str = ""    # e.g. "15.0"
    imei: str = ""
    activation_state: str = ""
    device_name: str = ""
    hardware_model: str = ""
    
    # raw untouched
    raw_plist: dict = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        return bool(self.udid and self.serial_number)
    
    @property
    def firmware_display(self) -> str:
        return f"{self.product_version} | {self.build_version}"


# ---------------------------------------------------------------------------
# pymobiledevice3 backend
# ---------------------------------------------------------------------------

def _get_device_info_pymd3() -> dict | None:
    """coba pake pymobiledevice3 buat ambil info device."""
    try:
        from pymobiledevice3.lockdown import LockdownClient
        from pymobiledevice3.usbmux import list_devices
        
        devices = list_devices()
        if not devices:
            return None
        
        device = devices[0]  # ambil device pertama
        lockdown = LockdownClient(device.serial, autopair=False)
        
        # query all domains
        all_values = lockdown.all_values
        
        return all_values
        
    except ImportError:
        return None
    except Exception as e:
        print(f"[pymd3] error: {e}")
        return None


# ---------------------------------------------------------------------------
# ideviceinfo CLI backend (Linux / macOS)
# ---------------------------------------------------------------------------

def _find_ideviceinfo() -> str | None:
    """cari binary ideviceinfo di PATH atau lokasi umum."""
    # check PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(path, "ideviceinfo")
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    
    # linux common paths
    for base in ["/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]:
        candidate = os.path.join(base, "ideviceinfo")
        if os.path.isfile(candidate):
            return candidate
    
    # windows — check bundled binary
    if sys.platform == "win32":
        bundled = os.path.join(os.path.dirname(__file__), "..", "bin", "ideviceinfo.exe")
        if os.path.isfile(bundled):
            return bundled
    
    return None


def _get_device_info_ideviceinfo() -> dict | None:
    """panggil ideviceinfo --xml dan parse output."""
    binary = _find_ideviceinfo()
    if not binary:
        return None
    
    try:
        result = subprocess.run(
            [binary, "-x"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode != 0:
            print(f"[ideviceinfo] exit code {result.returncode}: {result.stderr}")
            return None
        
        # parse XML plist
        xml_data = result.stdout.encode("utf-8")
        try:
            plist_data = plistlib.loads(xml_data)
        except Exception:
            # some versions output binary plist despite -x flag
            plist_data = plistlib.loads(xml_data, fmt=plistlib.FMT_XML)
        
        return plist_data
        
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        print("[ideviceinfo] timeout")
        return None
    except Exception as e:
        print(f"[ideviceinfo] error: {e}")
        return None


# ---------------------------------------------------------------------------
# main API
# ---------------------------------------------------------------------------

def get_device_info() -> DeviceInfo:
    """
    ambil info device iOS yang terhubung via USB.
    return DeviceInfo (bisa kosong/partial kalau gak ada device).
    
    prerequisite:
      - device di Hello screen (setup assistant)
      - JANGAN konek WiFi
      - screen unlocked, trust prompt di-allow
    """
    info = DeviceInfo()
    
    # coba berbagai backend
    plist_data = None
    
    # 1. pymobiledevice3
    plist_data = _get_device_info_pymd3()
    
    # 2. ideviceinfo CLI
    if not plist_data:
        plist_data = _get_device_info_ideviceinfo()
    
    if not plist_data:
        return info
    
    info.raw_plist = plist_data
    
    # extract key fields
    info.udid = plist_data.get("UniqueDeviceID", "")
    info.serial_number = plist_data.get("SerialNumber", "")
    info.product_type = plist_data.get("ProductType", "")
    info.build_version = plist_data.get("BuildVersion", "")
    info.product_version = plist_data.get("ProductVersion", "")
    info.imei = plist_data.get("InternationalMobileEquipmentIdentity", "")
    info.activation_state = plist_data.get("ActivationState", "")
    info.device_name = plist_data.get("DeviceName", "")
    info.hardware_model = plist_data.get("HardwareModel", "")
    
    return info


def is_device_connected() -> bool:
    """check apakah ada iOS device yang terhubung."""
    info = get_device_info()
    return info.is_valid


def idevice_id_list() -> list[str]:
    """dapatkan list UDID device yang terhubung."""
    # coba idevice_id CLI
    for name in ["idevice_id", "ideviceid"]:
        try:
            result = subprocess.run(
                [name, "-l"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    # fallback ke get_device_info
    info = get_device_info()
    if info.udid:
        return [info.udid]
    return []
