"""
crypto_utils.py - RNCryptor v3 decryption + byte swapping
ported dari ViewController.swift + deobfuscation.swift

format RNCryptor v3 (spec):
  byte 0      : version (3)
  byte 1      : options
  bytes 2-9   : encryptionSalt (8)
  bytes 10-17 : hmacSalt (8)  
  bytes 18-33 : IV (16)
  bytes 34+   : ciphertext | HMAC-SHA256 (32 bytes trailing)
"""

import struct
import hashlib
import hmac as hmac_module

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1, SHA256, HMAC as CryptoHMAC

# ---------------------------------------------------------------------------
# constants (from original Swift code)
# ---------------------------------------------------------------------------

# 6 pasang byte swap positions
SWAP_PAIRS = [
    (3, 5),
    (8, 17),
    (128, 345),
    (15, 65),
    (33, 133),
    (16, 64),
]

# placeholder hex values used in template plists (dari ViewController.swift)
PLACEHOLDER_BUILD_VERSION = bytes([0x31, 0x38, 0x43, 0x36, 0x36])       # "18C66"
PLACEHOLDER_PRODUCT_TYPE  = bytes([0x69, 0x50, 0x68, 0x6F, 0x6E, 0x65, 0x31, 0x32, 0x2C, 0x38])  # "iPhone12,8"
PLACEHOLDER_SERIAL        = bytes([0x46, 0x31, 0x37, 0x46, 0x34, 0x4D, 0x4C, 0x53, 0x50, 0x4C, 0x4B, 0x32])  # "F17F4MLSPLK2"
PLACEHOLDER_UDID          = bytes([0x30, 0x30, 0x30, 0x30, 0x38, 0x30, 0x33, 0x30, 0x2D, 0x30, 0x30, 0x31, 0x38, 0x35, 0x34, 0x45, 0x34, 0x32, 0x45, 0x30, 0x36, 0x34, 0x30, 0x32, 0x45])
PLACEHOLDER_IMEI          = bytes([0x33, 0x35, 0x37, 0x31, 0x34, 0x35, 0x34, 0x31, 0x33, 0x35, 0x31, 0x34, 0x37, 0x39, 0x37])  # "357145413514797"
PLACEHOLDER_IMEI_BLOCK    = bytes([
    0x09, 0x3C, 0x6B, 0x65, 0x79, 0x3E, 0x49, 0x4D, 0x45, 0x49, 0x3C, 0x2F, 0x6B, 0x65, 0x79, 0x3E,
    0x0A, 0x09, 0x3C, 0x73, 0x74, 0x72, 0x69, 0x6E, 0x67, 0x3E, 0x33, 0x35, 0x37, 0x31, 0x34, 0x35,
    0x34, 0x31, 0x33, 0x35, 0x31, 0x34, 0x37, 0x39, 0x37, 0x3C, 0x2F, 0x73, 0x74, 0x72, 0x69, 0x6E,
    0x67, 0x3E, 0x0A
])  # "\t<key>IMEI</key>\n\t<string>357145413514797</string>\n"


# ---------------------------------------------------------------------------
# password derivation (identik dengan Swift)
# ---------------------------------------------------------------------------

def calculate_password() -> str:
    """generate password yang sama persis dengan Swift version."""
    i = 4 * 2 * 4 * 6           # 192.0
    i = i * 7 / 5 + 23          # 291.8
    i = i - 546 * 5464564 * 64635645 * 4536454 * 462  # huge negative number
    
    template = f"qepkwotkgpeqgpeokqgokgqoe{i}fdlgkdlgfklsdöfdgsj{i}gfdads23ji4jgi3vqewö"
    password = template.replace("q", "r")
    return password


# ---------------------------------------------------------------------------
# byte swapping (identik dengan Swift Data.swapAt)
# ---------------------------------------------------------------------------

def swap_bytes(data: bytearray, pairs: list = None) -> bytearray:
    """swap byte positions sesuai daftar pasangan.
    identik dengan Data.swapAt() di Swift.
    """
    if pairs is None:
        pairs = SWAP_PAIRS
    
    max_idx = max(max(p) for p in pairs)
    if len(data) <= max_idx:
        raise ValueError(f"data too short for swap: {len(data)} <= {max_idx}")
    
    for a, b in pairs:
        data[a], data[b] = data[b], data[a]
    
    return data


# ---------------------------------------------------------------------------
# RNCryptor v3 decrypt
# ---------------------------------------------------------------------------

RNCryptorHeader = struct.Struct("! B B 8s 8s 16s")  # version, options, encSalt, hmacSalt, IV
HEADER_SIZE = RNCryptorHeader.size  # 34
HMAC_SIZE = 32
PBKDF2_ITERATIONS = 10000


def rncryptor_decrypt(data: bytes, password: str) -> bytes:
    """
    decrypt RNCryptor v3 format data.
    matches RNCryptor.decrypt(data:withPassword:) in Swift v5.x.
    
    format:
      [version:1][options:1][encSalt:8][hmacSalt:8][IV:16][ciphertext][HMAC:32]
    """
    if len(data) < HEADER_SIZE + HMAC_SIZE + 16:  # min 1 block ciphertext
        raise ValueError(f"data too short for RNCryptor v3: {len(data)} bytes")
    
    # parse header
    version, options, enc_salt, hmac_salt, iv = RNCryptorHeader.unpack(data[:HEADER_SIZE])
    
    if version != 3:
        raise ValueError(f"unsupported RNCryptor version: {version}")
    
    # split ciphertext and hmac
    ciphertext = data[HEADER_SIZE:-HMAC_SIZE]
    expected_hmac = data[-HMAC_SIZE:]
    
    # derive keys via PBKDF2-HMAC-SHA1
    pw_bytes = password.encode("utf-8")
    
    encryption_key = PBKDF2(pw_bytes, enc_salt, dkLen=32, count=PBKDF2_ITERATIONS,
                            hmac_hash_module=SHA1)
    hmac_key = PBKDF2(pw_bytes, hmac_salt, dkLen=32, count=PBKDF2_ITERATIONS,
                      hmac_hash_module=SHA1)
    
    # verify HMAC (over header + ciphertext, excluding the HMAC itself)
    hmac_data = data[:HEADER_SIZE + len(ciphertext)]
    computed_hmac = CryptoHMAC.new(hmac_key, hmac_data, SHA256).digest()
    
    if not hmac_module.compare_digest(computed_hmac, expected_hmac):
        # for debugging: sometimes RNCryptor uses different HMAC scope
        # try without options byte (some versions)
        hmac_data_v2 = data[:1] + data[2:HEADER_SIZE + len(ciphertext)]
        computed_hmac_v2 = CryptoHMAC.new(hmac_key, hmac_data_v2, SHA256).digest()
        if not hmac_module.compare_digest(computed_hmac_v2, expected_hmac):
            raise ValueError("HMAC verification failed — wrong password or corrupted data")
    
    # decrypt AES-256-CBC
    cipher = AES.new(encryption_key, AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(ciphertext)
    
    # remove PKCS#7 padding
    pad_len = plaintext[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError(f"invalid PKCS#7 padding: {pad_len}")
    
    return plaintext[:-pad_len]


def decrypt_resource(data: bytes, password: str = None) -> bytes:
    """
    full decrypt pipeline for resource files:
    1. byte swap (pre-decrypt)
    2. RNCryptor decrypt
    3. byte swap (post-decrypt)
    
    identik dengan logic di patchFile1/2/3() + deobfuscation.swift
    """
    if password is None:
        password = calculate_password()
    
    data = bytearray(data)
    
    # pre-decrypt swap
    data = swap_bytes(data)
    
    # RNCryptor decrypt
    decrypted = rncryptor_decrypt(bytes(data), password)
    
    # post-decrypt swap
    decrypted = bytearray(decrypted)
    decrypted = swap_bytes(decrypted)
    
    return bytes(decrypted)


# ---------------------------------------------------------------------------
# plist patching helpers
# ---------------------------------------------------------------------------

def patch_info_plist(plist_str: str, build_id: str, imei: str,
                     product_type: str, sn: str, udid: str) -> str:
    """
    patch Info.plist content — identik dengan patchFile1() di Swift.
    """
    result = plist_str
    
    # BuildVersion
    placeholder = PLACEHOLDER_BUILD_VERSION.decode("utf-8")
    result = result.replace(placeholder, build_id)
    
    # IMEI
    if not imei or imei.strip() == "":
        placeholder_block = PLACEHOLDER_IMEI_BLOCK.decode("utf-8")
        result = result.replace(placeholder_block, "")
    else:
        placeholder_imei = PLACEHOLDER_IMEI.decode("utf-8")
        result = result.replace(placeholder_imei, imei)
    
    # ProductType
    placeholder = PLACEHOLDER_PRODUCT_TYPE.decode("utf-8")
    result = result.replace(placeholder, product_type)
    
    # SerialNumber
    placeholder = PLACEHOLDER_SERIAL.decode("utf-8")
    result = result.replace(placeholder, sn)
    
    # UDID (2 kali di Swift — TargetIdentifier + UniqueDeviceID, dua2nya UDID)
    placeholder = PLACEHOLDER_UDID.decode("utf-8")
    result = result.replace(placeholder, udid)
    
    return result


def patch_manifest_plist(plist_str: str, build_id: str, imei: str,
                         product_type: str, sn: str, udid: str) -> str:
    """
    patch Manifest.plist content — identik dengan patchFile2() di Swift.
    """
    result = plist_str
    
    # BuildVersion
    placeholder = PLACEHOLDER_BUILD_VERSION.decode("utf-8")
    result = result.replace(placeholder, build_id)
    
    # ProductType
    placeholder = PLACEHOLDER_PRODUCT_TYPE.decode("utf-8")
    result = result.replace(placeholder, product_type)
    
    # SerialNumber
    placeholder = PLACEHOLDER_SERIAL.decode("utf-8")
    result = result.replace(placeholder, sn)
    
    # UDID
    placeholder = PLACEHOLDER_UDID.decode("utf-8")
    result = result.replace(placeholder, udid)
    
    return result
