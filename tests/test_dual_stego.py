"""Comprehensive Unit Tests for Dual-Carrier Steganography (Audio + Image)."""

import unittest
import os
import sys
import wave
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.crypto import CryptoEngine
from core.steganography import AudioSteganography
from core.image_steganography import ImageSteganography

class TestDualCarrierStego(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.carrier_audio = os.path.join(self.temp_dir, "test_carrier.wav")
        self.cover_image = os.path.join(self.temp_dir, "test_cover.png")
        self.stego_audio = os.path.join(self.temp_dir, "test_stego.wav")
        self.stego_image = os.path.join(self.temp_dir, "test_stego.png")

        # Create dummy carrier WAV (0.5 sec stereo 44.1kHz = 44100 samples)
        sample_rate = 44100
        frames = bytearray(sample_rate * 2)
        for i in range(len(frames)):
            frames[i] = (i * 3) % 256

        with wave.open(self.carrier_audio, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(frames))

        # Create dummy cover PNG (120x120)
        ImageSteganography.create_sample_cover_png(self.cover_image, width=120, height=120)

    def tearDown(self):
        for f in [self.carrier_audio, self.cover_image, self.stego_audio, self.stego_image]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_key_package_packaging(self):
        pkg = CryptoEngine.generate_key_package()
        self.assertEqual(len(pkg["session_key"]), 32)
        self.assertEqual(len(pkg["key_id"]), 8)

        unpacked = CryptoEngine.unpack_key_package(pkg["packed_bytes"])
        self.assertEqual(pkg["session_key"], unpacked["session_key"])
        self.assertEqual(pkg["key_id"], unpacked["key_id"])

    def test_full_dual_stego_workflow(self):
        # 1. Secret Audio Simulation
        secret_audio_bytes = b"ID3v2.3.0Simulated_MP3_Frame_Data_Stream_1234567890abcdefghijklmnopqrstuvwxyz" * 10
        original_ext = ".mp3"

        # 2. Key Generation
        key_package = CryptoEngine.generate_key_package()

        # 3. Encrypt Secret Audio
        encrypted_audio = CryptoEngine.encrypt_secret_audio(secret_audio_bytes, key_package)

        # 4. Steg Encrypted Audio into Carrier Song
        AudioSteganography.embed_data(
            carrier_wav_path=self.carrier_audio,
            secret_bytes=encrypted_audio,
            file_extension=original_ext,
            output_wav_path=self.stego_audio,
            key_id=key_package["key_id"],
        )

        # 5. Steg Cryptographic Key into Cover Image
        ImageSteganography.embed_key_in_image_file(
            input_image_path=self.cover_image,
            key_payload=key_package["packed_bytes"],
            output_image_path=self.stego_image,
        )

        self.assertTrue(os.path.exists(self.stego_audio))
        self.assertTrue(os.path.exists(self.stego_image))

        # --- REVERSE EXTRACTION & DECRYPTION ---
        # 6. Extract Key from Image
        extracted_key_raw = ImageSteganography.extract_key_from_image_file(self.stego_image)
        recovered_key_package = CryptoEngine.unpack_key_package(extracted_key_raw)

        # 7. Extract Encrypted Audio from Stego Song
        audio_key_id, extracted_payload, extracted_ext = AudioSteganography.extract_data(self.stego_audio)

        # 8. Cryptographic Binding Check
        self.assertEqual(audio_key_id, recovered_key_package["key_id"])
        self.assertEqual(extracted_ext, original_ext)

        # 9. Decrypt Audio
        decrypted_secret_audio = CryptoEngine.decrypt_secret_audio(extracted_payload, recovered_key_package)

        # 10. Assert Bit-for-bit Equality
        self.assertEqual(secret_audio_bytes, decrypted_secret_audio)

if __name__ == "__main__":
    unittest.main()
