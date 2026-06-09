# ErFlasher MDM Tools — Cross-Platform Edition

**Bypass MDM enrollment on iOS devices** — now on **Windows & Linux**.

Built by **Erzambayu** — based on [MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced) by fled-dev.

---

## 📱 iOS Version Support

| Supported | Details |
|---|---|
| **iOS 15.0 – 18.5+** | ✅ Fully tested |
| **iOS 16.x, 17.x** | ✅ Works |
| **iOS 18.0 – 18.5+** | ✅ Latest confirmed working |
| **iOS 26.0 – 26.2** | ✅ Confirmed working by users (iPhone 15, various iPads) |
| **iOS 26.3+** | ⚠️ Mixed reports — some work, some error. Try blocking Apple MDM hosts (see troubleshooting) |
| **Below iOS 15** | ⚠️ May work, not tested |
| **Above iOS 26.5** | ⚠️ Not yet tested — backup format rarely changes between minor versions |

**Why does this work across versions?**
This tool does not use exploits or jailbreaks. It leverages the **MobileBackup2** protocol (iTunes backup/restore), a legitimate iOS feature present since iOS 4. Apple cannot easily patch this without breaking their own restore flow.

### Devices Supported

- **iPhone 5s** to **iPhone 16** (all models)
- **All iPads** (including Pro, Air, Mini)
- Cellular & Wi-Fi only models

---

## 🔗 Links

- **GitHub**: [github.com/Erzambayu/ErFlasher-MDM-Tools](https://github.com/Erzambayu/ErFlasher-MDM-Tools)
- **Original**: [github.com/fled-dev/MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced)

---

## 📋 Requirements Before Starting

### Hardware

- USB Lightning / USB-C cable (original recommended)
- Windows or Linux computer

### Device State (Mandatory)

```
┌─────────────────────────────────────────────────────┐
│  1. Device at Hello screen (Setup Assistant)        │
│  2. Do NOT connect to Wi-Fi or cellular data        │
│  3. Screen unlocked, display on                     │
│  4. Trust this computer? → tap "Trust"             │
└─────────────────────────────────────────────────────┘
```

⚠️ **Why no internet before patching?**
If the device connects to Wi-Fi, it can auto-check Apple Business Manager / MDM enrollment servers. Once detected, the device may lock before patching completes.

### Required File

- **IPSW file** for your device — download from [ipsw.me](https://ipsw.me)
  - Check model number on device back (e.g. A1567)
  - Match device name via [The iPhone Wiki](https://www.theiphonewiki.com/wiki/Models)
  - **Cellular vs Wi-Fi**: if device has SIM slot, download Cellular IPSW; otherwise use Wi-Fi only version

---

## 🚀 Full Guide (Step by Step)

### Step 1: Restore Device with IPSW (Clean Wipe)

```
┌──────────────────────────────────────────┐
│  Enter RECOVERY MODE                     │
│                                          │
│  iPhone 8 and later (Face ID):           │
│    1. tap Volume Up                      │
│    2. tap Volume Down                    │
│    3. hold Side Button while plugging USB│
│                                          │
│  iPhone 7 / 7 Plus:                      │
│    hold Volume Down while plugging USB   │
│                                          │
│  iPhone 6s and earlier:                  │
│    hold Home Button while plugging USB   │
│                                          │
│  iPad without Home button:               │
│    hold Top Button while plugging USB    │
│                                          │
│  iPad with Home button:                  │
│    hold Home Button while plugging USB   │
└──────────────────────────────────────────┘
```

- After entering recovery mode, Finder/iTunes shows the **Update or Restore** popup
- **Windows**: hold **SHIFT** + click **Restore**
- **Linux**: use `idevicerestore` CLI:
  ```bash
  idevicerestore -e <path-to-ipsw.ipsw>
  ```
- Select IPSW file you downloaded
- Wait for restore to finish (5–15 minutes)

### Step 2: Initial Setup Until Wi-Fi Screen

- After restore, device reboots to Hello screen
- Follow initial setup:
  - Choose language
  - Choose region
  - **When you reach "Choose a Wi-Fi Network" → STOP. Do NOT select any network.**
  - Do not connect Wi-Fi, do not connect cellular
- Leave device on that Wi-Fi screen

### Step 3: Install Dependencies

**Linux:**
```bash
# Python dependencies
pip install -r requirements.txt

# System tools (libimobiledevice)
sudo apt update
sudo apt install libimobiledevice-utils usbmuxd

# Start usbmuxd service
sudo systemctl start usbmuxd
```

**Windows:**
```bash
# Python dependencies
pip install -r requirements.txt

# Install iTunes (provides Apple Mobile Device Support + usbmuxd)
# Download from: https://www.apple.com/itunes/
#
# OR install via MSYS2:
# pacman -S mingw-w64-x86_64-libimobiledevice
```

### Step 4: Connect Device & Trust

- Connect device to computer via USB cable
- **Unlock device** (screen must be on, not at lock screen)
- "Trust This Computer?" popup → tap **Trust**
- If asked for passcode, enter old passcode

### Step 5: Verify Device Detected

```bash
# Check device detected
idevice_id -l
# output: 00008030-001854E42E06402E  (example UDID)

# Check device info
ideviceinfo -s
# should show ProductType, SerialNumber, BuildVersion, etc.
```

If `ideviceinfo` fails, make sure device is unlocked and trusted.

### Step 6: Open ErFlasher MDM Tools & Patch

```bash
python main.py
```

1. App auto-detects device
2. Device info (model, SN, UDID, firmware, IMEI) shows in UI
3. Click **"🔧 PATCH MDM"** button
4. Watch progress:
   - decrypting backup archive...
   - patching plist files...
   - restoring to device...
5. Device will **reboot automatically**
6. After reboot, device returns to Hello screen → **now you CAN connect Wi-Fi** — MDM is gone!

### Step 7: Finish Setup

- Continue iOS setup normally
- Connect Wi-Fi → activation → iCloud → done
- Device is now **MDM-free**

---

## 🐛 Troubleshooting

### "No device found" / Device not detected

```
1. Check USB cable (use original if possible)
2. Unlock device, screen on
3. Make sure you tapped "Trust"
4. Unplug → replug USB
5. Check usbmuxd service running:
   Linux: sudo systemctl status usbmuxd
   Windows: check iTunes / Apple Mobile Device Service in Services
```

### "ERROR: Could Not Connect to Lockdownd"

```
- Device must be at Hello screen (normal mode), NOT recovery mode
- Make sure screen is unlocked
- Try unlocking device, closing/opening app
- Restart usbmuxd: sudo systemctl restart usbmuxd (Linux)
```

### "ERROR: Restore Failed"

```
- Device may not be fully activated yet
- Open Finder/iTunes, click device, wait for "Get Started" to appear
- Unplug → replug USB
- Try again
```

### Error saat klik "PATCH" / "There was an error while patching" 🔥

Ini issue paling umum. Coba langkah-langkah ini (berdasarkan laporan user yang berhasil):

#### a) Block Apple MDM enrollment servers

Device iOS bisa ngecek MDM status ke server Apple bahkan tanpa Wi-Fi (via cached DNS atau koneksi background). Block hostnames ini di komputer lo:

**Windows** — edit `C:\Windows\System32\drivers\etc\hosts` (run Notepad as Administrator):
```
0.0.0.0    iprofiles.apple.com
0.0.0.0    mdmenrollment.apple.com
0.0.0.0    deviceenrollment.apple.com
```

**Linux** — edit `/etc/hosts` (pakai `sudo`):
```bash
sudo nano /etc/hosts
# tambahin 3 baris yang sama di atas
```

> ⚠️ Jangan lupa hapus entries ini setelah selesai biar iTunes/iCloud normal lagi.

#### b) Power cycle device sebelum patch

```
1. Pastikan device gak konek Wi-Fi (tetap di Wi-Fi screen, jangan pilih network)
2. Biarin iPad/iPhone tetap ke-plug USB
3. Biarin ErFlasher MDM Tools tetap kebuka
4. Restart device (power off → power on)
5. Setelah nyala lagi & balik ke Hello screen → langsung klik PATCH
```

Kenapa ini membantu: power cycle nge-reset koneksi network internal & cache. Device jadi "fresh" tanpa sempat ngecek Apple server.

#### c) Pastikan aktivasi selesai

```
- Buka iTunes/Finder, klik device lo
- Tunggu sampai muncul "Get Started" atau "Welcome to your new iPhone/iPad"
- Baru buka ErFlasher MDM Tools & klik PATCH
```

### Patch sukses tapi MDM balik setelah factory reset

Ini **fundamental limitation**, bukan bug. Penjelasannya:

- Tools ini nge-patch **backup lokal yang direstore ke device** — bukan deregister dari Apple server
- Kalau lo factory reset dari **Settings HP** (tanpa restore via komputer), device narik config langsung dari Apple Business Manager — dan serial number lo masih terdaftar di server mereka
- **Solusi:** kalau perlu reset lagi, harus restore IPSW via komputer + patch ulang. Jangan reset dari Settings.

### Activation Lock vs MDM — beda!

Banyak user bingung antara dua ini:

| | MDM (Mobile Device Management) | Activation Lock (Find My) |
|---|---|---|
| **Penyebab** | Device terdaftar di Apple Business Manager / School Manager | iCloud / Find My iPhone masih nyala |
| **Yang muncul di layar** | "Remote Management" / "This device is managed by..." | "Activation Lock" / minta Apple ID & password |
| **Bisa dibypass tools ini?** | ✅ iya | ❌ tidak |
| **Yang dibutuhkan** | Restore IPSW + patch backup | Apple ID & password pemilik asli |

**ErFlasher MDM Tools tidak bisa bypass Activation Lock / iCloud lock.**

### Patch berhasil, tapi setelah setup normal MDM notification muncul lagi

Ini bisa terjadi kalau device sempat konek internet **setelah** patch di tahap setup normal (setelah Hello screen selesai). Device yang terdaftar di ABM akan ngecek ulang saat sudah online.

**Mitigasi:**
1. Selama setup awal setelah patch, skip semua yang berhubungan sama internet semaksimal mungkin
2. Setelah masuk homescreen, langsung matikan Wi-Fi
3. Install MDM-blocking configuration profile (opsional, advanced users)

### App blocked on Windows (SmartScreen)

```
- Click "More info" → "Run anyway"
- Atau tambahkan project folder ke Windows Defender exceptions
```

---

## 🏗️ Build Standalone Executable

Build output sudah disiapkan untuk Windows dan Linux.

```bash
# Windows
python build.py --clean
# output: dist/ErFlasher-MDM-Tools.exe
# hanya bundle resource yang dipakai build Windows

# Linux
python build_linux.py --clean
# output: dist/ErFlasher-MDM-Tools
```

### Runtime Logs

- App menulis error log ke `erflasher.log`
- Lokasi:
  - frozen exe: folder yang sama dengan `ErFlasher-MDM-Tools.exe`
  - dev run: project root

Kalau app crash / patch fail, kirim `erflasher.log`.

---

## ⚠️ Legal Disclaimer

This project is intended **strictly for educational, diagnostic, and personal device recovery use only**. It must **only** be used on iOS devices that the user **legally owns** and has the right to modify.

ErFlasher MDM Tools **does not jailbreak, exploit, or modify firmware**. It relies entirely on public interfaces (AFC, plist editing, USB restore flows).

Using this software on managed, corporate, or institutional devices **without permission** is prohibited and may be illegal.

---

## 🙏 Credits

- **Erzambayu** — cross-platform port, maintenance, GUI rebuild
- **fled-dev** — original [MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced) (macOS)
- **j4nf4b3l** — [MDMPatcher-Universal](https://github.com/j4nf4b3l/MDMPatcher-Universal) (original concept)
- **libimobiledevice** team — iOS device communication library

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| GUI | CustomTkinter (dark theme, native look) |
| Crypto | pycryptodome — RNCryptor v3 AES-256-CBC |
| USB detection | polling via `idevice_id -l` + pyusb |
| Device comm | libimobiledevice CLI (`ideviceinfo`, `idevicebackup2`) |
| Fallback | pymobiledevice3 (pure Python) |
| Packaging | PyInstaller (single-file executable) |

---

## 📂 Project Structure

```
ErFlasher-MDM-Tools/
├── main.py                          # entry point
├── src/
│   ├── core/
│   │   ├── crypto_utils.py          # RNCryptor v3 decrypt + byte swap
│   │   ├── device_info.py           # iOS device info retrieval
│   │   ├── usb_detector.py          # USB device polling
│   │   ├── plist_patcher.py         # backup patching orchestrator
│   │   └── backup_restore.py        # backup restore engine
│   ├── gui/
│   │   └── main_window.py           # CustomTkinter GUI
│   └── resources/
│       ├── extension1.pdf           # encrypted Info.plist template
│       ├── extension2.pdf           # encrypted Manifest.plist template
│       └── libiMobileeDevice.dylib  # encrypted backup archive
├── requirements.txt
├── setup.py
├── build.py                         # Windows build script
├── build_linux.py                   # Linux build script
└── README.md
```

---

## 📝 License

MIT — [github.com/Erzambayu/ErFlasher-MDM-Tools](https://github.com/Erzambayu/ErFlasher-MDM-Tools)
