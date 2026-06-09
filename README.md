# ErFlasher MDM Tools — Cross-Platform Edition

**bypass MDM enrollment on iOS devices** — now on **Windows & Linux**.

built by **Erzambayu** — based on [MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced) by fled-dev.

---

## 📱 iOS version support

| supported | details |
|---|---|
| **iOS 15.0 – 18.5+** | ✅ fully tested |
| **iOS 16.x, 17.x** | ✅ works |
| **iOS 18.0 – 18.5+** | ✅ latest confirmed working |
| **iOS 26.0 – 26.2** | ✅ confirmed working by users (iPhone 15, various iPads) |
| **iOS 26.3+** | ⚠️ mixed reports — some work, some error. try blocking Apple MDM hosts (see troubleshooting) |
| **below iOS 15** | ⚠️ may work, not tested |
| **above iOS 26.5** | ⚠️ not yet tested — backup format rarely changes between minor versions

**why does this work across versions?** — this tool doesn't use exploits or jailbreaks. it leverages the **MobileBackup2** protocol (iTunes backup/restore), a legitimate iOS feature present since iOS 4. Apple can't easily "patch" this without breaking their own restore functionality.

### devices supported

- **iPhone 5s** to **iPhone 16** (all models)
- **all iPads** (including Pro, Air, Mini)
- cellular & Wi-Fi only

---

## 🔗 links

- **GitHub**: [github.com/Erzambayu/ErFlasher-MDM-Tools](https://github.com/Erzambayu/ErFlasher-MDM-Tools)
- **Original**: [github.com/fled-dev/MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced)

---

## 📋 requirements before starting

### hardware
- USB Lightning / USB-C cable (original recommended)
- Windows or Linux computer

### device state (MANDATORY!)
```
┌─────────────────────────────────────────────────────┐
│  1. device at Hello screen (setup assistant)        │
│  2. DO NOT connect to Wi-Fi or cellular data        │
│  3. screen unlocked, display on                     │
│  4. trust this computer? → tap "Trust"              │
└─────────────────────────────────────────────────────┘
```

⚠️ **why no internet before patching?** if the device connects to Wi-Fi, it auto-checks Apple Business Manager / MDM enrollment server. once detected, the device locks before patching can complete.

### required file
- **IPSW file** for your device — download from [ipsw.me](https://ipsw.me)
  - check model number on device back (e.g. A1567)
  - match to device name via [The iPhone Wiki](https://www.theiphonewiki.com/wiki/Models)
  - **cellular vs Wi-Fi**: SIM slot → download Cellular IPSW, otherwise → Wi-Fi only

---

## 🚀 full guide (step by step)

### step 1: restore device with IPSW (clean wipe)

```
┌──────────────────────────────────────────┐
│  enter RECOVERY MODE                      │
│                                           │
│  iPhone 8 and later (Face ID):            │
│    1. tap Volume Up                       │
│    2. tap Volume Down                     │
│    3. hold Side Button while plugging USB │
│                                           │
│  iPhone 7 / 7 Plus:                       │
│    hold Volume Down while plugging USB    │
│                                           │
│  iPhone 6s and earlier:                   │
│    hold Home Button while plugging USB    │
│                                           │
│  iPad without Home button:                │
│    hold Top Button while plugging USB     │
│                                           │
│  iPad with Home button:                   │
│    hold Home Button while plugging USB    │
└──────────────────────────────────────────┘
```

- after entering recovery mode, Finder/iTunes shows "Update or Restore" popup
- **Windows**: hold **SHIFT** + click "Restore"
- **Linux**: use `idevicerestore` CLI:
  ```bash
  idevicerestore -e <path-to-ipsw.ipsw>
  ```
- select the IPSW file you downloaded
- wait for restore to finish (5–15 minutes)

### step 2: initial setup until Wi-Fi screen

- after restore, device reboots to Hello screen
- follow initial setup:
  - choose language
  - choose region
  - **when you reach "Choose a Wi-Fi Network" → STOP! DO NOT select ANY network!**
  - do not connect Wi-Fi, do not connect cellular
- leave device on that Wi-Fi screen

### step 3: install dependencies

**Linux:**
```bash
# python dependencies
pip install -r requirements.txt

# system tools (libimobiledevice)
sudo apt update
sudo apt install libimobiledevice-utils usbmuxd

# start usbmuxd service
sudo systemctl start usbmuxd
```

**Windows:**
```bash
# python dependencies
pip install -r requirements.txt

# install iTunes (provides Apple Mobile Device Support + usbmuxd)
# download from: https://www.apple.com/itunes/
#
# OR install via MSYS2:
# pacman -S mingw-w64-x86_64-libimobiledevice
```

### step 4: connect device & trust

- connect device to computer via USB cable
- **unlock device** (screen must be on, not at lock screen)
- "Trust This Computer?" popup → tap **"Trust"**
- if asked for passcode, enter old passcode

### step 5: verify device detected

```bash
# check device detected
idevice_id -l
# output: 00008030-001854E42E06402E  (example UDID)

# check device info
ideviceinfo -s
# should show ProductType, SerialNumber, BuildVersion, etc.
```

if `ideviceinfo` fails → make sure device is unlocked + trusted.

### step 6: open ErFlasher MDM Tools & patch

```bash
python main.py
```

1. app auto-detects device
2. device info (model, SN, UDID, firmware, IMEI) shows in UI
3. click **"🔧 PATCH MDM"** button
4. watch progress:
   - decrypting backup archive...
   - patching plist files...
   - restoring to device...
5. device will **reboot automatically**
6. after reboot → device returns to Hello screen → **now you CAN connect Wi-Fi** — MDM is gone!

### step 7: finish setup

- continue iOS setup normally
- connect Wi-Fi → activation → iCloud → done
- device is now **MDM-free**

---

## 🐛 troubleshooting

### "No device found" / device not detected

```
1. check USB cable (use original if possible)
2. unlock device, screen on
3. make sure you tapped "Trust"
4. unplug → replug USB
5. check usbmuxd service running:
   Linux: sudo systemctl status usbmuxd
   Windows: check iTunes / Apple Mobile Device Service in Services
```

### "ERROR: Could not connect to lockdownd"

```
- device must be at Hello screen (normal mode), NOT recovery mode
- make sure screen is unlocked
- try unlocking device, closing/opening app
- restart usbmuxd: sudo systemctl restart usbmuxd (Linux)
```

### "ERROR: Restore failed"

```
- device may not be fully activated yet
- open Finder/iTunes, click device, wait for "Get Started" to appear
- unplug → replug USB
- try again
```

### error saat klik "PATCH" / "There was an error while patching" 🔥

ini issue paling umum. coba langkah-langkah ini (berdasarkan laporan user yg berhasil):

#### a) blokir Apple MDM enrollment servers

device iOS secara diam-diam ngecek MDM status ke server Apple bahkan tanpa Wi-Fi (via cached DNS atau koneksi background). blokir hostnames ini di komputer lo:

**Windows** — edit `C:\Windows\System32\drivers\etc\hosts` (run Notepad as Administrator):
```
0.0.0.0    iprofiles.apple.com
0.0.0.0    mdmenrollment.apple.com
0.0.0.0    deviceenrollment.apple.com
```

**Linux** — edit `/etc/hosts` (pakai `sudo`):
```bash
sudo nano /etc/hosts
# tambahin 3 baris yg sama di atas
```

> ⚠️ jangan lupa hapus entries ini setelah selesai biar iTunes/iCloud normal lagi

#### b) power cycle device sebelum patch

```
1. pastikan device gak konek Wi-Fi (tetep di Wi-Fi screen, jangan pilih network)
2. biarin iPad/iPhone tetep ke-plug USB
3. biarin ErFlasher MDM Tools tetep kebuka
4. restart device (power off → power on)
5. setelah nyala lagi & balik ke Hello screen → langsung klik PATCH
```

kenapa ini membantu: power cycle nge-reset koneksi network internal & cache. device jadi "fresh" tanpa sempet ngecek Apple server.

#### c) pastikan aktivasi selesai

```
- buka iTunes/Finder, klik device lo
- tunggu sampai muncul "Get Started" atau "Welcome to your new iPhone/iPad"
- baru buka ErFlasher MDM Tools & klik PATCH
```

### patch sukses tapi MDM balik setelah factory reset

ini **fundamental limitation**, bukan bug. penjelasannya:

- tools ini nge-patch **backup lokal yg direstore ke device** — bukan deregister dari Apple server
- kalo lo factory reset dari **Settings HP** (tanpa restore via komputer), device narik config langsung dari Apple Business Manager — dan serial number lo masih terdaftar di server mereka
- **solusi:** kalo perlu reset lagi, harus restore IPSW via komputer + patch ulang. jangan reset dari Settings.

### activation lock vs MDM — beda!

banyak user bingung antara dua ini:

| | MDM (Mobile Device Management) | Activation Lock (Find My) |
|---|---|---|
| **penyebab** | device terdaftar di Apple Business Manager / School Manager | iCloud / Find My iPhone masih nyala |
| **yg muncul di layar** | "Remote Management" / "This device is managed by..." | "Activation Lock" / minta Apple ID & password |
| **bisa dibypass tools ini?** | ✅ iya | ❌ tidak |
| **yg dibutuhin** | restore IPSW + patch backup | Apple ID & password pemilik asli |

**ErFlasher MDM Tools tidak bisa bypass Activation Lock / iCloud lock.**

### patch berhasil, tapi setelah setup normal MDM notification muncul lagi

ini bisa terjadi kalo device sempet konek internet **setelah** patch di tahap setup normal (setelah Hello screen selesai). devices yg registered di ABM akan ngecek ulang pas udah online.

**mitigasi:**
1. selama setup awal setelah patch, skip semua yg berhubungan sama internet semaksimal mungkin
2. setelah masuk homescreen, langsung matiin Wi-Fi
3. install MDM-blocking configuration profile (opsional, advanced users)

### app blocked on Windows (SmartScreen)

```
- click "More info" → "Run anyway"
- or add project folder to Windows Defender exceptions
```

---

## 🏗️ build standalone executable

```bash
# Windows
python build.py --clean
# output: dist/ErFlasher-MDM-Tools.exe
# bundles only required resources for Windows build

# Linux
python build_linux.py --clean
# output: dist/ErFlasher-MDM-Tools
```

### runtime logs

- app writes error log to `erflasher.log`
- location:
  - frozen exe: same folder as `ErFlasher-MDM-Tools.exe`
  - dev run: project root

if app crash / patch fail, send `erflasher.log`

---

## ⚠️ legal disclaimer

this project is intended **strictly for educational, diagnostic, and personal device recovery use only**. it must **only** be used on iOS devices that the user **legally owns** and has the right to modify.

ErFlasher MDM Tools **does not jailbreak, exploit, or modify firmware**. it relies entirely on public interfaces (AFC, plist editing, USB restore flows).

using this software on managed, corporate, or institutional devices **without permission** is prohibited and may be illegal.

---

## 🙏 credits

- **Erzambayu** — cross-platform port, maintenance, GUI rebuild
- **fled-dev** — original [MDMPatcher-Enhanced](https://github.com/fled-dev/mdmpatcher-enhanced) (macOS)
- **j4nf4b3l** — [MDMPatcher-Universal](https://github.com/j4nf4b3l/MDMPatcher-Universal) (original concept)
- **libimobiledevice** team — iOS device communication library

---

## 🔧 tech stack

| layer | technology |
|---|---|
| GUI | CustomTkinter (dark theme, native look) |
| crypto | pycryptodome — RNCryptor v3 AES-256-CBC |
| USB detection | polling via `idevice_id -l` + pyusb |
| device comm | libimobiledevice CLI (`ideviceinfo`, `idevicebackup2`) |
| fallback | pymobiledevice3 (pure Python) |
| packaging | PyInstaller (single-file executable) |

---

## 📂 project structure

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
│       ├── extension1.pdf            # encrypted Info.plist template
│       ├── extension2.pdf            # encrypted Manifest.plist template
│       └── libiMobileeDevice.dylib   # encrypted backup archive
├── requirements.txt
├── setup.py
├── build.py                         # Windows build script
├── build_linux.py                   # Linux build script
└── README.md
```

---

## 📝 license

MIT — [github.com/Erzambayu/ErFlasher-MDM-Tools](https://github.com/Erzambayu/ErFlasher-MDM-Tools)
