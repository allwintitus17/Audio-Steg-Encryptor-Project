"""Global configuration constants, protocol headers, and defaults."""

import os
from pathlib import Path

# Application Meta
APP_NAME = "Audio Cryptography & Dual-Steganography Studio"
APP_VERSION = "2.0.0"

# Protocol Headers
STEGO_MAGIC_HEADER = b"ASTG"
IMAGE_STEGO_MAGIC = b"IMGK"
HEADER_VERSION = 2

# Supported File Formats
SUPPORTED_CARRIER_FORMATS = [
    ("Lossless Audio (*.wav)", "*.wav"),
    ("All Files (*.*)", "*.*"),
]

SUPPORTED_SECRET_FORMATS = [
    ("All Audio Files (*.mp3, *.wav, *.aac, *.flac, *.m4a)", "*.mp3;*.wav;*.aac;*.flac;*.m4a"),
    ("MP3 Audio (*.mp3)", "*.mp3"),
    ("WAV Audio (*.wav)", "*.wav"),
    ("All Files (*.*)", "*.*"),
]

SUPPORTED_IMAGE_FORMATS = [
    ("Lossless Images (*.png, *.bmp)", "*.png;*.bmp"),
    ("PNG Image (*.png)", "*.png"),
    ("BMP Image (*.bmp)", "*.bmp"),
    ("All Files (*.*)", "*.*"),
]

# Cryptography Settings
DEFAULT_KDF_ITERATIONS = 100_000
AES_KEY_SIZE_BYTES = 32  # 256-bit AES / ChaCha20
SALT_SIZE_BYTES = 16
NONCE_SIZE_BYTES = 12    # Standard AEAD nonce size
KEY_ID_SIZE_BYTES = 8    # 64-bit session association token
