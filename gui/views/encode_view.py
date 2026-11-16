"""Encode View: Responsive scrollable layout with fixed bottom action toolbar.
Encrypts secret audio with an uncrackable key, stego-embeds it into a song,
and stego-embeds the cryptographic key into an image.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

from utils.config import (
    SUPPORTED_CARRIER_FORMATS,
    SUPPORTED_SECRET_FORMATS,
    SUPPORTED_IMAGE_FORMATS,
)
from utils.threading_utils import run_async
from gui.styles import COLORS
from gui.components.file_picker import FilePicker
from gui.components.audio_player import AudioPlayer
from core.crypto import CryptoEngine, HAS_CRYPTOGRAPHY
from core.steganography import AudioSteganography
from core.image_steganography import ImageSteganography
from core.audio_handler import AudioHandler
from core.validator import Validator

class EncodeView(ttk.Frame):
    """View orchestrating: Secret Audio -> Key Generation -> Song Steganography -> Image Key Steganography."""

    def __init__(self, master, **kwargs):
        super().__init__(master, style="Main.TFrame", **kwargs)
        self._build_ui()

    def _build_ui(self):
        # -------------------------------------------------------------
        # 1. FIXED BOTTOM ACTION TOOLBAR (Always visible, never clipped)
        # -------------------------------------------------------------
        self.bottom_bar = ttk.Frame(self, style="Card.TFrame", relief="solid", borderwidth=1)
        self.bottom_bar.pack(side="bottom", fill="x", padx=10, pady=(4, 8), ipady=6)

        btn_row = ttk.Frame(self.bottom_bar, style="Card.TFrame")
        btn_row.pack(fill="x", padx=10, pady=(4, 2))

        self.btn_process = ttk.Button(
            btn_row,
            text="🔒 Generate Key, Encrypt Audio & Embed Both",
            command=self._start_pipeline,
            style="Action.TButton",
        )
        self.btn_process.pack(side="left", padx=(0, 10))

        engine_name = "AES-256-GCM" if HAS_CRYPTOGRAPHY else "ChaCha20-Poly1305 (Pure Python)"
        self.status_label = ttk.Label(btn_row, text=f"Ready | Cipher: {engine_name}", style="Card.TLabel")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.progress_bar = ttk.Progressbar(self.bottom_bar, mode="indeterminate")

        # -------------------------------------------------------------
        # 2. SCROLLABLE CANVAS FOR FORM STEPS
        # -------------------------------------------------------------
        canvas_container = ttk.Frame(self, style="Main.TFrame")
        canvas_container.pack(side="top", fill="both", expand=True, padx=5, pady=2)

        self.canvas = tk.Canvas(canvas_container, bg=COLORS["bg_main"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        self.scroll_content = ttk.Frame(self.canvas, style="Main.TFrame")

        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfig(self.canvas_window, width=event.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Mousewheel scroll binding
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # -------------------------------------------------------------
        # STEP 1: Secret Audio
        # -------------------------------------------------------------
        self.secret_picker = FilePicker(
            self.scroll_content,
            label_text="Step 1: Import Secret Audio (To Encrypt & Hide)",
            file_types=SUPPORTED_SECRET_FORMATS,
            on_change_callback=self._auto_suggest_outputs,
        )
        self.secret_picker.pack(fill="x", padx=10, pady=(2, 6))

        # -------------------------------------------------------------
        # STEP 2: Carrier Audio (Cover Song)
        # -------------------------------------------------------------
        step2_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        step2_card.pack(fill="x", padx=10, pady=(2, 6), ipady=2)

        s2_header = ttk.Frame(step2_card, style="Card.TFrame")
        s2_header.pack(fill="x", padx=10, pady=(6, 2))

        ttk.Label(
            s2_header,
            text="Step 2: Carrier Song (Cover Audio - Lossless WAV)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        btn_auto_wav = ttk.Button(
            s2_header,
            text="✨ Auto-Generate Carrier WAV",
            command=self._generate_default_carrier_wav,
            style="Primary.TButton",
        )
        btn_auto_wav.pack(side="right")

        self.carrier_picker = FilePicker(
            step2_card,
            label_text="",
            file_types=SUPPORTED_CARRIER_FORMATS,
            on_change_callback=self._on_carrier_selected,
        )
        self.carrier_picker.pack(fill="x", padx=4, pady=(0, 2))

        self.carrier_player = AudioPlayer(step2_card)
        self.carrier_player.pack(fill="x", padx=4, pady=(0, 4))

        # -------------------------------------------------------------
        # STEP 3: Key Carrier Image
        # -------------------------------------------------------------
        img_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        img_card.pack(fill="x", padx=10, pady=(2, 6), ipady=2)

        img_header = ttk.Frame(img_card, style="Card.TFrame")
        img_header.pack(fill="x", padx=10, pady=(6, 2))

        ttk.Label(
            img_header,
            text="Step 3: Cover Image (To Steg & Conceal the Generated Decryption Key)",
            style="CardTitle.TLabel"
        ).pack(side="left")

        btn_auto_img = ttk.Button(
            img_header,
            text="✨ Auto-Generate Image",
            command=self._generate_default_image,
            style="Primary.TButton",
        )
        btn_auto_img.pack(side="right")

        self.image_picker = FilePicker(
            img_card,
            label_text="",
            file_types=SUPPORTED_IMAGE_FORMATS,
        )
        self.image_picker.pack(fill="x", padx=4, pady=(0, 4))

        # -------------------------------------------------------------
        # STEP 4: Output Destinations
        # -------------------------------------------------------------
        out_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        out_card.pack(fill="x", padx=10, pady=(2, 10), ipady=2)

        ttk.Label(out_card, text="Step 4: Output Products", style="CardTitle.TLabel").pack(
            anchor="w", padx=10, pady=(6, 2)
        )

        self.out_audio_picker = FilePicker(
            out_card,
            label_text="Output Stego Audio (Cover Song + Encrypted Audio)",
            file_types=[("WAV Audio (*.wav)", "*.wav")],
            is_save_dialog=True,
            default_extension=".wav",
        )
        self.out_audio_picker.pack(fill="x", padx=4, pady=(0, 2))

        self.out_image_picker = FilePicker(
            out_card,
            label_text="Output Stego Key Image (Cover Image + Hidden Cryptographic Key)",
            file_types=[("PNG Image (*.png)", "*.png")],
            is_save_dialog=True,
            default_extension=".png",
        )
        self.out_image_picker.pack(fill="x", padx=4, pady=(0, 4))

    def _on_carrier_selected(self, path: str):
        self.carrier_player.load_audio(path)
        self._auto_suggest_outputs(path)

    def _generate_default_carrier_wav(self):
        dest_dir = os.getcwd()
        sample_wav = os.path.join(dest_dir, "acoustic_carrier_song.wav")
        self.status_label.config(text="Generating 3-minute stereo acoustic carrier WAV...")
        AudioHandler.create_sample_carrier_wav(sample_wav, duration_sec=180)
        self.carrier_picker.set_path(sample_wav)
        self.carrier_player.load_audio(sample_wav)
        self.status_label.config(text="Carrier song generated successfully (~8MB capacity).")
        messagebox.showinfo(
            "Carrier Song Created",
            f"An uncompressed 3-minute stereo carrier WAV song has been generated:\n{sample_wav}\n\n"
            f"Capacity: Over 8 Megabytes (Supports large secret audio payloads)."
        )

    def _generate_default_image(self):
        dest_dir = os.getcwd()
        sample_img = os.path.join(dest_dir, "cover_key_canvas.png")
        ImageSteganography.create_sample_cover_png(sample_img)
        self.image_picker.set_path(sample_img)
        messagebox.showinfo(
            "Cover Image Created",
            f"An optimized 250x250 PNG cover image has been generated:\n{sample_img}"
        )

    def _auto_suggest_outputs(self, _path: str = ""):
        carrier = self.carrier_picker.get_path()
        secret = self.secret_picker.get_path()
        target_dir = os.path.dirname(carrier) if carrier else (os.path.dirname(secret) if secret else os.getcwd())

        if target_dir and os.path.isdir(target_dir):
            if not self.out_audio_picker.get_path():
                self.out_audio_picker.set_path(os.path.join(target_dir, "stego_song.wav"))
            if not self.out_image_picker.get_path():
                self.out_image_picker.set_path(os.path.join(target_dir, "stego_key_image.png"))

    def _start_pipeline(self):
        secret_audio = self.secret_picker.get_path()
        carrier_audio = self.carrier_picker.get_path()
        cover_image = self.image_picker.get_path()
        out_audio = self.out_audio_picker.get_path()
        out_image = self.out_image_picker.get_path()

        # Validation
        if not secret_audio or not os.path.exists(secret_audio):
            messagebox.showerror("Missing Secret Audio", "Please select a valid Secret Audio file.")
            return

        if not carrier_audio or not os.path.exists(carrier_audio):
            messagebox.showerror("Missing Carrier Audio", "Please select a valid Carrier Song (.wav) or click 'Auto-Generate Carrier WAV'.")
            return

        if not cover_image or not os.path.exists(cover_image):
            messagebox.showerror(
                "Missing Cover Image",
                "Please select a cover image or click 'Auto-Generate Image' to create one."
            )
            return

        if not out_audio or not out_image:
            messagebox.showerror("Missing Output Paths", "Please specify output paths for both Stego Audio and Stego Image.")
            return

        valid_cap, cap_err = Validator.validate_embedding_suitability(carrier_audio, secret_audio)
        if not valid_cap:
            messagebox.showerror("Carrier Validation Error", cap_err)
            return

        valid_img, img_err = Validator.validate_image_file(cover_image)
        if not valid_img:
            messagebox.showerror("Image Format Error", img_err)
            return

        self.btn_process.config(state="disabled")
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.progress_bar.start(10)
        self.status_label.config(text="1/3: Generating 256-bit uncrackable key & encrypting secret audio...")

        def worker():
            # 1. Read secret audio bytes
            with open(secret_audio, "rb") as sf:
                secret_raw = sf.read()
            ext = os.path.splitext(secret_audio)[1]

            # 2. Generate cryptographically secure uncrackable key package
            key_package = CryptoEngine.generate_key_package()

            # 3. Encrypt secret audio
            encrypted_audio = CryptoEngine.encrypt_secret_audio(secret_raw, key_package)

            # 4. Steg encrypted audio into carrier song (adaptive multi-bit LSB)
            AudioSteganography.embed_data(
                carrier_wav_path=carrier_audio,
                secret_bytes=encrypted_audio,
                file_extension=ext,
                output_wav_path=out_audio,
                key_id=key_package["key_id"],
                bits_per_sample=0,  # Auto-select optimal bit depth
            )

            # 5. Steg the key package into the cover image
            ImageSteganography.embed_key_in_image_file(
                input_image_path=cover_image,
                key_payload=key_package["packed_bytes"],
                output_image_path=out_image,
            )

            return key_package["key_id"].hex(), len(secret_raw)

        def on_success(result):
            key_id_hex, byte_len = result
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_process.config(state="normal")
            self.status_label.config(text=f"Success! Encrypted {byte_len:,} bytes. Dual stego carriers produced.")
            messagebox.showinfo(
                "Process Completed Successfully!",
                f"✅ Operation Completed Successfully!\n\n"
                f"1. Secret Audio Encrypted ({byte_len:,} bytes) with 256-bit uncrackable key.\n\n"
                f"2. Output Stego Song:\n   -> {out_audio}\n\n"
                f"3. Output Stego Key Image:\n   -> {out_image}\n\n"
                f"Session Pairing Key ID: {key_id_hex}\n\n"
                f"Both files are now saved and ready to share or archive!"
            )

        def on_error(err):
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_process.config(state="normal")
            self.status_label.config(text="Operation failed.")
            messagebox.showerror("Error", str(err))

        run_async(worker, on_success=on_success, on_error=on_error)
