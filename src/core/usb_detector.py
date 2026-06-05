"""
usb_detector.py - cross-platform iOS USB device detection

strategi:
  - polling-based: periodic check via idevice_id -l / device_info
  - (optional) event-based via pyusb kalau tersedia
  
original (macOS): IOKit-based USBWatcher dengan product ID 4776/4779
cross-platform: polling timer + idevice_id
"""

import threading
import time
from typing import Callable, Optional

from .device_info import idevice_id_list, get_device_info, DeviceInfo


class USBDetector:
    """
    detects iOS devices via USB on Windows & Linux.
    uses polling with configurable interval.
    
    usage:
        detector = USBDetector(on_connect=lambda d: print(f"connected: {d}"),
                                on_disconnect=lambda: print("disconnected"))
        detector.start()
        # ... later ...
        detector.stop()
    """
    
    def __init__(
        self,
        on_connect: Optional[Callable[[DeviceInfo], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        poll_interval: float = 1.5  # seconds
    ):
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._poll_interval = poll_interval
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_udid: Optional[str] = None
        self._was_connected = False
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def start(self):
        """start polling thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """stop polling thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def check_now(self) -> Optional[DeviceInfo]:
        """force immediate check, return device info if connected."""
        udids = idevice_id_list()
        
        if udids:
            # device terdeteksi
            current_udid = udids[0]
            
            if current_udid != self._last_udid or not self._was_connected:
                # device baru connect atau ganti device
                info = get_device_info()
                self._last_udid = current_udid
                self._was_connected = True
                
                if info.is_valid and self._on_connect:
                    self._on_connect(info)
                
                return info
            else:
                # device sama, gak perlu trigger event lagi
                return get_device_info()
        else:
            # gak ada device
            if self._was_connected:
                self._was_connected = False
                self._last_udid = None
                
                if self._on_disconnect:
                    self._on_disconnect()
            
            return None
    
    def _poll_loop(self):
        """main polling loop, jalan di background thread."""
        while self._running:
            try:
                self.check_now()
            except Exception as e:
                print(f"[USBDetector] poll error: {e}")
            
            # sleep with interruptible chunks
            for _ in range(int(self._poll_interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)
