"""Steganography Engine: Multi-Bit Adaptive LSB Audio Embedding and Extraction."""

import struct
from typing import Tuple
from utils.config import STEGO_MAGIC_HEADER
from core.audio_handler import AudioHandler

class AudioSteganography:
    """Handles embedding and extraction of binary payloads into uncompressed WAV audio."""

    @classmethod
    def determine_optimal_bits_per_sample(cls, carrier_total_samples: int, payload_size_bytes: int) -> int:
        """
        Determines the lowest bit depth (1 to 4 bits per sample) needed to store the payload.
        Returns 1, 2, 3, or 4.
        """
        header_reserve = 300  # samples reserved for fixed 1-bit bootstrap header
        available = carrier_total_samples - header_reserve
        if available <= 0:
            raise ValueError("Carrier audio is too short to store any steganographic payload.")

        payload_bits = payload_size_bytes * 8
        for b in (1, 2, 3, 4):
            if payload_bits <= (available * b):
                return b

        max_capacity_bytes = (available * 4) // 8
        raise ValueError(
            f"Secret audio payload ({payload_size_bytes:,} bytes) exceeds maximum 4-bit carrier capacity "
            f"({max_capacity_bytes:,} bytes). Please use a longer carrier song or compress the secret audio."
        )

    @classmethod
    def embed_data(
        cls,
        carrier_wav_path: str,
        secret_bytes: bytes,
        file_extension: str,
        output_wav_path: str,
        key_id: bytes = b"\x00" * 8,
        bits_per_sample: int = 0  # 0 = Auto-detect optimal bit depth (1 to 4)
    ) -> int:
        """
        Embeds secret data into the carrier audio file using adaptive LSB.
        Bootstrap header is stored at 1 bit/sample so extraction is automatic.
        """
        frames, params = AudioHandler.read_wav_raw_frames(carrier_wav_path)
        frame_bytes = bytearray(frames)
        sampwidth = params.sampwidth
        total_samples = len(frame_bytes) // sampwidth

        if len(key_id) != 8:
            key_id = (key_id + b"\x00" * 8)[:8]

        ext_bytes = file_extension.lower().encode("utf-8")
        ext_len = len(ext_bytes)
        payload_len = len(secret_bytes)

        # Auto-calculate optimal bit depth if not specified
        if bits_per_sample <= 0 or bits_per_sample > 4:
            bits_per_sample = cls.determine_optimal_bits_per_sample(total_samples, payload_len)

        # 1. Build Bootstrap Header (embedded strictly at 1-bit/sample)
        # Format: [4B Magic 'ASTG'] + [8B Key ID] + [1B BitsPerSample] + [1B Ext Len] + [Ext Bytes] + [4B PayloadLen]
        header = (
            STEGO_MAGIC_HEADER
            + key_id
            + struct.pack(">BB", bits_per_sample, ext_len)
            + ext_bytes
            + struct.pack(">I", payload_len)
        )

        header_bits = []
        for b in header:
            for s in range(7, -1, -1):
                header_bits.append((b >> s) & 1)

        header_sample_count = len(header_bits)
        if header_sample_count >= total_samples:
            raise ValueError("Carrier audio is too short to store steganographic metadata.")

        # Embed header bits into the least significant bit of each sample
        for i, bit in enumerate(header_bits):
            offset = i * sampwidth
            frame_bytes[offset] = (frame_bytes[offset] & ~1) | bit

        # 2. Embed payload at chosen bits_per_sample (1 to 4)
        mask = (1 << bits_per_sample) - 1
        total_payload_bits = payload_len * 8
        chunks = []

        for i in range(0, total_payload_bits, bits_per_sample):
            val = 0
            for b in range(bits_per_sample):
                idx = i + b
                if idx < total_payload_bits:
                    byte_pos = idx // 8
                    shift = 7 - (idx % 8)
                    val = (val << 1) | ((secret_bytes[byte_pos] >> shift) & 1)
                else:
                    val = val << 1
            chunks.append(val)

        if (header_sample_count + len(chunks)) > total_samples:
            raise ValueError(
                f"Carrier audio has insufficient capacity ({total_samples} samples) for payload chunks ({header_sample_count + len(chunks)} required)."
            )

        for i, chunk in enumerate(chunks):
            offset = (header_sample_count + i) * sampwidth
            frame_bytes[offset] = (frame_bytes[offset] & ~mask) | chunk

        AudioHandler.write_wav_raw_frames(output_wav_path, bytes(frame_bytes), params)
        return payload_len

    @classmethod
    def extract_data(cls, stego_wav_path: str) -> Tuple[bytes, bytes, str]:
        """
        Extracts key association ID, encrypted audio payload, and original file extension.
        Returns (key_id, payload_bytes, file_extension).
        """
        frames, params = AudioHandler.read_wav_raw_frames(stego_wav_path)
        frame_bytes = frames
        sampwidth = params.sampwidth
        total_samples = len(frame_bytes) // sampwidth

        def read_1bit_bytes(count: int, sample_offset: int = 0) -> bytes:
            buf = bytearray(count)
            for i in range(count):
                val = 0
                for b in range(8):
                    sample_idx = sample_offset + (i * 8) + b
                    if sample_idx >= total_samples:
                        raise ValueError("Stego audio ended prematurely while reading header.")
                    byte_offset = sample_idx * sampwidth
                    val = (val << 1) | (frame_bytes[byte_offset] & 1)
                buf[i] = val
            return bytes(buf)

        # 1. Read Magic Header (4 bytes)
        magic = read_1bit_bytes(4, sample_offset=0)
        if magic != STEGO_MAGIC_HEADER:
            raise ValueError("No hidden steganography signature detected in this audio file.")

        # 2. Read Key ID (8 bytes)
        key_id = read_1bit_bytes(8, sample_offset=4 * 8)

        # 3. Read BitsPerSample (1 byte) and Ext Length (1 byte)
        meta = read_1bit_bytes(2, sample_offset=12 * 8)
        bits_per_sample, ext_len = struct.unpack(">BB", meta)
        if bits_per_sample < 1 or bits_per_sample > 4:
            raise ValueError(f"Corrupted stego header: invalid bit depth ({bits_per_sample}).")

        # 4. Read File Extension
        ext_bytes = read_1bit_bytes(ext_len, sample_offset=14 * 8)
        file_ext = ext_bytes.decode("utf-8", errors="ignore")

        # 5. Read Payload Length (4 bytes)
        payload_len_offset = (14 + ext_len) * 8
        payload_len_bytes = read_1bit_bytes(4, sample_offset=payload_len_offset)
        payload_len = struct.unpack(">I", payload_len_bytes)[0]

        # 6. Extract payload at bits_per_sample
        header_sample_count = (14 + ext_len + 4) * 8
        mask = (1 << bits_per_sample) - 1
        total_bits = payload_len * 8
        chunks_needed = (total_bits + bits_per_sample - 1) // bits_per_sample

        if (header_sample_count + chunks_needed) > total_samples:
            raise ValueError("Stego audio file is truncated or corrupted.")

        bit_chunks = [
            frame_bytes[(header_sample_count + i) * sampwidth] & mask
            for i in range(chunks_needed)
        ]

        out = bytearray(payload_len)
        curr_byte = 0
        bits_in_curr = 0
        byte_idx = 0

        for chunk in bit_chunks:
            for s in range(bits_per_sample - 1, -1, -1):
                if byte_idx < payload_len:
                    bit_val = (chunk >> s) & 1
                    curr_byte = (curr_byte << 1) | bit_val
                    bits_in_curr += 1
                    if bits_in_curr == 8:
                        out[byte_idx] = curr_byte
                        byte_idx += 1
                        curr_byte = 0
                        bits_in_curr = 0

        return key_id, bytes(out), file_ext
