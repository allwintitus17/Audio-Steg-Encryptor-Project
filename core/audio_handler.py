"""Audio Handler: Reads, inspects, and processes WAV and compressed audio files."""

import os
import wave
import math
import struct
from typing import Dict, Any, Tuple

class AudioHandler:
    """Manages audio file I/O, format extraction, and sample conversions."""

    @staticmethod
    def inspect_audio_file(file_path: str) -> Dict[str, Any]:
        """Reads audio metadata such as sample rate, channels, bit depth, and duration."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        info = {
            "path": file_path,
            "filename": os.path.basename(file_path),
            "size_bytes": file_size,
            "extension": ext,
            "channels": None,
            "sample_rate": None,
            "bit_depth": None,
            "total_samples": None,
            "duration_sec": 0.0,
            "is_valid_wav": False,
        }

        if ext == ".wav":
            try:
                with wave.open(file_path, "rb") as wf:
                    info["channels"] = wf.getnchannels()
                    info["sample_rate"] = wf.getframerate()
                    info["bit_depth"] = wf.getsampwidth() * 8
                    total_frames = wf.getnframes()
                    info["total_samples"] = total_frames * info["channels"]
                    info["duration_sec"] = total_frames / float(info["sample_rate"]) if info["sample_rate"] else 0.0
                    info["is_valid_wav"] = True
            except Exception:
                info["is_valid_wav"] = False
        else:
            # Compressed formats like .m4a, .mp3
            info["is_valid_wav"] = False

        return info

    @staticmethod
    def calculate_embedding_capacity(carrier_path: str, bits_per_sample: int = 1) -> int:
        """
        Calculates maximum hidden payload capacity in bytes for a given carrier audio.
        Formula: (Total Samples * bits_per_sample) // 8
        """
        info = AudioHandler.inspect_audio_file(carrier_path)
        if info["total_samples"]:
            total_bits = info["total_samples"] * bits_per_sample
            return total_bits // 8
        return 0

    @staticmethod
    def read_wav_raw_frames(wav_path: str) -> Tuple[bytes, wave._wave_params]:
        """Reads raw PCM audio frames and returns parameters for reconstructing."""
        with wave.open(wav_path, "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(wf.getnframes())
            return frames, params

    @staticmethod
    def write_wav_raw_frames(output_path: str, frames: bytes, params: wave._wave_params) -> None:
        """Writes modified raw PCM frames back into a valid WAV file."""
        with wave.open(output_path, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(frames)

    @staticmethod
    def create_sample_carrier_wav(output_path: str, duration_sec: int = 180) -> str:
        """
        Generates a synthetic pleasant acoustic harmonic stereo WAV carrier song.
        Provides high embedding capacity (~8MB+) in standard uncompressed PCM format.
        """
        sample_rate = 44100
        channels = 2
        total_frames = int(sample_rate * duration_sec)

        # Generate a soothing harmonic progression (A4 440Hz, C#5 554Hz, E5 659Hz chords)
        frequencies = [440.0, 554.37, 659.25, 329.63]
        frames = bytearray()

        for i in range(total_frames):
            t = float(i) / sample_rate
            chord_idx = int(t / 4.0) % len(frequencies)
            base_freq = frequencies[chord_idx]

            # Harmonic synthesis with soft envelope
            envelope = 0.5 + 0.3 * math.sin(2 * math.pi * 0.25 * t)
            left_val = envelope * (
                0.5 * math.sin(2 * math.pi * base_freq * t)
                + 0.3 * math.sin(2 * math.pi * base_freq * 1.5 * t)
            )
            right_val = envelope * (
                0.5 * math.sin(2 * math.pi * base_freq * 1.25 * t)
                + 0.3 * math.sin(2 * math.pi * base_freq * 2.0 * t)
            )

            # Convert to 16-bit signed integer (-32767 to +32767)
            left_int = int(max(-32767, min(32767, left_val * 24000)))
            right_int = int(max(-32767, min(32767, right_val * 24000)))

            frames.extend(struct.pack("<hh", left_int, right_int))

        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(frames))

        return output_path
