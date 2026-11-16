"""Validation utilities for user inputs, files, and capacities."""

import os
from typing import Tuple, Optional
from core.audio_handler import AudioHandler

class Validator:
    """Validates files, carrier capacities, and format compatibility."""

    @staticmethod
    def validate_embedding_suitability(carrier_path: str, secret_path: str) -> Tuple[bool, Optional[str]]:
        """Checks if carrier audio has sufficient capacity to store the secret audio."""
        if not os.path.exists(carrier_path):
            return False, "Carrier audio file does not exist."
        if not os.path.exists(secret_path):
            return False, "Secret audio file does not exist."

        carrier_info = AudioHandler.inspect_audio_file(carrier_path)
        if not carrier_info.get("is_valid_wav"):
            ext = carrier_info.get("extension", "")
            return False, (
                f"Selected carrier file format '{ext}' is not supported as a carrier song!\n\n"
                f"Carrier songs MUST be uncompressed WAV audio (.wav) so hidden data is not corrupted by lossy audio compression (like AAC/MP3).\n\n"
                f"Tip: Click the '✨ Auto-Generate Carrier WAV' button in Step 2 to generate an optimized carrier song instantly!"
            )

        secret_size = os.path.getsize(secret_path)
        # Overhead: 100B key ID/metadata
        estimated_payload = secret_size + 100

        # Maximum capacity with 4 bits/sample
        max_4bit_capacity = AudioHandler.calculate_embedding_capacity(carrier_path, bits_per_sample=4)

        if estimated_payload > max_4bit_capacity:
            return False, (
                f"Secret file ({secret_size:,} bytes) is too large for the selected carrier song!\n"
                f"Maximum safe capacity of this song: {max_4bit_capacity:,} bytes.\n"
                f"Please select a longer carrier song or compress your secret audio."
            )

        return True, None

    @staticmethod
    def validate_image_file(image_path: str) -> Tuple[bool, Optional[str]]:
        """Checks if image exists and is a supported lossless format (PNG or BMP)."""
        if not os.path.exists(image_path):
            return False, f"Image file not found: {image_path}"
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in [".png", ".bmp"]:
            return False, (
                f"Cover Image must be a lossless format (.png or .bmp), got: '{ext}'.\n"
                f"Lossy JPEG images corrupt hidden data. Click '✨ Auto-Generate Image' to create one automatically."
            )
        return True, None
