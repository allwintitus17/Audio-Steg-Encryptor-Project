# 🎵 Audio Cryptography & Dual-Carrier Steganography Studio

A desktop security application built with **100% pure Python and Tkinter** that provides military-grade audio encryption and dual-carrier steganography. It encrypts any secret audio file, embeds the encrypted audio into an ordinary cover song, generates an uncrackable 256-bit cryptographic key, and conceals that key inside a companion cover image.

Decryption requires **both** the Stego Song and the Stego Key Image — neither is sufficient on its own.

---

## 📑 Table of Contents
1. [System Overview & Architecture](#-system-overview--architecture)
2. [Algorithms & Cryptographic Specifications](#-algorithms--cryptographic-specifications)
3. [Audio & Image Format Rules](#-audio--image-format-rules)
4. [Step-by-Step User Guide](#-step-by-step-user-guide)
   - [Phase 1: Encrypting and Hiding Audio](#phase-1-encrypting-and-hiding-audio)
   - [Phase 2: Extracting and Decrypting Audio](#phase-2-extracting-and-decrypting-audio)
   - [Phase 3: Audio Capacity Diagnostics](#phase-3-audio-capacity-diagnostics)
5. [UI Architecture & Layout Features](#-ui-architecture--layout-features)
6. [Project File Structure](#-project-file-structure)
7. [Installation & Quickstart](#-installation--quickstart)
8. [Security & Anti-Forensic Properties](#-security--anti-forensic-properties)
9. [Running Verification Tests](#-running-verification-tests)

---

## 🏛 System Overview & Architecture

Traditional steganography embeds data into a single medium and relies on user-remembered passwords or leaves key files vulnerable on disk. This system implements **Dual-Carrier Split-Steganography**:

```text
[Secret Audio File] (Any format: .m4a, .mp3, .wav, .aac, .flac)
         │
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 256-Bit Cryptographically Secure Pseudo-Random Key Generator (CSPRNG)   │
│   Package: [Key ID (8B)] + [Key (32B)] + [Nonce (12B)] + [Salt (16B)]   │
│            + [HMAC-SHA256 Anti-Tamper Checksum (32B)]                  │
└──────────────────┬─────────────────────────────────────┬───────────────┘
                   │                                     │
                   ▼                                     ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│ Audio Encryption & Steganography     │  │ Key Image Steganography              │
│ 1. Encrypt audio with Session Key    │  │ 1. Read lossless PNG / BMP pixels    │
│    (AES-256-GCM / ChaCha20-Poly1305) │  │ 2. Embed 100-byte key package via    │
│ 2. Embed ciphertext into Song WAV    │  │    Image LSB substitution            │
│    via Adaptive Multi-Bit Audio LSB  │  │ 3. Output normal-looking image       │
│ 3. Store paired 8-byte Key ID        │  │                                      │
└──────────────────┬───────────────────┘  └──────────────────┬───────────────────┘
                   │                                         │
                   ▼                                         ▼
        🎵 [stego_song.wav]                       🖼️ [stego_key_image.png]
   (Sounds like an ordinary song)             (Displays like an ordinary photo)
```

---

## 🔬 Algorithms & Cryptographic Specifications

### 1. Key Generation (CSPRNG)
* **Algorithm**: Cryptographically Secure Pseudo-Random Number Generation (`os.urandom`).
* **Keyspace**: $2^{256} \approx 1.1579 \times 10^{77}$ combinations.
* **Resistance**: Immune to dictionary attacks, rainbow tables, and brute-force cracking.

### 2. Key Package Structure (100 Bytes)
Stored inside [core/crypto.py](file:///C:/Users/allwi/OneDrive/Documents/Desktop/Audio%20Encryption%20Software%20Product/core/crypto.py):
$$\text{Package} = \underbrace{\text{Key ID}}_{8\text{ B}} + \underbrace{\text{Session Key}}_{32\text{ B}} + \underbrace{\text{Nonce}}_{12\text{ B}} + \underbrace{\text{Salt}}_{16\text{ B}} + \underbrace{\text{HMAC-SHA256 Tag}}_{32\text{ B}} = \mathbf{100\text{ Bytes}}$$

* **Key ID (8 Bytes / 64 bits)**: A session association token bound to both the song and the image.
* **Nonce (12 Bytes / 96 bits)**: Unique initialization vector ensuring cryptographic uniqueness across sessions.
* **Salt (16 Bytes / 128 bits)**: High-entropy cryptographic salt.
* **HMAC-SHA256 Signature (32 Bytes / 256 bits)**: Computed over $\text{Key ID} \parallel \text{Nonce} \parallel \text{Salt}$ using the Session Key. Any byte modification to the image invalidates the signature and aborts decryption.

### 3. Authenticated Symmetric Audio Encryption
* **Primary Engine**: **AES-256-GCM** (Galois/Counter Mode, NIST SP 800-38D). Provides simultaneous confidentiality and data integrity verification with a 16-byte authentication tag.
* **Zero-Dependency Fallback**: **ChaCha20 Stream Cipher** (IETF RFC 7539 / RFC 8439) combined with **HMAC-SHA256** (Encrypt-then-MAC). Built purely from Python's standard library.

### 4. Audio Steganography: Adaptive Multi-Bit LSB
Stored inside [core/steganography.py](file:///C:/Users/allwi/OneDrive/Documents/Desktop/Audio%20Encryption%20Software%20Product/core/steganography.py):
* **Format**: 16-bit linear PCM uncompressed WAV audio.
* **Bootstrap Header (1-Bit/Sample)**: The first 176 samples store metadata at strictly 1 bit per sample:
  $$\text{Header} = \text{b"ASTG"} + \text{Key ID (8B)} + \text{BitsPerSample (1B)} + \text{ExtLen (1B)} + \text{Ext} + \text{PayloadLen (4B)}$$
* **Adaptive Multi-Bit Payload ($k \in \{1, 2, 3, 4\}$ bits/sample)**:
  $$\text{Sample Byte}_{\text{new}} = (\text{Sample Byte}_{\text{orig}} \ \& \ \sim ((1 \ll k) - 1)) \ | \ \text{Payload Chunk}$$
  * $k=1$: Maximum acoustic fidelity ($\approx 1.98\text{ MB}$ per 3-min song).
  * $k=2$: Balanced mode ($\approx 3.96\text{ MB}$ per 3-min song).
  * $k=3$: High capacity ($\approx 5.95\text{ MB}$ per 3-min song, fits large 5MB+ audio files).
  * $k=4$: Maximum capacity ($\approx 7.93\text{ MB}$ per 3-min song).
* The algorithm automatically selects the lowest bit-depth $k$ required to fit the secret payload, preserving the best possible sound quality.

### 5. Image Steganography: Spatial Domain LSB
Stored inside [core/image_steganography.py](file:///C:/Users/allwi/OneDrive/Documents/Desktop/Audio%20Encryption%20Software%20Product/core/image_steganography.py):
* **Formats**: Lossless 24-bit RGB / 32-bit RGBA PNG and BMP images.
* **Bit Depth**: 1 bit embedded per color channel byte.
* **Visual Inconspicuity**: Maximum luminance alteration is $\pm 1$ out of 255 ($\approx 0.39\%$), which is undetectable to the human visual system.
* **Pure Standard Library**: Reads, decompresses (`zlib`), modifies, and rebuilds standard PNG chunks (`IHDR`, `IDAT`, `IEND`) without external imaging dependencies.

### 6. Acoustic Carrier Waveform Synthesis
Stored inside [core/audio_handler.py](file:///C:/Users/allwi/OneDrive/Documents/Desktop/Audio%20Encryption%20Software%20Product/core/audio_handler.py):
* Synthesizes a 3-minute, 44.1 kHz, 16-bit stereo harmonic WAV song using soft chord progressions (A4 440 Hz, C#5 554 Hz, E5 659 Hz) with sinusoidal envelopes. Provides an instant carrier with over 8 Megabytes of steganographic capacity.

---

## 📀 Audio & Image Format Rules

| File Role | Supported Formats | Why This Format? |
| :--- | :--- | :--- |
| **Secret Audio File** *(File to hide)* | **Any Format**: `.mp3`, `.m4a`, `.wav`, `.aac`, `.flac`, `.ogg` | The software reads raw binary bytes, encrypts them, and restores the exact original format upon extraction. |
| **Carrier Song** *(Cover music)* | **Lossless WAV only**: `.wav` (16-bit PCM) | **Lossy audio (like `.mp3` or `.m4a`) CANNOT be used as carriers** because lossy compression algorithms (MDCT quantization) discard fine bit-level variations, destroying embedded data. |
| **Cover Image** *(Carrier for key)* | **Lossless PNG or BMP**: `.png`, `.bmp` | **Lossy images (like `.jpg` or `.jpeg`) CANNOT be used** because JPEG DCT quantization permanently erases least significant bits. |

> [!TIP]
> If you do not have a `.wav` song or `.png` image on hand, use the built-in **"✨ Auto-Generate Carrier WAV"** and **"✨ Auto-Generate Image"** buttons in the application to generate compatible carriers in one click.

---

## 📖 Step-by-Step User Guide

### Phase 1: Encrypting and Hiding Audio

1. Launch the application:
   ```powershell
   python main.py
   ```
2. Navigate to the **"🔒 Encrypt & Hide (Audio + Image)"** tab.
3. **Step 1 (Secret Audio)**: Click **Browse...** and select the audio file you want to protect (e.g., `.m4a`, `.mp3`, `.wav`).
4. **Step 2 (Carrier Song)**:
   * Select a lossless `.wav` cover song, **OR**
   * Click **"✨ Auto-Generate Carrier WAV"** to generate an optimized 3-minute stereo carrier song.
   * *(Optional)*: Click **▶ Play Preview** to listen to the carrier song.
5. **Step 3 (Cover Image)**:
   * Select a `.png` or `.bmp` picture from your computer, **OR**
   * Click **"✨ Auto-Generate Image"** to create a 250×250 gradient cover image.
6. **Step 4 (Output Products)**:
   * Verify the output paths for your **Stego Audio** (`stego_song.wav`) and **Stego Key Image** (`stego_key_image.png`).
7. **Execute**:
   * Click **`🔒 Generate Key, Encrypt Audio & Embed Both`** in the bottom action bar.
   * The status bar and progress indicator will display completion progress.
   * Upon completion, a confirmation dialog displays the unique **Session Pairing Key ID**.

---

### Phase 2: Extracting and Decrypting Audio

1. Open the **"🔓 Extract & Decrypt (Audio + Image)"** tab.
2. **Step 1 (Stego Audio)**: Click **Browse...** and select the `stego_song.wav` file.
3. **Step 2 (Stego Key Image)**: Click **Browse...** and select the companion `stego_key_image.png` file.
4. **Step 3 (Destination Folder)**: Choose where you want the recovered audio file saved.
5. **Execute**:
   * Click **`🔓 Extract Key from Image & Decrypt Audio`** in the bottom action bar.
   * The system will:
     1. Extract and verify the key package from the image.
     2. Extract the encrypted payload and Key ID from the song.
     3. Verify that the **Key IDs match**.
     4. Decrypt the secret audio and restore the original file (e.g., `restored_secret_audio.m4a`).
6. **Preview**:
   * Use the **Recovered Audio Preview** player directly inside Tkinter to listen to the restored file.

---

### Phase 3: Audio Capacity Diagnostics

1. Navigate to the **"📊 Audio Capacity & Info"** tab.
2. Select any audio file on your computer.
3. The diagnostic engine will display:
   * Channel count (Mono / Stereo)
   * Sampling rate (e.g., 44,100 Hz)
   * Bit-depth (e.g., 16-bit PCM)
   * Audio duration (in seconds)
   * Maximum safe hidden payload capacity across 1-bit, 2-bit, and 4-bit LSB modes.

---

## 🖥 UI Architecture & Layout Features

* **Fixed Bottom Action Toolbar**: The main action button, status label, and progress bar are permanently docked at the bottom of the window (`side="bottom"`). They remain visible and clickable across all screen resolutions and Windows display scaling levels (100%, 125%, 150%).
* **Smooth Mousewheel Scrollable Canvas**: The form steps are hosted inside a scrollable canvas. Users on smaller laptop screens can navigate using their mouse wheel or the vertical scrollbar.
* **Native Tkinter Audio Player**: Audio preview controls (**▶ Play Preview** / **⏹ Stop**) utilize Windows' built-in `winsound` multimedia engine. No third-party media players or SDL libraries are required.
* **Non-Blocking Multithreading**: All heavy cryptographic operations and sample traversals run in background daemon threads (`utils/threading_utils.py`), ensuring the Tkinter user interface never freezes.

---

## 📁 Project File Structure

```text
Audio Encryption Software Product/
├── assets/                                 # UI styling resources
│   ├── icons/                              # Application icons
│   └── styles/                             # Theme configurations
│
├── core/                                   # Algorithmic & Processing Engines
│   ├── __init__.py                         # Package marker
│   ├── crypto.py                           # 256-bit CSPRNG key gen, AES-256-GCM, ChaCha20, HMAC-SHA256
│   ├── audio_handler.py                    # PCM frame I/O, metadata analysis, 3-min carrier synthesizer
│   ├── steganography.py                    # Adaptive multi-bit LSB audio steganography (1-4 bits/sample)
│   ├── image_steganography.py              # Pure standard-library PNG/BMP spatial LSB steganography
│   └── validator.py                        # Carrier compatibility & capacity limit validation
│
├── gui/                                    # Presentation Layer (Pure Tkinter)
│   ├── __init__.py                         # Package marker
│   ├── app.py                              # Window lifecycle, layout manager, tab controller
│   ├── styles.py                           # Modern dark slate color palette & ttk style maps
│   ├── components/                         # Modular UI Widgets
│   │   ├── __init__.py                     # Package marker
│   │   ├── file_picker.py                  # Entry + browse dialog + file size inspection
│   │   └── audio_player.py                 # Pure Tkinter audio preview player via winsound
│   └── views/                              # Application Screens
│       ├── __init__.py                     # Package marker
│       ├── encode_view.py                  # 🔒 Tab 1: Secret Audio + Song + Image Dual-Stego
│       ├── decode_view.py                  # 🔓 Tab 2: Stego Song + Stego Key Image Decryption
│       └── analysis_view.py                # 📊 Tab 3: Carrier diagnostics & capacity calculator
│
├── utils/                                  # Shared System Utilities
│   ├── __init__.py                         # Package marker
│   ├── config.py                           # Protocol magic bytes ('ASTG', 'IMGK') and limits
│   ├── logger.py                           # Application logger
│   └── threading_utils.py                  # Background asynchronous task dispatcher
│
├── tests/                                  # Automated Test Suite
│   ├── __init__.py                         # Package marker
│   ├── test_crypto.py                      # Cipher & tamper verification tests
│   ├── test_stego.py                       # Multi-bit audio embedding roundtrip tests
│   └── test_dual_stego.py                  # End-to-end dual-carrier integration test
│
├── main.py                                 # Application launch entry point
├── requirements.txt                        # Zero mandatory dependencies specification
└── README.md                               # Complete system documentation
```

---

## ⚡ Installation & Quickstart

### Prerequisites
* **Operating System**: Windows 10 or Windows 11.
* **Python**: Python 3.9 through Python 3.14+ (tested on Python 3.14.6).

### 1. Launch the Software
The application runs directly with Python's built-in standard library (Tkinter, wave, struct, hashlib, zlib, winsound). **No pip packages are required to run.**

```powershell
python main.py
```

### 2. Optional Hardware Acceleration
If you wish to enable hardware-accelerated AES-256-GCM via OpenSSL, you may optionally install `cryptography`:
```powershell
pip install cryptography
```
*(If omitted, the app automatically runs its built-in pure-Python ChaCha20-Poly1305 engine).*

---

## 🛡️ Security & Anti-Forensic Properties

1. **Zero System Footprint**: The application does not write to the Windows Registry, create local databases, or cache keys in temporary directories. All keys exist strictly in RAM during execution and inside the carriers.
2. **Cryptographic Binding**: The 8-byte Key ID prevents key-substitution attacks. Attempting to decrypt a stego song with an unrelated key image results in immediate rejection.
3. **Anti-Tamper HMAC Signatures**: If an image is cropped, compressed, or tampered with, the 32-byte HMAC-SHA256 signature check fails, preventing corrupted decryption attempts.
4. **Natural Carrier Acoustics**: Modifying the least significant bits introduces changes of only $\pm 1$ unit out of 65,536 in 16-bit audio, remaining completely inaudible during normal music playback.

---

## 🧪 Running Verification Tests

Run the full automated test suite from the project root:

```powershell
python -m unittest discover -s tests
```

Output:
```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.489s

OK
```
*(All 6 unit tests verify cryptographic key generation, tamper rejection, image LSB embedding, multi-bit audio embedding, and end-to-end dual-carrier restoration).*
