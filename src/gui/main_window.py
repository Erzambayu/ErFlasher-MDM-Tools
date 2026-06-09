"""
main_window.py - CustomTkinter GUI for ErFlasher MDM Tools
dark theme, modern, clean. ported from macOS Cocoa storyboard layout.

github: https://github.com/Erzambayu/ErFlasher-MDM-Tools
credit: Erzambayu
"""

import customtkinter as ctk
import threading
import time
import logging
from typing import Optional

from ..core.device_info import DeviceInfo, get_device_info
from ..core.usb_detector import USBDetector
from ..core.plist_patcher import BackupPatcher
from ..core.backup_restore import execute_full_restore

logger = logging.getLogger("erflasher.gui")


# ---------------------------------------------------------------------------
# theme configuration
# ---------------------------------------------------------------------------

# color palette — dark industrial with red accent
COLORS = {
    "bg_dark": "#0d1117",
    "bg_card": "#161b22",
    "bg_input": "#21262d",
    "border": "#30363d",
    "text_primary": "#e6edf3",
    "text_secondary": "#8b949e",
    "accent": "#f85149",          # red accent
    "accent_hover": "#ff6b63",
    "success": "#3fb950",
    "warning": "#d2991d",
    "error": "#f85149",
    "connected": "#3fb950",
    "disconnected": "#8b949e",
}

FONTS = {
    "title": ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 12),
    "heading": ("Segoe UI", 11, "bold"),
    "body": ("Segoe UI", 11),
    "mono": ("Cascadia Code", 10),
    "button": ("Segoe UI", 13, "bold"),
    "status": ("Segoe UI", 10),
    "version": ("Segoe UI", 9),
}


# ---------------------------------------------------------------------------
# main application window
# ---------------------------------------------------------------------------

class ErFlasherApp(ctk.CTk):
    """main application window."""
    
    def __init__(self):
        super().__init__()
        
        # window setup
        self.title("ErFlasher MDM Tools")
        self.geometry("560x620")
        self.minsize(480, 550)
        self.resizable(True, True)
        
        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # state
        self._device: Optional[DeviceInfo] = None
        self._patcher: Optional[BackupPatcher] = None
        self._usb_detector: Optional[USBDetector] = None
        self._patching = False
        
        # build UI
        self._build_ui()
        
        # start USB detection
        self._start_usb_detection()
        
        # initial device check
        self._check_device()
    
    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    
    def _build_ui(self):
        """construct the main UI layout."""
        
        # ---- main scrollable frame ----
        self._main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self._main_frame.grid_columnconfigure(0, weight=1)
        
        # ---- header ----
        header = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 0))
        
        title_label = ctk.CTkLabel(
            header, text="ErFlasher MDM Tools",
            font=FONTS["title"], text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor="w")
        
        subtitle_label = ctk.CTkLabel(
            header, text="Cross-Platform Edition — Windows & Linux",
            font=FONTS["subtitle"], text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # ---- status indicator ----
        status_frame = ctk.CTkFrame(
            self._main_frame, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1, border_color=COLORS["border"]
        )
        status_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 0))
        status_frame.grid_columnconfigure(1, weight=1)
        
        self._status_dot = ctk.CTkLabel(
            status_frame, text="●", font=("Segoe UI", 20),
            text_color=COLORS["disconnected"], width=30
        )
        self._status_dot.grid(row=0, column=0, padx=(12, 4), pady=10)
        
        self._status_label = ctk.CTkLabel(
            status_frame, text="No device connected",
            font=FONTS["heading"], text_color=COLORS["text_secondary"],
            anchor="w"
        )
        
        self._status_hint = ctk.CTkLabel(
            status_frame, text="",
            font=FONTS["status"], text_color=COLORS["warning"],
            anchor="w"
        )
        self._status_hint.grid(row=1, column=1, sticky="w", pady=(0, 8))
        self._status_label.grid(row=0, column=1, sticky="w", pady=10)
        
        # ---- device info card ----
        self._info_frame = ctk.CTkFrame(
            self._main_frame, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1, border_color=COLORS["border"]
        )
        self._info_frame.grid(row=2, column=0, sticky="ew", padx=24, pady=(12, 0))
        self._info_frame.grid_columnconfigure(1, weight=1)
        
        # info fields
        self._info_fields = {}
        fields = [
            ("Device Model", "product_type"),
            ("Serial Number", "serial_number"),
            ("UDID", "udid"),
            ("Firmware", "firmware"),
            ("IMEI", "imei"),
        ]
        
        for i, (label, key) in enumerate(fields):
            # label
            lbl = ctk.CTkLabel(
                self._info_frame, text=label,
                font=FONTS["heading"], text_color=COLORS["text_secondary"],
                anchor="e", width=110
            )
            lbl.grid(row=i, column=0, sticky="e", padx=(16, 8), pady=6)
            
            # value
            val = ctk.CTkLabel(
                self._info_frame, text="—",
                font=FONTS["mono"], text_color=COLORS["text_primary"],
                anchor="w"
            )
            val.grid(row=i, column=1, sticky="ew", padx=(0, 16), pady=6)
            self._info_fields[key] = val
        
        # ---- progress area ----
        progress_frame = ctk.CTkFrame(
            self._main_frame, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1, border_color=COLORS["border"]
        )
        progress_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 0))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self._progress_text = ctk.CTkLabel(
            progress_frame, text="Ready",
            font=FONTS["status"], text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self._progress_text.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
        
        self._progress_bar = ctk.CTkProgressBar(
            progress_frame, height=8, corner_radius=4,
            fg_color=COLORS["bg_input"],
            progress_color=COLORS["accent"]
        )
        self._progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 12))
        self._progress_bar.set(0)
        
        # ---- action button ----
        btn_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", padx=24, pady=(20, 0))
        
        self._patch_btn = ctk.CTkButton(
            btn_frame, text="🔧 PATCH MDM",
            font=FONTS["button"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#ffffff",
            height=46,
            corner_radius=8,
            command=self._on_patch_clicked,
            state="disabled"
        )
        self._patch_btn.pack(fill="x")
        
        # ---- footer ----
        footer = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", padx=24, pady=(16, 24))
        
        version_label = ctk.CTkLabel(
            footer, text="v2.0.0 • cross-platform • github.com/Erzambayu/ErFlasher-MDM-Tools",
            font=FONTS["version"], text_color=COLORS["text_secondary"]
        )
        version_label.pack()
    
    # ------------------------------------------------------------------
    # USB detection
    # ------------------------------------------------------------------
    
    def _start_usb_detection(self):
        """start background USB device polling."""
        self._usb_detector = USBDetector(
            on_connect=self._on_device_connected,
            on_disconnect=self._on_device_disconnected,
            poll_interval=2.0
        )
        self._usb_detector.start()
    
    def _check_device(self):
        """check for device on startup."""
        info = get_device_info()
        if info.is_valid:
            self._on_device_connected(info)
    
    def _on_device_connected(self, device: DeviceInfo):
        """callback when iOS device is connected (called from bg thread)."""
        # schedule everything on main thread to avoid race conditions
        self.after(0, self._handle_device_connect, device)
    
    def _handle_device_connect(self, device: DeviceInfo):
        """handle device connection on main thread."""
        self._device = device
        logger.info(f"device connected: {device.product_type} SN={device.serial_number} UDID={device.udid}")
        self._update_device_ui(device)
    
    def _on_device_disconnected(self):
        """callback when iOS device is disconnected (called from bg thread)."""
        self.after(0, self._handle_device_disconnect)
    
    def _handle_device_disconnect(self):
        """handle device disconnection on main thread."""
        logger.info("device disconnected")
        self._device = None
        self._clear_device_ui()
    
    # ------------------------------------------------------------------
    # UI updates (must run on main thread via after())
    # ------------------------------------------------------------------
    
    def _update_device_ui(self, device: DeviceInfo):
        """update all UI fields with device info."""
        # status
        self._status_dot.configure(text_color=COLORS["connected"])
        self._status_label.configure(
            text=f"Connected — {device.product_type or 'iOS Device'}",
            text_color=COLORS["connected"]
        )
        
        # hints for proper device state
        hints = []
        if not device.activation_state or "Unactivated" in device.activation_state:
            hints.append("⚠ device must be at Hello screen (setup assistant)")
        hints.append("⚠ do NOT connect to Wi-Fi before patching")
        hints.append("⚠ make sure device screen is unlocked (trust prompt)")
        self._status_hint.configure(text=" | ".join(hints))
        
        # info fields
        self._info_fields["product_type"].configure(text=device.product_type or "—")
        self._info_fields["serial_number"].configure(text=device.serial_number or "—")
        self._info_fields["udid"].configure(text=device.udid or "—")
        self._info_fields["firmware"].configure(text=device.firmware_display or "—")
        self._info_fields["imei"].configure(text=device.imei or "—")
        
        # enable patch button
        if not self._patching:
            self._patch_btn.configure(state="normal", text="🔧 PATCH MDM")
    
    def _clear_device_ui(self):
        """clear all device info from UI."""
        self._status_dot.configure(text_color=COLORS["disconnected"])
        self._status_label.configure(
            text="No device connected",
            text_color=COLORS["text_secondary"]
        )
        self._status_hint.configure(text="")
        
        for field in self._info_fields.values():
            field.configure(text="—")
        
        # disable patch button
        if not self._patching:
            self._patch_btn.configure(state="disabled")
    
    def _set_progress(self, text: str, value: float = -1):
        """update progress text and bar. value -1 = indeterminate."""
        self._progress_text.configure(text=text)
        
        if value < 0:
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()
        else:
            self._progress_bar.configure(mode="determinate")
            self._progress_bar.stop()
            self._progress_bar.set(max(0.0, min(1.0, value)))
    
    def _show_dialog(self, title: str, message: str, is_error: bool = False):
        """show a popup dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x220")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # center on parent
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # content
        color = COLORS["error"] if is_error else COLORS["success"]
        emoji = "✗" if is_error else "✓"
        
        header = ctk.CTkLabel(
            dialog, text=f"{emoji}  {title}",
            font=FONTS["title"], text_color=color
        )
        header.pack(pady=(24, 8))
        
        msg = ctk.CTkLabel(
            dialog, text=message,
            font=FONTS["body"], text_color=COLORS["text_secondary"],
            wraplength=360, justify="center"
        )
        msg.pack(pady=(0, 16), padx=20)
        
        ok_btn = ctk.CTkButton(
            dialog, text="OK",
            font=FONTS["button"],
            fg_color=color,
            hover_color=COLORS["accent_hover"],
            width=100, height=36,
            command=dialog.destroy
        )
        ok_btn.pack()
    
    # ------------------------------------------------------------------
    # patch workflow
    # ------------------------------------------------------------------
    
    def _on_patch_clicked(self):
        """handle PATCH button click."""
        if self._patching or not self._device:
            return
        
        self._patching = True
        self._patch_btn.configure(state="disabled", text="⏳ Patching...")
        self._set_progress("Preparing...", -1)
        
        # run in background thread
        thread = threading.Thread(target=self._run_patch_workflow, daemon=True)
        thread.start()
    
    def _run_patch_workflow(self):
        """main patching workflow — runs in background thread."""
        device = self._device
        patcher = BackupPatcher(device)
        temp_dir = None
        
        try:
            # ---- step 1: decrypt & prepare backup ----
            logger.info(f"patch started for device: {device.udid}")
            self.after(0, self._set_progress, "Decrypting backup archive...", 0.1)
            
            temp_dir, mdmb_path = patcher.prepare()
            
            self.after(0, self._set_progress, "Backup prepared. Starting restore...", 0.4)
            
            # ---- step 2: restore to device ----
            def progress_handler(msg: str):
                self.after(0, self._set_progress, f"Restoring: {msg[:60]}...", 0.6)
            
            success, message = execute_full_restore(
                temp_dir, device.udid, progress_callback=progress_handler
            )
            
            # ---- step 3: show result ----
            if success:
                logger.info(f"patch success: {message}")
                self.after(0, self._set_progress, "Done! Device will reboot.", 1.0)
                time.sleep(1)
                self.after(0, self._show_dialog, "Success", message, False)
            else:
                logger.error(f"patch failed: {message}")
                self.after(0, self._set_progress, "Failed.", 0.0)
                self.after(0, self._show_dialog, "Error", message, True)
        
        except Exception as e:
            logger.error(f"patch exception: {e}", exc_info=True)
            self.after(0, self._set_progress, f"Error: {e}", 0.0)
            self.after(0, self._show_dialog, "Error", str(e), True)
        
        finally:
            # cleanup
            if temp_dir and patcher:
                try:
                    patcher.cleanup()
                except Exception:
                    pass
            
            # reset UI
            self.after(0, self._reset_ui)
    
    def _reset_ui(self):
        """reset UI after patch completes."""
        self._patching = False
        self._patch_btn.configure(
            state="normal" if self._device else "disabled",
            text="🔧 PATCH MDM"
        )
        
        # refresh device info in background (don't block main thread)
        def _refresh():
            fresh = get_device_info()
            if fresh.is_valid:
                self.after(0, self._handle_device_connect, fresh)
        
        threading.Thread(target=_refresh, daemon=True).start()
