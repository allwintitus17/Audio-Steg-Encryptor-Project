"""Unit tests for LSB Audio Steganography engine."""

import unittest
import os
import sys
import wave
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.steganography import AudioSteganography

class TestSteganography(unittest.TestCase):

    def setUp(self):
        # Create a temporary synthetic 16-bit 44.1kHz stereo WAV carrier (0.5 sec)
        self.temp_dir = tempfile.mkdtemp()
        self.carrier_path = os.path.join(self.temp_dir, "test_carrier.wav")
        self.stego_path = os.path.join(self.temp_dir, "test_stego.wav")

        sample_rate = 44100
        num_samples = sample_rate // 2  # 0.5 second = 22050 samples per channel
        # 2 channels, 16-bit = 4 bytes per frame => 88,200 bytes total
        raw_frames = bytearray(num_samples * 4)
        # Fill with a dummy ramp pattern
        for i in range(len(raw_frames)):
            raw_frames[i] = (i * 7) % 256

        with wave.open(self.carrier_path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(raw_frames))

    def tearDown(self):
        for f in [self.carrier_path, self.stego_path]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_embed_and_extract(self):
        secret_payload = b"Sample hidden binary audio stream data!"
        original_ext = ".mp3"

        embedded_count = AudioSteganography.embed_data(
            carrier_wav_path=self.carrier_path,
            secret_bytes=secret_payload,
            file_extension=original_ext,
            output_wav_path=self.stego_path
        )
        self.assertGreater(embedded_count, 0)
        self.assertTrue(os.path.exists(self.stego_path))

        # Extract
        _, extracted_data, extracted_ext = AudioSteganography.extract_data(self.stego_path)
        self.assertEqual(secret_payload, extracted_data)
        self.assertEqual(original_ext, extracted_ext)

if __name__ == "__main__":
    unittest.main()
