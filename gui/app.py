"""Main Application Window & Navigation Controller."""

import tkinter as tk
from tkinter import ttk

from utils.config import APP_NAME, APP_VERSION
from gui.styles import apply_app_styles, COLORS
from gui.views.encode_view import EncodeView
from gui.views.decode_view import DecodeView
from gui.views.analysis_view import AnalysisView

class AudioStegoApp(tk.Tk):
    """Root Application Window managing views and tabs."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - v{APP_VERSION}")
        self.geometry("880x680")
        self.minsize(740, 500)
        self.configure(bg=COLORS["bg_main"])

        # Setup styling
        self.style = apply_app_styles(self)

        self._build_header()
        self._build_tabs()
        self._build_footer()

    def _build_header(self):
        header_frame = ttk.Frame(self, style="Main.TFrame")
        header_frame.pack(fill="x", padx=20, pady=(12, 4))

        title_label = tk.Label(
            header_frame,
            text=APP_NAME,
            font=("Segoe UI", 16, "bold"),
            bg=COLORS["bg_main"],
            fg=COLORS["accent_primary"],
        )
        title_label.pack(anchor="w")

        subtitle = tk.Label(
            header_frame,
            text="Dual-Carrier Steganography: Encrypted Audio into Song + Cryptographic Key into Image",
            font=("Segoe UI", 9),
            bg=COLORS["bg_main"],
            fg=COLORS["fg_muted"],
        )
        subtitle.pack(anchor="w")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=8)

        # Tab 1: Encode View
        self.encode_tab = EncodeView(self.notebook)
        self.notebook.add(self.encode_tab, text=" 🔒 Encrypt & Hide (Audio + Image) ")

        # Tab 2: Decode View
        self.decode_tab = DecodeView(self.notebook)
        self.notebook.add(self.decode_tab, text=" 🔓 Extract & Decrypt (Audio + Image) ")

        # Tab 3: Analysis View
        self.analysis_tab = AnalysisView(self.notebook)
        self.notebook.add(self.analysis_tab, text=" 📊 Audio Capacity & Info ")

    def _build_footer(self):
        footer_frame = ttk.Frame(self, style="Main.TFrame")
        footer_frame.pack(fill="x", side="bottom", padx=20, pady=4)

        lbl = tk.Label(
            footer_frame,
            text=f"Dual-Carrier Stego Engine Active | v{APP_VERSION} | Pure Tkinter & Standard Library",
            font=("Segoe UI", 8),
            bg=COLORS["bg_main"],
            fg=COLORS["fg_muted"],
        )
        lbl.pack(side="left")
