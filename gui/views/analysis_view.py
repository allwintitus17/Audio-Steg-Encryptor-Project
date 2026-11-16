"""Analysis View: Audio file inspector, capacity diagnostics, and metadata viewer."""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from utils.config import SUPPORTED_CARRIER_FORMATS
from gui.components.file_picker import FilePicker
from core.audio_handler import AudioHandler

class AnalysisView(ttk.Frame):
    """Screen for inspecting carrier audio properties and calculating maximum secret payload capacity."""

    def __init__(self, master, **kwargs):
        super().__init__(master, style="Main.TFrame", **kwargs)
        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, style="Main.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        self.picker = FilePicker(
            container,
            label_text="Select Carrier Audio File to Analyze",
            file_types=SUPPORTED_CARRIER_FORMATS,
            on_change_callback=self._analyze_file,
        )
        self.picker.pack(fill="x", pady=(0, 15))

        # Card: Analysis Results
        self.result_card = ttk.Frame(container, style="Card.TFrame")
        self.result_card.pack(fill="both", expand=True, ipady=10)

        header = ttk.Label(self.result_card, text="Audio Specifications & Stego Capacity", style="CardTitle.TLabel")
        header.pack(anchor="w", padx=15, pady=(10, 10))

        self.tree = ttk.Treeview(self.result_card, columns=("Property", "Value"), show="headings", height=8)
        self.tree.heading("Property", text="Property")
        self.tree.heading("Value", text="Value")
        self.tree.column("Property", width=220, anchor="w")
        self.tree.column("Value", width=380, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=15, pady=5)

    def _analyze_file(self, file_path: str):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not os.path.exists(file_path):
            return

        try:
            info = AudioHandler.inspect_audio_file(file_path)

            self.tree.insert("", "end", values=("File Name", info["filename"]))
            self.tree.insert("", "end", values=("File Size", f"{info['size_bytes']:,} bytes ({info['size_bytes'] / (1024*1024):.2f} MB)"))
            self.tree.insert("", "end", values=("Audio Format", info["extension"].upper()))

            if info["channels"] is not None:
                self.tree.insert("", "end", values=("Channels", f"{info['channels']} ({'Stereo' if info['channels'] == 2 else 'Mono'})"))
                self.tree.insert("", "end", values=("Sample Rate", f"{info['sample_rate']:,} Hz"))
                self.tree.insert("", "end", values=("Bit Depth", f"{info['bit_depth']}-bit PCM"))
                self.tree.insert("", "end", values=("Duration", f"{info['duration_sec']:.2f} seconds"))

                # Capacities
                cap_1bit = AudioHandler.calculate_embedding_capacity(file_path, bits_per_sample=1)
                self.tree.insert("", "end", values=("Max Secret Payload (1-bit LSB)", f"{cap_1bit:,} bytes (~{cap_1bit / 1024:.1f} KB)"))
                self.tree.insert("", "end", values=("Audio Fidelity Impact", "Imperceptible (Preserves original acoustics)"))
            else:
                self.tree.insert("", "end", values=("Status", "Compressed format; convert to lossless WAV for LSB embedding."))

        except Exception as exc:
            messagebox.showerror("Analysis Error", str(exc))
