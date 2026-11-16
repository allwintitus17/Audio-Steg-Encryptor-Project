"""Native Audio Player preview widget using Python standard library (winsound).

Zero external dependencies - no pygame, no external audio drivers required.
"""

import os
import tkinter as tk
from tkinter import ttk

class AudioPlayer(ttk.Frame):
    """Pure Tkinter Audio Preview component using Python's built-in Windows sound system."""

    def __init__(self, master, **kwargs):
        super().__init__(master, style="Card.TFrame", **kwargs)
        self.current_file = None
        self.is_playing = False
        self._build_ui()

    def _build_ui(self):
        row = ttk.Frame(self, style="Card.TFrame")
        row.pack(fill="x", padx=10, pady=6)

        self.btn_play = ttk.Button(row, text="▶ Play Preview", command=self.play, style="Primary.TButton")
        self.btn_play.pack(side="left", padx=(0, 6))

        self.btn_stop = ttk.Button(row, text="⏹ Stop", command=self.stop, style="Primary.TButton")
        self.btn_stop.pack(side="left", padx=(0, 10))

        self.status_lbl = ttk.Label(row, text="No audio loaded", style="Muted.TLabel")
        self.status_lbl.pack(side="left", fill="x", expand=True)

    def load_audio(self, file_path: str):
        """Prepares an audio file for playback preview."""
        self.stop()
        self.current_file = file_path
        if file_path and os.path.exists(file_path):
            self.status_lbl.config(text=f"Loaded: {os.path.basename(file_path)}")
        else:
            self.status_lbl.config(text="No audio loaded")

    def play(self):
        """Plays the audio asynchronously without freezing Tkinter."""
        if not self.current_file or not os.path.exists(self.current_file):
            self.status_lbl.config(text="Please select a valid audio file first.")
            return

        ext = os.path.splitext(self.current_file)[1].lower()
        if ext == ".wav":
            try:
                import winsound
                winsound.PlaySound(self.current_file, winsound.SND_ASYNC | winsound.SND_FILENAME)
                self.is_playing = True
                self.status_lbl.config(text=f"Playing: {os.path.basename(self.current_file)}")
            except Exception as exc:
                self.status_lbl.config(text=f"Playback error: {exc}")
        else:
            self.status_lbl.config(text="Direct playback preview is supported for .wav audio.")

    def stop(self):
        """Stops ongoing audio playback."""
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
            self.is_playing = False
            if self.current_file:
                self.status_lbl.config(text=f"Stopped: {os.path.basename(self.current_file)}")
        except Exception:
            pass
