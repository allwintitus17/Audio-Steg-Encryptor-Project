"""Decode View: Responsive scrollable layout with fixed bottom action toolbar.
Extracts key package from Stego Image, extracts encrypted audio from Stego Song,
verifies cryptographic binding, and restores original secret audio.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from utils.config import SUPPORTED_CARRIER_FORMATS, SUPPORTED_IMAGE_FORMATS
from utils.threading_utils import run_async
from gui.styles import COLORS
from gui.components.file_picker import FilePicker
from gui.components.audio_player import AudioPlayer
from core.crypto import CryptoEngine
from core.steganography import AudioSteganography
from core.image_steganography import ImageSteganography

class DecodeView(ttk.Frame):
    """View orchestrating: Stego Image -> Key Extraction -> Stego Song Extraction -> Decryption."""

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

        self.btn_extract = ttk.Button(
            btn_row,
            text="🔓 Extract Key from Image & Decrypt Audio",
            command=self._start_decoding,
            style="Action.TButton",
        )
        self.btn_extract.pack(side="left", padx=(0, 10))

        self.status_label = ttk.Label(btn_row, text="Ready to decrypt", style="Card.TLabel")
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
        # STEP 1: Stego Audio Song
        # -------------------------------------------------------------
        step1_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        step1_card.pack(fill="x", padx=10, pady=(2, 6), ipady=2)

        self.stego_audio_picker = FilePicker(
            step1_card,
            label_text="Step 1: Stego Audio Song (Carrier containing hidden encrypted audio)",
            file_types=SUPPORTED_CARRIER_FORMATS,
            on_change_callback=self._on_stego_audio_selected,
        )
        self.stego_audio_picker.pack(fill="x", padx=4, pady=(2, 2))

        self.stego_player = AudioPlayer(step1_card)
        self.stego_player.pack(fill="x", padx=4, pady=(0, 4))

        # -------------------------------------------------------------
        # STEP 2: Stego Key Image
        # -------------------------------------------------------------
        self.stego_image_picker = FilePicker(
            self.scroll_content,
            label_text="Step 2: Stego Key Image (Image containing concealed decryption key)",
            file_types=SUPPORTED_IMAGE_FORMATS,
        )
        self.stego_image_picker.pack(fill="x", padx=10, pady=(2, 6))

        # -------------------------------------------------------------
        # STEP 3: Destination Folder
        # -------------------------------------------------------------
        dest_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        dest_card.pack(fill="x", padx=10, pady=(2, 6), ipady=2)

        ttk.Label(
            dest_card,
            text="Step 3: Destination Folder for Restored Secret Audio",
            style="CardTitle.TLabel"
        ).pack(anchor="w", padx=10, pady=(6, 2))

        dir_row = ttk.Frame(dest_card, style="Card.TFrame")
        dir_row.pack(fill="x", padx=10, pady=4)

        self.dir_var = tk.StringVar(value=os.getcwd())
        self.dir_entry = ttk.Entry(dir_row, textvariable=self.dir_var)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=3)

        btn_browse_dir = ttk.Button(dir_row, text="Browse Folder...", command=self._browse_dir, style="Primary.TButton")
        btn_browse_dir.pack(side="right")

        # -------------------------------------------------------------
        # RECOVERED AUDIO PREVIEW
        # -------------------------------------------------------------
        rec_card = ttk.Frame(self.scroll_content, style="Card.TFrame")
        rec_card.pack(fill="x", padx=10, pady=(2, 10), ipady=2)

        ttk.Label(rec_card, text="Recovered Audio Preview", style="CardTitle.TLabel").pack(
            anchor="w", padx=10, pady=(4, 2)
        )
        self.recovered_player = AudioPlayer(rec_card)
        self.recovered_player.pack(fill="x", padx=4, pady=(0, 4))

    def _on_stego_audio_selected(self, path: str):
        self.stego_player.load_audio(path)
        if path:
            base_dir = os.path.dirname(path)
            candidate_img = os.path.join(base_dir, "stego_key_image.png")
            if os.path.exists(candidate_img) and not self.stego_image_picker.get_path():
                self.stego_image_picker.set_path(candidate_img)

    def _browse_dir(self):
        selected = filedialog.askdirectory(title="Select Destination Folder")
        if selected:
            self.dir_var.set(selected)

    def _start_decoding(self):
        stego_audio = self.stego_audio_picker.get_path()
        stego_image = self.stego_image_picker.get_path()
        dest_dir = self.dir_var.get()

        if not stego_audio or not os.path.exists(stego_audio):
            messagebox.showerror("Missing Stego Audio", "Please select a valid Stego Audio Song (.wav).")
            return

        if not stego_image or not os.path.exists(stego_image):
            messagebox.showerror("Missing Stego Image", "Please select the Stego Key Image (.png or .bmp).")
            return

        if not os.path.isdir(dest_dir):
            messagebox.showerror("Invalid Directory", "Destination folder does not exist.")
            return

        self.btn_extract.config(state="disabled")
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.progress_bar.start(10)
        self.status_label.config(text="1/3: Extracting cryptographic key package from image...")

        def worker():
            # 1. Extract key package from image
            key_raw = ImageSteganography.extract_key_from_image_file(stego_image)
            key_package = CryptoEngine.unpack_key_package(key_raw)

            # 2. Extract encrypted audio and key_id from stego song
            audio_key_id, encrypted_payload, file_ext = AudioSteganography.extract_data(stego_audio)

            # 3. Cryptographic Binding Check
            if audio_key_id != key_package["key_id"]:
                raise ValueError(
                    f"Pairing Mismatch! This Stego Key Image does not belong to this Stego Audio Song.\n"
                    f"Audio Key ID: {audio_key_id.hex()}\n"
                    f"Image Key ID: {key_package['key_id'].hex()}"
                )

            # 4. Decrypt audio using the session key from image
            decrypted_audio_bytes = CryptoEngine.decrypt_secret_audio(encrypted_payload, key_package)

            # 5. Save restored secret audio
            out_filename = f"restored_secret_audio{file_ext}"
            out_path = os.path.join(dest_dir, out_filename)
            with open(out_path, "wb") as f:
                f.write(decrypted_audio_bytes)

            return out_path, len(decrypted_audio_bytes), key_package["key_id"].hex()

        def on_success(result):
            out_path, byte_count, key_id_hex = result
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_extract.config(state="normal")
            self.status_label.config(text=f"Decryption successful! Restored {byte_count:,} bytes.")
            self.recovered_player.load_audio(out_path)

            messagebox.showinfo(
                "Decryption Successful",
                f"✅ Secret Audio Restored Successfully!\n\n"
                f"Key Verified: {key_id_hex}\n"
                f"Restored File: {out_path}\n"
                f"Size: {byte_count:,} bytes"
            )

        def on_error(err):
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            self.btn_extract.config(state="normal")
            self.status_label.config(text="Decryption failed.")
            messagebox.showerror("Decryption Failed", str(err))

        run_async(worker, on_success=on_success, on_error=on_error)
