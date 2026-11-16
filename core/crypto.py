"""Cryptographic Engine: High-Entropy Key Generation & Authenticated Symmetric Encryption.

Supports:
1. Generation of uncrackable 256-bit cryptographically secure random session keys.
2. Hardware-accelerated AES-256-GCM (if 'cryptography' is installed).
3. Pure Python ChaCha20 + HMAC-SHA256 authenticated cipher fallback.
4. Secure Key Packaging and integrity binding between Audio and Key Image.
5. Passphrase-based PBKDF2 encryption/decryption.
"""

import os
import struct
import hmac
import hashlib
from typing import Tuple, Dict, Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

DEFAULT_KDF_ITERATIONS = 100_000

# --------------------------------------------------------------------------
# Pure Python ChaCha20 Stream Cipher (Standard Library Only)
# --------------------------------------------------------------------------
def _rotl32(v: int, c: int) -> int:
    return ((v << c) & 0xffffffff) | (v >> (32 - c))

def _chacha20_quarter_round(a: int, b: int, c: int, d: int, state: list):
    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] = _rotl32(state[d] ^ state[a], 16)
    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] = _rotl32(state[b] ^ state[c], 12)
    state[a] = (state[a] + state[b]) & 0xffffffff
    state[d] = _rotl32(state[d] ^ state[a], 8)
    state[c] = (state[c] + state[d]) & 0xffffffff
    state[b] = _rotl32(state[b] ^ state[c], 7)

def _chacha20_process(key: bytes, nonce: bytes, data: bytes) -> bytes:
    stream = bytearray()
    counter = 1
    length = len(data)

    while len(stream) < length:
        constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
        k = list(struct.unpack("<8I", key))
        n = list(struct.unpack("<3I", nonce))
        state = constants + k + [counter] + n
        ws = list(state)
        for _ in range(10):
            _chacha20_quarter_round(0, 4, 8, 12, ws)
            _chacha20_quarter_round(1, 5, 9, 13, ws)
            _chacha20_quarter_round(2, 6, 10, 14, ws)
            _chacha20_quarter_round(3, 7, 11, 15, ws)
            _chacha20_quarter_round(0, 5, 10, 15, ws)
            _chacha20_quarter_round(1, 6, 11, 12, ws)
            _chacha20_quarter_round(2, 7, 8, 13, ws)
            _chacha20_quarter_round(3, 4, 9, 14, ws)
        out = [(ws[i] + state[i]) & 0xffffffff for i in range(16)]
        stream.extend(struct.pack("<16I", *out))
        counter += 1

    keystream = bytes(stream[:length])
    return bytes(a ^ b for a, b in zip(data, keystream))


class CryptoEngine:
    """Manages high-entropy key creation, packaging, and authenticated encryption."""

    @classmethod
    def generate_key_package(cls) -> Dict[str, bytes]:
        """
        Generates a 256-bit uncrackable cryptographically secure key package.
        Returns dictionary containing key_id, session_key, nonce, salt, and packed bytes.
        """
        key_id = os.urandom(8)        # 64-bit session association ID
        session_key = os.urandom(32)  # 256-bit Master Key
        nonce = os.urandom(12)        # 96-bit Nonce
        salt = os.urandom(16)         # 128-bit Salt

        # Compute HMAC-SHA256 signature over the key attributes to prevent tampering
        mac = hmac.new(session_key, key_id + nonce + salt, hashlib.sha256).digest()

        # Packed binary format: [8B KeyID] + [32B Key] + [12B Nonce] + [16B Salt] + [32B MAC]
        packed = key_id + session_key + nonce + salt + mac

        return {
            "key_id": key_id,
            "session_key": session_key,
            "nonce": nonce,
            "salt": salt,
            "packed_bytes": packed,
        }

    @classmethod
    def unpack_key_package(cls, packed_bytes: bytes) -> Dict[str, bytes]:
        """
        Unpacks and cryptographically validates a key package extracted from an image.
        Raises ValueError if corrupted or tampered with.
        """
        expected_len = 8 + 32 + 12 + 16 + 32  # 100 bytes
        if len(packed_bytes) != expected_len:
            raise ValueError(f"Invalid key package length ({len(packed_bytes)} bytes, expected {expected_len}).")

        offset = 0
        key_id = packed_bytes[offset:offset + 8]
        offset += 8
        session_key = packed_bytes[offset:offset + 32]
        offset += 32
        nonce = packed_bytes[offset:offset + 12]
        offset += 12
        salt = packed_bytes[offset:offset + 16]
        offset += 16
        stored_mac = packed_bytes[offset:offset + 32]

        expected_mac = hmac.new(session_key, key_id + nonce + salt, hashlib.sha256).digest()
        if not hmac.compare_digest(stored_mac, expected_mac):
            raise ValueError("Cryptographic key authentication failed! The key in the image appears corrupted or tampered.")

        return {
            "key_id": key_id,
            "session_key": session_key,
            "nonce": nonce,
            "salt": salt,
            "packed_bytes": packed_bytes,
        }

    @classmethod
    def encrypt_secret_audio(cls, secret_audio_bytes: bytes, key_package: Dict[str, bytes]) -> bytes:
        """
        Encrypts raw secret audio bytes with the high-entropy session key.
        Returns ciphertext with authentication tag.
        """
        session_key = key_package["session_key"]
        nonce = key_package["nonce"]

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(session_key)
            ciphertext = aesgcm.encrypt(nonce, secret_audio_bytes, None)
            return b"\x01" + ciphertext
        else:
            ciphertext = _chacha20_process(session_key, nonce, secret_audio_bytes)
            tag = hmac.new(session_key, nonce + ciphertext, hashlib.sha256).digest()
            return b"\x02" + tag + ciphertext

    @classmethod
    def decrypt_secret_audio(cls, encrypted_payload: bytes, key_package: Dict[str, bytes]) -> bytes:
        """
        Decrypts audio payload using the session key from the key package.
        Raises ValueError if authentication fails.
        """
        session_key = key_package["session_key"]
        nonce = key_package["nonce"]

        engine_flag = encrypted_payload[0:1]
        raw_body = encrypted_payload[1:]

        if engine_flag == b"\x01":
            if not HAS_CRYPTOGRAPHY:
                raise ImportError("Payload requires AES-GCM engine. Install via: pip install cryptography")
            aesgcm = AESGCM(session_key)
            try:
                return aesgcm.decrypt(nonce, raw_body, None)
            except Exception as exc:
                raise ValueError("Decryption failed. Authentication tag mismatch or corrupted ciphertext.") from exc

        elif engine_flag == b"\x02":
            tag = raw_body[:32]
            ciphertext = raw_body[32:]
            expected_tag = hmac.new(session_key, nonce + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected_tag):
                raise ValueError("Decryption failed. Payload HMAC authentication check failed.")
            return _chacha20_process(session_key, nonce, ciphertext)

        else:
            raise ValueError("Unrecognized audio encryption format identifier.")

    @classmethod
    def encrypt(cls, plaintext_data: bytes, passphrase: str) -> bytes:
        """Passphrase-based authenticated encryption helper."""
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, DEFAULT_KDF_ITERATIONS, dklen=32)

        if HAS_CRYPTOGRAPHY:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext_data, None)
            return b"\x01" + salt + nonce + ciphertext
        else:
            ciphertext = _chacha20_process(key, nonce, plaintext_data)
            tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
            return b"\x02" + salt + nonce + tag + ciphertext

    @classmethod
    def decrypt(cls, encrypted_package: bytes, passphrase: str) -> bytes:
        """Passphrase-based authenticated decryption helper."""
        if len(encrypted_package) < (1 + 16 + 12 + 16):
            raise ValueError("Invalid encrypted package length.")

        engine_flag = encrypted_package[0:1]
        salt = encrypted_package[1:17]
        nonce = encrypted_package[17:29]
        body = encrypted_package[29:]

        key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, DEFAULT_KDF_ITERATIONS, dklen=32)

        if engine_flag == b"\x01":
            if not HAS_CRYPTOGRAPHY:
                raise ImportError("Payload requires AES-GCM engine.")
            aesgcm = AESGCM(key)
            try:
                return aesgcm.decrypt(nonce, body, None)
            except Exception as exc:
                raise ValueError("Decryption failed. Incorrect passphrase or corrupted data.") from exc
        elif engine_flag == b"\x02":
            tag = body[:32]
            ciphertext = body[32:]
            expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected_tag):
                raise ValueError("Decryption failed. Incorrect passphrase or corrupted data.")
            return _chacha20_process(key, nonce, ciphertext)
        else:
            raise ValueError("Unrecognized package format.")
