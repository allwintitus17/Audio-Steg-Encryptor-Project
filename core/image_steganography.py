"""Image Steganography Engine: LSB embedding and extraction for PNG and BMP images.

Implemented entirely with Python standard library (zlib, struct).
Zero external dependencies required (no PIL / Pillow required).
"""

import os
import zlib
import struct
from typing import Tuple, Optional

# Magic header for key package embedded in image
IMAGE_STEGO_MAGIC = b"IMGK"

class ImageSteganography:
    """Embeds and extracts binary key packages into PNG and BMP images."""

    @staticmethod
    def create_sample_cover_png(output_path: str, width: int = 250, height: int = 250) -> str:
        """
        Generates a synthetic elegant gradient cover PNG image.
        Useful when the user does not have a cover image ready.
        """
        raw_data = bytearray()
        for y in range(height):
            raw_data.append(0)  # Filter type 0 (None)
            for x in range(width):
                r = int((x / width) * 180 + 30)
                g = int((y / height) * 160 + 40)
                b = int(((x + y) / (width + height)) * 220 + 35)
                raw_data.extend([r, g, b])

        compressed = zlib.compress(bytes(raw_data), level=6)

        def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            crc = zlib.crc32(chunk_type + data)
            return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

        png_header = b"\x89PNG\r\n\x1a\n"
        ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        png_content = (
            png_header
            + make_chunk(b"IHDR", ihdr)
            + make_chunk(b"IDAT", compressed)
            + make_chunk(b"IEND", b"")
        )

        with open(output_path, "wb") as f:
            f.write(png_content)

        return output_path

    @classmethod
    def embed_key_in_png(cls, png_bytes: bytes, key_payload: bytes) -> bytes:
        """Embeds key payload into PNG pixel scanlines using LSB."""
        if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG file signature.")

        idx = 8
        chunks = []
        idat_parts = []
        ihdr_info = None

        while idx < len(png_bytes):
            if idx + 8 > len(png_bytes):
                break
            length = struct.unpack(">I", png_bytes[idx:idx + 4])[0]
            ctype = png_bytes[idx + 4:idx + 8]
            cdata = png_bytes[idx + 8:idx + 8 + length]
            idx += 12 + length

            if ctype == b"IHDR":
                ihdr_info = cdata
                chunks.append((ctype, cdata))
            elif ctype == b"IDAT":
                idat_parts.append(cdata)
            elif ctype == b"IEND":
                break
            else:
                chunks.append((ctype, cdata))

        if not ihdr_info or not idat_parts:
            raise ValueError("Malformed PNG structure.")

        decompressed = bytearray(zlib.decompress(b"".join(idat_parts)))
        width, height, bit_depth, color_type = struct.unpack(">IIBB", ihdr_info[:10])

        if bit_depth != 8:
            raise ValueError("Only 8-bit depth PNG images are supported for steganography.")

        # Bytes per pixel based on color type
        if color_type == 2:    # Truecolor RGB
            bpp = 3
        elif color_type == 6:  # Truecolor with Alpha RGBA
            bpp = 4
        elif color_type == 0:  # Grayscale
            bpp = 1
        else:
            raise ValueError(f"PNG color type {color_type} not supported. Use RGB or RGBA.")

        stride = 1 + (width * bpp)

        # Build packet: [4B Magic 'IMGK'] + [4B Len] + [Payload]
        packet = IMAGE_STEGO_MAGIC + struct.pack(">I", len(key_payload)) + key_payload
        packet_bits = []
        for byte_val in packet:
            for shift in range(7, -1, -1):
                packet_bits.append((byte_val >> shift) & 1)

        total_bits = len(packet_bits)
        available_bits = height * (width * bpp)

        if total_bits > available_bits:
            raise ValueError(
                f"Image is too small to embed key ({total_bits} bits needed, {available_bits} available)."
            )

        bit_idx = 0
        for y in range(height):
            row_offset = y * stride
            # Skip byte 0 of scanline (PNG row filter type)
            for x in range(1, stride):
                if bit_idx >= total_bits:
                    break
                decompressed[row_offset + x] = (decompressed[row_offset + x] & ~1) | packet_bits[bit_idx]
                bit_idx += 1
            if bit_idx >= total_bits:
                break

        # Recompress IDAT
        new_idat = zlib.compress(bytes(decompressed), level=6)

        # Reassemble PNG
        out = bytearray(b"\x89PNG\r\n\x1a\n")
        idat_written = False
        for ctype, cdata in chunks:
            crc = zlib.crc32(ctype + cdata)
            out.extend(struct.pack(">I", len(cdata)) + ctype + cdata + struct.pack(">I", crc))
            if ctype == b"IHDR" and not idat_written:
                crc_idat = zlib.crc32(b"IDAT" + new_idat)
                out.extend(struct.pack(">I", len(new_idat)) + b"IDAT" + new_idat + struct.pack(">I", crc_idat))
                idat_written = True

        out.extend(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND")))
        return bytes(out)

    @classmethod
    def extract_key_from_png(cls, png_bytes: bytes) -> bytes:
        """Extracts key payload from PNG pixel scanlines."""
        if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG file signature.")

        idx = 8
        idat_parts = []
        ihdr_info = None

        while idx < len(png_bytes):
            if idx + 8 > len(png_bytes):
                break
            length = struct.unpack(">I", png_bytes[idx:idx + 4])[0]
            ctype = png_bytes[idx + 4:idx + 8]
            cdata = png_bytes[idx + 8:idx + 8 + length]
            idx += 12 + length

            if ctype == b"IHDR":
                ihdr_info = cdata
            elif ctype == b"IDAT":
                idat_parts.append(cdata)
            elif ctype == b"IEND":
                break

        if not ihdr_info or not idat_parts:
            raise ValueError("Malformed PNG structure.")

        decompressed = zlib.decompress(b"".join(idat_parts))
        width, height, bit_depth, color_type = struct.unpack(">IIBB", ihdr_info[:10])

        bpp = 3 if color_type == 2 else 4 if color_type == 6 else 1
        stride = 1 + (width * bpp)

        def bit_generator():
            for y in range(height):
                row_offset = y * stride
                for x in range(1, stride):
                    yield decompressed[row_offset + x] & 1

        bit_gen = bit_generator()

        def read_bytes(count: int) -> bytes:
            buf = bytearray(count)
            for i in range(count):
                val = 0
                for _ in range(8):
                    try:
                        val = (val << 1) | next(bit_gen)
                    except StopIteration:
                        raise ValueError("Unexpected end of image stream.")
                buf[i] = val
            return bytes(buf)

        # Verify magic header
        magic = read_bytes(4)
        if magic != IMAGE_STEGO_MAGIC:
            raise ValueError("No cryptographic key steganography signature found in this image.")

        length = struct.unpack(">I", read_bytes(4))[0]
        if length <= 0 or length > 65536:
            raise ValueError(f"Invalid key payload length header ({length} bytes).")

        return read_bytes(length)

    @classmethod
    def embed_key_in_image_file(cls, input_image_path: str, key_payload: bytes, output_image_path: str) -> None:
        """Loads an image file, embeds key payload, and writes out the stego image."""
        ext = os.path.splitext(input_image_path)[1].lower()
        with open(input_image_path, "rb") as f:
            data = f.read()

        if ext == ".png":
            stego_data = cls.embed_key_in_png(data, key_payload)
        elif ext == ".bmp":
            stego_data = cls._embed_key_in_bmp(data, key_payload)
        else:
            raise ValueError(f"Unsupported image format: '{ext}'. Please provide a lossless .png or .bmp image.")

        with open(output_image_path, "wb") as f:
            f.write(stego_data)

    @classmethod
    def extract_key_from_image_file(cls, stego_image_path: str) -> bytes:
        """Extracts key payload from an image file (.png or .bmp)."""
        ext = os.path.splitext(stego_image_path)[1].lower()
        with open(stego_image_path, "rb") as f:
            data = f.read()

        if ext == ".png":
            return cls.extract_key_from_png(data)
        elif ext == ".bmp":
            return cls._extract_key_from_bmp(data)
        else:
            raise ValueError(f"Unsupported image format: '{ext}'. Expected .png or .bmp.")

    @staticmethod
    def _embed_key_in_bmp(bmp_bytes: bytes, key_payload: bytes) -> bytes:
        if bmp_bytes[:2] != b"BM":
            raise ValueError("Invalid BMP file signature.")
        pixel_offset = struct.unpack("<I", bmp_bytes[10:14])[0]
        header = bmp_bytes[:pixel_offset]
        pixels = bytearray(bmp_bytes[pixel_offset:])

        packet = IMAGE_STEGO_MAGIC + struct.pack(">I", len(key_payload)) + key_payload
        packet_bits = []
        for b in packet:
            for s in range(7, -1, -1):
                packet_bits.append((b >> s) & 1)

        if len(packet_bits) > len(pixels):
            raise ValueError("BMP image is too small to embed key payload.")

        for i, bit in enumerate(packet_bits):
            pixels[i] = (pixels[i] & ~1) | bit

        return header + bytes(pixels)

    @staticmethod
    def _extract_key_from_bmp(bmp_bytes: bytes) -> bytes:
        if bmp_bytes[:2] != b"BM":
            raise ValueError("Invalid BMP file signature.")
        pixel_offset = struct.unpack("<I", bmp_bytes[10:14])[0]
        pixels = bmp_bytes[pixel_offset:]

        def bit_generator():
            for byte in pixels:
                yield byte & 1

        bit_gen = bit_generator()
        def read_bytes(count: int) -> bytes:
            buf = bytearray(count)
            for i in range(count):
                val = 0
                for _ in range(8):
                    val = (val << 1) | next(bit_gen)
                buf[i] = val
            return bytes(buf)

        magic = read_bytes(4)
        if magic != IMAGE_STEGO_MAGIC:
            raise ValueError("No cryptographic key signature found in this BMP image.")

        length = struct.unpack(">I", read_bytes(4))[0]
        return read_bytes(length)
